from django import template

register = template.Library()


@register.filter(name='format_as_dollar')
def format_as_dollar(value):
    return "${:,.2f}".format(value)
