from django.contrib import admin
from django.urls import path
from store import views 
from django.conf import settings 
from django.conf.urls.static import static 

urlpatterns = [
    # --- 1. System Admin (หน้ามาตรฐาน Django) ---
    path('admin/', admin.site.urls),
    
    # --- 2. หน้าเว็บหลัก (User Interface) ---
    path('', views.home, name='home'),
    path('shop/', views.shop, name='shop'),
    path('veggie-plots/', views.veggie_plots, name='veggie_plots'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('plot-detail/', views.plot_detail, name='plot_detail'),
    path('cart/', views.cart, name='cart'),

    # --- 3. ระบบสมาชิก (Authentication) ---
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('process-booking/', views.process_booking, name='process_booking'),

    # --- 4. 🟢 Quantum Admin Dashboard (หน้าสุดล้ำที่เราทำใหม่) 🟢 ---
    # หน้าแสดงตารางรวม (List Views)
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-dashboard/users/', views.admin_users_view, name='admin_users'),
    path('admin-dashboard/orders/', views.admin_orders_view, name='admin_orders'),
    path('admin-dashboard/plots/', views.admin_plots_view, name='admin_plots'),
    path('admin-dashboard/products/', views.admin_products_view, name='admin_products'),
    
    # ระบบลบข้อมูล - ใช้ admin_delete_handler
    path('admin-dashboard/delete/<str:model_type>/<int:item_id>/', views.admin_delete_handler, name='admin_delete'),

    # ใน urlpatterns ของไฟล์ urls.py
    path('admin-dashboard/manage/<str:model_type>/', views.admin_manager_view, name='admin_add'),
    path('admin-dashboard/manage/<str:model_type>/<int:item_id>/', views.admin_manager_view, name='admin_edit'),
    path('admin-dashboard/delete/<str:model_type>/<int:item_id>/', views.admin_delete_handler, name='admin_delete'),
]

# สำหรับแสดงรูปภาพในเครื่องตอนพัฒนา
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)