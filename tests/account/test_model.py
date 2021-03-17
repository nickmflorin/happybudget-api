from greenbudget.app.account.models import Account
from greenbudget.app.history.models import FieldAlterationEvent


def test_field_changes(create_budget, user):
    budget = create_budget()
    # account = Account.objects.create(
    #     description="Description",
    #     identifier="Identifier",
    #     budget=budget
    # )
    account = Account(
        description="Description",
        identifier="Identifier",
        budget=budget,
        updated_by=user
    )
    account.save()
    account.description = "New Description"
    account.save()
    # assert FieldAlterationEvent.objects.count() == 0
    import ipdb
    ipdb.set_trace()
