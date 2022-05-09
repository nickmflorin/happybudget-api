import nested_admin


class BudgetingTreePolymorphicOrderedRowModelInline(
        nested_admin.NestedStackedInline):
    sortable_field_name = "identifier"
    fields = ('identifier', 'description', 'markups', 'group')

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        field = super().formfield_for_manytomany(db_field, request, **kwargs)
        if db_field.name == "markups":
            assert hasattr(request, '__obj__'), \
                "The request must be privately attributed with the object " \
                "being edited in the form for this inline to work properly."
            if request.__obj__ is not None:
                field.queryset = field.queryset.get_table(request.__obj__)
            else:
                field.queryset = field.queryset.none()
        return field

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'group':
            assert hasattr(request, '__obj__'), \
                "The request must be privately attributed with the object " \
                "being edited in the form for this inline to work properly."
            if request.__obj__ is not None:
                field.queryset = field.queryset.get_table(request.__obj__)
            else:
                field.queryset = field.queryset.none()
        return field
