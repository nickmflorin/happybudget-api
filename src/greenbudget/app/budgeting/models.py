from polymorphic.models import PolymorphicModel

from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from greenbudget.lib.utils import set_or_list
from greenbudget.lib.utils.decorators import deprecated
from greenbudget.lib.django_utils.models import import_model_at_path

from greenbudget.app.tabling.models import RowModel, RowPolymorphicModel


@deprecated(reason="Planning on imlementing better cacheing system.")
class CacheControlMixin:
    def get_cache(self, entity, strict=True):
        for cache in getattr(self, 'CACHES', []):
            if self._get_cache(cache).entity == entity:
                return cache
        if strict:
            raise Exception(
                "Could not find cache for entity %s on model %s."
                % (entity, self.__class__.__name__)
            )

    def _get_cache(self, cache):
        if hasattr(cache, '__iter__'):
            assert len(cache) in (1, 2), "Invalid cache object provided."
            return cache[0]
        return cache

    def _get_cache_conditional(self, cache):
        if hasattr(cache, '__iter__'):
            assert len(cache) in (1, 2), "Invalid cache object provided."
            if len(cache) == 2:
                return cache[1]
        return None

    def _do_invalidate(self, cache):
        conditional = self._get_cache_conditional(cache)
        return conditional is None or conditional(self)

    def _invalidate_cache(self, cache):
        if self._do_invalidate(cache):
            self._get_cache(cache).invalidate(self)

    def invalidate_markups_cache(self, trickle=False):
        cache = self.get_cache("markup")
        self._invalidate_cache(cache)
        if trickle and hasattr(self, 'parent'):
            self.parent.invalidate_markups_cache(trickle=trickle)

    def invalidate_groups_cache(self, trickle=False):
        cache = self.get_cache("group")
        self._invalidate_cache(cache)
        if trickle and hasattr(self, 'parent'):
            self.parent.invalidate_groups_cache(trickle=trickle)

    def invalidate_instance_cache(self, trickle=False):
        # Note: The Budget level will not have a parent cache so this is not
        # applicable.
        instance_cache = self.get_cache("detail")
        self._invalidate_cache(instance_cache)
        if trickle and hasattr(self, 'parent'):
            self.parent.invalidate_instance_cache(trickle=trickle)

    def invalidate_children_cache(self, trickle=False):
        # Note: The Budget level will not have a parent cache so this is not
        # applicable.
        cache = self.get_cache("children", strict=False)
        if cache:
            self._invalidate_cache(cache)
            if trickle:
                self.parent.invalidate_children_cache(trickle=trickle)

    def invalidate_caches(self, entities=None, trickle=False):
        for cache in getattr(self, 'CACHES', []):
            if entities is not None \
                    and self._get_cache(cache).entity not in entities:
                continue
            self._invalidate_cache(cache)
        if trickle and hasattr(self, 'parent'):
            self.parent.invalidate_caches()


class AssociatedModel:
    def __init__(self, *model_lookup):
        self._model_lookup = tuple(model_lookup)

    def __get__(self, obj, objtype=None):
        if self._model_lookup == ('self', ):
            return objtype
        elif len(self._model_lookup) == 1:
            return getattr(obj, self._model_lookup[0])
        return import_model_at_path(*self._model_lookup)


class BudgetingModelMixin:
    budget_cls = AssociatedModel('budget', 'basebudget')
    account_cls = AssociatedModel('account', 'account')
    subaccount_cls = AssociatedModel('subaccount', 'subaccount')
    domain = None


class BudgetingTreeModelMixin(BudgetingModelMixin, CacheControlMixin):
    @property
    def intermittent_parent(self):
        try:
            self.parent.refresh_from_db()
        except (ObjectDoesNotExist, AttributeError):
            # The parent instance can be deleted in the process of deleting
            # it's parent, at which point the parent will be None or raise a
            # DoesNotExist Exception, until that child instance is deleted.
            return None
        else:
            return self.parent

    @property
    def ancestors(self):
        # If the parent is a Budget or Template, it will not have any ancestors.
        if hasattr(self.parent, 'ancestors'):
            return self.parent.ancestors + [self.parent]
        return [self.parent]

    @property
    def parent_instance_cls(self):
        return type(self.parent)

    @property
    def parent_type(self):
        return self.parent.type

    @property
    def budget(self):
        parent = self.parent
        while hasattr(parent, 'parent'):
            parent = parent.parent
        return parent

    @property
    def reestimated_fields(self):
        return [
            fld for fld in self.ESTIMATED_FIELDS
            if getattr(self, fld) != self.previous_value(fld)
        ]

    def children_from_kwargs(self, **kwargs):
        unsaved_children = kwargs.pop('unsaved_children', []) or []
        children = kwargs.pop('children', None) or self.children.all()

        # If the estimation is being performed in the context of children
        # that are not yet saved (due to bulk write behavior) then we need to
        # make sure to reference the value from that unsaved child, not the
        # child that is pulled from the database.
        if isinstance(children, models.QuerySet):
            children = list(children.exclude(
                # Unsaved does not mean never saved, the child could have a PK.
                pk__in=[c.pk for c in unsaved_children if c.pk is not None]
            ))
        else:
            children = [c for c in children if c.pk not in [
                c.pk for c in unsaved_children if c.pk is not None]]
        children += set_or_list(unsaved_children)
        return children, kwargs


class BudgetingModel(models.Model, BudgetingModelMixin):
    class Meta:
        abstract = True


class BudgetingRowModel(RowModel, BudgetingModelMixin):
    class Meta:
        abstract = True


class BudgetingTreeModel(RowModel, BudgetingTreeModelMixin):
    class Meta:
        abstract = True


class BudgetingTreePolymorphicModel(PolymorphicModel, BudgetingTreeModelMixin):
    class Meta:
        abstract = True


class BudgetingTreePolymorphicRowModel(
        RowPolymorphicModel, BudgetingTreeModelMixin):
    class Meta:
        abstract = True
