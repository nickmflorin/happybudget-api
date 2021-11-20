def test_ordering_bulk_create(api_client, user, models):
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/contacts/bulk-create/",
        format='json',
        data={'data': [{}, {}, {}]}
    )
    assert response.status_code == 201
    contacts = models.Contact.objects.all()
    assert len(contacts) == 3
    assert [c.order for c in contacts] == ["n", "t", "w"]


def test_move_contact_down(api_client, user, models, create_contacts):
    contacts = create_contacts(count=10)
    assert [c.order for c in contacts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [c.pk for c in contacts] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/contacts/%s/" % contacts[4].pk, data={
        'order': 8
    })
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'yntwynk'

    contacts = models.Contact.objects.all()
    assert [c.pk for c in contacts] == [1, 2, 3, 4, 6, 7, 8, 9, 5, 10]


def test_move_contact_same_order(api_client, user, models, create_contacts):
    contacts = create_contacts(count=10)
    assert [c.order for c in contacts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [c.pk for c in contacts] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/contacts/%s/" % contacts[3].pk, data={
        'order': 3
    })
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'y'

    contacts = models.Contact.objects.all()
    assert [c.pk for c in contacts] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


def test_move_contact_up(api_client, user, models, create_contacts):
    contacts = create_contacts(count=10)
    assert [c.order for c in contacts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [c.pk for c in contacts] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/contacts/%s/" % contacts[4].pk, data={
        'order': 2
    })
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'v'

    contacts = models.Contact.objects.all()
    assert [c.pk for c in contacts] == [1, 2, 5, 3, 4, 6, 7, 8, 9, 10]
