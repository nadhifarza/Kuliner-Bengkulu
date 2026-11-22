from django.utils import timezone
from django.db import transaction
from .models import Order,Notification

def rupiah(value): return 'Rp '+f'{int(value or 0):,}'.replace(',','.')

def notify(user,title,body,kind='INFO',order=None):
    if user: Notification.objects.create(recipient=user,title=title,body=body,kind=kind,order=order)

def expire_pending_orders():
    now=timezone.now(); count=0
    qs=Order.objects.filter(status='WAITING_PAYMENT',payment__status='WAITING',payment__deadline__lt=now).select_related('payment')
    for order in qs:
        with transaction.atomic():
            o=Order.objects.select_for_update().get(pk=order.pk)
            if o.status=='WAITING_PAYMENT' and o.payment.status=='WAITING' and o.payment.deadline<now:
                o.status='CANCELLED'; o.save(update_fields=['status','updated_at'])
                o.payment.status='EXPIRED'; o.payment.save(update_fields=['status'])
                for line in o.items.select_related('product'):
                    p=line.product; p.stock+=line.quantity; p.save(update_fields=['stock'])
                notify(o.customer,'Pesanan kedaluwarsa',f'Pesanan {o.code} dibatalkan karena melewati batas pembayaran 30 menit.','ORDER',o)
                count+=1
    return count
