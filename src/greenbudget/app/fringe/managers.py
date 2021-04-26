from django.db import models

from greenbudget.app.common.managers import (
    ModelTemplateManager, ModelDuplicateManager)


class FringeManager(
        ModelDuplicateManager(ModelTemplateManager(models.Manager))):
    template_cls = 'fringe.Fringe'
