from rest_framework.views import exception_handler
from gaytri_farm_app.utils import wrap_response
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated,PermissionDenied,ValidationError
from django.conf import settings
import jwt
import time

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        if isinstance(exc, AuthenticationFailed):
            try:
                request = context.get('request')
                token = request.headers.get('Authorization', '').split(' ')[-1]
                access_token = jwt.decode(token,settings.SECRET_KEY,algorithms=["HS256"],options={"verify_exp": False})
                exp_timestamp = access_token['exp']
                now_timestamp = time.time()
                if exp_timestamp <= now_timestamp:
                    return wrap_response(
                        success=False,
                        code="expired_token",
                        errors=[{"field": "token", "message": "Expired token."}],
                        status_code=response.status_code if response else 401
                    )
                return wrap_response(
                    success=False,
                    code="invalid_token",
                    errors=[{"field": "token", "message": "Invalid token."}],
                    status_code=response.status_code if response else 401
                )
            except:
                return wrap_response(
                    success=False,
                    code="invalid_token",
                    errors=[{"field": "token", "message": "Invalid token."}],
                    status_code=response.status_code if response else 401
                )
        if isinstance(exc, NotAuthenticated):
            return wrap_response(
                success=False,
                code="access_token_missing",
                errors=[{"field": "token", "message": "Authentication credentials were not provided."}],
                status_code=response.status_code if response else 401
            )
    if isinstance(exc, PermissionDenied):
        error_detail = exc.detail if hasattr(exc, 'detail') else "Permission Denied"
        data={}
        if isinstance(error_detail,dict):
            data=error_detail.get('data')
        if data is not None:
            message=error_detail.get('message')
            return wrap_response(
                success=False,
                code="permission_denied",
                data=data,
                message=message,
                status_code= 200
            )
        return wrap_response(
            success=False,
            code="invalid_token",
            status_code= 200
        )
    if isinstance(exc, ValidationError):
        message="validation_error"
        # if isinstance(exc.detail, dict):
        #     if len(exc.detail) == 1:
        #         for k, v in exc.detail.items():
        #             try:
        #                 message = v[0].code
        #             except:
        #                 pass
        errors = [{"field": k, "message": v[0]} for k, v in response.data.items()]
        
        return wrap_response(
            success=False,
            code=message,
            errors=errors,
            status_code=response.status_code if response else 400
        )
    if response is not None:
        message = "An_error_occurred"
        if isinstance(response.data, dict):
            errors = [{"field": k, "message": v[0].__str__() if isinstance(v, list) and len(v) > 0 else str(v)} for k, v in response.data.items()]
        else:
            errors = [{"field": "", "message": str(response.data)}]
        return wrap_response(success=False, code=message, errors=errors, status_code=response.status_code)
    return wrap_response(success=False, code="An_unknown_error_occurred",message=str(exc),errors=[], status_code=500)
