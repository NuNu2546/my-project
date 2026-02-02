from django.contrib import admin
from django.urls import path
from store import views # เรียกใช้ views จากแอป store
from django.conf import settings # สำหรับตั้งค่ารูปภาพ
from django.conf.urls.static import static # สำหรับตั้งค่ารูปภาพ

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # หน้าหลัก
    path('', views.home, name='home'),
    
    # เมนูต่างๆ
    path('shop/', views.shop, name='shop'),
    path('veggie-plots/', views.veggie_plots, name='veggie_plots'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # หน้ารายละเอียดสินค้า (รับ ID)
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
]

# เพิ่มส่วนนี้เพื่อให้โชว์รูปที่อัปโหลดได้ (เฉพาะตอน Debug)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)