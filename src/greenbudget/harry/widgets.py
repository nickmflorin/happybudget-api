from django.contrib.admin.widgets import RelatedFieldWidgetWrapper


class CustomRelatedFieldWidgetWrapper(RelatedFieldWidgetWrapper):
    """
    Overrides the default :obj:`django.contrib.admin.widgets.
    RelatedFieldWidgetWrapper` such that our custom related widget wrapper
    template is used.
    """
    template_name = 'admin/widgets/custom_related_widget_wrapper.html'

    @classmethod
    def create_from_root(cls, root_widget: RelatedFieldWidgetWrapper):
        set_attr_fields = [
            "widget", "rel", "admin_site", "can_add_related",
            "can_change_related", "can_delete_related", "can_view_related"
        ]
        init_args = {
            field: getattr(root_widget, field)
            for field in set_attr_fields
        }
        return CustomRelatedFieldWidgetWrapper(**init_args)


def use_custom_related_field_wrapper(cls):
    original_formfield_for_dbfield = getattr(cls, 'formfield_for_dbfield')

    def decorated(instance, db_field, request, **kwargs):
        formfield = original_formfield_for_dbfield(
            instance, db_field, request, **kwargs)
        if hasattr(formfield, 'widget') \
                and isinstance(formfield.widget, RelatedFieldWidgetWrapper):
            formfield.widget = CustomRelatedFieldWidgetWrapper.create_from_root(
                formfield.widget
            )
        return formfield

    setattr(cls, 'formfield_for_dbfield', decorated)
    return cls
