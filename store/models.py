from django.conf import settings as django_settings
from django.db import models


BOOKING_STATUS_CHOICES = [
    ('pending',                   'รอชำระเงิน'),
    ('paid',                      'ยืนยันการจอง'),
    ('growing',                   'กำลังปลูก'),
    ('ready_to_harvest',          'พร้อมเก็บเกี่ยว'),
    ('harvested',                 'เก็บเกี่ยวแล้ว รอเลือกวิธีรับ'),
    ('awaiting_shipping_payment', 'รอชำระค่าจัดส่ง'),
    ('preparing',                 'กำลังแพ็คผลผลิต'),
    ('shipped',                   'จัดส่งแล้ว'),
    ('delivered',                 'ได้รับผลผลิตแล้ว'),
    ('ready_for_pickup',          'รอรับที่สวน'),
    ('completed',                 'เสร็จสิ้น'),
    ('cancelled',                 'ยกเลิก'),
    ('expired',                   'หมดอายุ'),
]

DELIVERY_METHOD_CHOICES = [
    ('pickup',   'มารับเองที่สวน'),
    ('shipping', 'จัดส่งถึงบ้าน'),
]

BOOKING_CARRIER_CHOICES = [
    ('kerry',         'Kerry Express'),
    ('flash',         'Flash Express'),
    ('jnt',           'J&T Express'),
    ('thailand_post', 'ไปรษณีย์ไทย'),
    ('other',         'อื่นๆ'),
]

ORDER_STATUS_CHOICES = [
    ('pending',    'รอชำระเงิน'),
    ('paid',       'ชำระแล้ว กำลังเตรียมสินค้า'),
    ('shipped',    'จัดส่งแล้ว'),
    ('in_transit', 'กำลังนำส่ง'),
    ('delivered',  'จัดส่งสำเร็จ'),
    ('cancelled',  'ยกเลิก'),
    ('failed',     'ล้มเหลว'),
    ('expired',    'หมดอายุ'),
]

ORDER_CARRIER_CHOICES = [
    ('kerry',         'Kerry Express'),
    ('flash',         'Flash Express'),
    ('jnt',           'J&T Express'),
    ('thailand_post', 'ไปรษณีย์ไทย'),
    ('other',         'อื่นๆ'),
]


PRODUCT_CATEGORY_CHOICES = [
    ('tools',   'เครื่องมือทำสวน'),
    ('seeds',   'เมล็ดพันธุ์'),
    ('natural', 'ผลิตภัณฑ์ธรรมชาติ'),
    ('aroma',   'อโรมาเธอราพี'),
    ('flowers', 'ดอกไม้แห้ง'),
]


class Product(models.Model):
    CATEGORY_CHOICES = PRODUCT_CATEGORY_CHOICES

    name           = models.CharField(max_length=200, verbose_name='ชื่อสินค้า')
    slug           = models.SlugField(max_length=220, blank=True, verbose_name='Slug')
    price          = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='ราคา')
    image          = models.CharField(max_length=200, default='default.png', verbose_name='รูปภาพ')
    description    = models.TextField(verbose_name='รายละเอียด', blank=True)
    category       = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True, verbose_name='หมวดหมู่')
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name='สต๊อก')
    is_active      = models.BooleanField(default=True, verbose_name='เปิดขาย')
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'สินค้า'
        verbose_name_plural = 'สินค้า'

    def __str__(self):
        return self.name

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0

    @property
    def is_low_stock(self):
        return 0 < self.stock_quantity < 5


STOCK_REASON_CHOICES = [
    ('sale',    'ขาย'),
    ('return',  'คืนสต๊อก'),
    ('restock', 'เติมสต๊อก'),
    ('adjust',  'ปรับยอด'),
]


class StockMovement(models.Model):
    REASON_CHOICES = STOCK_REASON_CHOICES

    product    = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='movements', verbose_name='สินค้า')
    change     = models.IntegerField(verbose_name='จำนวนเปลี่ยนแปลง (+/-)')
    reason     = models.CharField(max_length=20, choices=REASON_CHOICES, verbose_name='เหตุผล')
    order      = models.ForeignKey('Order', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='ออเดอร์')
    note       = models.TextField(blank=True, verbose_name='หมายเหตุ')
    staff      = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        verbose_name='สต๊าฟ',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'ความเคลื่อนไหวสต๊อก'
        verbose_name_plural = 'ความเคลื่อนไหวสต๊อก'

    def __str__(self):
        sign = '+' if self.change >= 0 else ''
        return f'{self.product.name} {sign}{self.change} ({self.get_reason_display()})'


class Order(models.Model):
    STATUS_CHOICES = ORDER_STATUS_CHOICES
    CARRIER_CHOICES = ORDER_CARRIER_CHOICES

    user = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='orders',
    )
    customer_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True, verbose_name='เบอร์โทร')
    address = models.TextField(blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='สถานะ',
    )
    charge_id = models.CharField(max_length=100, blank=True)
    session_key = models.CharField(max_length=40, blank=True, db_index=True)
    tracking_number = models.CharField(max_length=100, blank=True, verbose_name='เลขพัสดุ')
    shipping_carrier = models.CharField(
        max_length=20, choices=CARRIER_CHOICES, blank=True, verbose_name='ขนส่ง',
    )
    is_viewed_by_staff = models.BooleanField(default=False, verbose_name='เปิดดูแล้ว')
    staff_note = models.TextField(blank=True, verbose_name='หมายเหตุภายใน (staff เท่านั้น)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = self.status

    _STOCK_DEDUCTED_STATUSES = frozenset({'paid', 'shipped', 'in_transit', 'delivered'})
    _CANCELLED_STATUSES = frozenset({'cancelled', 'expired', 'failed'})

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        prev = self._original_status
        super().save(*args, **kwargs)
        if is_new or self.status != prev:
            OrderStatusHistory.objects.create(order=self, status=self.status, note=getattr(self, '_status_note', ''), staff=getattr(self, '_status_staff', None))
            # Return stock when a previously-paid order gets cancelled/expired
            if (
                prev in self._STOCK_DEDUCTED_STATUSES
                and self.status in self._CANCELLED_STATUSES
            ):
                self._return_stock()
        self._original_status = self.status

    def _return_stock(self):
        from django.db import transaction as _tx
        existing_returns = set(
            StockMovement.objects.filter(order=self, reason='return').values_list('product_id', flat=True)
        )
        with _tx.atomic():
            for item in self.items.all():
                if item.product_id in existing_returns:
                    continue
                try:
                    product = Product.objects.select_for_update().get(pk=item.product_id)
                    product.stock_quantity += item.quantity
                    product.save(update_fields=['stock_quantity', 'updated_at'])
                    StockMovement.objects.create(
                        product=product,
                        change=+item.quantity,
                        reason='return',
                        order=self,
                        note=f'คืนสต๊อกจากออเดอร์ #{self.id} ({self.status})',
                    )
                except Product.DoesNotExist:
                    pass

    def __str__(self):
        return f'Order #{self.id} ({self.get_status_display()})'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_id = models.IntegerField()
    product_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()

    def __str__(self):
        return f'{self.product_name} ×{self.quantity}'


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='history')
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES)
    note = models.TextField(blank=True)
    staff = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name='staff ที่ดำเนินการ',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Order #{self.order_id}: {self.get_status_display()}'


# ============================================================
#  Veggie Plot Booking System
# ============================================================

class Plot(models.Model):
    code        = models.CharField(max_length=10, unique=True, verbose_name='รหัสแปลง')
    name        = models.CharField(max_length=100, verbose_name='ชื่อแปลง')
    size        = models.CharField(max_length=50, verbose_name='ขนาด')
    sun_type    = models.CharField(max_length=100, verbose_name='แสงแดด')
    price_per_day = models.DecimalField(max_digits=6, decimal_places=2, verbose_name='ราคา (฿/วัน)')
    image       = models.CharField(max_length=200, verbose_name='รูปภาพ')
    description = models.TextField(verbose_name='รายละเอียด', blank=True)
    is_active   = models.BooleanField(default=True, verbose_name='เปิดใช้งาน')

    class Meta:
        ordering = ['code']
        verbose_name = 'แปลง'
        verbose_name_plural = 'แปลงผัก'

    def __str__(self):
        return f'{self.code} — {self.name}'


class Plant(models.Model):
    name       = models.CharField(max_length=100, unique=True, verbose_name='ชื่อพืช')
    grow_days  = models.PositiveIntegerField(verbose_name='จำนวนวันจนเก็บเกี่ยว')
    seed_price = models.DecimalField(max_digits=8, decimal_places=2, default=50, verbose_name='ค่าเมล็ดพันธุ์/ต้นกล้า (฿)')
    image      = models.CharField(max_length=200, blank=True, verbose_name='รูปภาพ')
    is_active  = models.BooleanField(default=True, verbose_name='เปิดใช้งาน')

    class Meta:
        ordering = ['name']
        verbose_name = 'พืช'
        verbose_name_plural = 'รายการพืช'

    def __str__(self):
        return f'{self.name} ({self.grow_days} วัน)'


class PlotBooking(models.Model):
    STATUS_CHOICES = BOOKING_STATUS_CHOICES

    plot          = models.ForeignKey(Plot, on_delete=models.PROTECT, related_name='bookings', verbose_name='แปลง')
    plant         = models.ForeignKey(Plant, on_delete=models.PROTECT, related_name='bookings', verbose_name='พืช')
    customer_name = models.CharField(max_length=200, verbose_name='ชื่อลูกค้า')
    phone         = models.CharField(max_length=20, verbose_name='เบอร์โทร')
    start_date    = models.DateField(verbose_name='วันเริ่มปลูก')
    harvest_date  = models.DateField(verbose_name='วันคาดว่าเก็บเกี่ยว')
    total_price   = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='ราคารวม')
    status             = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending', verbose_name='สถานะ')
    charge_id          = models.CharField(max_length=100, blank=True, verbose_name='Charge ID')
    session_key        = models.CharField(max_length=40, blank=True, db_index=True)
    delivery_method    = models.CharField(max_length=10, choices=DELIVERY_METHOD_CHOICES, blank=True, verbose_name='วิธีรับผลผลิต')
    shipping_address   = models.TextField(blank=True, verbose_name='ที่อยู่จัดส่ง')
    shipping_fee       = models.DecimalField(max_digits=8, decimal_places=2, default=50, verbose_name='ค่าจัดส่ง (฿)')
    shipping_charge_id = models.CharField(max_length=100, blank=True, verbose_name='Charge ID ค่าส่ง')
    tracking_number    = models.CharField(max_length=100, blank=True, verbose_name='เลขพัสดุ')
    shipping_carrier   = models.CharField(max_length=20, choices=BOOKING_CARRIER_CHOICES, blank=True, verbose_name='ขนส่ง')
    harvest_weight     = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True, verbose_name='น้ำหนักผลผลิต (กก.)')
    pickup_deadline    = models.DateField(null=True, blank=True, verbose_name='วันสุดท้ายที่ต้องมารับ')
    user               = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='plot_bookings',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'การจองแปลง'
        verbose_name_plural = 'การจองแปลง'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = self.status

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new or self.status != self._original_status:
            PlotBookingStatusHistory.objects.create(booking=self, status=self.status, note=getattr(self, '_status_note', ''), staff=getattr(self, '_status_staff', None))
        self._original_status = self.status

    def __str__(self):
        return f'Booking #{self.id} — {self.plot.code} ({self.get_status_display()})'


class PlotBookingStatusHistory(models.Model):
    booking    = models.ForeignKey(PlotBooking, on_delete=models.CASCADE, related_name='history')
    status     = models.CharField(max_length=30, choices=BOOKING_STATUS_CHOICES)
    note       = models.TextField(blank=True)
    staff      = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name='staff ที่ดำเนินการ',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Booking #{self.booking_id}: {self.get_status_display()}'


# ============================================================
#  Chat System
# ============================================================

class ChatRoom(models.Model):
    session_key        = models.CharField(max_length=40, blank=True, db_index=True)
    user               = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name='chat_rooms',
    )
    customer_name      = models.CharField(max_length=100, blank=True, verbose_name='ชื่อลูกค้า')
    phone              = models.CharField(max_length=20, blank=True, verbose_name='เบอร์โทร')
    related_order      = models.ForeignKey(
        'Order', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='chat_rooms', verbose_name='ออเดอร์ที่เกี่ยวข้อง',
    )
    is_closed          = models.BooleanField(default=False, verbose_name='ปิดเคสแล้ว')
    unread_by_staff    = models.PositiveIntegerField(default=0)
    unread_by_customer = models.PositiveIntegerField(default=0)
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'ห้องแชท'
        verbose_name_plural = 'ห้องแชท'

    def __str__(self):
        return f'Chat #{self.id} — {self.customer_name or self.session_key[:8]}'


class ChatMessage(models.Model):
    SENDER_CHOICES = [
        ('customer', 'ลูกค้า'),
        ('staff',    'เจ้าหน้าที่'),
    ]

    room        = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender_type = models.CharField(max_length=10, choices=SENDER_CHOICES)
    sender_name = models.CharField(max_length=100, blank=True)
    message     = models.CharField(max_length=500)
    is_read     = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'ข้อความแชท'
        verbose_name_plural = 'ข้อความแชท'

    def __str__(self):
        return f'[{self.sender_type}] {self.message[:40]}'


# ============================================================
#  Coins System
# ============================================================

class CoinWallet(models.Model):
    session_key  = models.CharField(max_length=40, unique=True, db_index=True)
    user         = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name='coin_wallet',
    )
    balance      = models.IntegerField(default=0)
    total_earned = models.IntegerField(default=0)
    total_donated= models.IntegerField(default=0)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'กระเป๋า Coins'
        verbose_name_plural = 'กระเป๋า Coins'

    def __str__(self):
        return f'Wallet {self.session_key[:8]}… — {self.balance} coins'


class CoinTransaction(models.Model):
    REASON_CHOICES = [
        ('purchase', 'ได้จากการสั่งซื้อ'),
        ('donate',   'บริจาคปลูกต้นไม้'),
        ('adjust',   'ปรับโดยแอดมิน'),
    ]

    wallet    = models.ForeignKey(CoinWallet, on_delete=models.CASCADE, related_name='transactions')
    amount    = models.IntegerField()
    reason    = models.CharField(max_length=20, choices=REASON_CHOICES)
    order     = models.ForeignKey('Order', null=True, blank=True, on_delete=models.SET_NULL, related_name='coin_transactions')
    booking   = models.ForeignKey('PlotBooking', null=True, blank=True, on_delete=models.SET_NULL, related_name='coin_transactions')
    note      = models.TextField(blank=True)
    created_at= models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'รายการ Coins'
        verbose_name_plural = 'รายการ Coins'

    def __str__(self):
        sign = '+' if self.amount >= 0 else ''
        return f'{sign}{self.amount} ({self.get_reason_display()})'


class TreeDonation(models.Model):
    """Singleton — always pk=1. Stores the site-wide total of donated coins."""
    total_coins_donated = models.IntegerField(default=0)
    goal                = models.IntegerField(default=10000)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'ยอดบริจาคปลูกต้นไม้'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={'total_coins_donated': 0, 'goal': 10000})
        return obj

    def __str__(self):
        return f'TreeDonation: {self.total_coins_donated}/{self.goal}'


# ============================================================
#  Product Review System
# ============================================================

class UserProfile(models.Model):
    user            = models.OneToOneField(
        django_settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='userprofile',
        verbose_name='ผู้ใช้',
    )
    phone           = models.CharField(max_length=20, blank=True, verbose_name='เบอร์โทร')
    default_address = models.TextField(blank=True, verbose_name='ที่อยู่เริ่มต้น')
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'ข้อมูลสมาชิก'
        verbose_name_plural = 'ข้อมูลสมาชิก'

    def __str__(self):
        return f'Profile of {self.user.get_full_name() or self.user.username}'


class ProductReview(models.Model):
    product       = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name='สินค้า')
    order         = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='reviews', verbose_name='ออเดอร์')
    customer_name = models.CharField(max_length=100, verbose_name='ชื่อผู้รีวิว')
    rating        = models.PositiveSmallIntegerField(verbose_name='คะแนน (1-5)')
    comment       = models.TextField(max_length=1000, blank=True, verbose_name='ความคิดเห็น')
    is_visible    = models.BooleanField(default=True, verbose_name='แสดงรีวิว')
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('product', 'order')
        verbose_name = 'รีวิวสินค้า'
        verbose_name_plural = 'รีวิวสินค้า'

    def __str__(self):
        return f'รีวิว {self.product.name} by {self.customer_name} ({self.rating}★)'
