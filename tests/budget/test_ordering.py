def test_create_account_with_order(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    accounts = budget_f.create_accounts(parent=budget, count=20)

    api_client.force_login(user)
    response = api_client.post(
        "/v1/%ss/%s/accounts/" % (budget_f.context, budget.pk),
        data={
            'identifier': 'new_account',
            'order': 5
        })
    assert response.status_code == 201
    accounts = models.Account.objects.filter(parent=budget).all()
    assert accounts[5].identifier == 'new_account'
