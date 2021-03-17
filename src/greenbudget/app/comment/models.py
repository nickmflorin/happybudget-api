from django.db import models
from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation)
from django.contrib.contenttypes.models import ContentType


class Comment(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        to='user.User',
        on_delete=models.CASCADE,
        related_name="comments"
    )
    text = models.TextField(max_length=1028)
    likes = models.ManyToManyField(
        to='user.User',
        related_name="liked_comments"
    )
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(app_label='account', model='account')
        | models.Q(app_label='subaccount', model='subaccount')
        | models.Q(app_label='budget', model='budget')
        | models.Q(app_label='actual', model='actual')
        | models.Q(app_label='comment', model='comment')
    )
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    comments = GenericRelation('self')

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('created_at', )
        verbose_name = "Comment"
        verbose_name_plural = "Comments"

    def __str__(self):
        return "<{cls} id={id}, user={user}>".format(
            cls=self.__class__.__name__,
            id=self.pk,
            user=self.user.pk,
        )

    @property
    def content_object_type(self):
        from greenbudget.app.budget.models import Budget
        from greenbudget.app.account.models import Account
        if isinstance(self.content_object, Budget):
            return "budget"
        elif isinstance(self.content_object, Account):
            return "account"
        elif isinstance(self.content_object, type(self)):
            return "comment"
        return "subaccount"
