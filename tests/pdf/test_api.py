import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_get_header_template(api_client, user, create_paragraph_block,
        create_heading_block, create_export_field, create_header_template,
        create_text_fragment):
    left_info_field = create_export_field()
    paragraph_block = create_paragraph_block(field=left_info_field)
    paragraph_block_data_elements = [
        create_text_fragment(
            parent=paragraph_block,
            is_bold=True
        ),
        create_text_fragment(
            parent=paragraph_block,
            is_bold=True,
        ),
        create_text_fragment(
            parent=paragraph_block,
            is_italic=True
        )
    ]
    heading_block = create_heading_block(field=left_info_field)
    heading_block_data_elements = [
        create_text_fragment(
            parent=heading_block,
            is_bold=True
        ),
        create_text_fragment(
            parent=heading_block,
            is_bold=True,
        ),
        create_text_fragment(
            parent=heading_block,
            is_italic=True
        )
    ]
    template = create_header_template(left_info=left_info_field)

    api_client.force_login(user)
    response = api_client.get(
        "/v1/pdf/header-templates/%s/" % template.pk)

    assert response.json() == {
        "id": template.pk,
        "name": template.name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "left_image": None,
        "right_image": None,
        "right_info": None,
        "header": None,
        "left_info": [
            {
                "type": "paragraph",
                "data": [
                    {
                        "text": paragraph_block_data_elements[0].text,
                        "styles": ["bold"]
                    },
                    {
                        "text": paragraph_block_data_elements[1].text,
                        "styles": ["bold"]
                    },
                    {
                        "text": paragraph_block_data_elements[2].text,
                        "styles": ["italic"]
                    }
                ]
            },
            {
                "type": "header",
                "level": 2,
                "data": [
                    {
                        "text": heading_block_data_elements[0].text,
                        "styles": ["bold"]
                    },
                    {
                        "text": heading_block_data_elements[1].text,
                        "styles": ["bold"]
                    },
                    {
                        "text": heading_block_data_elements[2].text,
                        "styles": ["italic"]
                    }
                ]
            }
        ]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_get_header_templates(api_client, user, create_export_field,
        create_header_template):

    left_info_field = create_export_field()
    template = create_header_template(left_info=left_info_field)

    api_client.force_login(user)
    response = api_client.get("/v1/pdf/header-templates/")
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'] == [
        {
            "id": template.pk,
            "name": template.name,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
        }
    ]


def test_create_header_template_empty_field(api_client, user, models):
    api_client.force_login(user)
    response = api_client.post(
        "/v1/pdf/header-templates/",
        format='json',
        data={
            'name': 'Test Header Template',
            'left_info': []
        })
    assert response.status_code == 201
    assert models.HeaderTemplate.objects.count() == 1
    template = models.HeaderTemplate.objects.first()
    assert template.name == "Test Header Template"
    assert template.left_info is None


def test_create_header_template_non_unique_name(api_client, user, models,
        create_header_template):
    create_header_template(name="Test Header Template")
    api_client.force_login(user)
    response = api_client.post(
        "/v1/pdf/header-templates/",
        format='json',
        data={
            'name': 'Test Header Template',
            'left_info': []
        })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_create_header_template(api_client, user, models):
    api_client.force_login(user)
    response = api_client.post(
        "/v1/pdf/header-templates/",
        format='json',
        data={
            'name': 'Test Header Template',
            'left_info': [
                {
                    "type": "paragraph",
                    "data": [
                        {"text": 'First Paragraph Fragment'},
                        {"text": 'Second Paragraph Fragment', 'styles': []},
                        {
                            "text": 'Bold Paragraph Fragment',
                            "styles": ["bold"]
                        },
                        {
                            "text": 'Italic Paragraph Fragment',
                            "styles": ["italic"]
                        }
                    ]
                }
            ]
        })
    assert response.status_code == 201

    assert models.HeaderTemplate.objects.count() == 1
    template = models.HeaderTemplate.objects.first()
    assert template.left_info is not None
    assert template.name == "Test Header Template"
    assert template.left_info.blocks.count() == 1

    block = template.left_info.blocks.first()
    text_data_elements = block.data.all()

    assert len(text_data_elements) == 4
    assert text_data_elements[2].is_bold is True
    assert text_data_elements[3].is_italic is True

    assert response.json() == {
        "id": template.pk,
        "name": template.name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "left_image": None,
        "right_image": None,
        "right_info": None,
        "header": None,
        "left_info": [
            {
                "type": "paragraph",
                "data": [
                    {"text": 'First Paragraph Fragment'},
                    {"text": 'Second Paragraph Fragment'},
                    {
                        "text": 'Bold Paragraph Fragment',
                        "styles": ["bold"]
                    },
                    {
                        "text": 'Italic Paragraph Fragment',
                        "styles": ["italic"]
                    }
                ]
            },
        ]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_header_template(api_client, user, create_paragraph_block,
        create_heading_block, create_export_field, create_header_template,
        create_text_fragment, models):
    left_info_field = create_export_field()
    paragraph_block = create_paragraph_block(field=left_info_field)
    paragraph_block_data_elements = [
        create_text_fragment(
            parent=paragraph_block,
            is_bold=True
        ),
        create_text_fragment(
            parent=paragraph_block,
            is_bold=True,
        ),
        create_text_fragment(
            parent=paragraph_block,
            is_italic=True
        )
    ]
    heading_block = create_heading_block(field=left_info_field)
    heading_block_data_elements = [
        create_text_fragment(
            parent=heading_block,
            is_bold=True
        ),
        create_text_fragment(
            parent=heading_block,
            is_bold=True,
        ),
        create_text_fragment(
            parent=heading_block,
            is_italic=True
        )
    ]
    template = create_header_template(left_info=left_info_field)

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/pdf/header-templates/%s/" % template.pk,
        format='json',
        data={'left_info': [
            {
                "type": "paragraph",
                "data": [
                    {
                        "text": 'First Paragraph Fragment',
                        "styles": ["bold"]
                    },
                    {
                        "text": 'Second Paragraph Fragment',
                        "styles": ["bold"]
                    },
                    {
                        "text": 'Third Paragraph Fragment',
                        "styles": ["italic"]
                    }
                ]
            }
        ]})

    assert response.status_code == 200

    # Make sure the old field and associated blocks are indeed deleted.
    with pytest.raises(models.ExportField.DoesNotExist):
        left_info_field.refresh_from_db()

    with pytest.raises(models.HeadingBlock.DoesNotExist):
        heading_block.refresh_from_db()

    with pytest.raises(models.ParagraphBlock.DoesNotExist):
        paragraph_block.refresh_from_db()

    for fragment in paragraph_block_data_elements + heading_block_data_elements:
        with pytest.raises(models.TextFragment.DoesNotExist):
            fragment.refresh_from_db()

    assert models.HeaderTemplate.objects.count() == 1
    template = models.HeaderTemplate.objects.first()
    assert template.left_info is not None

    assert response.json() == {
        "id": template.pk,
        "name": template.name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "left_image": None,
        "right_image": None,
        "right_info": None,
        "header": None,
        "left_info": [
            {
                "type": "paragraph",
                "data": [
                    {
                        "text": 'First Paragraph Fragment',
                        "styles": ["bold"]
                    },
                    {
                        "text": 'Second Paragraph Fragment',
                        "styles": ["bold"]
                    },
                    {
                        "text": 'Third Paragraph Fragment',
                        "styles": ["italic"]
                    }
                ]
            },
        ]
    }


def test_delete_header_template(api_client, user, create_paragraph_block,
        create_heading_block, create_export_field, create_header_template,
        create_text_fragment, models):
    left_info_field = create_export_field()
    paragraph_block = create_paragraph_block(field=left_info_field)
    paragraph_block_data_elements = [
        create_text_fragment(
            parent=paragraph_block,
            is_bold=True
        ),
        create_text_fragment(
            parent=paragraph_block,
            is_bold=True,
        ),
        create_text_fragment(
            parent=paragraph_block,
            is_italic=True
        )
    ]
    heading_block = create_heading_block(field=left_info_field)
    heading_block_data_elements = [
        create_text_fragment(
            parent=heading_block,
            is_bold=True
        ),
        create_text_fragment(
            parent=heading_block,
            is_bold=True,
        ),
        create_text_fragment(
            parent=heading_block,
            is_italic=True
        )
    ]
    template = create_header_template(left_info=left_info_field)

    api_client.force_login(user)
    response = api_client.delete("/v1/pdf/header-templates/%s/" % template.pk)

    assert response.status_code == 204

    # Make sure the old field and associated blocks are indeed deleted.
    with pytest.raises(models.ExportField.DoesNotExist):
        left_info_field.refresh_from_db()

    with pytest.raises(models.HeadingBlock.DoesNotExist):
        heading_block.refresh_from_db()

    with pytest.raises(models.ParagraphBlock.DoesNotExist):
        paragraph_block.refresh_from_db()

    for fragment in paragraph_block_data_elements + heading_block_data_elements:
        with pytest.raises(models.TextFragment.DoesNotExist):
            fragment.refresh_from_db()

    assert models.HeaderTemplate.objects.count() == 0
