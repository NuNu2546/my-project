from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from store.models import (
    ChatMessage, ChatRoom,
    CoinTransaction, CoinWallet,
    Order, OrderItem,
    Plant, Plot,
    PlotBooking,
    Product, ProductReview,
    StockMovement, TreeDonation,
)

User = get_user_model()

DEMO_SESSION = 'demo_seed_00000000000000000000000001'
DEMO_EMAIL   = 'demo@digitalgarden.th'


class Command(BaseCommand):
    help = 'Seed realistic Thai demo data (orders, bookings, chat, coins). Use --reset to refresh.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                            help='Delete existing demo data before seeding')

    def handle(self, *args, **options):
        if options['reset']:
            self._reset()

        with transaction.atomic():
            self._ensure_base()
            demo_user, wallet = self._setup_user()
            orders   = self._create_orders(demo_user, wallet)
            bookings = self._create_bookings(demo_user, wallet)
            self._create_reviews(orders)
            self._create_chats(demo_user, orders)
            self._setup_donations()

        self.stdout.write(self.style.SUCCESS(
            f'\nDemo seeded: {len(orders)} orders, {len(bookings)} bookings\n'
            f'  Login : {DEMO_EMAIL} / Demo1234!\n'
            f'  Reset : python manage.py seed_demo --reset\n'
            f'  Pay   : python manage.py mark_order_paid <id>\n'
        ))

    # ────────────────────────────────────────────────────────────────
    # Reset
    # ────────────────────────────────────────────────────────────────

    def _reset(self):
        demo_user = User.objects.filter(email=DEMO_EMAIL).first()

        base_q_orders   = Q(session_key=DEMO_SESSION)
        base_q_bookings = Q(session_key=DEMO_SESSION)
        base_q_rooms    = Q(session_key__startswith='demo_seed_')
        base_q_wallets  = Q(session_key=DEMO_SESSION)

        if demo_user:
            base_q_orders   |= Q(user=demo_user)
            base_q_bookings |= Q(user=demo_user)
            base_q_rooms    |= Q(user=demo_user)
            base_q_wallets  |= Q(user=demo_user)

        n_o = Order.objects.filter(base_q_orders).count()
        n_b = PlotBooking.objects.filter(base_q_bookings).count()

        Order.objects.filter(base_q_orders).delete()
        PlotBooking.objects.filter(base_q_bookings).delete()
        ChatRoom.objects.filter(base_q_rooms).delete()
        CoinWallet.objects.filter(base_q_wallets).delete()

        if demo_user:
            demo_user.delete()

        self.stdout.write(f'Reset: deleted {n_o} orders, {n_b} bookings')

    # ────────────────────────────────────────────────────────────────
    # Base data
    # ────────────────────────────────────────────────────────────────

    def _ensure_base(self):
        if not Product.objects.filter(is_active=True).exists():
            call_command('seed_products', stdout=self.stdout)
        if not Plot.objects.exists():
            call_command('seed_plots', stdout=self.stdout)
        # Top up stock so demo orders can deduct freely
        Product.objects.filter(is_active=True, stock_quantity__lt=30).update(stock_quantity=50)

    # ────────────────────────────────────────────────────────────────
    # Demo user + wallet
    # ────────────────────────────────────────────────────────────────

    def _setup_user(self):
        user, _ = User.objects.get_or_create(
            email=DEMO_EMAIL,
            defaults={'username': 'demo_customer', 'first_name': 'สมชาย', 'last_name': 'ไทยดี'},
        )
        user.set_password('Demo1234!')
        user.save(update_fields=['password'])

        wallet, _ = CoinWallet.objects.get_or_create(
            session_key=DEMO_SESSION,
            defaults={'user': user, 'balance': 0, 'total_earned': 0, 'total_donated': 50},
        )
        if not wallet.user_id:
            CoinWallet.objects.filter(pk=wallet.pk).update(user=user)
        return user, wallet

    # ────────────────────────────────────────────────────────────────
    # Orders
    # ────────────────────────────────────────────────────────────────

    def _create_orders(self, demo_user, wallet):
        def _prods(cat, n=4):
            return list(Product.objects.filter(category=cat, is_active=True).order_by('id')[:n])

        tools   = _prods('tools')
        seeds   = _prods('seeds')
        natural = _prods('natural')
        aroma   = _prods('aroma')

        def p(lst, idx=0):
            return lst[idx] if idx < len(lst) else (lst[0] if lst else None)

        ORDER_SPECS = [
            dict(
                customer_name='สุดา พวงมาลัย',
                phone='081-234-5678',
                address='12/3 ถนนรัชดาภิเษก แขวงลาดยาว เขตจตุจักร กรุงเทพฯ 10900',
                status='pending', days_ago=0,
                items=[(p(tools, 0), 1), (p(seeds, 0), 2)],
            ),
            dict(
                customer_name='นิรัน สุขสบาย',
                phone='089-876-5432',
                address='45 ซอยลาดพร้าว 71 แขวงลาดพร้าว เขตลาดพร้าว กรุงเทพฯ 10230',
                status='paid', days_ago=3,
                items=[(p(tools, 1), 1), (p(natural, 0), 1), (p(seeds, 1), 3)],
            ),
            dict(
                customer_name='ประภาส ทรัพย์สมบูรณ์',
                phone='095-111-2233',
                address='7/8 ถนนงามวงศ์วาน แขวงทุ่งสองห้อง เขตหลักสี่ กรุงเทพฯ 10210',
                status='shipped', days_ago=5,
                tracking_number='EF789012345TH', shipping_carrier='thaipost',
                items=[(p(tools, 2), 2), (p(aroma, 0), 1)],
            ),
            dict(
                customer_name='มาลีวัลย์ รักต้นไม้',
                phone='062-555-8899',
                address='90 ถนนพหลโยธิน แขวงสามเสนใน เขตพญาไท กรุงเทพฯ 10400',
                status='in_transit', days_ago=4,
                tracking_number='GH456789012TH', shipping_carrier='flash',
                items=[(p(natural, 1), 1), (p(seeds, 2), 2), (p(tools, 3), 1)],
            ),
            dict(
                customer_name='สุรีย์ ใจดี',
                phone='083-777-4455',
                address='55/10 ถนนสุขุมวิท 77 แขวงพระโขนงเหนือ เขตวัฒนา กรุงเทพฯ 10260',
                status='delivered', days_ago=10,
                items=[(p(tools, 0), 1), (p(aroma, 0), 2), (p(natural, 0), 1)],
            ),
            dict(
                customer_name='อรพินท์ มณีรัตน์',
                phone='076-333-9900',
                address='3/1 ถนนแจ้งวัฒนะ แขวงทุ่งสองห้อง เขตหลักสี่ กรุงเทพฯ 10210',
                status='cancelled', days_ago=7,
                items=[(p(seeds, 0), 1), (p(seeds, 1), 2)],
            ),
        ]

        paid_statuses = frozenset({'paid', 'shipped', 'in_transit', 'delivered'})
        created = []

        for spec in ORDER_SPECS:
            items_raw = [(prod, qty) for prod, qty in spec['items'] if prod is not None]
            if not items_raw:
                continue

            total = sum(prod.price * qty for prod, qty in items_raw)

            order = Order(
                user=demo_user,
                session_key=DEMO_SESSION,
                customer_name=spec['customer_name'],
                phone=spec['phone'],
                address=spec['address'],
                total=total,
                status=spec['status'],
                tracking_number=spec.get('tracking_number', ''),
                shipping_carrier=spec.get('shipping_carrier', ''),
                staff_note='[DEMO] ข้อมูลทดสอบ',
            )
            order._status_note = 'สร้างโดย seed_demo'
            order.save()

            if spec['days_ago'] > 0:
                Order.objects.filter(pk=order.pk).update(
                    created_at=timezone.now() - timedelta(days=spec['days_ago'])
                )

            for prod, qty in items_raw:
                OrderItem.objects.create(
                    order=order,
                    product_id=prod.pk,
                    product_name=prod.name,
                    price=prod.price,
                    quantity=qty,
                )

            if spec['status'] in paid_statuses:
                self._deduct_stock(order, items_raw)
                coins = int(order.total) // 50
                if coins > 0 and not CoinTransaction.objects.filter(order=order, reason='purchase').exists():
                    CoinTransaction.objects.create(
                        wallet=wallet, amount=coins, reason='purchase', order=order,
                        note=f'ได้รับจากออเดอร์ #{order.id}',
                    )
                    CoinWallet.objects.filter(pk=wallet.pk).update(
                        balance=F('balance') + coins,
                        total_earned=F('total_earned') + coins,
                    )

            created.append(order)

        return created

    def _deduct_stock(self, order, items_raw):
        for prod, qty in items_raw:
            product = Product.objects.select_for_update().get(pk=prod.pk)
            product.stock_quantity = max(0, product.stock_quantity - qty)
            product.save(update_fields=['stock_quantity', 'updated_at'])
            StockMovement.objects.create(
                product=product, change=-qty, reason='sale', order=order,
                note='หักสต๊อกจาก seed_demo',
            )

    # ────────────────────────────────────────────────────────────────
    # Bookings
    # ────────────────────────────────────────────────────────────────

    def _create_bookings(self, demo_user, wallet):
        today   = date.today()
        plots   = list(Plot.objects.filter(is_active=True).order_by('code'))
        plants  = list(Plant.objects.filter(is_active=True).order_by('id'))

        if not plots or not plants:
            self.stderr.write(self.style.WARNING('No plots/plants found - skipping bookings'))
            return []

        def pl(idx):  return plots[idx % len(plots)]
        def pt(idx):  return plants[idx % len(plants)]

        BOOKING_SPECS = [
            dict(customer_name='ธีรพงษ์ สุขใจ',    phone='081-901-2345',
                 plot=pl(0), plant=pt(0),
                 start_date=today + timedelta(days=7),
                 harvest_offset=None,   # use plant.grow_days
                 status='pending',      delivery_method='pickup'),

            dict(customer_name='สุนันท์ พิมพ์ดี',   phone='085-234-6789',
                 plot=pl(1), plant=pt(1),
                 start_date=today - timedelta(days=14),
                 harvest_offset=None,
                 status='growing',      delivery_method='pickup'),

            dict(customer_name='ปิยะ ทองอร่าม',     phone='092-345-7890',
                 plot=pl(2), plant=pt(2),
                 start_date=today - timedelta(days=30),
                 harvest_offset=None,
                 status='ready_to_harvest', delivery_method='shipping',
                 shipping_address='88 ถนนบางนา-ตราด แขวงบางนา เขตบางนา กรุงเทพฯ 10260'),

            dict(customer_name='วิชัย เขียวชอุ่ม',  phone='086-456-8901',
                 plot=pl(3), plant=pt(3),
                 start_date=today - timedelta(days=40),
                 harvest_offset=-10,
                 status='harvested', delivery_method='pickup',
                 pickup_deadline=today + timedelta(days=5),
                 harvest_weight=Decimal('2.50')),

            dict(customer_name='พิมลรัตน์ สง่างาม', phone='093-567-9012',
                 plot=pl(4), plant=pt(0),
                 start_date=today - timedelta(days=44),
                 harvest_offset=-14,
                 status='ready_for_pickup', delivery_method='pickup',
                 pickup_deadline=today + timedelta(days=3),
                 harvest_weight=Decimal('3.20')),

            dict(customer_name='ณัฐพล แสงทอง',      phone='064-678-0123',
                 plot=pl(5), plant=pt(4),
                 start_date=today - timedelta(days=35),
                 harvest_offset=-7,
                 status='awaiting_shipping_payment', delivery_method='shipping',
                 shipping_address='12 ซอยเอกมัย 10 แขวงคลองเตยเหนือ เขตวัฒนา กรุงเทพฯ 10110',
                 harvest_weight=Decimal('1.80')),

            dict(customer_name='ชัยวัฒน์ ประโยชน์', phone='087-789-1234',
                 plot=pl(0), plant=pt(5),
                 start_date=today - timedelta(days=50),
                 harvest_offset=-20,
                 status='shipped', delivery_method='shipping',
                 shipping_address='100/5 ถนนพระรามเก้า แขวงห้วยขวาง เขตห้วยขวาง กรุงเทพฯ 10310',
                 tracking_number='TH12345678901', shipping_carrier='thaipost',
                 harvest_weight=Decimal('4.00')),

            dict(customer_name='รัตนา วิเชียรชัย',  phone='091-890-2345',
                 plot=pl(1), plant=pt(2),
                 start_date=today - timedelta(days=60),
                 harvest_offset=-30,
                 status='completed', delivery_method='pickup',
                 harvest_weight=Decimal('2.10')),
        ]

        paid_statuses = frozenset({
            'paid', 'growing', 'ready_to_harvest', 'harvested',
            'awaiting_shipping_payment', 'preparing', 'ready_for_pickup',
            'shipped', 'delivered', 'completed',
        })
        created = []

        for spec in BOOKING_SPECS:
            start_date = spec['start_date']
            offset = spec.get('harvest_offset')
            if offset is not None:
                harvest_date = today + timedelta(days=offset)
            else:
                harvest_date = start_date + timedelta(days=spec['plant'].grow_days)

            days = max(1, (harvest_date - start_date).days)
            total_price = spec['plot'].price_per_day * days + spec['plant'].seed_price

            booking = PlotBooking(
                plot=spec['plot'],
                plant=spec['plant'],
                user=demo_user,
                session_key=DEMO_SESSION,
                customer_name=spec['customer_name'],
                phone=spec['phone'],
                start_date=start_date,
                harvest_date=harvest_date,
                total_price=total_price,
                status=spec['status'],
                delivery_method=spec.get('delivery_method', 'pickup'),
                shipping_address=spec.get('shipping_address', ''),
                tracking_number=spec.get('tracking_number', ''),
                shipping_carrier=spec.get('shipping_carrier', ''),
                harvest_weight=spec.get('harvest_weight'),
                pickup_deadline=spec.get('pickup_deadline'),
            )
            booking._status_note = 'สร้างโดย seed_demo'
            booking.save()

            if spec['status'] in paid_statuses:
                coins = int(booking.total_price) // 50
                if coins > 0 and not CoinTransaction.objects.filter(booking=booking, reason='purchase').exists():
                    CoinTransaction.objects.create(
                        wallet=wallet, amount=coins, reason='purchase', booking=booking,
                        note=f'ได้รับจากการจองแปลง #{booking.id}',
                    )
                    CoinWallet.objects.filter(pk=wallet.pk).update(
                        balance=F('balance') + coins,
                        total_earned=F('total_earned') + coins,
                    )

            created.append(booking)

        return created

    # ────────────────────────────────────────────────────────────────
    # Reviews
    # ────────────────────────────────────────────────────────────────

    def _create_reviews(self, orders):
        delivered = [o for o in orders if o.status == 'delivered']
        if not delivered:
            return

        TEXTS = [
            (5, 'สินค้าดีมาก ส่งไวมาก บรรจุภัณฑ์แน่นหนา ซื้อซ้ำแน่นอนค่ะ'),
            (5, 'คุณภาพดีเกินราคา แนะนำเลยครับ สินค้าตรงปก ไม่มีตำหนิ'),
            (4, 'ใช้งานได้ดีค่ะ บรรจุภัณฑ์เรียบร้อย แต่ถ้ามีสีให้เลือกมากกว่านี้จะดีมากเลย'),
            (5, 'ประทับใจมากเลยครับ แพ็กดีมาก มีกันกระแทกครบ ส่งเร็วด้วย'),
        ]

        for order in delivered:
            for i, item in enumerate(list(order.items.all())[:2]):
                try:
                    prod = Product.objects.get(pk=item.product_id)
                except Product.DoesNotExist:
                    continue
                rating, comment = TEXTS[i % len(TEXTS)]
                ProductReview.objects.get_or_create(
                    product=prod, order=order,
                    defaults={
                        'customer_name': order.customer_name,
                        'rating': rating,
                        'comment': comment,
                        'is_visible': True,
                    },
                )

    # ────────────────────────────────────────────────────────────────
    # Chat rooms
    # ────────────────────────────────────────────────────────────────

    def _create_chats(self, demo_user, orders):
        if ChatRoom.objects.filter(user=demo_user).exists():
            return

        paid_order = next((o for o in orders if o.status == 'paid'), None)

        room1 = ChatRoom.objects.create(
            user=demo_user,
            session_key='demo_seed_chat01',
            customer_name='วีระ เพชรชมภู',
            phone='088-111-3344',
            related_order=paid_order,
            unread_by_staff=2,
        )
        for msg in [
            ('customer', 'วีระ เพชรชมภู', 'สวัสดีครับ สอบถามเรื่องออเดอร์หน่อยได้ไหมครับ'),
            ('staff',    'เจ้าหน้าที่',    'สวัสดีค่ะ รับทราบค่ะ มีอะไรให้ช่วยไหมคะ'),
            ('customer', 'วีระ เพชรชมภู', 'ออเดอร์ผมจะส่งวันไหนครับ รีบใช้งานอยู่ครับ'),
            ('customer', 'วีระ เพชรชมภู', 'กดจ่ายตังค์ไปแล้ว รอจัดส่งอยู่นะครับ'),
        ]:
            ChatMessage.objects.create(room=room1, sender_type=msg[0], sender_name=msg[1], message=msg[2])

        room2 = ChatRoom.objects.create(
            user=demo_user,
            session_key='demo_seed_chat02',
            customer_name='สมปอง แสนดี',
            phone='065-222-6677',
            unread_by_staff=1,
        )
        for msg in [
            ('customer', 'สมปอง แสนดี', 'อยากสอบถามเรื่องการจองแปลงผักค่ะ'),
            ('staff',    'เจ้าหน้าที่',  'ยินดีช่วยเหลือค่ะ มีแปลงว่างหลายแปลงเลยค่ะ'),
            ('customer', 'สมปอง แสนดี', 'ราคาแปลงเดือนละเท่าไหร่คะ และปลูกอะไรได้บ้าง?'),
        ]:
            ChatMessage.objects.create(room=room2, sender_type=msg[0], sender_name=msg[1], message=msg[2])

    # ────────────────────────────────────────────────────────────────
    # Donations
    # ────────────────────────────────────────────────────────────────

    def _setup_donations(self):
        donation = TreeDonation.get()
        if donation.total_coins_donated < 3200:
            TreeDonation.objects.filter(pk=1).update(total_coins_donated=3200)
