from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User,Address,Category,Product,Cart,CartItem,Order,OrderItem,Payment,Notification,BusinessProfile,Banner
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets=UserAdmin.fieldsets+(('Kuliner Bengkulu',{'fields':('role','phone','email_verified')}),)
    list_display=('username','email','role','email_verified','is_staff')
admin.site.register([Address,Category,Product,Cart,CartItem,Order,OrderItem,Payment,Notification,BusinessProfile,Banner])
