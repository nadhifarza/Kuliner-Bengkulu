from django.test import TestCase,Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Category,Product
class StoreSmokeTests(TestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user(username='buyer@example.com',email='buyer@example.com',password='StrongPass123!',email_verified=True,role='CUSTOMER')
        c=Category.objects.create(name='Kue',slug='kue')
        Product.objects.create(name='By Tat',slug='by-tat-test',category=c,price=15000,stock=3,is_active=True)
    def test_login_required_catalog(self):
        r=self.client.get(reverse('catalog')); self.assertEqual(r.status_code,302)
    def test_customer_catalog(self):
        self.client.login(username='buyer@example.com',password='StrongPass123!')
        r=self.client.get(reverse('catalog')); self.assertEqual(r.status_code,200); self.assertContains(r,'By Tat')
