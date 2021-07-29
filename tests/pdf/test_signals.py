import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_rich_text_field_changed(create_export_field, create_header_template,
        models):
    left_info_field = create_export_field()
    template = create_header_template(left_info=left_info_field)
    another_field = create_export_field()

    template.left_info = another_field
    template.save()

    with pytest.raises(models.ExportField.DoesNotExist):
        left_info_field.refresh_from_db()
