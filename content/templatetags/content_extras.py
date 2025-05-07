from django import template

register = template.Library()

@register.filter
def modulo(value, arg):
    """Returns the remainder of value divided by arg"""
    return int(value) % int(arg)

@register.filter
def multiply(value, arg):
    """Multiplies the value by the argument"""
    return float(value) * float(arg)
