from django.apps import apps

from polymorphic.managers import PolymorphicManager
from polymorphic.query import PolymorphicQuerySet


def ModelTemplateManager(*bases):
    class FromTemplateManagerMixin(*bases):
        def _get_template_cls(self):
            assert getattr(self, 'template_cls', None) is not None, \
                "The manager %s must define the `template_cls` attribute if "\
                "using the %s mixin." % (
                    self.__class__.__name__, ModelTemplateManager.__name__)
            template_cls = getattr(self, 'template_cls')
            if isinstance(template_cls, str):
                try:
                    return apps.get_model(
                        app_label=template_cls.split('.')[0],
                        model_name=template_cls.split('.')[1]
                    )
                except IndexError:
                    raise LookupError(
                        'Invalid `template_cls`: %s.' % template_cls)
            return template_cls

        def create_from_template(self, *args, **kwargs):
            template = kwargs.pop('template')
            template_cls = self._get_template_cls()

            assert isinstance(template, template_cls), \
                "When creating %s from a template model, the template model" \
                "must be of type %s." \
                % (self.model.__name__, type(template_cls))

            assert hasattr(self.model, 'MAP_FIELDS_FROM_TEMPLATE'), \
                "The model %s must define the `MAP_FIELDS_FROM_TEMPLATE`." \
                % self.model.__name__

            for field in getattr(self.model, 'MAP_FIELDS_FROM_TEMPLATE'):
                if field not in kwargs:
                    kwargs[field] = getattr(template, field)

            return super().create(*args, **kwargs)
    return FromTemplateManagerMixin


class BudgetQuerier(object):

    def active(self):
        # pylint: disable=no-member
        return self.filter(trash=False)

    def inactive(self):
        # pylint: disable=no-member
        return self.filter(trash=True)


class BudgetQuery(BudgetQuerier, PolymorphicQuerySet):
    pass


class BaseBudgetManager(BudgetQuerier, PolymorphicManager):
    queryset_class = BudgetQuery

    def get_queryset(self):
        return self.queryset_class(self.model)


class BudgetManager(ModelTemplateManager(BaseBudgetManager)):
    template_cls = 'template.Template'

    def create_from_template(self, *args, **kwargs):
        from greenbudget.app.account.models import BudgetAccount
        from greenbudget.app.fringe.models import Fringe

        instance = super().create_from_template(*args, **kwargs)

        # When creating a Budget from a Template, not only do we need to
        # create parallels for the Fringes that are associated with the Template
        # such that they are associated wtih the Budget, but we need to make
        # sure those Fringes are also correctly associated with the new
        # SubAccounts of this Budget.  In orer to do this, we need to provide
        # a mapping of Fringe IDs to the manager responsible for creating the
        # SubAccounts.
        fringe_map = {}
        for template_fringe in kwargs['template'].fringes.all():
            fringe = Fringe.objects.create(
                created_by=instance.created_by,
                updated_by=instance.created_by,
                template=template_fringe,
                budget=instance
            )
            fringe_map[template_fringe.id] = fringe.id
        for template_account in kwargs['template'].accounts.all():
            BudgetAccount.objects.create(
                created_by=instance.created_by,
                updated_by=instance.created_by,
                template=template_account,
                budget=instance,
                fringe_map=fringe_map
            )
        return instance

    def create(self, *args, **kwargs):
        if 'template' in kwargs:
            return self.create_from_template(*args, **kwargs)
        return super().create(*args, **kwargs)
