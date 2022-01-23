from greenbudget.app import mixins

from .models import Contact


class ContactNestedMixin(mixins.NestedObjectViewMixin):
    """
    A mixin for views that extend off of an contacts's detail endpoint.
    """
    view_name = 'contact'
    owner_field = 'user'
    contact_lookup_field = ("pk", "contact_pk")

    def get_contact_queryset(self, request):
        return Contact.objects.filter(created_by=request.user)

    @property
    def instance(self):
        return self.contact
