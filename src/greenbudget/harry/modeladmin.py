import collections

from django.contrib import admin
from django.utils.html import mark_safe

from .widgets import use_custom_related_field_wrapper


RowAction = collections.namedtuple('RowAction', ['name', 'title'])


@use_custom_related_field_wrapper
class HarryModelAdmin(admin.ModelAdmin):
    row_actions = []
    base_list_display = []

    @property
    def list_display(self):
        if self.row_actions:
            return list(self.base_list_display) + ['get_row_actions']
        return self.base_list_display

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        for k, _ in request.POST.items():
            for action in self.row_actions:
                if k.startswith(f"_{action.name}_"):
                    instance_id = int(k.split(f"_{action.name}_")[1])
                    getattr(self, action.name)(request, instance_id)
                    break
        return response

    def _row_action_button(self, instance, action):
        return """
            <button type="submit" name="_{name}_{id}" class="link">
                {title}
            </button>
        """.format(name=action.name, title=action.title, id=instance.pk)

    def get_row_actions(self, instance):
        separator = """
            <div style="margin-left: 5px; margin-right: 5px;">
                <span class="link">|</span>
            </div>
        """
        buttons = [
            self._row_action_button(instance, action)
            for action in self.row_actions
        ]
        return mark_safe(u"""
            <div style="display: flex; flex-direction: row;">%s</div>
        """ % separator.join(buttons))

    get_row_actions.allow_tags = True
    get_row_actions.display_name = 'Actions'
