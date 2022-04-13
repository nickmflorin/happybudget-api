from django import forms

from greenbudget import harry
from .models import User


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'


class UserAdmin(harry.HarryModelAdmin):
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
    row_actions = [
        harry.RowAction(
            name='send_email_verification',
            title='Send Email Verification'
        ),
        harry.RowAction(
            name='send_forgot_password',
            title='Send Forgot Password'
        )
    ]
    form = UserAdminForm

    def send_email_verification(self, request, instance_id):
        self.message_user(
            request,
            "This feature is currently being built.",
            level="warning"
        )

    def send_forgot_password(self, request, instance_id):
        self.message_user(
            request,
            "This feature is currently being built.",
            level="warning"
        )


harry.site.register(User, UserAdmin)
