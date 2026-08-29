from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import F

from store.models import (
    CoinTransaction, CoinWallet,
    Order, PlotBooking, Product, StockMovement,
)


class Command(BaseCommand):
    help = (
        'Mark an order or booking as paid — simulates the Opn webhook '
        'for offline demos.\n\n'
        'Usage:\n'
        '  python manage.py mark_order_paid <order_id>\n'
        '  python manage.py mark_order_paid <booking_id> --booking\n'
        '  python manage.py mark_order_paid <booking_id> --shipping'
    )

    def add_arguments(self, parser):
        parser.add_argument('pk', type=int, help='Order or Booking primary key')
        parser.add_argument(
            '--booking', action='store_true',
            help='Treat pk as PlotBooking ID (initial plot rent payment)',
        )
        parser.add_argument(
            '--shipping', action='store_true',
            help='Treat pk as PlotBooking ID (shipping fee payment only)',
        )

    def handle(self, *args, **options):
        pk = options['pk']
        if options['shipping']:
            self._pay_booking_shipping(pk)
        elif options['booking']:
            self._pay_booking(pk)
        else:
            self._pay_order(pk)

    # ──────────────────────────────────────────────────────────────
    # Wallet helper (mirrors _get_or_create_wallet in views.py)
    # ──────────────────────────────────────────────────────────────

    def _wallet(self, session_key, user=None):
        if user and user.pk:
            w = CoinWallet.objects.filter(user=user).first()
            if w:
                return w
        sk = (session_key or 'offline_markpaid_000000000000000001')[:40]
        w, _ = CoinWallet.objects.get_or_create(session_key=sk)
        if user and user.pk and not w.user_id:
            CoinWallet.objects.filter(pk=w.pk).update(user=user)
        return w

    # ──────────────────────────────────────────────────────────────
    # Order
    # ──────────────────────────────────────────────────────────────

    def _pay_order(self, order_id):
        try:
            order = Order.objects.prefetch_related('items').get(pk=order_id)
        except Order.DoesNotExist:
            raise CommandError(f'Order #{order_id} not found.')

        if order.status != 'pending':
            self.stderr.write(self.style.WARNING(
                f'Order #{order_id} is already "{order.get_status_display()}" — nothing changed.'
            ))
            return

        coins = 0
        with transaction.atomic():
            order.status = 'paid'
            order._status_note = 'ชำระเงินแล้ว (จำลองออฟไลน์)'
            order.save()

            for item in order.items.all():
                try:
                    prod = Product.objects.select_for_update().get(pk=item.product_id)
                    prod.stock_quantity = max(0, prod.stock_quantity - item.quantity)
                    prod.save(update_fields=['stock_quantity', 'updated_at'])
                    StockMovement.objects.create(
                        product=prod, change=-item.quantity, reason='sale', order=order,
                        note='หักสต๊อกจาก mark_order_paid',
                    )
                except Product.DoesNotExist:
                    pass

            coins = int(order.total) // 50
            if coins > 0 and not CoinTransaction.objects.filter(order=order, reason='purchase').exists():
                wallet = self._wallet(order.session_key, order.user)
                CoinTransaction.objects.create(
                    wallet=wallet, amount=coins, reason='purchase', order=order,
                    note=f'ได้รับจากออเดอร์ #{order.id}',
                )
                CoinWallet.objects.filter(pk=wallet.pk).update(
                    balance=F('balance') + coins,
                    total_earned=F('total_earned') + coins,
                )

        self.stdout.write(self.style.SUCCESS(
            f'Order #{order_id} -> PAID | items={order.items.count()} | coins=+{coins}'
        ))

    # ──────────────────────────────────────────────────────────────
    # Booking (initial rent payment)
    # ──────────────────────────────────────────────────────────────

    def _pay_booking(self, booking_id):
        try:
            booking = PlotBooking.objects.select_related('plot', 'plant').get(pk=booking_id)
        except PlotBooking.DoesNotExist:
            raise CommandError(f'Booking #{booking_id} not found.')

        if booking.status != 'pending':
            self.stderr.write(self.style.WARNING(
                f'Booking #{booking_id} is already "{booking.get_status_display()}" — nothing changed.'
            ))
            return

        coins = 0
        with transaction.atomic():
            booking.status = 'paid'
            booking._status_note = 'ชำระเงินแล้ว (จำลองออฟไลน์)'
            booking.save()

            coins = int(booking.total_price) // 50
            if coins > 0 and not CoinTransaction.objects.filter(booking=booking, reason='purchase').exists():
                wallet = self._wallet(booking.session_key, booking.user)
                CoinTransaction.objects.create(
                    wallet=wallet, amount=coins, reason='purchase', booking=booking,
                    note=f'ได้รับจากการจองแปลง #{booking.id}',
                )
                CoinWallet.objects.filter(pk=wallet.pk).update(
                    balance=F('balance') + coins,
                    total_earned=F('total_earned') + coins,
                )

        self.stdout.write(self.style.SUCCESS(
            f'Booking #{booking_id} -> PAID | plot={booking.plot.code} | total={booking.total_price} | coins=+{coins}'
        ))

    # ──────────────────────────────────────────────────────────────
    # Booking shipping fee
    # ──────────────────────────────────────────────────────────────

    def _pay_booking_shipping(self, booking_id):
        try:
            booking = PlotBooking.objects.select_related('plot').get(pk=booking_id)
        except PlotBooking.DoesNotExist:
            raise CommandError(f'Booking #{booking_id} not found.')

        if booking.status != 'awaiting_shipping_payment':
            self.stderr.write(self.style.WARNING(
                f'Booking #{booking_id} status is "{booking.get_status_display()}" '
                f'(expected: awaiting_shipping_payment) — nothing changed.'
            ))
            return

        with transaction.atomic():
            booking.status = 'preparing'
            booking._status_note = 'ชำระค่าจัดส่งแล้ว (จำลองออฟไลน์)'
            booking.save()

        self.stdout.write(self.style.SUCCESS(
            f'Booking #{booking_id} -> PREPARING | shipping_fee={booking.shipping_fee}'
        ))
