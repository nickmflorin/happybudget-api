import mock
import plaid

from happybudget.app.integrations.plaid.api import client


def test_create_link_token(api_client, user, monkeypatch):
    def mock_link_token_create(*args, **kwargs):
        response = mock.MagicMock()
        response.link_token = '5032t5'
        return response

    monkeypatch.setattr(client, 'link_token_create', mock_link_token_create)

    api_client.force_login(user)
    response = api_client.post("/v1/integrations/plaid/link-token/")
    assert response.status_code == 201
    assert response.json() == {'link_token': '5032t5'}


def test_create_link_token_plaid_error(api_client, user, monkeypatch):
    def mock_link_token_create(*args, **kwargs):
        raise plaid.ApiException("There was an error.")

    monkeypatch.setattr(client, 'link_token_create', mock_link_token_create)

    api_client.force_login(user)
    response = api_client.post("/v1/integrations/plaid/link-token/")
    assert response.status_code == 400
    assert response.json() == {'errors': [{
        'message': 'There was an error creating the link token.',
        'code': 'plaid_request_error',
        'error_type': 'bad_request'
    }]}
