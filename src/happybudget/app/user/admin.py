from django import forms
from django.conf import settings

from happybudget import harry

from .exceptions import EmailError
from .models import User


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'


class UserAdmin(harry.HarryModelAdmin):
    # Note: We may have to remove the `billing_status` and `product_id` fields
    # from the list_display because it will submit an API request to Stripe for
    # each user displayed in the table.
    base_list_display = (
        "first_name", "last_name", "email", "created_at", "last_login",
        "is_staff", "is_superuser", "billing_status", "product_id")
    fieldsets = (
        ('Profile info', {
            'fields': (
                'first_name', 'last_name', 'position', 'company',
                'address', 'phone_number', 'timezone', 'profile_image')
        }),
        ('Restrictions & Permissions', {
            'fields': (
                'is_superuser', 'is_staff', 'is_verified',
                'is_first_time'
            )
        }),
    )
    form = UserAdminForm

    @property
    def row_actions(self):
        actions = []
        if settings.EMAIL_ENABLED:
            actions += [harry.RowAction(
                name='send_forgot_password',
                title='Send Forgot Password'
            )]
            if settings.EMAIL_VERIFICATION_ENABLED:
                actions += [harry.RowAction(
                    name='send_email_verification',
                    title='Send Email Verification',
                    disabled=lambda user: user.email_is_verified
                )]
        return actions

    def send_email_verification(self, request, instance_id):
        user = User.objects.get(pk=instance_id)
        try:
            user.send_email_verification_email()
        except EmailError:
            self.message_user(
                request=request,
                message="There was an error communicating with the email API.",
                level="error"
            )
        else:
            self.message_user(
                request=request,
                message=f"Email successfully sent to {user.email}.",
                level="success"
            )

    def send_forgot_password(self, request, instance_id):
        user = User.objects.get(pk=instance_id)
        try:
            user.send_password_recovery_email()
        except EmailError:
            self.message_user(
                request=request,
                message="There was an error communicating with the email API.",
                level="error"
            )
        else:
            self.message_user(
                request=request,
                message=f"Email successfully sent to {user.email}.",
                level="success"
            )


harry.site.register(User, UserAdmin)
