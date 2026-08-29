from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """{{ my_dict|get_item:key }}"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, 0)
    return 0


@register.filter
def price_fmt(value):
    """
    Format a number as Thai price: ฿1,290 (no decimal if whole), ฿1,290.50 otherwise.
    Usage: {{ product.price|price_fmt }}
    """
    try:
        d = Decimal(str(value))
    except Exception:
        return value
    if d == d.to_integral_value():
        int_val = int(d)
        return f'฿{int_val:,}'
    return f'฿{d:,.2f}'
