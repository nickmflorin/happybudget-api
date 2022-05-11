from happybudget.app import views, exceptions

from .models import Collaborator
from .permissions import IsOwnerOrCollaboratingOwner
from .serializers import CollaboratorSerializer


class CollaboratorViewSet(
    views.UpdateModelMixin,
    views.DestroyModelMixin,
    views.GenericViewSet
):
    queryset_cls = Collaborator
    serializer_class = CollaboratorSerializer
    permission_classes = [IsOwnerOrCollaboratingOwner(
        get_permissioned_obj=lambda obj: obj.instance)]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # In the future, we might have to allow this such that users can stop
        # collaborating on a Budget - but for now this is important to prevent.
        if instance.user == request.user:
            raise exceptions.BadRequest(
                "A user cannot remove themselves as a collaborator.")
        return super().destroy(request, *args, **kwargs)
