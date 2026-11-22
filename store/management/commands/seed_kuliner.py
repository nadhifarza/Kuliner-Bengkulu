from django.core.management.base import BaseCommand
from django.utils.text import slugify
from store.models import Category,Product,BusinessProfile

MENUS={
'Makanan Utama':[
('Pendap','pendap',None,0,''),('Bagar Hiu','bagar_hiu', 'bagar_hiu.jpg',0,''),('Lema','lema','lema.jpg',0,''),
('Santan Palak Ikan','santan-palak-ikan','santan_palak_ikan.jpg',0,''),('Tempoyak','tempoyak','tempoyak.jpg',0,''),('Rendang Lokan','rendang-lokan','rendang_lokan.jpg',0,'')],
'Kue':[
('By Tat','by-tat','by_tat.jpg',0,''),('Perut Punai','perut-punai','perut_punai.jpg',0,''),('Lepek Binti','lepek-binti','lepek_binti.jpg',0,''),('Cucur Payung','cucur-payung','cucur_payung.jpg',0,''),('Lemang Tapai','lemang-tapai','lemang_tapai.jpg',0,''),('Lempuk Durian','lempuk-durian','lempuk_durian.jpg',0,''),('Kerupuk Tuiri','kerupuk-tuiri','kerupuk_tuiri.jpg',0,''),('Gelamai','gelamai','gelamai.jpg',0,''),('Bubur Sekoi','bubur-sekoi','bubur_sekoi.jpg',0,''),('Kembang Goyang','kembang-goyang','kembang_goyang.jpg',0,''),('Bolu Koja','bolu-koja','bolu_koja.jpg',0,''),('Cucur Pandan','cucur-pandan','cucur_pandan.jpg',0,''),('Lupis','lupis','lupis.jpg',0,''),('Emping Melinjo','emping-melinjo','emping_melinjo.jpg',0,'')],
'Minuman':[
('Sirup Kalamansi','sirup-kalamansi','sirup_kalamansi.jpg',0,''),('Kopi Robusta','kopi-robusta','kopi_robusta.jpg',0,''),('Es Jeruk Kalamansi','es-jeruk-kalamansi','es_jeruk_kalamansi.jpg',0,'')]
}
class Command(BaseCommand):
    help='Membuat kategori dan 23 menu awal Kuliner Bengkulu tanpa mengarang harga/stok.'
    def handle(self,*args,**options):
        for name,items in MENUS.items():
            cat,_=Category.objects.get_or_create(name=name,defaults={'slug':slugify(name)})
            for title,slug,img,price,desc in items:
                Product.objects.get_or_create(slug=slug,defaults={'name':title,'category':cat,'image_path':img or '', 'price':None,'stock':0,'description':'Deskripsi produk belum dilengkapi. Silakan lengkapi melalui dashboard admin.','composition':'Komposisi belum dilengkapi.','history':'Informasi sejarah/asal-usul belum dilengkapi.'})
        if not BusinessProfile.objects.exists(): BusinessProfile.objects.create(description='Kuliner Bengkulu menghadirkan beragam makanan, kue, jajanan, dan minuman tradisional khas Bengkulu.',history='Sejarah usaha dapat dilengkapi melalui pengaturan profil usaha.')
        self.stdout.write(self.style.SUCCESS('Berhasil menambahkan 23 menu dalam 3 kategori. Harga dan stok sengaja dibiarkan belum diatur.'))
