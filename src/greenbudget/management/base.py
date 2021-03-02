import six
from django.core import management


class CustomCommandMixin(object):
    def newline(self):
        self.prompt("\n")

    def warn(self, value):
        self.prompt(value, style_func=self.style.WARNING)

    def info(self, value):
        self.prompt(value, style_func=self.style.HTTP_NOT_MODIFIED)

    def success(self, value):
        self.prompt(value, style_func=self.style.SUCCESS)

    def query(self, prompt=None, prefix="Value", converter=None):
        """
        Displays a prompt and then asks the user for generic input.

        Parameters:
        ----------
        prompt: :obj:`str`  (optional)
            The prompt to display to the user before asking for the input.

        prefix: :obj:`str` (optional)
            The prefix that will be displayed before the character space for
            the user provided input.

            Ex.
            --
            >>> Value: __

            Default: "Value"

        converter: :obj:`func` (optional)
            A function that takes the provided value as an argument and converts
            it to the boolean value that is returned.
        """
        if prompt:
            self.prompt(prompt, style_func=self.style.SQL_TABLE)
        value = input("%s: " % prefix)
        if converter:
            return converter(value)
        return value

    def query_boolean(
        self,
        prompt=None,
        prefix="(Yes/No)",
        converter=lambda ans: (
            ans.lower().strip() == "yes" or ans.lower().strip() == "y")
    ):
        """
        Displays a prompt and then asks the user for boolean input.

        Parameters:
        ----------
        prompt: :obj:`str`  (optional)
            The prompt to display to the user before asking for the input.

        prefix: :obj:`str` (optional)
            The prefix that will be displayed before the character space for
            the user provided input.

            Ex.
            --
            >>> Value: __

            Default: "Value"

        converter: :obj:`func` (optional)
            A function that takes the provided value as an argument and converts
            it to the boolean value that is returned.
        """
        if prompt:
            self.prompt(prompt, style_func=self.style.SQL_TABLE)
        return self.query(prefix=prefix, converter=converter)

    def query_until(self,
        prompt=None,
        is_valid=None,
        prefix="Value",
        invalid_prompt="Invalid value, try again.",
        converter=lambda value: value,
    ):
        """
        Displays a prompt and then asks the user for input until the provided
        input is valid.

        Parameters:
        ----------
        prompt: :obj:`str`  (optional)
            The prompt to display to the user before asking for the input.

        prefix: :obj:`str` (optional)
            The prefix that will be displayed before the character space for
            the user provided input.

            Ex.
            --
            >>> Value: __

            Default: "Value"

        invalid_prompt: :obj:`str` (optional)
            The prompt to display to the user in the event that the input is
            not valid.

            Default: "Invalid value, try again."

        is_valid: :obj:`func` (optional)
            A function that takes the provided value as an argument and returns
            whether or not the user provided value is valid.  If provided, the
            user will be continually asked to provide the input until the input
            is valid.

        converter: :obj:`func` (optional)
            A function that takes the provided value as an argument and converts
            it to the value that should be returned from the method.
        """
        if prompt:
            self.prompt(prompt, style_func=self.style.SQL_TABLE)
        while True:
            value = self.query(prefix=prefix)
            if is_valid is None or is_valid(value):
                return converter(value)
            else:
                self.prompt(invalid_prompt)

    def query_options(self, options, prompt=None, option_display=None,
            **kwargs):
        """
        Displays a prompt to the user and then a series of options, asking
        the user for a selection from those options.  The user will be
        continually asked to select from the options until a valid selection
        is chosen.
        """
        if prompt:
            self.prompt(prompt, style_func=self.style.SQL_TABLE)
        self.prompt_options(options, option_display=option_display)
        return self.query_until(**kwargs)

    def prompt_options(self, options, prompt=None, option_display=None):
        """
        Displays a series of options to the user.
        """
        def display_option(option):
            if option_display is not None:
                if isinstance(option_display, str):
                    if isinstance(option, dict):
                        try:
                            return option[option_display]
                        except KeyError:
                            return option
                    else:
                        return getattr(option, option_display, option)
                elif six.callable(option_display):
                    return option_display(option)
                else:
                    raise ValueError(
                        "The option_display must either be a callable or a "
                        "string key/attribute."
                    )
            return option

        self.stdout.write("\n".join([
            "(%s) %s" % (i + 1, display_option(option))
            for i, option in enumerate(options)
        ]))

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
    pass
