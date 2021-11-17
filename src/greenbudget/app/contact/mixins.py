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

    def get_contact_queryset(self, request):
        return Contact.objects.all()
