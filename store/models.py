from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

class User(AbstractUser):
    ROLE_CHOICES=[('CUSTOMER','Pelanggan'),('EMPLOYEE','Pegawai'),('ADMIN','Admin')]
    role=models.CharField(max_length=12,choices=ROLE_CHOICES,default='CUSTOMER')
    phone=models.CharField(max_length=25,blank=True)
    email_verified=models.BooleanField(default=False)
    @property
    def display_role(self): return 'Admin' if self.is_superuser else self.get_role_display()

class Address(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='addresses')
    label=models.CharField(max_length=60,default='Rumah')
    recipient=models.CharField(max_length=120)
    phone=models.CharField(max_length=25)
    address=models.TextField()
    is_default=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['-is_default','-created_at']
    def __str__(self): return f'{self.label} - {self.recipient}'

class Category(models.Model):
    name=models.CharField(max_length=80,unique=True)
    slug=models.SlugField(unique=True)
    description=models.CharField(max_length=240,blank=True)
    class Meta: ordering=['id']
    def __str__(self): return self.name

class Product(models.Model):
    name=models.CharField(max_length=140)
    slug=models.SlugField(unique=True)
    category=models.ForeignKey(Category,on_delete=models.PROTECT,related_name='products')
    price=models.PositiveBigIntegerField(null=True,blank=True)
    description=models.TextField(blank=True)
    composition=models.TextField(blank=True)
    history=models.TextField(blank=True)
    image=models.ImageField(upload_to='products/',blank=True,null=True)
    image_path=models.CharField(max_length=180,blank=True,help_text='Path gambar bawaan dari static/images/products.')
    stock=models.PositiveIntegerField(default=0)
    is_active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta: ordering=['category_id','name']
    def __str__(self): return self.name
    @property
    def is_purchasable(self): return self.is_active and self.price is not None and self.price > 0 and self.stock > 0
    @property
    def photo_url(self):
        if self.image: return self.image.url
        if self.image_path: return '/static/images/products/'+self.image_path
        return '/static/images/placeholder-food.svg'

class Cart(models.Model):
    customer=models.OneToOneField(User,on_delete=models.CASCADE,related_name='cart')
    updated_at=models.DateTimeField(auto_now=True)
    def total(self): return sum((i.subtotal for i in self.items.select_related('product')),Decimal('0'))

class CartItem(models.Model):
    cart=models.ForeignKey(Cart,on_delete=models.CASCADE,related_name='items')
    product=models.ForeignKey(Product,on_delete=models.PROTECT)
    quantity=models.PositiveIntegerField(default=1)
    note=models.CharField(max_length=240,blank=True)
    class Meta: unique_together=('cart','product')
    @property
    def subtotal(self): return (self.product.price or 0)*self.quantity

class Order(models.Model):
    FULFILLMENT=[('DELIVERY','Pengiriman'),('PICKUP','Ambil di toko')]
    STATUS=[('WAITING_PAYMENT','Menunggu Pembayaran'),('WAITING_CONFIRMATION','Menunggu Konfirmasi'),('PROCESSING','Diproses'),('READY','Siap Diambil/Dikirim'),('COMPLETED','Selesai'),('CANCELLED','Dibatalkan')]
    customer=models.ForeignKey(User,on_delete=models.PROTECT,related_name='orders')
    code=models.CharField(max_length=22,unique=True)
    status=models.CharField(max_length=24,choices=STATUS,default='WAITING_PAYMENT')
    fulfillment=models.CharField(max_length=12,choices=FULFILLMENT)
    recipient=models.CharField(max_length=120,blank=True)
    recipient_phone=models.CharField(max_length=25,blank=True)
    delivery_address=models.TextField(blank=True)
    customer_note=models.TextField(blank=True)
    subtotal=models.PositiveBigIntegerField(default=0)
    shipping_fee=models.PositiveBigIntegerField(default=0)
    total=models.PositiveBigIntegerField(default=0)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta: ordering=['-created_at']
    @property
    def get_status(self): return dict(self.STATUS).get(self.status,self.status)

class OrderItem(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name='items')
    product=models.ForeignKey(Product,on_delete=models.PROTECT)
    product_name=models.CharField(max_length=140)
    unit_price=models.PositiveBigIntegerField()
    quantity=models.PositiveIntegerField()
    note=models.CharField(max_length=240,blank=True)
    @property
    def subtotal(self): return self.unit_price*self.quantity

class Payment(models.Model):
    METHOD=[('BANK_TRANSFER','Transfer Bank'),('QRIS','QRIS')]
    STATUS=[('WAITING','Menunggu Pembayaran'),('DETECTED','Pembayaran Terdeteksi'),('REVIEW','Menunggu Pemeriksaan'),('PAID','Berhasil'),('REJECTED','Ditolak'),('EXPIRED','Kedaluwarsa')]
    order=models.OneToOneField(Order,on_delete=models.CASCADE,related_name='payment')
    method=models.CharField(max_length=20,choices=METHOD)
    amount=models.PositiveBigIntegerField()
    status=models.CharField(max_length=16,choices=STATUS,default='WAITING')
    gateway_transaction_id=models.CharField(max_length=140,blank=True)
    gateway_status=models.CharField(max_length=80,blank=True)
    deadline=models.DateTimeField(default=timezone.now)
    verified_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name='verified_payments')
    verified_at=models.DateTimeField(null=True,blank=True)
    staff_note=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    def save(self,*args,**kwargs):
        if not self.deadline: self.deadline=timezone.now()+timedelta(minutes=30)
        super().save(*args,**kwargs)

class Notification(models.Model):
    recipient=models.ForeignKey(User,on_delete=models.CASCADE,related_name='notifications')
    title=models.CharField(max_length=150)
    body=models.CharField(max_length=280)
    kind=models.CharField(max_length=40,default='INFO')
    order=models.ForeignKey(Order,on_delete=models.CASCADE,null=True,blank=True)
    is_read=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['-created_at']

class BusinessProfile(models.Model):
    name=models.CharField(max_length=140,default='Kuliner Bengkulu')
    tagline=models.CharField(max_length=180,default='Cita Rasa Khas Bumi Rafflesia')
    description=models.TextField(blank=True)
    history=models.TextField(blank=True)
    address=models.CharField(max_length=255,default='Ruko UNIB Depan, Bengkulu')
    phone=models.CharField(max_length=30,default='08123456789')
    opening_hours=models.CharField(max_length=120,default='Setiap hari, 09.00–22.00 WIB')
    instagram=models.CharField(max_length=120,default='@kulinerbengkulu_')
    facebook=models.CharField(max_length=120,default='RM. Kuliner Bengkulu')
    tiktok=models.CharField(max_length=120,default='@kulinerbengkulu_')
    def __str__(self): return self.name

class Banner(models.Model):
    title=models.CharField(max_length=140)
    subtitle=models.CharField(max_length=240,blank=True)
    image=models.ImageField(upload_to='banners/',blank=True,null=True)
    is_active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.title
