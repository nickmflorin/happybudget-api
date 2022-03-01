import pytest


@pytest.mark.postgresdb
@pytest.mark.django_db(transaction=True)
def test_bulk_create_subaccount_subaccounts_concurrently(api_client, user,
        budget_f, test_concurrently):

    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    budget_f.create_subaccount(count=2, parent=subaccount)
    api_client.force_login(user)

    @test_concurrently(2)
    def perform_request():
        return api_client.patch(
            "/v1/subaccounts/%s/bulk-create-children/" % subaccount.pk,
            format='json',
            data={'data': [
                {
                    'multiplier': 2,
                    'quantity': 2,
                    'rate': 5
                },
                {
                    'multiplier': 2,
                    'quantity': 2,
                    'rate': 5
                }
            ]})

    responses = perform_request()
    response_order = [
        [obj['order'] for obj in r.json()['children']] for r in responses]
    # There are two possible response orders, depending on which request
    # executed first.  We cannot safely assert that the response order is
    # a specific one, because the timing surrounding the threads results in
    # the order that the responses are received not being deterministic.  We
    # can however assert that the response order is one of the expected forms.
    assert len(response_order) == 2
    assert ['w', 'y'] in response_order and ['yn', 'ynt'] in response_order
