from rest_framework import viewsets, mixins

from .serializers import BudgetSerializer


class UserBudgetViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    lookup_field = 'pk'
    serializer_class = BudgetSerializer
    ordering_fields = ['status_changed_at', 'name', 'created_at']
    search_fields = ['name']

    def get_queryset(self):
        return self.request.user.budgets.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
