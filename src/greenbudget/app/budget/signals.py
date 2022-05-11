from django import dispatch

from happybudget.app import signals

from happybudget.app.account.models import BudgetAccount, TemplateAccount
from happybudget.app.actual.models import Actual
from happybudget.app.fringe.models import Fringe
from happybudget.app.group.models import Group
from happybudget.app.markup.models import Markup
from happybudget.app.subaccount.models import (
    BudgetSubAccount, TemplateSubAccount)
from happybudget.app.template.models import Template

from .cache import budget_instance_cache
from .models import Budget


@dispatch.receiver(signals.post_save, sender=Budget)
@dispatch.receiver(signals.post_save, sender=Template)
def budget_saved(instance, **kwargs):
    budget_instance_cache.invalidate(instance)


@dispatch.receiver(signals.post_update_by_user, sender=BudgetAccount)
@dispatch.receiver(signals.pre_delete_by_user, sender=BudgetAccount)
@dispatch.receiver(signals.post_update_by_user, sender=BudgetSubAccount)
@dispatch.receiver(signals.pre_delete_by_user, sender=BudgetSubAccount)
@dispatch.receiver(signals.post_update_by_user, sender=TemplateAccount)
@dispatch.receiver(signals.pre_delete_by_user, sender=TemplateAccount)
@dispatch.receiver(signals.post_update_by_user, sender=TemplateSubAccount)
@dispatch.receiver(signals.pre_delete_by_user, sender=TemplateSubAccount)
@dispatch.receiver(signals.post_update_by_user, sender=Fringe)
@dispatch.receiver(signals.pre_delete_by_user, sender=Fringe)
@dispatch.receiver(signals.post_update_by_user, sender=Actual)
@dispatch.receiver(signals.pre_delete_by_user, sender=Actual)
@dispatch.receiver(signals.post_update_by_user, sender=Group)
@dispatch.receiver(signals.pre_delete_by_user, sender=Group)
@dispatch.receiver(signals.post_update_by_user, sender=Markup)
@dispatch.receiver(signals.pre_delete_by_user, sender=Markup)
def update_budget_updated_at(instance, **kwargs):
    """
    Marks the :obj:`Budget` or :obj:`Template` as having been updated by a
    :obj:`User` at the current time when a model related to the :obj:`Budget`
    or :obj:`Template` is updated or deleted inside of the context of an active
    request.

    The :obj:`User` will only possibly be None or not authenticated if the
    update or delete is happening outside of the context of an active request -
    because the :obj:`User` or request will always be set on the
    :obj:`happybudget.app.model.model` local thread via the
    :obj:`happybudget.app.middleware.ModelRequestMiddleware` when the update or
    delete is being performed inside the request context.

    If the update or delete is not being performed inside of the request context,
    it is happening programatically (or in a Test enviroment) in which case we
    do not want to denote the :obj:`Budget` or :obj:`Template` as having been
    updated.

    TODO:
    ----
    Instead of doing this via signals, since it is only applicable when inside
    the context of an active request it might be smarter to simply and
    explicitly perform the logic in the views/serializers associated with the
    relevant endpoints.
    """
    if kwargs['user'] is not None and kwargs['user'].is_authenticated \
            and not instance.budget.is_deleting:
        instance.budget.mark_updated(kwargs['user'])


@dispatch.receiver(signals.pre_delete, sender=Budget)
@dispatch.receiver(signals.pre_delete, sender=Template)
def budget_to_be_deleted(instance, **kwargs):
    instance.image.delete(False)
    budget_instance_cache.invalidate(instance)
