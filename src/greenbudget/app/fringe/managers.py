from django.db import models


class FringeManager(models.Manager):

    def create(self, *args, **kwargs):
        from greenbudget.app.budget.models import Budget
        from greenbudget.app.template.models import Template
        template = kwargs.pop('template', None)

        if template is not None:
            assert isinstance(template.budget, Template)
            for field in self.model.MAP_FIELDS_FROM_TEMPLATE:
                if field not in kwargs:
                    kwargs[field] = getattr(template, field)
            if 'budget' in kwargs:
                assert isinstance(kwargs['budget'], Budget)

        return super().create(*args, **kwargs)
