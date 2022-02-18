def test_get_account_not_logged_in(api_client, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 401


def test_get_account_subaccounts_not_logged_in(api_client, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    response = api_client.get("/v1/accounts/%s/children/" % account.pk)
    assert response.status_code == 401


def test_get_budget_account_with_public_token(api_client, create_budget,
        create_public_token, create_budget_account):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    public_token = create_public_token(instance=budget)
    api_client.include_public_token(public_token)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200


def test_get_template_account_with_public_token(api_client, create_template,
        create_public_token, create_template_account):
    budget = create_template()
    account = create_template_account(parent=budget)
    public_token = create_public_token(instance=budget)
    api_client.include_public_token(public_token)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 401


def test_get_another_user_account(api_client, budget_f, user, admin_user):
    budget = budget_f.create_budget(created_by=admin_user)
    account = budget_f.create_account(parent=budget)
    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 403


def test_get_public_budget_account_subaccounts(api_client, create_budget,
        create_public_token, create_budget_account):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    public_token = create_public_token(instance=budget)
    api_client.include_public_token(public_token)
    response = api_client.get("/v1/accounts/%s/children/" % account.pk)
    assert response.status_code == 200


def test_get_another_public_budget_account_subaccounts(api_client, create_budget,
        create_public_token, create_budget_account):
    budget = create_budget()
    another_budget = create_budget()
    another_account = create_budget_account(parent=another_budget)
    public_token = create_public_token(instance=budget)
    api_client.include_public_token(public_token)
    response = api_client.get("/v1/accounts/%s/children/" % another_account.pk)
    assert response.status_code == 401


def test_get_template_account_subaccounts_with_public_token(api_client,
        create_template, create_template_account, create_public_token):
    budget = create_template()
    account = create_template_account(parent=budget)
    public_token = create_public_token(instance=budget)
    api_client.include_public_token(public_token)
    response = api_client.get("/v1/accounts/%s/children/" % account.pk)
    assert response.status_code == 401


def test_get_public_budget_account(api_client, create_budget,
        create_public_token, create_budget_account):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    public_token = create_public_token(instance=budget)
    api_client.include_public_token(public_token)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200


def test_get_another_public_budget_account(api_client, create_budget,
        create_public_token, create_budget_account):
    budget = create_budget()
    another_budget = create_budget()
    account = create_budget_account(parent=another_budget)
    public_token = create_public_token(instance=budget)
    api_client.include_public_token(public_token)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 401


def test_update_public_budget_account(api_client, create_budget,
        create_public_token, create_budget_account):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    public_token = create_public_token(instance=budget)
    api_client.include_public_token(public_token)

    response = api_client.post("/v1/accounts/%s/" % account.pk, data={
        'identifier': 'New Identifier'
    })
    assert response.status_code == 401


def test_get_permissioned_account(api_client, user, budget_df):
    budgets = [budget_df.create_budget(), budget_df.create_budget()]
    account = budget_df.create_account(parent=budgets[1])
    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 403
    assert response.json() == {'errors': [{
        'message': "The user's subscription does not support multiple budgets.",
        'code': 'product_permission_error',
        'error_type': 'permission',
        'products': '__any__',
        'permission_id': 'multiple_budgets'
    }]}
