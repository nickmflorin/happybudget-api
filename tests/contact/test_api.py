from greenbudget.lib.utils.dateutils import api_datetime_string


def test_get_contact(api_client, user, f, models):
    contact = f.create_contact()
    api_client.force_login(user)
    response = api_client.get("/v1/contacts/%s/" % contact.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": contact.pk,
        "type": "contact",
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "city": contact.city,
        "rate": contact.rate,
        "phone_number": contact.phone_number,
        "email": contact.email,
        "full_name": contact.full_name,
        "company": contact.company,
        "position": contact.position,
        "image": None,
        "attachments": [],
        "order": "n",
        "notes": None,
        "contact_type": {
            "id": contact.contact_type,
            "name": models.Contact.TYPES[contact.contact_type].name,
            "slug": models.Contact.TYPES[contact.contact_type].slug
        }
    }


def test_get_contact_tagged_actuals(api_client, user, f):
    budget = f.create_budget()
    contact = f.create_contact()
    actuals = [
        f.create_actual(budget=budget, contact=contact),
        f.create_actual(budget=budget, contact=contact)
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/contacts/%s/tagged-actuals/" % contact.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            'id': actuals[0].pk,
            'name': actuals[0].name,
            'value': actuals[0].value,
            'date': api_datetime_string(actuals[0].date, strict=False),
            'owner': None,
            'type': 'actual',
            'budget': {
                'id': budget.pk,
                'name': budget.name,
                'type': 'budget',
                'domain': 'budget',
                'updated_at': api_datetime_string(budget.updated_at),
                'image': None,
                'is_permissioned': False,
                "updated_by": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "full_name": user.full_name,
                    "email": user.email,
                    "profile_image": None
                }
            }
        },
        {
            'id': actuals[1].pk,
            'name': actuals[1].name,
            'value': actuals[1].value,
            'date': api_datetime_string(actuals[1].date, strict=False),
            'owner': None,
            'type': 'actual',
            'budget': {
                'id': budget.pk,
                'name': budget.name,
                'type': 'budget',
                'domain': 'budget',
                'updated_at': api_datetime_string(budget.updated_at),
                'image': None,
                'is_permissioned': False,
                "updated_by": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "full_name": user.full_name,
                    "email": user.email,
                    "profile_image": None
                }
            }
        }
    ]


def test_get_contacts(api_client, user, f, models):
    contacts = f.create_contact(count=2)
    api_client.force_login(user)
    response = api_client.get("/v1/contacts/")
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": contacts[0].pk,
            "type": "contact",
            "first_name": contacts[0].first_name,
            "last_name": contacts[0].last_name,
            "city": contacts[0].city,
            "rate": contacts[0].rate,
            "company": contacts[0].company,
            "phone_number": contacts[0].phone_number,
            "email": contacts[0].email,
            "full_name": contacts[0].full_name,
            "position": contacts[0].position,
            "image": None,
            "attachments": [],
            "order": "n",
            "notes": None,
            "contact_type": {
                "id": contacts[0].contact_type,
                "name": models.Contact.TYPES[contacts[0].contact_type].name,
                "slug": models.Contact.TYPES[contacts[0].contact_type].slug
            }
        },
        {
            "id": contacts[1].pk,
            "type": "contact",
            "first_name": contacts[1].first_name,
            "last_name": contacts[1].last_name,
            "city": contacts[1].city,
            "rate": contacts[1].rate,
            "company": contacts[1].company,
            "phone_number": contacts[1].phone_number,
            "email": contacts[1].email,
            "full_name": contacts[1].full_name,
            "position": contacts[1].position,
            "image": None,
            "attachments": [],
            "order": "t",
            "notes": None,
            "contact_type": {
                "id": contacts[1].contact_type,
                "name": models.Contact.TYPES[contacts[1].contact_type].name,
                "slug": models.Contact.TYPES[contacts[1].contact_type].slug
            }
        }
    ]


def test_create_contact(api_client, user, models):
    api_client.force_login(user)
    response = api_client.post("/v1/contacts/", data={
        'city': 'New York',
        'rate': 5,
        'first_name': 'Jack',
        'last_name': 'Johnson',
        'contact_type': 1,
        'phone_number': '15183696530',
        'email': 'jjohnson@gmail.com',
        "company": "Boeing"
    })
    assert response.status_code == 201
    contact = models.Contact.objects.first()

    assert contact is not None
    assert contact.city == "New York"
    assert contact.rate == 5
    assert contact.first_name == "Jack"
    assert contact.last_name == "Johnson"
    assert contact.contact_type == 1
    assert contact.phone_number == "15183696530"
    assert contact.email == "jjohnson@gmail.com"
    assert contact.company == "Boeing"

    assert response.json() == {
        "id": contact.pk,
        "type": "contact",
        "first_name": "Jack",
        "last_name": "Johnson",
        "city": "New York",
        "rate": 5,
        "phone_number": "15183696530",
        "email": "jjohnson@gmail.com",
        "full_name": "Jack Johnson",
        "company": "Boeing",
        "position": None,
        "image": None,
        "attachments": [],
        "order": "n",
        "notes": None,
        "contact_type": {
            "id": 1,
            "name": models.Contact.TYPES[1].name,
            "slug": models.Contact.TYPES[1].slug
        }
    }


def test_create_blank_contact(api_client, user, models):
    api_client.force_login(user)
    response = api_client.post("/v1/contacts/", data={})
    assert response.status_code == 201
    contact = models.Contact.objects.first()

    assert contact is not None
    assert contact.city is None
    assert contact.rate is None
    assert contact.first_name is None
    assert contact.last_name is None
    assert contact.contact_type is None
    assert contact.phone_number is None
    assert contact.email is None
    assert contact.company is None

    assert response.json() == {
        "id": contact.pk,
        "type": "contact",
        "first_name": None,
        "last_name": None,
        "company": None,
        "city": None,
        "rate": None,
        "phone_number": None,
        "email": None,
        "full_name": "",
        "contact_type": None,
        "position": None,
        "image": None,
        "notes": None,
        "attachments": [],
        "order": "n",
    }


def test_update_contact(api_client, user, f, models):
    contact = f.create_contact()
    api_client.force_login(user)
    response = api_client.patch("/v1/contacts/%s/" % contact.pk, data={
        'city': 'New York',
        'rate': 5,
        'first_name': 'Jack',
        'last_name': 'Johnson',
    })
    assert response.status_code == 200
    contact.refresh_from_db()

    assert contact.city == "New York"
    assert contact.rate == 5
    assert contact.first_name == "Jack"
    assert contact.last_name == "Johnson"

    assert response.json() == {
        "id": contact.pk,
        "type": "contact",
        "first_name": "Jack",
        "last_name": "Johnson",
        "city": "New York",
        "rate": 5,
        "company": contact.company,
        "phone_number": contact.phone_number,
        "email": contact.email,
        "full_name": contact.full_name,
        "position": contact.position,
        "image": None,
        "attachments": [],
        "order": "n",
        "notes": None,
        "contact_type": {
            "id": contact.contact_type,
            "name": models.Contact.TYPES[contact.contact_type].name,
            "slug": models.Contact.TYPES[contact.contact_type].slug

        }
    }


def test_delete_contact(api_client, user, f, models):
    contact = f.create_contact()
    api_client.force_login(user)
    response = api_client.delete("/v1/contacts/%s/" % contact.pk)
    assert response.status_code == 204
    assert models.Contact.objects.first() is None


def test_bulk_delete_contacts(api_client, user, f, models):
    contacts = f.create_contact(count=2)
    api_client.force_login(user)
    response = api_client.patch("/v1/contacts/bulk-delete/", data={
        'ids': [c.pk for c in contacts]
    })
    assert response.status_code == 204
    assert models.Contact.objects.count() == 0


def test_bulk_create_contacts(api_client, user, models):
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/contacts/bulk-create/",
        format='json',
        data={"data": [
            {
                'city': 'New York',
                'rate': 5,
                'first_name': 'Jack',
                'last_name': 'Johnson',
                'contact_type': 1,
            },
            {
                'phone_number': '15183696530',
                'email': 'jjohnson@gmail.com',
                "company": "Boeing"
            }
        ]}
    )
    assert response.status_code == 200
    assert models.Contact.objects.count() == 2
    contacts = models.Contact.objects.all()
    assert response.json()['children'] == [
        {
            "id": contacts[0].pk,
            "type": "contact",
            "first_name": "Jack",
            "last_name": "Johnson",
            "city": "New York",
            "rate": 5,
            "company": contacts[0].company,
            "phone_number": contacts[0].phone_number,
            "email": contacts[0].email,
            "full_name": contacts[0].full_name,
            "position": contacts[0].position,
            "image": None,
            "attachments": [],
            "order": "n",
            "notes": None,
            "contact_type": {
                "id": 1,
                "name": models.Contact.TYPES[1].name,
                "slug": models.Contact.TYPES[1].slug
            }
        },
        {
            "id": contacts[1].pk,
            "type": "contact",
            "first_name": contacts[1].first_name,
            "last_name": contacts[1].last_name,
            "city": contacts[1].city,
            "rate": contacts[1].rate,
            "company": "Boeing",
            "phone_number": '15183696530',
            "email": 'jjohnson@gmail.com',
            "full_name": contacts[1].full_name,
            "position": contacts[1].position,
            "image": None,
            "attachments": [],
            "order": "t",
            "notes": None,
            "contact_type": None
        }
    ]


def test_bulk_update_contacts(api_client, user, f):
    contacts = f.create_contact(count=2)
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/contacts/bulk-update/",
        format='json',
        data={'data': [
            {
                'id': contacts[0].pk,
                'city': 'New York',
                'rate': 5,
                'first_name': 'Jack',
                'last_name': 'Johnson',
            },
            {
                'id': contacts[1].pk,
                'phone_number': '15183696530',
                'email': 'jjohnson@gmail.com',
                "company": "Boeing"
            }
        ]})
    assert response.status_code == 200
    # pylint: disable=expression-not-assigned
    [c.refresh_from_db() for c in contacts]

    assert contacts[0].city == "New York"
    assert contacts[0].rate == 5
    assert contacts[0].first_name == "Jack"
    assert contacts[0].last_name == "Johnson"

    assert contacts[1].phone_number == "15183696530"
    assert contacts[1].email == 'jjohnson@gmail.com'
    assert contacts[1].company == "Boeing"


def test_search_filter(api_client, user, f, models):
    contacts = [
        f.create_contact(
            contact_type=models.Contact.TYPES.vendor,
            first_name='Jack',
            last_name='Smith'
        ),
        f.create_contact(
            contact_type=models.Contact.TYPES.vendor,
            company='Jack Box TV'
        ),
        f.create_contact(
            contact_type=models.Contact.TYPES.employee,
            first_name='Ginger',
        ),
        f.create_contact(
            contact_type=models.Contact.TYPES.employee,
            first_name='Jack'
        ),
        f.create_contact(
            contact_type=models.Contact.TYPES.employee,
            first_name='Jim'
        )
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/contacts/?search=jack")
    assert response.json()['count'] == 3
    assert response.json()['data'][0]['id'] == contacts[0].pk
    assert response.json()['data'][1]['id'] == contacts[1].pk
    assert response.json()['data'][2]['id'] == contacts[3].pk
