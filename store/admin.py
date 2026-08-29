from decimal import Decimal, InvalidOperation
from datetime import timedelta

from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from .models import (
    Product, Order, OrderItem, OrderStatusHistory,
    Plot, Plant, PlotBooking, PlotBookingStatusHistory,
    StockMovement,
    CoinWallet, CoinTransaction, TreeDonation,
    ProductReview, UserProfile,
    BOOKING_CARRIER_CHOICES,
)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price', 'stock_quantity', 'is_active')
    list_display_links = ('id', 'name')
    list_filter = ('category', 'is_active')
    search_fields = ('name',)
    list_editable = ('price', 'stock_quantity', 'is_active')
    ordering = ('id',)
    readonly_fields = ('created_at', 'updated_at')


# ── Order admin ─────────────────────────────────────────────────────────────

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_id', 'product_name', 'price', 'quantity')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ('status', 'note', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.action(description='ทำเครื่องหมายว่าจัดส่งแล้ว (shipped)')
def mark_as_shipped(modeladmin, request, queryset):
    for order in queryset.exclude(status='shipped'):
        order.status = 'shipped'
        order.save()


@admin.action(description='จัดส่งสำเร็จ (delivered)')
def mark_as_delivered(modeladmin, request, queryset):
    for order in queryset.exclude(status='delivered'):
        order.status = 'delivered'
        order.save()


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'customer_name', 'phone', 'total',
        'status', 'tracking_number', 'shipping_carrier', 'created_at',
    )
    list_display_links = ('id', 'customer_name')
    list_filter = ('status', 'shipping_carrier')
    search_fields = ('id', 'customer_name', 'phone', 'charge_id', 'tracking_number')
    list_editable = ('status', 'tracking_number', 'shipping_carrier')
    readonly_fields = ('charge_id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    actions = [mark_as_shipped, mark_as_delivered]


# ── Plot Booking admin ───────────────────────────────────────────────────────

@admin.register(Plot)
class PlotAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'size', 'sun_type', 'price_per_day', 'is_active')
    list_editable = ('price_per_day', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')
    ordering = ('code',)


@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    list_display = ('name', 'grow_days', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('name',)


class PlotBookingStatusHistoryInline(admin.TabularInline):
    model = PlotBookingStatusHistory
    extra = 0
    readonly_fields = ('status', 'note', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.action(description='เปลี่ยนสถานะเป็น กำลังปลูก (growing)')
def mark_booking_growing(modeladmin, request, queryset):
    for b in queryset.filter(status='paid'):
        b.status = 'growing'
        b.save()


@admin.action(description='เปลี่ยนสถานะเป็น พร้อมเก็บเกี่ยว (ready_to_harvest)')
def mark_booking_ready(modeladmin, request, queryset):
    for b in queryset.filter(status='growing'):
        b.status = 'ready_to_harvest'
        b.save()


@admin.action(description='เก็บเกี่ยวแล้ว (harvested) — กรอกน้ำหนักผลผลิต')
def mark_booking_harvested(modeladmin, request, queryset):
    if 'apply' in request.POST:
        weight_str = request.POST.get('harvest_weight', '').strip()
        harvest_weight = None
        if weight_str:
            try:
                harvest_weight = Decimal(weight_str)
            except InvalidOperation:
                modeladmin.message_user(request, 'น้ำหนักผลผลิตไม่ถูกต้อง', level='error')
                return
        updated = 0
        for b in queryset.filter(status='ready_to_harvest'):
            if harvest_weight is not None:
                b.harvest_weight = harvest_weight
            b.pickup_deadline = b.harvest_date + timedelta(days=7)
            b.status = 'harvested'
            b.save()
            updated += 1
        modeladmin.message_user(request, f'อัปเดต {updated} รายการเป็น harvested เรียบร้อย')
        return
    # Intermediate form
    csrf = request.META.get('CSRF_COOKIE', '')
    hidden_ids = ''.join(f'<input type="hidden" name="_selected_action" value="{b.pk}">' for b in queryset)
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>เก็บเกี่ยวแล้ว</title>
<link rel="stylesheet" href="/static/admin/css/base.css">
</head><body><div style="padding:24px;max-width:500px">
<h2>เก็บเกี่ยวแล้ว — กรอกน้ำหนักผลผลิต</h2>
<p>จะอัปเดต {queryset.count()} รายการ (เฉพาะที่มีสถานะ ready_to_harvest)</p>
<form method="post">
<input type="hidden" name="csrfmiddlewaretoken" value="{csrf}">
<input type="hidden" name="action" value="mark_booking_harvested">
{hidden_ids}
<p><label>น้ำหนักผลผลิต (กก.) — ไม่บังคับ:</label><br>
<input type="number" name="harvest_weight" step="0.01" min="0" style="width:200px;padding:6px"></p>
<input type="hidden" name="apply" value="1">
<button type="submit" style="padding:8px 20px;background:#417690;color:#fff;border:none;border-radius:4px;cursor:pointer">ยืนยัน</button>
&nbsp;<a href="javascript:history.back()">ยกเลิก</a>
</form></div></body></html>"""
    return HttpResponse(html)


@admin.action(description='กำลังแพ็คผลผลิต (preparing)')
def mark_booking_preparing(modeladmin, request, queryset):
    for b in queryset.filter(status__in=['awaiting_shipping_payment', 'harvested']):
        if b.delivery_method == 'shipping' or b.status == 'awaiting_shipping_payment':
            b.status = 'preparing'
            b.save()


@admin.action(description='จัดส่งแล้ว (shipped) — กรอกเลขพัสดุ')
def mark_booking_shipped(modeladmin, request, queryset):
    if 'apply' in request.POST:
        tracking_number  = request.POST.get('tracking_number', '').strip()
        shipping_carrier = request.POST.get('shipping_carrier', '').strip()
        if not tracking_number:
            modeladmin.message_user(request, 'กรุณากรอกเลขพัสดุ', level='error')
            return
        updated = 0
        for b in queryset.filter(status='preparing'):
            b.tracking_number  = tracking_number
            b.shipping_carrier = shipping_carrier
            b.status           = 'shipped'
            b.save()
            updated += 1
        modeladmin.message_user(request, f'อัปเดต {updated} รายการเป็น shipped เรียบร้อย')
        return
    # Intermediate form
    carrier_options = ''.join(f'<option value="{v}">{l}</option>' for v, l in BOOKING_CARRIER_CHOICES)
    hidden_ids = ''.join(f'<input type="hidden" name="_selected_action" value="{b.pk}">' for b in queryset)
    csrf = request.META.get('CSRF_COOKIE', '')
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>จัดส่งแล้ว</title>
<link rel="stylesheet" href="/static/admin/css/base.css">
</head><body><div style="padding:24px;max-width:500px">
<h2>จัดส่งแล้ว — กรอกข้อมูลพัสดุ</h2>
<p>จะอัปเดต {queryset.count()} รายการ (เฉพาะที่มีสถานะ preparing)</p>
<form method="post">
<input type="hidden" name="csrfmiddlewaretoken" value="{csrf}">
<input type="hidden" name="action" value="mark_booking_shipped">
{hidden_ids}
<p><label>เลขพัสดุ (บังคับ):</label><br>
<input type="text" name="tracking_number" style="width:300px;padding:6px" required></p>
<p><label>ขนส่ง:</label><br>
<select name="shipping_carrier" style="width:300px;padding:6px">
<option value="">— เลือก —</option>{carrier_options}</select></p>
<input type="hidden" name="apply" value="1">
<button type="submit" style="padding:8px 20px;background:#417690;color:#fff;border:none;border-radius:4px;cursor:pointer">ยืนยัน</button>
&nbsp;<a href="javascript:history.back()">ยกเลิก</a>
</form></div></body></html>"""
    return HttpResponse(html)


@admin.action(description='ได้รับผลผลิตแล้ว (delivered)')
def mark_booking_delivered(modeladmin, request, queryset):
    for b in queryset.filter(status='shipped'):
        b.status = 'delivered'
        b.save()


@admin.action(description='เสร็จสิ้น (completed)')
def mark_booking_completed(modeladmin, request, queryset):
    for b in queryset.filter(status__in=['delivered', 'ready_for_pickup']):
        b.status = 'completed'
        b.save()


@admin.register(PlotBooking)
class PlotBookingAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'plot', 'plant', 'customer_name', 'phone',
        'start_date', 'harvest_date', 'status',
        'delivery_method', 'tracking_number', 'created_at',
    )
    list_display_links = ('id', 'customer_name')
    list_filter = ('status', 'delivery_method', 'plot')
    search_fields = ('customer_name', 'phone', 'charge_id', 'tracking_number')
    readonly_fields = (
        'charge_id', 'shipping_charge_id',
        'created_at', 'updated_at', 'total_price', 'harvest_date',
    )
    ordering = ('-created_at',)
    inlines = [PlotBookingStatusHistoryInline]
    actions = [
        mark_booking_growing,
        mark_booking_ready,
        mark_booking_harvested,
        mark_booking_preparing,
        mark_booking_shipped,
        mark_booking_delivered,
        mark_booking_completed,
    ]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display  = ('product', 'change', 'reason', 'order', 'staff', 'created_at')
    list_filter   = ('reason',)
    search_fields = ('product__name', 'note')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


# ── Coins admin ──────────────────────────────────────────────────────────────

class CoinTransactionInline(admin.TabularInline):
    model = CoinTransaction
    extra = 0
    readonly_fields = ('amount', 'reason', 'order', 'booking', 'note', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(CoinWallet)
class CoinWalletAdmin(admin.ModelAdmin):
    list_display  = ('id', 'session_key', 'balance', 'total_earned', 'total_donated', 'created_at')
    search_fields = ('session_key',)
    readonly_fields = ('session_key', 'balance', 'total_earned', 'total_donated', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    inlines = [CoinTransactionInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CoinTransaction)
class CoinTransactionAdmin(admin.ModelAdmin):
    list_display  = ('id', 'wallet', 'amount', 'reason', 'order', 'booking', 'created_at')
    list_filter   = ('reason',)
    search_fields = ('wallet__session_key', 'note')
    readonly_fields = ('wallet', 'amount', 'reason', 'order', 'booking', 'note', 'created_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TreeDonation)
class TreeDonationAdmin(admin.ModelAdmin):
    list_display = ('id', 'total_coins_donated', 'goal', 'updated_at')
    readonly_fields = ('total_coins_donated', 'updated_at')
    fields = ('total_coins_donated', 'goal', 'updated_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'customer_name', 'rating', 'is_visible', 'created_at')
    list_display_links = ('id', 'product')
    list_filter = ('rating', 'is_visible')
    list_editable = ('is_visible',)
    search_fields = ('customer_name', 'product__name')
    readonly_fields = ('product', 'order', 'customer_name', 'rating', 'comment', 'created_at')
    ordering = ('-created_at',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'phone', 'created_at')
    list_display_links = ('id', 'user')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone')
    readonly_fields = ('user', 'created_at')
    ordering = ('-created_at',)

