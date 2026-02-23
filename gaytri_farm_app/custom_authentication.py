from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from user.models import UserToken


class CustomAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that extends the built-in JWTAuthentication
    to also verify that the token matches the stored UserToken for the user.

    This ensures that only the most recently issued token is valid,
    effectively implementing single-session / token-revocation support.
    """

    def authenticate(self, request):
        # First, perform the standard JWT authentication
        result = super().authenticate(request)

        # If standard JWT auth returned None (no token provided), skip
        if result is None:
            return None

        user, validated_token = result

        # Check if the user has a stored UserToken and if it matches
        if not UserToken.objects.filter(user=user, access_token=str(validated_token)).exists():
            raise AuthenticationFailed({
                "success": False,
                "code": "token_not_exist",
                "message": "Authentication token not exist.",
            }) 

        return (user, validated_token)
