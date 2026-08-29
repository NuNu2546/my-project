import json
import re
from decimal import Decimal
from datetime import datetime, timedelta

import omise
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import Http404, JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User

from django.db.models import Sum
from django.core.cache import cache

from django.db.models import Avg, Count, Q

from .models import (
    Order, OrderItem, Plot, Plant, PlotBooking, Product, StockMovement,
    ChatRoom, ChatMessage,
    CoinWallet, CoinTransaction, TreeDonation,
    ProductReview, UserProfile,
)

# PLANT_GROW_TIMES removed — data now lives in Plant model (use seed_plots command)


@ensure_csrf_cookie
def cart(request):
    user_prefill = {}
    if request.user.is_authenticated:
        user_prefill['name'] = request.user.get_full_name()
        try:
            profile = request.user.userprofile
            user_prefill['phone'] = profile.phone
            user_prefill['address'] = profile.default_address
        except UserProfile.DoesNotExist:
            pass
    return render(request, 'cart.html', {'user_prefill': user_prefill})

def home(request):
    best_sellers = cache.get('home_best_sellers')
    if best_sellers is None:
        from datetime import timedelta
        thirty_ago = timezone.now() - timedelta(days=30)
        paid_statuses = ['paid', 'shipped', 'in_transit', 'delivered']
        top_ids = list(
            OrderItem.objects
            .filter(order__status__in=paid_statuses, order__created_at__gte=thirty_ago)
            .values('product_id')
            .annotate(total_qty=Sum('quantity'))
            .order_by('-total_qty')
            .values_list('product_id', flat=True)[:8]
        )
        id_order = {pk: idx for idx, pk in enumerate(top_ids)}
        best_sellers = list(Product.objects.filter(pk__in=top_ids, is_active=True))
        best_sellers.sort(key=lambda p: id_order.get(p.pk, 999))
        if len(best_sellers) < 4:
            extra_ids = [p.pk for p in best_sellers]
            extra = list(Product.objects.filter(is_active=True).exclude(pk__in=extra_ids).order_by('?')[:8 - len(best_sellers)])
            best_sellers = best_sellers + extra
        cache.set('home_best_sellers', best_sellers, 600)

    # Annotate best_sellers with review stats (fast single query)
    if best_sellers:
        ids = [p.pk for p in best_sellers]
        rating_map = {
            r['product_id']: r
            for r in ProductReview.objects
            .filter(product_id__in=ids, is_visible=True)
            .values('product_id')
            .annotate(avg_rating=Avg('rating'), review_count=Count('id'))
        }
        for p in best_sellers:
            info = rating_map.get(p.pk, {})
            p.avg_rating    = round(info['avg_rating'], 1) if info.get('avg_rating') else None
            p.review_count  = info.get('review_count', 0)

    tree_donation = TreeDonation.get()

    wallet_balance = 0
    w = None
    if request.user.is_authenticated:
        w = CoinWallet.objects.filter(user=request.user).first()
    if w is None and request.session.session_key:
        w = CoinWallet.objects.filter(session_key=request.session.session_key).first()
    if w:
        wallet_balance = w.balance

    return render(request, 'home.html', {
        'best_sellers': best_sellers,
        'tree_donation': tree_donation,
        'wallet_balance': wallet_balance,
    })

def shop(request):
    products = (
        Product.objects
        .filter(is_active=True)
        .annotate(
            avg_rating=Avg('reviews__rating', filter=Q(reviews__is_visible=True)),
            review_count=Count('reviews', filter=Q(reviews__is_visible=True)),
        )
        .order_by('category', 'name')
    )
    return render(request, 'shop.html', {'products': products})

def product_detail(request, product_id):
    try:
        product = Product.objects.get(pk=product_id, is_active=True)
    except Product.DoesNotExist:
        raise Http404("ไม่พบสินค้านี้")

    related_products = (
        Product.objects
        .filter(is_active=True)
        .exclude(pk=product_id)
        .annotate(
            avg_rating=Avg('reviews__rating', filter=Q(reviews__is_visible=True)),
            review_count=Count('reviews', filter=Q(reviews__is_visible=True)),
        )[:6]
    )

    # Aggregate review summary
    review_qs = ProductReview.objects.filter(product=product, is_visible=True)
    agg = review_qs.aggregate(avg=Avg('rating'), total=Count('id'))
    avg_rating = round(agg['avg'], 1) if agg['avg'] else None
    review_count = agg['total']

    dist = {i: 0 for i in range(1, 6)}
    for r in review_qs.values('rating').annotate(n=Count('id')):
        dist[r['rating']] = r['n']

    # Pre-computed list for template: [{star, count, pct}]
    rating_dist_list = [
        {
            'star': s,
            'count': dist[s],
            'pct': round(dist[s] / review_count * 100) if review_count else 0,
        }
        for s in [5, 4, 3, 2, 1]
    ]

    context = {
        'product': product,
        'related_products': related_products,
        'avg_rating': avg_rating,
        'review_count': review_count,
        'rating_dist_list': rating_dist_list,
    }
    return render(request, 'product_detail.html', context)


@ensure_csrf_cookie
def plot_detail(request, plot_id):
    try:
        plot = Plot.objects.get(pk=plot_id, is_active=True)
    except Plot.DoesNotExist:
        raise Http404

    # Lazily expire stale pending bookings for this plot
    _expire_pending_bookings(plot)

    plants_qs   = list(Plant.objects.filter(is_active=True).order_by('name'))
    plants_json = json.dumps(
        [{'name': p.name, 'grow_days': p.grow_days, 'seed_price': float(p.seed_price), 'image': p.image} for p in plants_qs],
        ensure_ascii=False,
    )

    today = timezone.now().date()
    active_bookings = PlotBooking.objects.filter(
        plot=plot,
        status__in=['paid', 'growing', 'ready_to_harvest', 'pending'],
        harvest_date__gte=today,
    ).values('start_date', 'harvest_date')
    booked_ranges_json = json.dumps(
        [{'start': b['start_date'].isoformat(), 'end': b['harvest_date'].isoformat()}
         for b in active_bookings],
    )

    user_prefill = {}
    if request.user.is_authenticated:
        user_prefill['name'] = request.user.get_full_name()
        try:
            profile = request.user.userprofile
            user_prefill['phone'] = profile.phone
        except UserProfile.DoesNotExist:
            pass

    return render(request, 'plot_detail.html', {
        'plot': plot,
        'plants': plants_qs,
        'plants_json': plants_json,
        'booked_ranges_json': booked_ranges_json,
        'user_prefill': user_prefill,
    })


def veggie_plots(request):
    plots = Plot.objects.filter(is_active=True)
    today = timezone.now().date()
    plots_with_status = []
    for plot in plots:
        _expire_pending_bookings(plot)
        active = PlotBooking.objects.filter(
            plot=plot,
            status__in=['paid', 'growing', 'ready_to_harvest', 'pending'],
            start_date__lte=today,
            harvest_date__gte=today,
        ).order_by('harvest_date').first()
        plots_with_status.append({
            'plot': plot,
            'is_available': active is None,
            'booked_until': active.harvest_date if active else None,
        })
    return render(request, 'Veggie_Plots.html', {'plots_with_status': plots_with_status})


def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')


# ── Booking helpers ──────────────────────────────────────────────────────────

def _expire_pending_bookings(plot):
    PlotBooking.objects.filter(
        plot=plot,
        status='pending',
        created_at__lt=timezone.now() - timedelta(hours=1),
    ).update(status='expired')


def _is_overlapping(plot, start_date, harvest_date, exclude_id=None):
    """Return True if [start_date, harvest_date] overlaps any active booking on plot."""
    qs = PlotBooking.objects.filter(
        plot=plot,
        status__in=['paid', 'growing', 'ready_to_harvest', 'pending'],
        start_date__lt=harvest_date,
        harvest_date__gt=start_date,
    )
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    return qs.exists()


def _add_to_my_bookings(request, booking_id):
    """Prepend booking_id to session['my_bookings'], dedup, keep latest first."""
    bookings = list(request.session.get('my_bookings', []))
    if booking_id in bookings:
        bookings.remove(booking_id)
    bookings.insert(0, booking_id)
    request.session['my_bookings'] = bookings
    request.session.modified = True


def get_my_bookings(request):
    """Return PlotBookings for this user (if logged in) or session, newest first."""
    from django.db.models import Case, When, IntegerField
    if request.user.is_authenticated:
        user_ids = list(
            PlotBooking.objects.filter(user=request.user).values_list('pk', flat=True)
        )
        session_ids = [i for i in request.session.get('my_bookings', []) if i not in user_ids]
        all_ids = user_ids + session_ids
        if not all_ids:
            return PlotBooking.objects.none()
        return (
            PlotBooking.objects.filter(pk__in=all_ids)
            .select_related('plot', 'plant')
            .order_by('-created_at')
        )
    booking_ids = request.session.get('my_bookings', [])
    if not booking_ids:
        return PlotBooking.objects.none()
    preserve_order = Case(
        *[When(pk=pk, then=pos) for pos, pk in enumerate(booking_ids)],
        output_field=IntegerField(),
    )
    return (
        PlotBooking.objects
        .filter(pk__in=booking_ids)
        .select_related('plot', 'plant')
        .order_by(preserve_order)
    )


# ── process_booking — JSON API endpoint ─────────────────────────────────────

def process_booking(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    plot_id      = data.get('plot_id')
    plant_name   = str(data.get('plant_name', '')).strip()
    start_date_s = str(data.get('start_date', '')).strip()
    customer_name = str(data.get('customer_name', '')).strip()[:200]
    phone_raw    = re.sub(r'[\s\-]', '', str(data.get('phone', '')).strip())

    # Validate required fields
    if not all([plot_id, plant_name, start_date_s, customer_name, phone_raw]):
        return JsonResponse({'error': 'กรุณากรอกข้อมูลให้ครบทุกช่อง'}, status=400)

    if not re.match(r'^\d{9,10}$', phone_raw):
        return JsonResponse({'error': 'เบอร์โทรศัพท์ไม่ถูกต้อง (9-10 หลัก)'}, status=400)

    # Validate plot
    try:
        plot = Plot.objects.get(pk=int(plot_id), is_active=True)
    except (Plot.DoesNotExist, TypeError, ValueError):
        return JsonResponse({'error': 'ไม่พบแปลงที่เลือก'}, status=400)

    # Validate plant
    try:
        plant = Plant.objects.get(name=plant_name, is_active=True)
    except Plant.DoesNotExist:
        return JsonResponse({'error': 'ไม่พบพืชที่เลือก'}, status=400)

    # Validate start_date
    try:
        start_date = datetime.strptime(start_date_s, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'รูปแบบวันที่ไม่ถูกต้อง'}, status=400)

    today = timezone.now().date()
    if start_date < today:
        return JsonResponse({'error': 'วันเริ่มปลูกต้องไม่ย้อนหลัง'}, status=400)
    if (start_date - today).days > 60:
        return JsonResponse({'error': 'วันเริ่มปลูกต้องไม่เกิน 60 วันจากวันนี้'}, status=400)

    # Calculate harvest_date and total_price from DB — never trust frontend
    # Formula: (price_per_day × grow_days) + seed_price
    harvest_date = start_date + timedelta(days=plant.grow_days)
    rent_cost    = Decimal(str(plant.grow_days)) * plot.price_per_day
    total_price  = rent_cost + plant.seed_price

    # Check availability + create booking in one atomic block (basic race protection)
    with transaction.atomic():
        _expire_pending_bookings(plot)
        if _is_overlapping(plot, start_date, harvest_date):
            return JsonResponse({'error': 'แปลงไม่ว่างในช่วงเวลานี้ กรุณาเลือกวันอื่น'}, status=409)

        if not request.session.session_key:
            request.session.save()
        booking = PlotBooking.objects.create(
            user=request.user if request.user.is_authenticated else None,
            plot=plot,
            plant=plant,
            customer_name=customer_name,
            phone=phone_raw,
            start_date=start_date,
            harvest_date=harvest_date,
            total_price=total_price,
            status='pending',
            session_key=request.session.session_key or '',
        )

    _add_to_my_bookings(request, booking.id)

    # Create Opn PromptPay charge
    try:
        omise.api_secret = settings.OMISE_SECRET_KEY
        amount_satang = int(round(float(total_price) * 100))

        source = omise.Source.create(
            type='promptpay',
            amount=amount_satang,
            currency='thb',
        )
        charge = omise.Charge.create(
            amount=amount_satang,
            currency='thb',
            source=source.id,
            metadata={'booking_id': str(booking.id)},
        )

        booking.charge_id = charge.id
        booking.save(update_fields=['charge_id'])

        try:
            qr_image = charge.source.scannable_code.image.download_uri
        except AttributeError:
            qr_image = None

        return JsonResponse({
            'booking_id': booking.id,
            'qr_image': qr_image,
            'amount': float(total_price),
        })

    except Exception as e:
        booking.status = 'failed'
        booking.save(update_fields=['status'])
        return JsonResponse({'error': f'ไม่สามารถสร้าง QR Code: {str(e)}'}, status=500)


def check_booking(request, booking_id):
    try:
        booking = PlotBooking.objects.get(pk=booking_id)
        return JsonResponse({'status': booking.status})
    except PlotBooking.DoesNotExist:
        return JsonResponse({'error': 'ไม่พบการจอง'}, status=404)


def booking_success(request, booking_id):
    try:
        booking = PlotBooking.objects.select_related('plot', 'plant').get(pk=booking_id)
    except PlotBooking.DoesNotExist:
        raise Http404
    _add_to_my_bookings(request, booking_id)
    coins_earned = 0
    tx = CoinTransaction.objects.filter(booking=booking, reason='purchase').first()
    if tx:
        coins_earned = tx.amount
    return render(request, 'booking_success.html', {'booking': booking, 'coins_earned': coins_earned})


# ── booking_track_detail ─────────────────────────────────────────────────────

_BOOKING_NEGATIVE = frozenset({'cancelled', 'expired'})

_COMMON_PATH   = ['pending', 'paid', 'growing', 'ready_to_harvest', 'harvested']
_PICKUP_PATH   = _COMMON_PATH + ['ready_for_pickup', 'completed']
_SHIPPING_PATH = _COMMON_PATH + ['awaiting_shipping_payment', 'preparing', 'shipped', 'delivered', 'completed']

_GARDEN_INFO = {
    'address': '123 ถนนวิภาวดีรังสิต แขวงลาดยาว เขตจตุจักร กรุงเทพฯ 10900',
    'hours':   'จ–ศ 8:00–17:00 น. / ส–อ 9:00–16:00 น.',
}

SHIPPING_FEE = 60  # ค่าจัดส่งผลผลิตแปลงผัก


def _reset_expired_shipping(booking):
    """If awaiting_shipping_payment has been pending > 24 h, revert to harvested."""
    if booking.status != 'awaiting_shipping_payment':
        return False
    if (timezone.now() - booking.updated_at).total_seconds() > 86400:
        booking.delivery_method    = ''
        booking.shipping_charge_id = ''
        booking.status             = 'harvested'
        booking.save(update_fields=['delivery_method', 'shipping_charge_id', 'status'])
        return True
    return False


def _build_timeline(booking, status_history, is_negative):
    from .models import BOOKING_STATUS_CHOICES
    label_map = dict(BOOKING_STATUS_CHOICES)

    dm = booking.delivery_method
    if dm == 'pickup':
        flow = _PICKUP_PATH
    elif dm == 'shipping':
        flow = _SHIPPING_PATH
    else:
        flow = _COMMON_PATH

    status = booking.status
    try:
        current_idx = flow.index(status)
    except ValueError:
        current_idx = len(flow) - 1

    steps = []
    for i, s in enumerate(flow):
        entry = status_history.get(s)
        if is_negative:
            state = 'done' if entry else 'upcoming'
        elif i < current_idx:
            state = 'done'
        elif i == current_idx:
            state = 'current'
        else:
            state = 'upcoming'
        steps.append({
            'status':    s,
            'label':     label_map.get(s, s),
            'state':     state,
            'timestamp': entry.created_at if entry else None,
            'note':      entry.note if entry else '',
        })
    return steps


def _user_owns_booking(request, booking_id):
    if request.user.is_authenticated:
        if PlotBooking.objects.filter(pk=booking_id, user=request.user).exists():
            return True
    return booking_id in request.session.get('my_bookings', [])


def _user_owns_order(request, order_id):
    if request.user.is_authenticated:
        if Order.objects.filter(pk=order_id, user=request.user).exists():
            return True
    return order_id in request.session.get('my_orders', [])


def booking_track_detail(request, booking_id):
    if not _user_owns_booking(request, booking_id):
        return redirect('my_orders')

    try:
        booking = (
            PlotBooking.objects
            .select_related('plot', 'plant')
            .prefetch_related('history')
            .get(pk=booking_id)
        )
    except PlotBooking.DoesNotExist:
        raise Http404

    # Auto-expire stale shipping payment window
    _reset_expired_shipping(booking)

    status_history = {}
    for entry in booking.history.all():
        if entry.status not in status_history:
            status_history[entry.status] = entry

    is_negative = booking.status in _BOOKING_NEGATIVE
    timeline    = _build_timeline(booking, status_history, is_negative)

    # Pickup deadline countdown (days remaining)
    pickup_days_left = None
    if booking.pickup_deadline:
        pickup_days_left = (booking.pickup_deadline - timezone.now().date()).days

    return render(request, 'booking_track.html', {
        'booking':           booking,
        'timeline':          timeline,
        'is_negative':       is_negative,
        'garden_info':       _GARDEN_INFO,
        'shipping_fee':      SHIPPING_FEE,
        'pickup_days_left':  pickup_days_left,
        'show_delivery_choice':  booking.status == 'harvested',
        'show_shipping_qr':      booking.status == 'awaiting_shipping_payment',
        'show_pickup_info':      booking.status == 'ready_for_pickup',
        'show_confirm_received': booking.status == 'shipped',
    })


# ── choose_delivery — POST: select pickup or shipping ────────────────────────

def choose_delivery(request, booking_id):
    if not _user_owns_booking(request, booking_id):
        return JsonResponse({'error': 'ไม่มีสิทธิ์เข้าถึง'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    method = data.get('method', '')
    if method not in ('pickup', 'shipping'):
        return JsonResponse({'error': 'วิธีรับไม่ถูกต้อง'}, status=400)

    try:
        booking = PlotBooking.objects.get(pk=booking_id)
    except PlotBooking.DoesNotExist:
        return JsonResponse({'error': 'ไม่พบการจอง'}, status=404)

    # Allow re-selection only from harvested (or expired shipping window)
    _reset_expired_shipping(booking)
    if booking.status != 'harvested':
        return JsonResponse({'error': 'ไม่สามารถเลือกวิธีรับได้ในสถานะนี้'}, status=400)

    if method == 'pickup':
        from datetime import date as _date
        booking.delivery_method = 'pickup'
        booking.status          = 'ready_for_pickup'
        if not booking.pickup_deadline:
            booking.pickup_deadline = booking.harvest_date + timedelta(days=7)
        booking.save(update_fields=['delivery_method', 'status', 'pickup_deadline'])
        return JsonResponse({'status': 'ready_for_pickup'})

    # ── shipping branch ──────────────────────────────────────────────────────
    shipping_address = str(data.get('shipping_address', '')).strip()
    if not shipping_address:
        return JsonResponse({'error': 'กรุณากรอกที่อยู่จัดส่ง'}, status=400)

    # Calculate fee server-side — never trust frontend
    fee_baht  = SHIPPING_FEE
    fee_satang = int(round(fee_baht * 100))

    booking.delivery_method  = 'shipping'
    booking.shipping_address = shipping_address
    booking.shipping_fee     = fee_baht
    booking.status           = 'awaiting_shipping_payment'
    booking.save(update_fields=['delivery_method', 'shipping_address', 'shipping_fee', 'status'])

    try:
        omise.api_secret = settings.OMISE_SECRET_KEY
        source = omise.Source.create(type='promptpay', amount=fee_satang, currency='thb')
        charge = omise.Charge.create(
            amount=fee_satang,
            currency='thb',
            source=source.id,
            metadata={'shipping_booking_id': str(booking.id)},
        )
        booking.shipping_charge_id = charge.id
        booking.save(update_fields=['shipping_charge_id'])

        try:
            qr_image = charge.source.scannable_code.image.download_uri
        except AttributeError:
            qr_image = None

        return JsonResponse({'status': 'awaiting_shipping_payment', 'qr_image': qr_image, 'amount': fee_baht})
    except Exception as e:
        # Revert to harvested so customer can retry
        booking.status           = 'harvested'
        booking.delivery_method  = ''
        booking.shipping_charge_id = ''
        booking.save(update_fields=['status', 'delivery_method', 'shipping_charge_id'])
        return JsonResponse({'error': f'ไม่สามารถสร้าง QR: {str(e)}'}, status=500)


# ── check_shipping_payment — GET: poll shipping QR status ───────────────────

def check_shipping_payment(request, booking_id):
    if not _user_owns_booking(request, booking_id):
        return JsonResponse({'error': 'ไม่มีสิทธิ์เข้าถึง'}, status=403)
    try:
        booking = PlotBooking.objects.get(pk=booking_id)
    except PlotBooking.DoesNotExist:
        return JsonResponse({'error': 'ไม่พบการจอง'}, status=404)

    if _reset_expired_shipping(booking):
        return JsonResponse({'status': 'harvested', 'reset': True})

    qr_image = None
    if booking.status == 'awaiting_shipping_payment' and booking.shipping_charge_id:
        try:
            omise.api_secret = settings.OMISE_SECRET_KEY
            charge = omise.Charge.retrieve(booking.shipping_charge_id)
            try:
                qr_image = charge.source.scannable_code.image.download_uri
            except AttributeError:
                pass
        except Exception:
            pass

    return JsonResponse({
        'status':    booking.status,
        'qr_image':  qr_image,
        'amount':    float(booking.shipping_fee),
    })


# ── confirm_received — POST: customer confirms delivery ─────────────────────

def confirm_received(request, booking_id):
    if not _user_owns_booking(request, booking_id):
        return JsonResponse({'error': 'ไม่มีสิทธิ์เข้าถึง'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        booking = PlotBooking.objects.get(pk=booking_id)
    except PlotBooking.DoesNotExist:
        return JsonResponse({'error': 'ไม่พบการจอง'}, status=404)

    if booking.status != 'shipped':
        return JsonResponse({'error': 'ไม่สามารถยืนยันได้ในสถานะนี้'}, status=400)

    booking.status = 'delivered'
    booking.save(update_fields=['status'])
    booking.status = 'completed'
    booking.save(update_fields=['status'])
    return JsonResponse({'status': 'completed'})


# ============================================================
#  Opn Payments (Omise) — PromptPay QR
# ============================================================

def create_payment(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    items_data = data.get('items', [])
    customer_name = str(data.get('customer_name', 'ลูกค้า'))[:200]
    phone = str(data.get('phone', ''))[:20]
    address = str(data.get('address', ''))[:1000]
    coupon_code = str(data.get('coupon_code', '')).strip().upper()

    if not items_data:
        return JsonResponse({'error': 'ไม่มีสินค้าในตะกร้า'}, status=400)

    # Shipping constants (server-side authoritative)
    SHOP_SHIPPING_FEE       = Decimal('50')
    FREE_SHIPPING_THRESHOLD = Decimal('800')
    # Valid coupons: code → discount amount
    VALID_COUPONS = {'GREEN2026': Decimal('80')}

    # คำนวณยอดรวมฝั่ง server จาก DB — ห้ามเชื่อราคาจาก frontend
    product_lookup = {p.id: p for p in Product.objects.filter(is_active=True)}
    order_items_data = []
    subtotal = Decimal('0')

    for item in items_data:
        try:
            product_id = int(item.get('id'))
            qty = int(item.get('qty', 1))
        except (TypeError, ValueError):
            return JsonResponse({'error': 'ข้อมูลสินค้าไม่ถูกต้อง'}, status=400)

        if qty < 1 or qty > 99:
            return JsonResponse({'error': 'จำนวนสินค้าไม่ถูกต้อง'}, status=400)

        product = product_lookup.get(product_id)
        if not product:
            return JsonResponse({'error': f'ไม่พบสินค้า ID {product_id}'}, status=400)

        if product.stock_quantity < qty:
            return JsonResponse({
                'error': f'สินค้า "{product.name}" มีสต๊อกเหลือเพียง {product.stock_quantity} ชิ้น (ต้องการ {qty} ชิ้น)'
            }, status=400)

        price = product.price
        subtotal += price * qty
        order_items_data.append({
            'product_id': product_id,
            'product_name': product.name,
            'price': float(price),
            'quantity': qty,
        })

    # ค่าส่ง: ฿50 / ส่งฟรีเมื่อซื้อครบ ฿800
    shipping_fee = Decimal('0') if subtotal >= FREE_SHIPPING_THRESHOLD else SHOP_SHIPPING_FEE

    # คูปองส่วนลด (server-side validate)
    coupon_discount = Decimal('0')
    if coupon_code and coupon_code in VALID_COUPONS:
        coupon_discount = VALID_COUPONS[coupon_code]

    total_baht = max(Decimal('0'), subtotal + shipping_fee - coupon_discount)

    if not request.session.session_key:
        request.session.save()
    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        customer_name=customer_name,
        phone=phone,
        address=address,
        total=total_baht.quantize(Decimal('0.01')),
        status='pending',
        session_key=request.session.session_key or '',
    )
    for oi in order_items_data:
        OrderItem.objects.create(
            order=order,
            product_id=oi['product_id'],
            product_name=oi['product_name'],
            price=Decimal(str(oi['price'])),
            quantity=oi['quantity'],
        )

    _add_to_my_orders(request, order.id)

    try:
        omise.api_secret = settings.OMISE_SECRET_KEY
        amount_satang = int(round(float(total_baht) * 100))  # แปลงบาท → สตางค์

        source = omise.Source.create(
            type='promptpay',
            amount=amount_satang,
            currency='thb',
        )
        charge = omise.Charge.create(
            amount=amount_satang,
            currency='thb',
            source=source.id,
            metadata={'order_id': str(order.id)},
        )

        order.charge_id = charge.id
        order.save(update_fields=['charge_id'])

        try:
            qr_image = charge.source.scannable_code.image.download_uri
        except AttributeError:
            qr_image = None

        return JsonResponse({
            'order_id': order.id,
            'qr_image': qr_image,
            'amount': round(total_baht, 2),
        })

    except Exception as e:
        order.status = 'failed'
        order.save(update_fields=['status'])
        return JsonResponse({'error': f'ไม่สามารถสร้าง QR Code: {str(e)}'}, status=500)


def check_payment(request, order_id):
    try:
        order = Order.objects.get(pk=order_id)
        return JsonResponse({'status': order.status})
    except Order.DoesNotExist:
        return JsonResponse({'error': 'ไม่พบคำสั่งซื้อ'}, status=404)


def _get_or_create_wallet(session_key, user=None):
    """Return wallet for user (priority) or session_key. Creates if missing."""
    if user and user.pk:
        wallet = CoinWallet.objects.filter(user=user).first()
        if wallet:
            return wallet
    if not session_key:
        return None
    wallet, _ = CoinWallet.objects.get_or_create(session_key=session_key)
    if user and user.pk and not wallet.user_id:
        CoinWallet.objects.filter(pk=wallet.pk).update(user=user)
        wallet.user = user
    return wallet


def _award_coins_for_order(order):
    """Award coins (total ÷ 50, floor) for a paid order. Idempotent."""
    if CoinTransaction.objects.filter(order=order, reason='purchase').exists():
        return 0
    coins = int(order.total) // 50
    if coins <= 0:
        return 0
    user = order.user if order.user_id else None
    wallet = _get_or_create_wallet(order.session_key or '', user)
    if not wallet:
        return 0
    from django.db.models import F
    CoinTransaction.objects.create(
        wallet=wallet, amount=coins, reason='purchase', order=order,
        note=f'ได้รับจากออเดอร์ #{order.id} (฿{order.total})',
    )
    CoinWallet.objects.filter(pk=wallet.pk).update(
        balance=F('balance') + coins,
        total_earned=F('total_earned') + coins,
    )
    return coins


def _award_coins_for_booking(booking):
    """Award coins (total_price ÷ 50, floor) for a paid booking. Idempotent."""
    if CoinTransaction.objects.filter(booking=booking, reason='purchase').exists():
        return 0
    coins = int(booking.total_price) // 50
    if coins <= 0:
        return 0
    user = booking.user if booking.user_id else None
    wallet = _get_or_create_wallet(booking.session_key or '', user)
    if not wallet:
        return 0
    from django.db.models import F
    CoinTransaction.objects.create(
        wallet=wallet, amount=coins, reason='purchase', booking=booking,
        note=f'ได้รับจากการจองแปลง #{booking.id} (฿{booking.total_price})',
    )
    CoinWallet.objects.filter(pk=wallet.pk).update(
        balance=F('balance') + coins,
        total_earned=F('total_earned') + coins,
    )
    return coins


def _deduct_stock_for_order(order):
    """Deduct stock for each item in the order. Called inside a transaction."""
    for item in order.items.all():
        try:
            product = Product.objects.select_for_update().get(pk=item.product_id)
            product.stock_quantity = max(0, product.stock_quantity - item.quantity)
            product.save(update_fields=['stock_quantity', 'updated_at'])
            StockMovement.objects.create(
                product=product,
                change=-item.quantity,
                reason='sale',
                order=order,
            )
        except Product.DoesNotExist:
            pass


def _return_stock_for_order(order):
    """Return stock for each item in the order when cancelled/expired."""
    existing_returns = set(
        StockMovement.objects.filter(order=order, reason='return').values_list('product_id', flat=True)
    )
    for item in order.items.all():
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
                order=order,
                note=f'คืนสต๊อกจากออเดอร์ #{order.id} ({order.status})',
            )
        except Product.DoesNotExist:
            pass


@csrf_exempt
def opn_webhook(request):
    if request.method != 'POST':
        return HttpResponse(status=405)
    try:
        payload = json.loads(request.body)
        if payload.get('key') == 'charge.complete':
            charge_id = payload.get('data', {}).get('id')
            if charge_id:
                omise.api_secret = settings.OMISE_SECRET_KEY
                # ตรวจสอบสถานะจริงกับ Opn API — ห้ามเชื่อ payload ตรงๆ
                charge = omise.Charge.retrieve(charge_id)

                # ลอง match กับ Order ก่อน
                try:
                    order = Order.objects.get(charge_id=charge_id)
                    if charge.status == 'successful' and order.status == 'pending':
                        with transaction.atomic():
                            order.status = 'paid'
                            order.save(update_fields=['status'])
                            _deduct_stock_for_order(order)
                            _award_coins_for_order(order)
                        cache.delete('home_best_sellers')
                    elif charge.status in ('failed', 'expired') and order.status == 'pending':
                        with transaction.atomic():
                            order.status = charge.status
                            order.save(update_fields=['status'])
                except Order.DoesNotExist:
                    pass

                # ลอง match กับ PlotBooking (ค่าเช่า)
                try:
                    booking = PlotBooking.objects.get(charge_id=charge_id)
                    if charge.status == 'successful' and booking.status == 'pending':
                        booking.status = 'paid'
                        booking.save(update_fields=['status'])
                        _award_coins_for_booking(booking)
                    elif charge.status in ('failed', 'expired') and booking.status == 'pending':
                        booking.status = charge.status
                        booking.save(update_fields=['status'])
                except PlotBooking.DoesNotExist:
                    pass

                # ลอง match กับ PlotBooking (ค่าจัดส่ง)
                try:
                    booking = PlotBooking.objects.get(shipping_charge_id=charge_id)
                    if charge.status == 'successful':
                        booking.status = 'preparing'
                    elif charge.status in ('failed', 'expired'):
                        # คืนสถานะให้เลือกใหม่
                        booking.status           = 'harvested'
                        booking.delivery_method  = ''
                        booking.shipping_charge_id = ''
                    booking.save(update_fields=['status', 'delivery_method', 'shipping_charge_id'])
                except PlotBooking.DoesNotExist:
                    pass
    except Exception:
        pass
    return HttpResponse('OK', status=200)


def order_success(request, order_id):
    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        raise Http404("ไม่พบคำสั่งซื้อ")
    _add_to_my_orders(request, order_id)
    coins_earned = 0
    tx = CoinTransaction.objects.filter(order=order, reason='purchase').first()
    if tx:
        coins_earned = tx.amount
    return render(request, 'order_success.html', {'order': order, 'coins_earned': coins_earned})


# ============================================================
#  Order Tracking
# ============================================================

_FLOW_STATUSES = ['pending', 'paid', 'shipped', 'in_transit', 'delivered']
_NEGATIVE_STATUSES = frozenset({'cancelled', 'failed', 'expired'})


def _add_to_my_orders(request, order_id):
    """Prepend order_id to session['my_orders'], dedup, keep latest first."""
    orders = list(request.session.get('my_orders', []))
    if order_id in orders:
        orders.remove(order_id)
    orders.insert(0, order_id)
    request.session['my_orders'] = orders
    request.session.modified = True


def get_my_orders(request):
    """Return Orders for this user (if logged in) or session, newest first."""
    from django.db.models import Case, When, IntegerField
    if request.user.is_authenticated:
        user_ids = list(
            Order.objects.filter(user=request.user).values_list('pk', flat=True)
        )
        session_ids = [i for i in request.session.get('my_orders', []) if i not in user_ids]
        all_ids = user_ids + session_ids
        if not all_ids:
            return Order.objects.none()
        return Order.objects.filter(pk__in=all_ids).prefetch_related('items').order_by('-created_at')
    order_ids = request.session.get('my_orders', [])
    if not order_ids:
        return Order.objects.none()
    preserve_order = Case(
        *[When(pk=pk, then=pos) for pos, pk in enumerate(order_ids)],
        output_field=IntegerField(),
    )
    return Order.objects.filter(pk__in=order_ids).prefetch_related('items').order_by(preserve_order)


def serve_video(request, filename):
    """Serve a video file from static/videos/ with full Range request support."""
    import os, mimetypes
    safe = os.path.basename(filename)  # prevent path traversal
    path = os.path.join(settings.STATICFILES_DIRS[0], 'videos', safe)
    if not os.path.isfile(path):
        raise Http404

    file_size = os.path.getsize(path)
    content_type = mimetypes.guess_type(path)[0] or 'video/mp4'

    range_header = request.META.get('HTTP_RANGE', '').strip()
    range_match = re.match(r'bytes=(\d+)-(\d*)', range_header, re.I)

    if range_match:
        first = int(range_match.group(1))
        last  = int(range_match.group(2)) if range_match.group(2) else file_size - 1
        last  = min(last, file_size - 1)
        length = last - first + 1
        response = HttpResponse(status=206, content_type=content_type)
        response['Accept-Ranges']  = 'bytes'
        response['Content-Range']  = f'bytes {first}-{last}/{file_size}'
        response['Content-Length'] = length
        with open(path, 'rb') as f:
            f.seek(first)
            response.content = f.read(length)
    else:
        response = HttpResponse(content_type=content_type)
        response['Accept-Ranges']  = 'bytes'
        response['Content-Length'] = file_size
        with open(path, 'rb') as f:
            response.content = f.read()

    response['Cache-Control'] = 'public, max-age=86400'
    return response


def track_order(request):
    return redirect('my_orders')


def order_track_detail(request, order_id):
    if not _user_owns_order(request, order_id):
        return redirect('my_orders')

    try:
        order = Order.objects.prefetch_related('items', 'history').get(pk=order_id)
    except Order.DoesNotExist:
        raise Http404

    product_images = {p.id: p.image for p in Product.objects.only('id', 'image')}

    # Which products already have a review for this order
    reviewed_product_ids = set(
        ProductReview.objects.filter(order=order).values_list('product_id', flat=True)
    )
    can_review = order.status in ('delivered', 'completed')

    items_with_images = [
        {
            'item': item,
            'image': product_images.get(item.product_id, ''),
            'reviewed': item.product_id in reviewed_product_ids,
            'can_review': can_review,
        }
        for item in order.items.all()
    ]

    # Map status → first history entry with that status
    status_history = {}
    for entry in order.history.all():
        if entry.status not in status_history:
            status_history[entry.status] = entry

    is_negative = order.status in _NEGATIVE_STATUSES
    try:
        current_idx = _FLOW_STATUSES.index(order.status)
    except ValueError:
        current_idx = -1

    timeline = []
    for i, status_key in enumerate(_FLOW_STATUSES):
        entry = status_history.get(status_key)
        if is_negative:
            state = 'done' if entry else 'upcoming'
        elif i < current_idx:
            state = 'done'
        elif i == current_idx:
            state = 'current'
        else:
            state = 'upcoming'
        timeline.append({
            'status': status_key,
            'label': dict(Order.STATUS_CHOICES).get(status_key, status_key),
            'state': state,
            'timestamp': entry.created_at if entry else None,
            'note': entry.note if entry else '',
        })

    # Retrieve existing review ratings for "รีวิวแล้ว" display
    existing_reviews = {
        r.product_id: r.rating
        for r in ProductReview.objects.filter(order=order)
    }
    for row in items_with_images:
        row['existing_rating'] = existing_reviews.get(row['item'].product_id)

    return render(request, 'order_track.html', {
        'order': order,
        'timeline': timeline,
        'is_negative': is_negative,
        'carrier_display': dict(Order.CARRIER_CHOICES).get(order.shipping_carrier, ''),
        'items_with_images': items_with_images,
    })


def my_orders(request):
    error = None
    success = None
    if request.method == 'POST':
        order_id_str = request.POST.get('order_id', '').strip()
        phone_input = re.sub(r'[\s\-]', '', request.POST.get('phone', '').strip())
        try:
            order = Order.objects.get(pk=int(order_id_str))
            stored = re.sub(r'[\s\-]', '', order.phone)
            if stored and stored == phone_input:
                _add_to_my_orders(request, order.id)
                success = f'พบออเดอร์ #{order.id} แล้ว เพิ่มในรายการแล้ว'
            else:
                error = 'ไม่พบข้อมูลคำสั่งซื้อ กรุณาตรวจสอบเลขออเดอร์และเบอร์โทรศัพท์'
        except (Order.DoesNotExist, ValueError, TypeError):
            error = 'ไม่พบข้อมูลคำสั่งซื้อ กรุณาตรวจสอบเลขออเดอร์และเบอร์โทรศัพท์'

    product_images = {p.id: p.image for p in Product.objects.only('id', 'image')}
    orders_qs = get_my_orders(request)
    orders_meta = []
    for order in orders_qs:
        items_list = list(order.items.all())
        first_img = product_images.get(items_list[0].product_id, '') if items_list else ''
        orders_meta.append({
            'order': order,
            'first_img': first_img,
            'item_count': len(items_list),
        })

    bookings_qs = get_my_bookings(request)

    return render(request, 'my_orders.html', {
        'orders_meta': orders_meta,
        'bookings': bookings_qs,
        'error': error,
        'success': success,
    })


# ──────────────────────────────────────────────────────────────────────────────
#  Customer Chat API
# ──────────────────────────────────────────────────────────────────────────────

def _get_or_init_session(request):
    """Ensure the session has a key (creates one if needed)."""
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def _check_rate_limit(request):
    """Return True if over limit (10 messages per 60 s)."""
    now = timezone.now().timestamp()
    history = request.session.get('chat_ts', [])
    history = [t for t in history if now - t < 60]
    if len(history) >= 10:
        return True
    history.append(now)
    request.session['chat_ts'] = history
    request.session.modified = True
    return False


def _room_for_session(request):
    """Return the open ChatRoom for this session, or None."""
    sk = request.session.get('session_key') or request.session.session_key
    if not sk:
        return None
    room = ChatRoom.objects.filter(session_key=sk, is_closed=False).first()
    return room


def _serialize_message(msg):
    return {
        'id':          msg.id,
        'sender_type': msg.sender_type,
        'sender_name': msg.sender_name,
        'message':     msg.message,
        'created_at':  msg.created_at.strftime('%H:%M'),
    }


def chat_get_or_create_room(request):
    """POST: start or resume a chat room. Returns room_id + message history.
    If body contains resume=true and no room exists, returns room_id=null.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'method'}, status=405)

    sk = _get_or_init_session(request)

    try:
        body = json.loads(request.body)
    except (ValueError, KeyError):
        body = {}

    is_resume     = bool(body.get('resume'))
    customer_name = (body.get('customer_name') or '').strip()[:100]
    phone         = (body.get('phone') or '').strip()[:20]
    order_id      = body.get('order_id')

    room = ChatRoom.objects.filter(session_key=sk, is_closed=False).first()

    if room is None:
        if is_resume:
            # Page-load resume check: don't create a room, just report nothing
            return JsonResponse({'room_id': None, 'messages': []})

        # Find a previously closed room for this session to reuse identity
        old = ChatRoom.objects.filter(session_key=sk).order_by('-id').first()
        name_to_use  = customer_name or (old.customer_name if old else '')
        phone_to_use = phone or (old.phone if old else '')

        related_order = None
        if order_id:
            try:
                related_order = Order.objects.get(pk=order_id)
            except Order.DoesNotExist:
                pass

        room = ChatRoom.objects.create(
            session_key=sk,
            customer_name=name_to_use,
            phone=phone_to_use,
            related_order=related_order,
        )
        ChatMessage.objects.create(
            room=room,
            sender_type='staff',
            sender_name='Greenhearth',
            message='สวัสดีค่ะ! 🌿 ยินดีต้อนรับสู่ Digital Garden มีปัญหาการใช้งานตรงไหนให้แอดมินช่วยไหมคะ?',
        )
    else:
        if customer_name and not room.customer_name:
            room.customer_name = customer_name
            room.save(update_fields=['customer_name'])
        if phone and not room.phone:
            room.phone = phone
            room.save(update_fields=['phone'])
        if order_id and not room.related_order_id:
            try:
                room.related_order = Order.objects.get(pk=order_id)
                room.save(update_fields=['related_order'])
            except Order.DoesNotExist:
                pass
        # Mark staff messages as read by customer opening the popup
        room.messages.filter(sender_type='staff', is_read=False).update(is_read=True)
        room.unread_by_customer = 0
        room.save(update_fields=['unread_by_customer'])

    messages = [_serialize_message(m) for m in room.messages.all()]
    return JsonResponse({'room_id': room.id, 'messages': messages})


def chat_send_message(request):
    """POST: send a customer message."""
    if request.method != 'POST':
        return JsonResponse({'error': 'method'}, status=405)

    sk = request.session.session_key
    if not sk:
        return JsonResponse({'error': 'no_session'}, status=403)

    if _check_rate_limit(request):
        return JsonResponse({'error': 'rate_limit', 'message': 'ส่งข้อความได้สูงสุด 10 ข้อความต่อนาที'}, status=429)

    try:
        body = json.loads(request.body)
    except (ValueError, KeyError):
        return JsonResponse({'error': 'bad_json'}, status=400)

    text = (body.get('message') or '').strip()[:500]
    if not text:
        return JsonResponse({'error': 'empty'}, status=400)

    room = ChatRoom.objects.filter(session_key=sk, is_closed=False).first()
    if room is None:
        return JsonResponse({'error': 'no_room'}, status=404)

    msg = ChatMessage.objects.create(
        room=room,
        sender_type='customer',
        sender_name=room.customer_name or 'ลูกค้า',
        message=text,
    )
    room.unread_by_staff = ChatRoom.objects.filter(pk=room.pk).values_list('unread_by_staff', flat=True)[0] + 1
    room.updated_at = timezone.now()
    room.save(update_fields=['unread_by_staff', 'updated_at'])

    return JsonResponse({'message': _serialize_message(msg)})


def chat_poll(request, room_id):
    """GET: return messages newer than after_id, mark staff messages read."""
    sk = request.session.session_key
    if not sk:
        return JsonResponse({'messages': []})

    try:
        room = ChatRoom.objects.get(pk=room_id, session_key=sk)
    except ChatRoom.DoesNotExist:
        return JsonResponse({'error': 'forbidden'}, status=403)

    after_id = int(request.GET.get('after', 0))
    msgs = room.messages.filter(id__gt=after_id)
    data = [_serialize_message(m) for m in msgs]

    # Mark incoming staff messages as read
    room.messages.filter(sender_type='staff', is_read=False).update(is_read=True)
    room.unread_by_customer = 0
    room.save(update_fields=['unread_by_customer'])

    return JsonResponse({'messages': data, 'is_closed': room.is_closed})


# ──────────────────────────────────────────────────────────────────────────────
#  Coins API
# ──────────────────────────────────────────────────────────────────────────────

def coin_balance(request):
    """GET — return current wallet balance (user wallet if logged in, else session)."""
    w = None
    if request.user.is_authenticated:
        w = CoinWallet.objects.filter(user=request.user).first()
    if w is None:
        sk = request.session.session_key
        if sk:
            w = CoinWallet.objects.filter(session_key=sk).first()
    return JsonResponse({'balance': w.balance if w else 0})


def coin_donate(request):
    """POST — donate coins from wallet to TreeDonation. Server-side validated."""
    if request.method != 'POST':
        return JsonResponse({'error': 'method'}, status=405)

    try:
        body = json.loads(request.body)
        amount = int(body.get('amount', 0))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'error': 'invalid'}, status=400)

    if amount <= 0:
        return JsonResponse({'error': 'จำนวนต้องมากกว่า 0'}, status=400)
    if amount > 100000:
        return JsonResponse({'error': 'จำนวนสูงสุด 100,000 coins'}, status=400)

    wallet = None
    if request.user.is_authenticated:
        wallet = CoinWallet.objects.filter(user=request.user).first()
    if wallet is None:
        sk = request.session.session_key
        if sk:
            wallet = CoinWallet.objects.filter(session_key=sk).first()
    if not wallet:
        return JsonResponse({'error': 'ไม่พบกระเป๋า coins'}, status=400)

    with transaction.atomic():
        wallet = CoinWallet.objects.select_for_update().get(pk=wallet.pk)
        if wallet.balance < amount:
            return JsonResponse({'error': f'coins ไม่เพียงพอ (มี {wallet.balance})'}, status=400)

        from django.db.models import F
        CoinWallet.objects.filter(pk=wallet.pk).update(
            balance=F('balance') - amount,
            total_donated=F('total_donated') + amount,
        )
        CoinTransaction.objects.create(
            wallet=wallet, amount=-amount, reason='donate',
            note=f'บริจาค {amount} coins เพื่อปลูกต้นไม้',
        )
        tree, _ = TreeDonation.objects.select_for_update().get_or_create(pk=1)
        TreeDonation.objects.filter(pk=1).update(
            total_coins_donated=F('total_coins_donated') + amount,
        )

    tree_fresh = TreeDonation.objects.get(pk=1)
    wallet_fresh = CoinWallet.objects.get(pk=wallet.pk)
    return JsonResponse({
        'ok': True,
        'new_balance': wallet_fresh.balance,
        'total_donated': tree_fresh.total_coins_donated,
        'goal': tree_fresh.goal,
    })


# ──────────────────────────────────────────────────────────────────────────────
#  Review API
# ──────────────────────────────────────────────────────────────────────────────

def product_reviews_api(request, product_id):
    """GET — paginated JSON list of visible reviews for a product."""
    try:
        offset = max(0, int(request.GET.get('offset', 0)))
        star = int(request.GET.get('star', 0))   # 0 = all
    except (ValueError, TypeError):
        offset, star = 0, 0

    qs = ProductReview.objects.filter(product_id=product_id, is_visible=True)
    if 1 <= star <= 5:
        qs = qs.filter(rating=star)

    total = qs.count()
    reviews = list(qs[offset:offset + 10])
    data = [
        {
            'id': r.id,
            'name': r.customer_name,
            'rating': r.rating,
            'comment': r.comment,
            'date': r.created_at.strftime('%d/%m/%Y'),
        }
        for r in reviews
    ]
    return JsonResponse({'reviews': data, 'total': total, 'offset': offset})


# ──────────────────────────────────────────────────────────────────────────────
#  Auth helpers
# ──────────────────────────────────────────────────────────────────────────────

def _login_rate_limit(ip):
    """Return (is_blocked, seconds_remaining). Allows 5 failures per 15 min."""
    attempts = cache.get(f'login_fail:{ip}', [])
    now = timezone.now().timestamp()
    attempts = [t for t in attempts if now - t < 900]
    if len(attempts) >= 5:
        remaining = int(900 - (now - min(attempts)))
        return True, max(0, remaining)
    return False, 0


def _record_login_fail(ip):
    key = f'login_fail:{ip}'
    attempts = cache.get(key, [])
    now = timezone.now().timestamp()
    attempts = [t for t in attempts if now - t < 900]
    attempts.append(now)
    cache.set(key, attempts, 900)


def _clear_login_fail(ip):
    cache.delete(f'login_fail:{ip}')


def _merge_session_to_user(request, user, old_sk):
    """After login, link unclaimed session data to the user account."""
    from django.db.models import F
    with transaction.atomic():
        order_ids = request.session.get('my_orders', [])
        if order_ids:
            Order.objects.filter(pk__in=order_ids, user__isnull=True).update(user=user)

        booking_ids = request.session.get('my_bookings', [])
        if booking_ids:
            PlotBooking.objects.filter(pk__in=booking_ids, user__isnull=True).update(user=user)

        if old_sk:
            session_wallet = CoinWallet.objects.filter(session_key=old_sk).first()
            if session_wallet and not session_wallet.user_id:
                user_wallet = CoinWallet.objects.filter(user=user).exclude(pk=session_wallet.pk).first()
                if user_wallet:
                    # Merge session_wallet balance into user_wallet
                    if session_wallet.balance > 0:
                        CoinWallet.objects.filter(pk=user_wallet.pk).update(
                            balance=F('balance') + session_wallet.balance,
                            total_earned=F('total_earned') + session_wallet.total_earned,
                            total_donated=F('total_donated') + session_wallet.total_donated,
                        )
                        CoinTransaction.objects.create(
                            wallet=user_wallet,
                            amount=session_wallet.balance,
                            reason='adjust',
                            note=f'รวม {session_wallet.balance} coins จาก session {old_sk[:8]}… เข้าบัญชี',
                        )
                    CoinTransaction.objects.filter(wallet=session_wallet).update(wallet=user_wallet)
                    session_wallet.delete()
                else:
                    CoinWallet.objects.filter(pk=session_wallet.pk).update(user=user)


# ──────────────────────────────────────────────────────────────────────────────
#  Auth Views
# ──────────────────────────────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    errors = {}
    form_data = {}

    if request.method == 'POST':
        first_name    = str(request.POST.get('first_name', '')).strip()[:50]
        last_name     = str(request.POST.get('last_name', '')).strip()[:50]
        email         = str(request.POST.get('email', '')).strip().lower()[:254]
        phone_raw     = re.sub(r'[\s\-]', '', str(request.POST.get('phone', '')).strip())
        password      = request.POST.get('password', '')
        password2     = request.POST.get('password2', '')

        form_data = {'first_name': first_name, 'last_name': last_name, 'email': email, 'phone': phone_raw}

        if not first_name:
            errors['first_name'] = 'กรุณาระบุชื่อ'
        if not last_name:
            errors['last_name'] = 'กรุณาระบุนามสกุล'
        if not email or '@' not in email:
            errors['email'] = 'รูปแบบอีเมลไม่ถูกต้อง'
        elif User.objects.filter(username=email).exists():
            errors['email'] = 'อีเมลนี้มีผู้ใช้งานแล้ว'
        if phone_raw and not re.match(r'^\d{9,10}$', phone_raw):
            errors['phone'] = 'เบอร์โทรไม่ถูกต้อง (9-10 หลัก)'
        if len(password) < 8:
            errors['password'] = 'รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร'
        elif password != password2:
            errors['password2'] = 'รหัสผ่านไม่ตรงกัน'

        if not errors:
            old_sk = request.session.session_key
            with transaction.atomic():
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )
                UserProfile.objects.create(user=user, phone=phone_raw)
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            _merge_session_to_user(request, user, old_sk)
            next_url = request.GET.get('next', '')
            if next_url and next_url.startswith('/') and not next_url.startswith('//'):
                return redirect(next_url)
            return redirect('home')

    return render(request, 'register.html', {'errors': errors, 'form_data': form_data})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    error = None

    if request.method == 'POST':
        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')).split(',')[0].strip()
        is_blocked, seconds_left = _login_rate_limit(ip)
        if is_blocked:
            mins = (seconds_left + 59) // 60
            error = f'เข้าสู่ระบบผิดพลาดหลายครั้ง กรุณารอ {mins} นาที แล้วลองใหม่'
        else:
            email    = str(request.POST.get('email', '')).strip().lower()
            password = request.POST.get('password', '')
            remember = request.POST.get('remember', '')

            user = authenticate(request, username=email, password=password)
            if user is not None:
                old_sk = request.session.session_key
                auth_login(request, user)
                _clear_login_fail(ip)
                if not remember:
                    request.session.set_expiry(0)
                _merge_session_to_user(request, user, old_sk)
                next_url = request.POST.get('next') or request.GET.get('next', '')
                if next_url and next_url.startswith('/') and not next_url.startswith('//'):
                    return redirect(next_url)
                return redirect('home')
            else:
                _record_login_fail(ip)
                error = 'อีเมลหรือรหัสผ่านไม่ถูกต้อง'

    return render(request, 'login.html', {
        'error': error,
        'next': request.GET.get('next', ''),
    })


def logout_view(request):
    if request.method == 'POST':
        auth_logout(request)
        next_url = request.POST.get('next', '').strip()
        if next_url and next_url.startswith('/') and not next_url.startswith('//'):
            return redirect(next_url)
    return redirect('login')


def profile_view(request):
    if not request.user.is_authenticated:
        return redirect(f'/login/?next=/profile/')

    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    success = None
    errors = {}

    if request.method == 'POST':
        action = request.POST.get('action', 'profile')

        if action == 'profile':
            first_name      = str(request.POST.get('first_name', '')).strip()[:50]
            last_name       = str(request.POST.get('last_name', '')).strip()[:50]
            phone_raw       = re.sub(r'[\s\-]', '', str(request.POST.get('phone', '')).strip())
            default_address = str(request.POST.get('default_address', '')).strip()[:1000]

            if not first_name:
                errors['first_name'] = 'กรุณาระบุชื่อ'
            if not last_name:
                errors['last_name'] = 'กรุณาระบุนามสกุล'
            if phone_raw and not re.match(r'^\d{9,10}$', phone_raw):
                errors['phone'] = 'เบอร์โทรไม่ถูกต้อง (9-10 หลัก)'

            if not errors:
                user.first_name = first_name
                user.last_name  = last_name
                user.save(update_fields=['first_name', 'last_name'])
                profile.phone           = phone_raw
                profile.default_address = default_address
                profile.save(update_fields=['phone', 'default_address'])
                success = 'บันทึกข้อมูลสำเร็จ'

        elif action == 'password':
            old_pw  = request.POST.get('old_password', '')
            new_pw  = request.POST.get('new_password', '')
            new_pw2 = request.POST.get('new_password2', '')

            if not user.check_password(old_pw):
                errors['old_password'] = 'รหัสผ่านเดิมไม่ถูกต้อง'
            elif len(new_pw) < 8:
                errors['new_password'] = 'รหัสผ่านใหม่ต้องมีอย่างน้อย 8 ตัวอักษร'
            elif new_pw != new_pw2:
                errors['new_password2'] = 'รหัสผ่านใหม่ไม่ตรงกัน'
            else:
                user.set_password(new_pw)
                user.save()
                auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                success = 'เปลี่ยนรหัสผ่านสำเร็จ'

    wallet = CoinWallet.objects.filter(user=user).first()
    if not wallet and request.session.session_key:
        wallet = CoinWallet.objects.filter(session_key=request.session.session_key).first()

    return render(request, 'profile.html', {
        'profile': profile,
        'wallet_balance': wallet.balance if wallet else 0,
        'success': success,
        'errors': errors,
    })


def submit_review(request, order_id, product_id):
    """POST — submit a review. All validation server-side."""
    if request.method != 'POST':
        return JsonResponse({'error': 'method'}, status=405)

    # 1. order must belong to this user/session
    if not _user_owns_order(request, order_id):
        return JsonResponse({'error': 'ไม่พบออเดอร์นี้ในบัญชีของคุณ'}, status=403)

    try:
        order = Order.objects.prefetch_related('items').get(pk=order_id)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'ไม่พบออเดอร์'}, status=404)

    # 2. order must be delivered/completed
    if order.status not in ('delivered', 'completed'):
        return JsonResponse({'error': 'สามารถรีวิวได้เฉพาะสินค้าที่ได้รับแล้วเท่านั้น'}, status=403)

    # 3. product must be in this order
    if not order.items.filter(product_id=product_id).exists():
        return JsonResponse({'error': 'สินค้านี้ไม่ได้อยู่ในออเดอร์'}, status=403)

    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'ไม่พบสินค้า'}, status=404)

    # 4. not already reviewed
    if ProductReview.objects.filter(product=product, order=order).exists():
        return JsonResponse({'error': 'คุณรีวิวสินค้านี้จากออเดอร์นี้แล้ว'}, status=400)

    # 5. parse and validate body
    try:
        body = json.loads(request.body)
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({'error': 'bad_json'}, status=400)

    try:
        rating = int(body.get('rating', 0))
    except (ValueError, TypeError):
        rating = 0
    if not (1 <= rating <= 5):
        return JsonResponse({'error': 'คะแนนต้องเป็น 1-5'}, status=400)

    customer_name = str(body.get('customer_name', '')).strip()[:100]
    if not customer_name:
        return JsonResponse({'error': 'กรุณาระบุชื่อ'}, status=400)

    comment = str(body.get('comment', '')).strip()[:1000]

    ProductReview.objects.create(
        product=product,
        order=order,
        customer_name=customer_name,
        rating=rating,
        comment=comment,
    )
    return JsonResponse({'ok': True})
