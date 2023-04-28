# pylint: disable=redefined-outer-name
from datetime import timedelta, datetime
import mock

import pytest
from django.test import override_settings

from happybudget.lib.utils.dateutils import api_datetime_string
from happybudget.app.authentication.tokens import AccessToken
from happybudget.app.user.mail import get_template, Mail


@pytest.fixture
def validate_email_token(api_client, user):
    def inner():
        token = AccessToken.for_user(user)
        return api_client.post(
            "/v1/auth/validate-email-verification-token/",
            data={"token": str(token)}
        )
    return inner


@pytest.mark.freeze_time('2020-01-01')
@override_settings(EMAIL_VERIFICATION_ENABLED=True, EMAIL_ENABLED=True)
def test_validate_email_token(validate_email_token, unverified_user):
    response = validate_email_token()
    assert response.status_code == 201
    unverified_user.refresh_from_db()
    assert unverified_user.is_verified
    assert response.json() == {
        'id': unverified_user.pk,
        'first_name': unverified_user.first_name,
        'last_name': unverified_user.last_name,
        'full_name': unverified_user.full_name,
        'email': unverified_user.email,
        'is_active': unverified_user.is_active,
        'is_superuser': unverified_user.is_superuser,
        'is_staff': unverified_user.is_staff,
        "company": unverified_user.company,
        "position": unverified_user.position,
        "address": unverified_user.address,
        "phone_number": unverified_user.phone_number,
        'date_joined': api_datetime_string(unverified_user.date_joined),
        'last_login': None,
        'timezone': str(unverified_user.timezone),
        "profile_image": None,
        "is_first_time": False,
        "product_id": None,
        "billing_status": None,
        "metrics": {
            "num_budgets": 0,
            "num_templates": 0,
            "num_collaborating_budgets": 0,
            "num_archived_budgets": 0
        }
    }


@pytest.mark.freeze_time('2021-01-03')
@override_settings(
    ACCESS_TOKEN_LIFETIME=timedelta(hours=24),
    EMAIL_VERIFICATION_ENABLED=True,
    EMAIL_ENABLED=True
)
def test_verify_email_expired_token(api_client, unverified_user):
    token = AccessToken.for_user(unverified_user)
    token.set_exp(claim='exp', from_time=datetime(2021, 1, 1))
    response = api_client.post(
        "/v1/auth/validate-email-verification-token/",
        data={"token": str(token)}
    )
    assert response.json() == {
        'errors': [{
            'message': 'Token is expired.',
            'code': 'token_expired',
            'user_id': unverified_user.id,
        }]
    }


@pytest.mark.freeze_time('2020-01-01')
@override_settings(EMAIL_VERIFICATION_ENABLED=True, EMAIL_ENABLED=True)
def test_validate_email_token_inactive_user(inactive_user, validate_email_token):
    inactive_user.is_verified = False
    inactive_user.save()
    response = validate_email_token()
    assert response.status_code == 403
    assert response.json() == {
        'errors': [{
            'message': 'The account is not active.',
            'code': 'account_disabled',
            'user_id': inactive_user.pk,
        }]
    }


@override_settings(EMAIL_VERIFICATION_ENABLED=True, EMAIL_ENABLED=True)
def test_validate_email_token_user_logged_in(validate_email_token, api_client,
        user):
    api_client.force_login(user)
    response = validate_email_token()
    assert response.status_code == 403
    assert response.json() == {
        'errors': [{
            'message': 'User already has an active session.',
            'code': 'permission_error',
        }]
    }


@override_settings(EMAIL_VERIFICATION_ENABLED=True, EMAIL_ENABLED=True)
def test_validate_email_token_missing_token(api_client):
    response = api_client.post("/v1/auth/validate-email-verification-token/")
    assert response.status_code == 403


@override_settings(EMAIL_VERIFICATION_ENABLED=True, EMAIL_ENABLED=True)
def test_validate_email_token_invalid_token(api_client):
    response = api_client.post(
        "/v1/auth/validate-email-verification-token/",
        data={"token": "hoopla"}
    )
    assert response.status_code == 403
    assert response.json() == {
        'errors': [{
            'message': 'Token is invalid.',
            'code': 'token_not_valid',
        }]
    }


@override_settings(
    EMAIL_ENABLED=True,
    EMAIL_VERIFICATION_ENABLED=True,
    FROM_EMAIL="noreply@happybudget.io",
    FRONTEND_URL="https://app.happybudget.io"
)
def test_send_verification_email(api_client, unverified_user):
    # Use another user to generate the Access Token for mock purposes.
    token = AccessToken.for_user(unverified_user)

    def create_token(user):
        return token

    with mock.patch.object(AccessToken, 'for_user', create_token):
        with mock.patch.object(Mail, 'send', autospec=True) as m:
            response = api_client.post("/v1/auth/verify-email/", data={
                "user": unverified_user.pk
            })
    assert response.status_code == 201

    assert m.called
    mail_obj = m.call_args[0][0]
    assert mail_obj.to == [{'email': unverified_user.email}]
    assert mail_obj.template_id == get_template("email_verification").id
    assert mail_obj.params == {
        'redirect_url': (
            'https://app.happybudget.io/verify?token=%s' % str(token)
        )
    }


@override_settings(EMAIL_VERIFICATION_ENABLED=True, EMAIL_ENABLED=True)
def test_send_verification_email_verified_user(api_client, user):
    with mock.patch.object(Mail, 'send') as m:
        response = api_client.post("/v1/auth/verify-email/", data={
            "user": user.pk
        })
    assert response.status_code == 400
    assert not m.called


@override_settings(EMAIL_VERIFICATION_ENABLED=True, EMAIL_ENABLED=True)
def test_send_verification_email_inactive_user(api_client, inactive_user):
    with mock.patch.object(Mail, 'send') as m:
        response = api_client.post("/v1/auth/verify-email/", data={
            "user": inactive_user.pk
        })
    assert response.status_code == 400
    assert not m.called
