from django import template
register=template.Library()
@register.filter
def rupiah(value):
    try: return 'Rp '+f'{int(value):,}'.replace(',','.')
    except (ValueError,TypeError): return 'Harga belum diatur'
