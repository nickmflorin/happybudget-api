def test_ordering_bulk_create(api_client, user, models):
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/contacts/bulk-create/",
        format='json',
        data={'data': [{}, {}, {}]}
    )
    assert response.status_code == 200
    contacts = models.Contact.objects.all()
    assert len(contacts) == 3
    assert [c.order for c in contacts] == ["n", "t", "w"]


def test_move_contact_down(api_client, user, models, f):
    contacts = f.create_contact(count=10)
    assert [c.order for c in contacts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [c.pk for c in contacts] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/contacts/%s/" % contacts[4].pk, data={
        'previous': contacts[1].pk
    })
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'v'

    contacts = models.Contact.objects.all()
    assert [c.pk for c in contacts] == [1, 2, 5, 3, 4, 6, 7, 8, 9, 10]


def test_move_contact_to_start(api_client, user, models, f):
    contacts = f.create_contact(count=10)
    assert [c.order for c in contacts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [c.pk for c in contacts] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/contacts/%s/" % contacts[4].pk,
        format='json',
        data={'previous': None}
    )
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'h'

    contacts = models.Contact.objects.all()
    assert [a.pk for a in contacts] == [5, 1, 2, 3, 4, 6, 7, 8, 9, 10]


def test_move_contact_to_end(api_client, user, models, f):
    contacts = f.create_contact(count=10)
    assert [a.order for a in contacts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in contacts] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/contacts/%s/" % contacts[4].pk,
        format='json',
        data={'previous': contacts[9].pk}
    )
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'yntwyntw'

    contacts = models.Contact.objects.all()
    assert [a.pk for a in contacts] == [1, 2, 3, 4, 6, 7, 8, 9, 10, 5]


def test_move_contact_self_referential(api_client, user, f):
    contacts = f.create_contact(count=10)
    assert [a.order for a in contacts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in contacts] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/contacts/%s/" % contacts[3].pk, data={
        'previous': contacts[3].pk
    })
    assert response.status_code == 400


def test_move_contact_same_order(api_client, user, models, f):
    contacts = f.create_contact(count=10)
    assert [c.order for c in contacts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [c.pk for c in contacts] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/contacts/%s/" % contacts[3].pk, data={
        'previous': contacts[2].pk
    })
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'y'

    contacts = models.Contact.objects.all()
    assert [c.pk for c in contacts] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


def test_move_contact_up(api_client, user, models, f):
    contacts = f.create_contact(count=10)
    assert [c.order for c in contacts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [c.pk for c in contacts] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/contacts/%s/" % contacts[4].pk, data={
        'previous': contacts[8].pk
    })
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'yntwynk'

    contacts = models.Contact.objects.all()
    assert [c.pk for c in contacts] == [1, 2, 3, 4, 6, 7, 8, 9, 5, 10]
