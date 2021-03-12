from rest_framework import routers

from .views import (
    CommentViewSet, BudgetCommentViewSet, AccountCommentViewSet,
    SubAccountCommentViewSet)

app_name = "comment"

budget_comments_router = routers.SimpleRouter()
budget_comments_router.register(r'', BudgetCommentViewSet, basename='comment')
budget_comments_urlpatterns = budget_comments_router.urls

account_comments_router = routers.SimpleRouter()
account_comments_router.register(r'', AccountCommentViewSet, basename='comment')
account_comments_urlpatterns = account_comments_router.urls

subaccount_comments_router = routers.SimpleRouter()
subaccount_comments_router.register(
    r'', SubAccountCommentViewSet, basename='comment')
subaccount_comments_urlpatterns = subaccount_comments_router.urls

router = routers.SimpleRouter()
router.register(r'', CommentViewSet, basename='comment')
urlpatterns = router.urls
