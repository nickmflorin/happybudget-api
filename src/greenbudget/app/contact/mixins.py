from greenbudget.app.budgeting.mixins import NestedObjectViewMixin

from .models import Contact
from .permissions import ContactObjPermission


class ContactNestedMixin(NestedObjectViewMixin):
    """
    A mixin for views that extend off of an contacts's detail endpoint.
    """
    actual_permission_classes = (ContactObjPermission, )
    view_name = 'contact'
    owner_field = 'user'
    contact_lookup_field = ("pk", "contact_pk")

    def get_contact_queryset(self, request):
        return Contact.objects.all()

    @property
    def instance(self):
        return self.contact
