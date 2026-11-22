from django.core.management.base import BaseCommand
from store.utils import expire_pending_orders
class Command(BaseCommand):
    help='Batalkan dan kembalikan stok pesanan yang melewati 30 menit.'
    def handle(self,*args,**options): self.stdout.write(f'Pesanan kedaluwarsa diproses: {expire_pending_orders()}')
