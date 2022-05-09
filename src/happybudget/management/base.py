from django.core import management

from .query import Query


class CustomCommandMixin:
    def newline(self):
        self.prompt("\n")

    def warn(self, value):
        self.prompt(value, style_func=self.style.WARNING)

    def warning(self, value):
        self.prompt(value, style_func=self.style.WARNING)

    def info(self, value):
        self.prompt(value, style_func=self.style.HTTP_NOT_MODIFIED)

    def success(self, value):
        self.prompt(value, style_func=self.style.SUCCESS)

    def query_boolean(self, prompt, **kwargs):
        query = Query.Boolean(command=self, prompt=prompt, **kwargs)
        return query()

    def _get_style_func(self, style_func):
        if isinstance(style_func, str):
            return getattr(self.style, style_func)
        return style_func

    def prompt(self, *prompts, style_func=None):
        """
        Outputes a message or series of messages to STDOUT.

        Each prompt can be either a single message or a tuple of
        (message, style_func), where the style_func can either be the attribute
        on :obj:`management.base.BaseCommand.styles` or the string name of the
        attribute.
        """
        style_func = style_func or self.style.SQL_TABLE
        for prompt in prompts:
            if isinstance(prompt, str):
                self.stdout.write(
                    prompt, style_func=self._get_style_func(style_func))
            elif hasattr(prompt, '__iter__'):
                self.prompt(
                    prompt[0], style_func=self._get_style_func(prompt[1]))
            else:
                self.stdout.write(
                    prompt, style_func=self._get_style_func(style_func))


class CustomCommand(CustomCommandMixin, management.base.BaseCommand):
    """
    A base class for all Django management commands.  Provides utility
    functionality for writing better more customizable/flexible commands.
    """
