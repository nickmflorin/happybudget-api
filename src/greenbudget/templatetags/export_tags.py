from django import template

from greenbudget.app.subaccount.models import SubAccount

register = template.Library()


@register.filter(name='format_as_dollar')
def format_as_dollar(value):
    return "${:,.2f}".format(value)


@register.filter(name='format_unit')
def format_unit(value):
    if value is None:
        return ""
    return SubAccount.UNITS[value]
