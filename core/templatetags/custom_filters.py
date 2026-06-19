from django import template

register = template.Library()

@register.filter(name='split_string')
def split_string(value, arg):
    """Splits a string string value by a given delimiter argument inside templates."""
    if value:
        return [tag.strip() for tag in value.split(arg) if tag.strip()]
    return []