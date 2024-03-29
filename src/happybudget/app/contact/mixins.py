from happybudget.app import views

from .models import Contact


class ContactNestedMixin(views.NestedObjectViewMixin):
    """
    A mixin for views that extend off of an contacts's detail endpoint.
    """
    view_name = 'contact'

    def get_contact_queryset(self):
        return Contact.objects.filter(created_by=self.request.user)

    @property
    def instance(self):
        return self.contact
