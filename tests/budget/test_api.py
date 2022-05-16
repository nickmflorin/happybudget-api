from botocore import exceptions

from django.test import override_settings
import pytest

from happybudget.app.io.serializers import ImageFileFieldSerializer


@pytest.mark.freeze_time('2020-01-01')
@override_settings(
    BILLING_ENABLED=True,
    APP_URL="https://api.happybudget.io"
)
def test_get_budgets(api_client, user, f, test_uploaded_file, admin_user):
    image_files = [
        test_uploaded_file("budget1.jpeg"),
        test_uploaded_file("budget2.jpeg")
    ]
    budgets = f.create_budget(count=2, image_array=image_files)

    # Add additional budgets created by another use to ensure that those are
    # not included in the response.
    f.create_budget(count=2, created_by=admin_user)
    # Add additional archived budgets to ensure that those are not included in
    # the response.
    f.create_budget(count=2, created_by=user, archived=True)

    api_client.force_login(user)
    response = api_client.get("/v1/budgets/")
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": budgets[0].pk,
            "name": budgets[0].name,
            "type": "budget",
            "domain": "budget",
            "updated_at": "2020-01-01 00:00:00",
            "is_permissioned": False,
            "image": {
                "url": (
                    f"https://api.happybudget.io/media/users/{user.pk}"
                    "/budgets/budget1.jpeg"
                ),
                "size": 823,
                "width": 100,
                "height": 100,
                "extension": "jpeg"
            },
            "updated_by": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email
            }
        },
        {
            "id": budgets[1].pk,
            "name": budgets[1].name,
            "type": "budget",
            "domain": "budget",
            "updated_at": "2020-01-01 00:00:00",
            "is_permissioned": True,
            "image": {
                "url": (
                    f"https://api.happybudget.io/media/users/{user.pk}"
                    "/budgets/budget2.jpeg"
                ),
                "size": 823,
                "width": 100,
                "height": 100,
                "extension": "jpeg"
            },
            "updated_by": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email
            }
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
@override_settings(BILLING_ENABLED=True, APP_URL="https://api.happybudget.io")
@pytest.mark.parametrize('exc_cls', [
    exceptions.ClientError({}, 'PUT'),
    FileNotFoundError()
])
def test_get_budgets_image_not_found(api_client, user, budget_f, monkeypatch,
        test_uploaded_file, exc_cls):
    image_files = [
        test_uploaded_file("budget1.jpeg"),
        test_uploaded_file("budget2.jpeg")
    ]
    budget_f.create_budget(image_array=image_files, count=2)

    @property
    def data(instance):
        raise exc_cls

    # If there is a problem finding the image, the exception will be raised
    # when the serializer `.data` property is accessed, since this will trigger
    # accessing of the `size`, `width` and `height` params - which require
    # reading the file from the filesystem.
    monkeypatch.setattr(ImageFileFieldSerializer, 'data', data)

    api_client.force_login(user)

    response = api_client.get(f"/v1/{budget_f.domain}s/")
    assert response.status_code == 200
    # Instead of returning the URL of the image that does not exist in the
    # filesystem, or returning the serialized image object with all attributes
    # except the `url` being `None`, we need to make sure that if the image
    # cannot be found, it is not included in the response.
    assert response.json()['data'][0]['image'] is None
    assert response.json()['data'][1]['image'] is None


@pytest.mark.freeze_time('2020-01-01')
@override_settings(BILLING_ENABLED=True)
def test_get_archived_budgets(api_client, user, admin_user, f):
    archived_budgets = f.create_budget(count=2, archived=True)
    # Add additional budgets created by another use to ensure that those are
    # not included in the response.
    f.create_budget(count=2, created_by=admin_user, archived=True)
    # Add additional non-archived budgets to ensure that those are not included
    # in the response.
    f.create_budget(count=2, created_by=user)
    api_client.force_login(user)
    response = api_client.get("/v1/budgets/archived/")
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": archived_budgets[0].pk,
            "name": archived_budgets[0].name,
            "type": "budget",
            "domain": "budget",
            "image": None,
            "updated_at": "2020-01-01 00:00:00",
            "is_permissioned": False,
            "updated_by": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email
            }
        },
        {
            "id": archived_budgets[1].pk,
            "name": archived_budgets[1].name,
            "type": "budget",
            "domain": "budget",
            "image": None,
            "updated_at": "2020-01-01 00:00:00",
            "is_permissioned": True,
            "updated_by": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email
            }
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_collaborating_budgets(api_client, f):
    users = f.create_user(count=4)
    budgets = f.create_budget(count=4, created_by_array=users)
    # The second budget cannot have a collaborator assigned as the second user
    # because the second user will be registered as the creator of the second
    # budget.
    _ = [
        f.create_collaborator(instance=budgets[0], user=users[1]),
        f.create_collaborator(instance=budgets[2], user=users[1]),
        f.create_collaborator(instance=budgets[3], user=users[1]),
    ]
    api_client.force_login(users[1])
    response = api_client.get("/v1/budgets/collaborating/")
    assert response.status_code == 200
    assert response.json()['count'] == 3
    assert response.json()['data'] == [
        {
            "id": budgets[0].pk,
            "name": budgets[0].name,
            "type": "budget",
            "domain": "budget",
            "image": None,
            "updated_at": "2020-01-01 00:00:00",
            "updated_by": {
                "id": users[0].id,
                "first_name": users[0].first_name,
                "last_name": users[0].last_name,
                "full_name": users[0].full_name,
                "email": users[0].email
            }
        },
        {
            "id": budgets[2].pk,
            "name": budgets[2].name,
            "type": "budget",
            "domain": "budget",
            "image": None,
            "updated_at": "2020-01-01 00:00:00",
            "updated_by": {
                "id": users[2].id,
                "first_name": users[2].first_name,
                "last_name": users[2].last_name,
                "full_name": users[2].full_name,
                "email": users[2].email
            }
        },
        {
            "id": budgets[3].pk,
            "name": budgets[3].name,
            "type": "budget",
            "domain": "budget",
            "image": None,
            "updated_at": "2020-01-01 00:00:00",
            "updated_by": {
                "id": users[3].id,
                "first_name": users[3].first_name,
                "last_name": users[3].last_name,
                "full_name": users[3].full_name,
                "email": users[3].email
            }
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget(api_client, user, f):
    budget = f.create_budget()
    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": budget.pk,
        "name": budget.name,
        "updated_at": "2020-01-01 00:00:00",
        "nominal_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "type": "budget",
        "domain": "budget",
        "image": None,
        "is_permissioned": False,
        "public_token": None,
        "updated_by": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "email": user.email
        }
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_budget(api_client, user, f):
    budget = f.create_budget()
    api_client.force_login(user)
    response = api_client.patch("/v1/budgets/%s/" % budget.pk, data={
        "name": "New Name"
    })
    assert response.status_code == 200
    budget.refresh_from_db()
    assert budget.name == "New Name"
    assert response.json() == {
        "id": budget.pk,
        "name": "New Name",
        "updated_at": "2020-01-01 00:00:00",
        "nominal_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "type": "budget",
        "domain": "budget",
        "image": None,
        "is_permissioned": False,
        "public_token": None,
        "updated_by": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "email": user.email
        }
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget(api_client, user, models):
    api_client.force_login(user)
    response = api_client.post("/v1/budgets/", data={"name": "Test Name"})
    assert response.status_code == 201
    budget = models.Budget.objects.first()
    assert budget is not None
    assert response.json() == {
        "id": budget.pk,
        "name": budget.name,
        "updated_at": "2020-01-01 00:00:00",
        "nominal_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "type": "budget",
        "domain": "budget",
        "image": None,
        "is_permissioned": False,
        "public_token": None,
        "updated_by": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "email": user.email
        }
    }


@pytest.mark.freeze_time('2020-01-01')
def test_derive_budget(api_client, user, f, staff_user, models):
    template = f.create_template(created_by=staff_user)
    api_client.force_login(user)
    response = api_client.post("/v1/budgets/", data={
        "name": "Test Name",
        "production_type": 1,
        "template": template.pk,
    })
    assert response.status_code == 201
    assert models.Budget.objects.count() == 1
    budget = models.Budget.objects.all()[0]
    assert response.json() == {
        "id": budget.pk,
        "name": "Test Name",
        "updated_at": "2020-01-01 00:00:00",
        "nominal_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "type": "budget",
        "domain": "budget",
        "image": None,
        "is_permissioned": False,
        "public_token": None,
        "updated_by": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "email": user.email
        }
    }


@pytest.mark.freeze_time('2020-01-01')
# Note: If billing is not enabled, the value of `is_perissioned` in the response
# will always be True.
@override_settings(BILLING_ENABLED=True)
def test_duplicate_budget(api_client, standard_product_user, f, models):
    original = f.create_budget(created_by=standard_product_user)
    api_client.force_login(standard_product_user)
    response = api_client.post("/v1/budgets/%s/duplicate/" % original.pk)
    assert response.status_code == 201
    assert models.Budget.objects.count() == 2
    budget = models.Budget.objects.all()[1]
    assert response.json() == {
        "id": budget.pk,
        "name": original.name,
        "updated_at": "2020-01-01 00:00:00",
        "nominal_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "type": "budget",
        "domain": "budget",
        "image": None,
        "is_permissioned": False,
        "public_token": None,
        "updated_by": {
            "id": standard_product_user.id,
            "first_name": standard_product_user.first_name,
            "last_name": standard_product_user.last_name,
            "full_name": standard_product_user.full_name,
            "email": standard_product_user.email
        }
    }


def test_duplicate_archived_budget(api_client, standard_product_user, f):
    original = f.create_budget(created_by=standard_product_user, archived=True)
    api_client.force_login(standard_product_user)
    response = api_client.post("/v1/budgets/%s/duplicate/" % original.pk)
    assert response.status_code == 400
    assert response.json() == {'errors': [{
        'message': 'Duplicating archived budgets is not permitted.',
        'code': 'bad_request',
        'error_type': 'bad_request'
    }]}


def test_delete_budget(api_client, user, models, f):
    budget = f.create_budget()
    accounts = [
        f.create_budget_account(parent=budget),
        f.create_budget_account(parent=budget),
        f.create_budget_account(parent=budget)
    ]
    f.create_budget_subaccount(count=6, parent=accounts[0])
    f.create_budget_subaccount(count=6, parent=accounts[1])
    f.create_budget_subaccount(count=6, parent=accounts[2])

    api_client.force_login(user)
    response = api_client.delete("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 204
    assert models.Budget.objects.count() == 0
    assert models.Account.objects.count() == 0
    assert models.SubAccount.objects.count() == 0


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_pdf(api_client, user, f):
    budget = f.create_budget()
    budget_markups = [f.create_markup(parent=budget)]
    account = f.create_budget_account(parent=budget, markups=budget_markups)
    account_markups = [f.create_markup(parent=account)]
    subaccount = f.create_budget_subaccount(
        parent=account,
        markups=account_markups
    )
    subaccounts = [
        f.create_budget_subaccount(parent=subaccount),
        f.create_budget_subaccount(parent=subaccount)
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/pdf/" % budget.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": budget.pk,
        "name": budget.name,
        "groups": [],
        "nominal_value": 0.0,
        "type": "pdf-budget",
        "domain": "budget",
        "accumulated_markup_contribution": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "actual": 0.0,
        "children_markups": [{
            "id": budget_markups[0].pk,
            "type": "markup",
            "identifier": budget_markups[0].identifier,
            "description": budget_markups[0].description,
            "rate": budget_markups[0].rate,
            "actual": 0.0,
            "unit": {
                "id": budget_markups[0].unit,
                "name": budget_markups[0].UNITS[budget_markups[0].unit].name,
                "slug": budget_markups[0].UNITS[budget_markups[0].unit].slug
            },
            "children": [account.pk]
        }],
        "children": [
            {
                "id": account.pk,
                "identifier": account.identifier,
                "type": "pdf-account",
                "domain": "budget",
                "description": account.description,
                "nominal_value": 0.0,
                "markup_contribution": 0.0,
                "accumulated_markup_contribution": 0.0,
                "accumulated_fringe_contribution": 0.0,
                "actual": 0.0,
                "groups": [],
                "order": "n",
                "children_markups": [{
                    "id": account_markups[0].pk,
                    "type": "markup",
                    "identifier": account_markups[0].identifier,
                    "description": account_markups[0].description,
                    "rate": account_markups[0].rate,
                    "actual": 0.0,
                    "unit": {
                        "id": account_markups[0].unit,
                        "name": account_markups[0].UNITS[
                            account_markups[0].unit].name,
                        "slug": account_markups[0].UNITS[
                            account_markups[0].unit].slug
                    },
                    "children": [subaccount.pk]
                }],
                "children": [
                    {
                        "id": subaccount.pk,
                        "identifier": subaccount.identifier,
                        "type": "pdf-subaccount",
                        "domain": "budget",
                        "description": subaccount.description,
                        "nominal_value": 0.0,
                        "fringe_contribution": 0.0,
                        "markup_contribution": 0.0,
                        "accumulated_markup_contribution": 0.0,
                        "accumulated_fringe_contribution": 0.0,
                        "actual": 0.0,
                        "quantity": None,
                        "rate": None,
                        "multiplier": None,
                        "unit": None,
                        "contact": None,
                        "group": None,
                        "groups": [],
                        "children_markups": [],
                        "order": "n",
                        "children": [
                            {
                                "id": subaccounts[0].pk,
                                "identifier": subaccounts[0].identifier,
                                "type": "pdf-subaccount",
                                "domain": "budget",
                                "description": subaccounts[0].description,
                                "nominal_value": 0.0,
                                "fringe_contribution": 0.0,
                                "markup_contribution": 0.0,
                                "accumulated_markup_contribution": 0.0,
                                "accumulated_fringe_contribution": 0.0,
                                "actual": 0.0,
                                "quantity": None,
                                "rate": None,
                                "multiplier": None,
                                "unit": None,
                                "children": [],
                                "children_markups": [],
                                "contact": None,
                                "group": None,
                                "groups": [],
                                "order": "n",
                            },
                            {
                                "id": subaccounts[1].pk,
                                "identifier": subaccounts[1].identifier,
                                "type": "pdf-subaccount",
                                "domain": "budget",
                                "description": subaccounts[1].description,
                                "nominal_value": 0.0,
                                "fringe_contribution": 0.0,
                                "markup_contribution": 0.0,
                                "accumulated_markup_contribution": 0.0,
                                "accumulated_fringe_contribution": 0.0,
                                "actual": 0.0,
                                "quantity": None,
                                "rate": None,
                                "multiplier": None,
                                "unit": None,
                                "children": [],
                                "children_markups": [],
                                "contact": None,
                                "group": None,
                                "groups": [],
                                "order": "t",
                            }
                        ]
                    }
                ],
            }
        ],
    }
