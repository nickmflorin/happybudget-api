import mock
from django.test import override_settings

from greenbudget.app.user.mail import get_template


@override_settings(
    EMAIL_ENABLED=True,
    FROM_EMAIL="noreply@greenbudget.io",
    FRONTEND_URL="https://app.greenbudget.io"
)
def test_approve_user(unapproved_user):
    unapproved_user.is_approved = True
    with mock.patch('greenbudget.app.user.mail.send_mail') as m:
        unapproved_user.save()

    assert m.called
    mail_obj = m.call_args[0][0]
    assert mail_obj.get() == {
        'from': {'email': "noreply@greenbudget.io"},
        'template_id': get_template("post_activation").id,
        'personalizations': [
            {
                'to': [{'email': unapproved_user.email}],
                'dynamic_template_data': {
                    'redirect_url': 'https://app.greenbudget.io/login'
                }
            }
        ]
    }
