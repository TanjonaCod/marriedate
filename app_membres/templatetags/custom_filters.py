from django import template

register = template.Library()

@register.filter
def getattribute(obj, attr):
    return getattr(obj, attr, None)

@register.filter
def get_range(start, count):
    """Returns a range of numbers from start to start+count (inclusive)."""
    return range(int(start), int(start) + int(count))