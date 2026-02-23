from django.contrib import admin
from .models import User,EmailVerificationToken, Payment, BankAccount, UserBill,UserToken
# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'rank', 'user_name', 'email', 'role', 'role_accepted', 'distributor', 'delivery_staff')
    search_fields = ('user_id', 'user_name', 'email')
    list_filter = ('role', 'distributor', 'delivery_staff')
    ordering = ('-created',)

    def save_model(self, request, obj, form, change):
        if form.cleaned_data.get('password') and not obj.password.startswith('pbkdf2_'):
            obj.set_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)

admin.site.register(EmailVerificationToken)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id','user','amount','created']
    list_filter = ('user',)
    ordering = ('-created',)

admin.site.register(BankAccount)

@admin.register(UserBill)
class UserBillAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created','type')
    list_filter = ('user', 'type', 'created')


@admin.register(UserToken)
class UserTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created','modified')
    list_filter = ('user', 'created')
    search_fields = ('user__user_id','user__email')
