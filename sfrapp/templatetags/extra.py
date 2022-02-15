from django import template
import datetime
from django.utils import timezone

register = template.Library()

@register.filter
def index(indexable, i):
    return indexable[i]

@register.filter
def subtract(value, arg):
    return value - arg

@register.filter
def divide(value, arg):
    try:
        return int(value) / int(arg)
    except (ValueError, ZeroDivisionError):
        return None

@register.filter
def multiple(value, arg):
    return int(value) * int(arg)

@register.filter
def replace(value, arg):
    if len(arg.split('|')) != 2:
        return value

    what, to = arg.split('|')
    return value.replace(what, to)

@register.filter
def modulo(num, val):
    return num % val

@register.filter
def hours_ago(time, hours):
    return time + datetime.timedelta(hours=hours) < datetime.datetime.now()

@register.filter(name='chr')
def chr_(value):
    return chr(value + 65)

@register.filter
def convert_char(old):
    if len(old) != 1:
        return 0
    new = ord(old)
    if 65 <= new <= 90:
        # Upper case letter
        return new - 64
    elif 97 <= new <= 122:
        # Lower case letter
        return new - 96
    # Unrecognized character
    return 0
