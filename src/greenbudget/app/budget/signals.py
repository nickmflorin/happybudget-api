import contextlib
import threading

from django import dispatch
from django.db.models.signals import post_save

from greenbudget.app.account.models import Account
from greenbudget.app.actual.models import Actual
from greenbudget.app.fringe.models import Fringe
from greenbudget.app.group.models import Group
from greenbudget.app.subaccount.models import SubAccount


disabled = threading.local()


@contextlib.contextmanager
def disable_budget_tracking(id=None):
    disabled.value = True
    disabled.id = id
    try:
        yield
    finally:
        disabled.value = False
        disabled.id = None


@dispatch.receiver(post_save)
def update_budget_updated_at(instance, **kwargs):
    if isinstance(instance, (Account, SubAccount, Fringe, Actual, Group)):
        if getattr(disabled, 'value', False) is False \
                and not getattr(instance, '_suppress_budget_update', False) \
                and (getattr(disabled, 'id', None) is None
                    or getattr(disabled, 'id', None) == instance.pk):
            instance.budget.mark_updated()
