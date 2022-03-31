from greenbudget.app import views, mixins

from .models import Collaborator
from .permissions import IsOwnerOrCollaboratingOwner
from .serializers import CollaboratorSerializer


class CollaboratorViewSet(
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    views.GenericViewSet
):
    serializer_class = CollaboratorSerializer
    permission_classes = [IsOwnerOrCollaboratingOwner(
        get_permissioned_obj=lambda obj: obj.instance)]

    def get_queryset(self):
        return Collaborator.objects.all()
