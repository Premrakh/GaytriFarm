from django.contrib import admin
from .models import User,UserProfile,EmailVerificationToken
# Register your models here.
class UserAdmin(admin.ModelAdmin):
    # Show these fields in the list view
    list_display = (
        "user_id",
        "user_name",
        "email",
        "role",
        "role_accepted",
        "distributor",
        "delivery_staff",
        "is_active",
        "is_staff",
        "is_superuser",
        "is_registered",
        "is_email_verified",
        "allow_notification",
    )

    # Fields you can search by
    search_fields = ("user_name", "email", "user_id")

    # Default ordering
    ordering = ("-user_id",)

    # Group fields in admin detail view
    fieldsets = (
        ("Identification", {"fields": ("user_id", "user_name", "email")}),
        ("Roles", {"fields": ("role", "role_accepted", "distributor", "delivery_staff")}),
        ("Status Flags", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "is_registered",
                "is_email_verified",
            )
        }),
        ("Notifications", {"fields": ("fcm_token", "allow_notification")}),
        ("Authentication", {"fields": ("password", "reset_password_token")}),
    )

    # Fields shown when creating a new user
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("user_name", "email", "password1", "password2", "role"),
        }),
    )    

    readonly_fields = ("user_id",)

admin.site.register(User,UserAdmin)
admin.site.register(UserProfile)
admin.site.register(EmailVerificationToken)
