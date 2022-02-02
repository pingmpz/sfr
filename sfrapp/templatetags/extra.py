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
