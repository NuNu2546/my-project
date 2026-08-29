from django.contrib import admin
from django.urls import path
from store import views
from store import staff_views
from django.conf import settings
from django.conf.urls.static import static

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
    path('cart/', views.cart, name='cart'),

    # Veggie Plot Booking
    path('plot-detail/<int:plot_id>/', views.plot_detail, name='plot_detail'),
    path('process-booking/', views.process_booking, name='process_booking'),
    path('check-booking/<int:booking_id>/', views.check_booking, name='check_booking'),
    path('booking-success/<int:booking_id>/', views.booking_success, name='booking_success'),
    path('booking/<int:booking_id>/track/', views.booking_track_detail, name='booking_track_detail'),
    path('booking/<int:booking_id>/choose-delivery/', views.choose_delivery, name='choose_delivery'),
    path('booking/<int:booking_id>/check-shipping-payment/', views.check_shipping_payment, name='check_shipping_payment'),
    path('booking/<int:booking_id>/confirm-received/', views.confirm_received, name='confirm_received'),

    # Opn Payments (Omise) — PromptPay QR
    path('create-payment/', views.create_payment, name='create_payment'),
    path('check-payment/<int:order_id>/', views.check_payment, name='check_payment'),
    path('webhook/opn/', views.opn_webhook, name='opn_webhook'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),

    # Order Tracking
    path('my-orders/', views.my_orders, name='my_orders'),
    path('track-order/', views.track_order, name='track_order'),
    path('order/<int:order_id>/track/', views.order_track_detail, name='order_track_detail'),

    # ── Staff Dashboard ─────────────────────────────────────────────────
    path('staff/', staff_views.overview, name='staff_overview'),
    # Orders
    path('staff/orders/', staff_views.orders_list, name='staff_orders'),
    path('staff/orders/<int:order_id>/', staff_views.order_detail, name='staff_order_detail'),
    path('staff/orders/<int:order_id>/action/', staff_views.order_action, name='staff_order_action'),
    path('staff/orders/<int:order_id>/update-status/', staff_views.order_update_status, name='staff_order_update_status'),
    path('staff/orders/<int:order_id>/packing-slip/', staff_views.packing_slip, name='staff_packing_slip'),
    path('staff/orders/new-count/', staff_views.new_order_count, name='staff_new_order_count'),
    # Bookings
    path('staff/bookings/', staff_views.bookings_list, name='staff_bookings'),
    path('staff/bookings/<int:booking_id>/', staff_views.booking_detail, name='staff_booking_detail'),
    path('staff/bookings/<int:booking_id>/action/', staff_views.booking_action, name='staff_booking_action'),
    # Products
    path('staff/products/', staff_views.products_list, name='staff_products'),
    path('staff/products/bulk-save/', staff_views.products_bulk_save, name='staff_products_bulk_save'),
    path('staff/products/restock/', staff_views.product_restock, name='staff_product_restock'),
    path('staff/products/add/', staff_views.product_add, name='staff_product_add'),
    path('staff/products/toggle-active/', staff_views.product_toggle_active, name='staff_product_toggle_active'),
    # Chat
    path('staff/chat/', staff_views.chat_rooms, name='staff_chat'),
    path('staff/chat/<int:room_id>/send/', staff_views.chat_staff_send, name='staff_chat_send'),
    path('staff/chat/<int:room_id>/poll/', staff_views.chat_poll_staff, name='staff_chat_poll'),
    path('staff/chat/<int:room_id>/close/', staff_views.chat_close_room, name='staff_chat_close'),

    # Customer Chat API
    path('chat/get-room/', views.chat_get_or_create_room, name='chat_get_or_create_room'),
    path('chat/send/', views.chat_send_message, name='chat_send_message'),
    path('chat/poll/<int:room_id>/', views.chat_poll, name='chat_poll'),

    # Coins API
    path('coins/balance/', views.coin_balance, name='coin_balance'),
    path('coins/donate/', views.coin_donate, name='coin_donate'),

    # Review API
    path('product/<int:product_id>/reviews/', views.product_reviews_api, name='product_reviews_api'),
    path('order/<int:order_id>/review/<int:product_id>/', views.submit_review, name='submit_review'),

    # Static video with Range request support
    path('media/video/<str:filename>', views.serve_video, name='serve_video'),

    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
