import logging

from django import dispatch
from greenbudget.app import signals

from .models import HeaderTemplate, ExportField, TextFragmentGroup


logger = logging.getLogger('signals')


def recursive_delete_data_element(element):
    if isinstance(element, TextFragmentGroup):
        for subelement in element.data.all():
            recursive_delete_data_element(subelement)
    element.delete()


@dispatch.receiver(signals.pre_delete, sender=HeaderTemplate)
def delete_export_fields(instance, **kwargs):
    for field in HeaderTemplate.RICH_TEXT_FIELDS:
        export_field = getattr(instance, field)
        if export_field is not None:
            for block in export_field.blocks.all():
                # Since the relationship between TextDataElement and Blocks is
                # generic, CASCADE deletes will not work properly.
                for text_data_element in block.data.all():
                    recursive_delete_data_element(text_data_element)
                block.delete()
            export_field.delete()


@signals.any_fields_changed_receiver(
    fields=['left_info', 'right_info', 'header'],
    sender=HeaderTemplate
)
def rich_text_field_changed(instance, **kwargs):
    # Since we are using OneToOneField(s) for the Rich Text related fields of
    # the Header Template, when these fields are changed they won't necessarily
    # delete the old ones.  We want to make sure that we delete the old fields
    # so that we do not have lingering data in the database.
    for change in kwargs['changes']:
        export_field = ExportField.objects.get(pk=change.previous_value)
        for block in export_field.blocks.all():
            # Since the relationship between TextDataElement and Blocks is
            # generic, CASCADE deletes will not work properly.
            for text_data_element in block.data.all():
                recursive_delete_data_element(text_data_element)
            block.delete()
        export_field.delete()
