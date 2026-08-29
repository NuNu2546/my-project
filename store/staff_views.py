"""
Staff dashboard views — all protected by is_staff check.
URL prefix: /staff/
"""
import json
import os
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps

from django.conf import settings as django_settings
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import (
    BOOKING_STATUS_CHOICES, BOOKING_CARRIER_CHOICES,
    ORDER_CARRIER_CHOICES, ORDER_STATUS_CHOICES,
    PRODUCT_CATEGORY_CHOICES,
    Order, OrderItem, OrderStatusHistory,
    PlotBooking, PlotBookingStatusHistory,
    Product, StockMovement,
    ChatRoom, ChatMessage,
)

# ── Auth decorator ────────────────────────────────────────────────────────────

def staff_required(view_fn):
    @wraps(view_fn)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.utils.http import urlencode
            return redirect('/login/?' + urlencode({'next': request.get_full_path()}))
        if not request.user.is_staff:
            return render(request, '403.html', status=403)
        return view_fn(request, *args, **kwargs)
    return wrapped


# ── Helpers ───────────────────────────────────────────────────────────────────

def _count_new_orders():
    """Orders not yet viewed by staff."""
    return Order.objects.filter(is_viewed_by_staff=False, status__in=['paid', 'pending']).count()


def _count_unread_chats():
    return ChatRoom.objects.filter(is_closed=False, unread_by_staff__gt=0).count()


def _base_ctx(request):
    """Common context injected into every staff template."""
    return {
        'new_order_count': _count_new_orders(),
        'unread_chat_count': _count_unread_chats(),
    }


# ── Overview ──────────────────────────────────────────────────────────────────

@staff_required
def overview(request):
    today       = timezone.localdate()
    month_start = today.replace(day=1)

    orders_today        = Order.objects.filter(created_at__date=today).count()
    orders_pending_ship = Order.objects.filter(status='paid').count()
    revenue_today  = Order.objects.filter(
        status__in=['paid', 'shipped', 'in_transit', 'delivered'],
        created_at__date=today,
    ).aggregate(t=Sum('total'))['t'] or 0
    revenue_month  = Order.objects.filter(
        status__in=['paid', 'shipped', 'in_transit', 'delivered'],
        created_at__date__gte=month_start,
    ).aggregate(t=Sum('total'))['t'] or 0
    low_stock_count     = Product.objects.filter(is_active=True, stock_quantity__lt=5, stock_quantity__gt=0).count()
    out_of_stock_count  = Product.objects.filter(is_active=True, stock_quantity=0).count()
    bookings_action     = PlotBooking.objects.filter(
        status__in=['ready_to_harvest', 'harvested', 'preparing']
    ).count()
    new_orders          = _count_new_orders()

    recent_orders = Order.objects.prefetch_related('items').order_by('-created_at')[:10]

    ctx = _base_ctx(request)
    ctx.update({
        'stats': {
            'orders_today':       orders_today,
            'orders_pending_ship': orders_pending_ship,
            'revenue_today':      revenue_today,
            'revenue_month':      revenue_month,
            'low_stock_count':    low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'bookings_action':    bookings_action,
            'new_orders':         new_orders,
        },
        'recent_orders': recent_orders,
    })
    return render(request, 'staff/overview.html', ctx)


# ── New order count API (polling) ─────────────────────────────────────────────

@staff_required
def new_order_count(request):
    return JsonResponse({
        'count': _count_new_orders(),
        'chat_count': _count_unread_chats(),
    })


# ── Orders list ───────────────────────────────────────────────────────────────

# Tab definitions: (tab_key, label, status_filter_values)
ORDER_TABS = [
    ('pending',  'รอชำระ',     ['pending']),
    ('paid',     'รอจัดส่ง',   ['paid']),
    ('shipped',  'จัดส่งแล้ว', ['shipped', 'in_transit']),
    ('done',     'สำเร็จ',     ['delivered']),
    ('negative', 'ยกเลิก',     ['cancelled', 'expired', 'failed']),
    ('all',      'ทั้งหมด',    []),
]


@staff_required
def orders_list(request):
    tab           = request.GET.get('tab', 'paid')
    q             = request.GET.get('q', '').strip()
    date_from_str = request.GET.get('date_from', '').strip()
    date_to_str   = request.GET.get('date_to', '').strip()
    sort          = request.GET.get('sort', 'newest')

    # Counts for tab badges
    tab_counts = {}
    for key, _, statuses in ORDER_TABS:
        if key == 'all':
            tab_counts[key] = Order.objects.count()
        else:
            tab_counts[key] = Order.objects.filter(status__in=statuses).count()

    qs = Order.objects.prefetch_related('items')

    # Filter by tab
    for key, _, statuses in ORDER_TABS:
        if tab == key and statuses:
            qs = qs.filter(status__in=statuses)
            break

    # Search
    if q:
        qs = qs.filter(
            Q(id__icontains=q) | Q(customer_name__icontains=q) | Q(phone__icontains=q)
        )

    # Date range
    if date_from_str:
        try:
            df = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            qs = qs.filter(created_at__date__gte=df)
        except ValueError:
            pass
    if date_to_str:
        try:
            dt = datetime.strptime(date_to_str, '%Y-%m-%d').date()
            qs = qs.filter(created_at__date__lte=dt)
        except ValueError:
            pass

    # Sort
    qs = qs.order_by('created_at' if sort == 'oldest' else '-created_at')

    paginator = Paginator(qs, 30)
    orders    = paginator.get_page(request.GET.get('page'))

    ctx = _base_ctx(request)
    ctx.update({
        'orders':        orders,
        'tab':           tab,
        'tab_counts':    tab_counts,
        'ORDER_TABS':    ORDER_TABS,
        'q':             q,
        'date_from':     date_from_str,
        'date_to':       date_to_str,
        'sort':          sort,
    })
    return render(request, 'staff/orders.html', ctx)


# ── Order detail ──────────────────────────────────────────────────────────────

@staff_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, pk=order_id)

    # Mark as viewed
    if not order.is_viewed_by_staff:
        Order.objects.filter(pk=order_id).update(is_viewed_by_staff=True)
        order.is_viewed_by_staff = True

    # Product image lookup
    product_images = {p.id: p.image for p in Product.objects.only('id', 'image')}
    items_with_img = [
        {'item': item, 'image': product_images.get(item.product_id, '')}
        for item in order.items.all()
    ]
    movements = StockMovement.objects.filter(order=order).select_related('product')

    ctx = _base_ctx(request)
    ctx.update({
        'order':           order,
        'items_with_img':  items_with_img,
        'movements':       movements,
        'status_choices':  ORDER_STATUS_CHOICES,
        'carrier_choices': ORDER_CARRIER_CHOICES,
    })
    return render(request, 'staff/order_detail.html', ctx)


@staff_required
def order_action(request, order_id):
    """Handle status transitions + tracking info + staff note."""
    if request.method != 'POST':
        return redirect('staff_order_detail', order_id=order_id)

    order      = get_object_or_404(Order, pk=order_id)
    action     = request.POST.get('action', '').strip()
    note       = request.POST.get('note', '').strip()

    # Update staff note (always)
    staff_note = request.POST.get('staff_note', '').strip()
    if staff_note != order.staff_note:
        Order.objects.filter(pk=order_id).update(staff_note=staff_note)
        order.staff_note = staff_note

    status_map = {
        'preparing': ('paid',      'paid'),
        'ship':      ('paid',      None),    # special: needs tracking info
        'delivered': ('shipped',   'in_transit'),
        'complete':  ('delivered', None),
        'cancel':    (None,        None),    # any → cancelled
    }

    new_status        = None
    tracking_number   = request.POST.get('tracking_number', '').strip()
    shipping_carrier  = request.POST.get('shipping_carrier', '').strip()

    if action == 'preparing' and order.status == 'paid':
        new_status = 'paid'   # stay paid, just mark preparing conceptually?
        # Actually let's use in_transit as "preparing" conceptually
        # The spec says paid → preparing → shipped
        # We'll set status to 'in_transit' to mean "preparing/packed"
        new_status = 'in_transit'
    elif action == 'ship' and order.status in ('paid', 'in_transit'):
        if not tracking_number:
            # Redirect back with error — we'll just redirect without change
            return redirect('staff_order_detail', order_id=order_id)
        new_status = 'shipped'
        order.tracking_number  = tracking_number
        order.shipping_carrier = shipping_carrier
        order.save(update_fields=['tracking_number', 'shipping_carrier'])
    elif action == 'delivered' and order.status in ('shipped', 'in_transit'):
        new_status = 'delivered'
    elif action == 'complete' and order.status == 'delivered':
        new_status = 'delivered'  # already final, mark some way
    elif action == 'cancel' and order.status not in ('delivered', 'cancelled', 'expired', 'failed'):
        new_status = 'cancelled'

    if new_status and new_status != order.status:
        order._status_note  = note
        order._status_staff = request.user
        order.status = new_status
        order.save()

    return redirect('staff_order_detail', order_id=order_id)


@staff_required
def order_update_status(request, order_id):
    """Generic status + tracking update from detail form."""
    if request.method != 'POST':
        return redirect('staff_order_detail', order_id=order_id)

    order            = get_object_or_404(Order, pk=order_id)
    new_status       = request.POST.get('status', '').strip()
    tracking_number  = request.POST.get('tracking_number', '').strip()
    shipping_carrier = request.POST.get('shipping_carrier', '').strip()
    note             = request.POST.get('note', '').strip()
    staff_note       = request.POST.get('staff_note', '').strip()

    # staff note (internal, no history)
    Order.objects.filter(pk=order_id).update(staff_note=staff_note)

    valid_statuses = [v for v, _ in ORDER_STATUS_CHOICES]
    if new_status in valid_statuses and new_status != order.status:
        order._status_note  = note
        order._status_staff = request.user
        order.status = new_status
    order.tracking_number  = tracking_number
    order.shipping_carrier = shipping_carrier
    order.save()

    return redirect('staff_order_detail', order_id=order_id)


@staff_required
def packing_slip(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    product_images = {p.id: p.image for p in Product.objects.only('id', 'image')}
    items_with_img = [
        {'item': item, 'image': product_images.get(item.product_id, '')}
        for item in order.items.all()
    ]
    return render(request, 'staff/packing_slip.html', {
        'order': order,
        'items_with_img': items_with_img,
    })


# ── Bookings ──────────────────────────────────────────────────────────────────

BOOKING_TABS = [
    ('pending',    'รอชำระ',          ['pending']),
    ('active',     'กำลังดำเนินการ',  ['paid', 'growing', 'ready_to_harvest']),
    ('harvest',    'เก็บเกี่ยว/จัดส่ง', ['harvested', 'awaiting_shipping_payment', 'preparing', 'shipped', 'ready_for_pickup']),
    ('done',       'สำเร็จ',          ['completed', 'delivered']),
    ('negative',   'ยกเลิก',          ['cancelled', 'expired']),
    ('all',        'ทั้งหมด',         []),
]


@staff_required
def bookings_list(request):
    tab           = request.GET.get('tab', 'active')
    q             = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    date_from_str = request.GET.get('date_from', '').strip()
    date_to_str   = request.GET.get('date_to', '').strip()

    # Tab counts
    tab_counts = {}
    for key, _, statuses in BOOKING_TABS:
        if key == 'all':
            tab_counts[key] = PlotBooking.objects.count()
        else:
            tab_counts[key] = PlotBooking.objects.filter(status__in=statuses).count()

    qs = PlotBooking.objects.select_related('plot', 'plant').order_by('-created_at')

    for key, _, statuses in BOOKING_TABS:
        if tab == key and statuses:
            qs = qs.filter(status__in=statuses)
            break

    if q:
        qs = qs.filter(Q(customer_name__icontains=q) | Q(phone__icontains=q))
    if status_filter:
        qs = qs.filter(status=status_filter)
    if date_from_str:
        try:
            qs = qs.filter(created_at__date__gte=datetime.strptime(date_from_str, '%Y-%m-%d').date())
        except ValueError:
            pass
    if date_to_str:
        try:
            qs = qs.filter(created_at__date__lte=datetime.strptime(date_to_str, '%Y-%m-%d').date())
        except ValueError:
            pass

    paginator = Paginator(qs, 30)
    bookings  = paginator.get_page(request.GET.get('page'))

    ctx = _base_ctx(request)
    ctx.update({
        'bookings':       bookings,
        'tab':            tab,
        'tab_counts':     tab_counts,
        'BOOKING_TABS':   BOOKING_TABS,
        'q':              q,
        'status_filter':  status_filter,
        'date_from':      date_from_str,
        'date_to':        date_to_str,
        'status_choices': BOOKING_STATUS_CHOICES,
    })
    return render(request, 'staff/bookings.html', ctx)


@staff_required
def booking_detail(request, booking_id):
    booking  = get_object_or_404(PlotBooking.objects.select_related('plot', 'plant'), pk=booking_id)
    ctx = _base_ctx(request)
    ctx.update({
        'booking':          booking,
        'status_choices':   BOOKING_STATUS_CHOICES,
        'carrier_choices':  BOOKING_CARRIER_CHOICES,
    })
    return render(request, 'staff/booking_detail.html', ctx)


@staff_required
def booking_action(request, booking_id):
    """Advance booking status with optional harvest_weight / tracking."""
    if request.method != 'POST':
        return redirect('staff_booking_detail', booking_id=booking_id)

    from decimal import Decimal, InvalidOperation
    from datetime import timedelta

    booking = get_object_or_404(PlotBooking, pk=booking_id)
    action  = request.POST.get('action', '').strip()
    note    = request.POST.get('note', '').strip()

    new_status = None

    if action == 'growing' and booking.status == 'paid':
        new_status = 'growing'

    elif action == 'ready' and booking.status == 'growing':
        new_status = 'ready_to_harvest'

    elif action == 'harvested' and booking.status == 'ready_to_harvest':
        weight_raw = request.POST.get('harvest_weight', '').strip()
        if weight_raw:
            try:
                booking.harvest_weight = Decimal(weight_raw)
            except InvalidOperation:
                pass
        booking.pickup_deadline = booking.harvest_date + timedelta(days=7)
        new_status = 'harvested'

    elif action == 'preparing' and booking.status in ('harvested', 'awaiting_shipping_payment'):
        new_status = 'preparing'

    elif action == 'pickup' and booking.status == 'harvested':
        booking.delivery_method = 'pickup'
        new_status = 'ready_for_pickup'

    elif action == 'shipped' and booking.status == 'preparing':
        tracking = request.POST.get('tracking_number', '').strip()
        carrier  = request.POST.get('shipping_carrier', '').strip()
        if tracking:
            booking.tracking_number  = tracking
            booking.shipping_carrier = carrier
        new_status = 'shipped'

    elif action == 'delivered' and booking.status == 'shipped':
        new_status = 'delivered'

    elif action == 'completed' and booking.status in ('delivered', 'ready_for_pickup'):
        new_status = 'completed'
        # Free up the plot by ensuring no overlap — PlotBooking completed = available
        # (plot availability is checked against active statuses — completed is excluded)

    if new_status and new_status != booking.status:
        booking._status_note  = note
        booking._status_staff = request.user
        booking.status = new_status
        booking.save()

    return redirect('staff_booking_detail', booking_id=booking_id)


# ── Products & stock ──────────────────────────────────────────────────────────

@staff_required
def products_list(request):
    tab = request.GET.get('tab', 'products')

    q          = request.GET.get('q', '').strip()
    cat_filter = request.GET.get('cat', '').strip()
    sort       = request.GET.get('sort', 'id')

    qs = Product.objects.all()
    if q:
        qs = qs.filter(name__icontains=q)
    if cat_filter:
        qs = qs.filter(category=cat_filter)

    sort_map = {'id': 'id', 'stock_asc': 'stock_quantity', 'stock_desc': '-stock_quantity', 'name': 'name'}
    qs = qs.order_by(sort_map.get(sort, 'id'))

    prod_paginator = Paginator(qs, 25)
    products       = prod_paginator.get_page(request.GET.get('page'))

    mq      = request.GET.get('mq', '').strip()
    mreason = request.GET.get('mreason', '').strip()
    mqs     = StockMovement.objects.select_related('product', 'order', 'staff')
    if mq:
        mqs = mqs.filter(product__name__icontains=mq)
    if mreason:
        mqs = mqs.filter(reason=mreason)

    mov_paginator = Paginator(mqs, 30)
    movements     = mov_paginator.get_page(request.GET.get('page'))

    ctx = _base_ctx(request)
    ctx.update({
        'tab':              tab,
        'products':         products,
        'total_count':      Product.objects.count(),
        'q':                q,
        'cat_filter':       cat_filter,
        'sort':             sort,
        'category_choices': PRODUCT_CATEGORY_CHOICES,
        'movements':        movements,
        'mq':               mq,
        'mreason':          mreason,
    })
    return render(request, 'staff/products.html', ctx)


@staff_required
def products_bulk_save(request):
    if request.method != 'POST':
        return redirect('staff_products')
    save_ids_raw = request.POST.get('save_ids', '').strip()
    if not save_ids_raw:
        return redirect('staff_products')
    try:
        pid = int(save_ids_raw)
    except ValueError:
        return redirect('staff_products')

    product = get_object_or_404(Product, pk=pid)
    try:
        product.price = Decimal(request.POST.get(f'price_{pid}', '').strip())
    except InvalidOperation:
        pass
    try:
        new_stock = int(request.POST.get(f'stock_{pid}', '').strip())
        if new_stock >= 0:
            diff = new_stock - product.stock_quantity
            product.stock_quantity = new_stock
            if diff != 0:
                StockMovement.objects.create(product=product, change=diff, reason='adjust', staff=request.user, note='ปรับยอดสต๊อกผ่าน Staff Dashboard')
    except (ValueError, TypeError):
        pass
    product.save()
    return redirect(f'/staff/products/?tab={request.POST.get("tab", "products")}')


@staff_required
def product_toggle_active(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    try:
        data      = json.loads(request.body)
        product   = get_object_or_404(Product, pk=int(data['product_id']))
        product.is_active = bool(data['is_active'])
        product.save(update_fields=['is_active', 'updated_at'])
        return JsonResponse({'ok': True})
    except Exception:
        return JsonResponse({'error': 'bad request'}, status=400)


@staff_required
def product_restock(request):
    if request.method != 'POST':
        return redirect('staff_products')
    try:
        pid = int(request.POST.get('product_id', 0))
        qty = int(request.POST.get('qty', 0))
    except (ValueError, TypeError):
        return redirect('staff_products')
    if qty <= 0:
        return redirect('staff_products')
    note = request.POST.get('note', '').strip()
    with transaction.atomic():
        product = Product.objects.select_for_update().get(pk=pid)
        product.stock_quantity += qty
        product.save(update_fields=['stock_quantity', 'updated_at'])
        StockMovement.objects.create(product=product, change=+qty, reason='restock', staff=request.user, note=note or f'เติมสต๊อก {qty} ชิ้น ผ่าน Staff Dashboard')
    return redirect(f'/staff/products/?tab={request.POST.get("tab", "products")}')


@staff_required
def product_add(request):
    if request.method != 'POST':
        return redirect('staff_products')
    name           = request.POST.get('name', '').strip()
    description    = request.POST.get('description', '').strip()
    category       = request.POST.get('category', '').strip()
    image_path     = request.POST.get('image_path', '').strip()
    stock_quantity = 0
    price          = Decimal('0')
    try:
        price = Decimal(request.POST.get('price', '0'))
    except InvalidOperation:
        pass
    try:
        stock_quantity = int(request.POST.get('stock_quantity', '0'))
    except (ValueError, TypeError):
        pass

    image_file = request.FILES.get('image_file')
    if image_file:
        upload_dir = os.path.join(django_settings.STATICFILES_DIRS[0], 'images', 'products')
        os.makedirs(upload_dir, exist_ok=True)
        filename   = image_file.name.replace(' ', '_')
        with open(os.path.join(upload_dir, filename), 'wb') as f:
            for chunk in image_file.chunks():
                f.write(chunk)
        image_path = f'images/products/{filename}'

    product = Product.objects.create(
        name=name, price=price, description=description,
        category=category, image=image_path or 'default.png',
        stock_quantity=stock_quantity, is_active=True,
    )
    product.slug = f'product-{product.pk}'
    product.save(update_fields=['slug'])
    if stock_quantity > 0:
        StockMovement.objects.create(product=product, change=+stock_quantity, reason='restock', staff=request.user, note='สต๊อกเริ่มต้นเมื่อสร้างสินค้า')
    return redirect('staff_products')


# ── Chat ──────────────────────────────────────────────────────────────────────

CANNED_RESPONSES = [
    'ขอบคุณที่ติดต่อมาค่ะ เดี๋ยวรอสักครู่นะคะ',
    'รับทราบแล้วค่ะ กำลังตรวจสอบให้',
    'ขออภัยในความไม่สะดวกค่ะ',
    'สินค้าจัดส่งแล้วค่ะ กรุณาตรวจสอบเลขพัสดุในอีเมลนะคะ',
    'หากมีข้อสงสัยเพิ่มเติมสามารถถามได้เลยค่ะ 🌿',
]


@staff_required
def chat_rooms(request):
    tab = request.GET.get('tab', 'open')
    if tab == 'closed':
        rooms = ChatRoom.objects.filter(is_closed=True).prefetch_related('messages')
    else:
        rooms = ChatRoom.objects.filter(is_closed=False).prefetch_related('messages')

    selected_room = None
    messages = []
    room_id = request.GET.get('room')
    if room_id:
        try:
            selected_room = ChatRoom.objects.prefetch_related('messages', 'related_order').get(pk=room_id)
            messages = list(selected_room.messages.all())
            # Mark incoming customer messages as read
            selected_room.messages.filter(sender_type='customer', is_read=False).update(is_read=True)
            ChatRoom.objects.filter(pk=selected_room.pk).update(unread_by_staff=0)
            selected_room.unread_by_staff = 0
        except ChatRoom.DoesNotExist:
            pass

    ctx = _base_ctx(request)
    ctx.update({
        'rooms': rooms,
        'selected_room': selected_room,
        'messages': messages,
        'tab': tab,
        'canned_responses': CANNED_RESPONSES,
    })
    return render(request, 'staff/chat.html', ctx)


@staff_required
def chat_staff_send(request, room_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'method'}, status=405)
    try:
        room = ChatRoom.objects.get(pk=room_id, is_closed=False)
    except ChatRoom.DoesNotExist:
        return JsonResponse({'error': 'not_found'}, status=404)

    try:
        body = json.loads(request.body)
    except (ValueError, KeyError):
        return JsonResponse({'error': 'bad_json'}, status=400)

    text = (body.get('message') or '').strip()[:500]
    if not text:
        return JsonResponse({'error': 'empty'}, status=400)

    staff_name = request.user.get_full_name() or request.user.username
    msg = ChatMessage.objects.create(
        room=room,
        sender_type='staff',
        sender_name=staff_name,
        message=text,
    )
    from django.utils import timezone as tz
    ChatRoom.objects.filter(pk=room.pk).update(
        unread_by_customer=room.unread_by_customer + 1,
        updated_at=tz.now(),
    )

    return JsonResponse({
        'id':          msg.id,
        'sender_type': msg.sender_type,
        'sender_name': msg.sender_name,
        'message':     msg.message,
        'created_at':  msg.created_at.strftime('%H:%M'),
    })


@staff_required
def chat_poll_staff(request, room_id):
    """GET: return messages newer than after_id for the staff window."""
    try:
        room = ChatRoom.objects.get(pk=room_id)
    except ChatRoom.DoesNotExist:
        return JsonResponse({'error': 'not_found'}, status=404)

    after_id = int(request.GET.get('after', 0))
    msgs = room.messages.filter(id__gt=after_id)
    data = [{
        'id':          m.id,
        'sender_type': m.sender_type,
        'sender_name': m.sender_name,
        'message':     m.message,
        'created_at':  m.created_at.strftime('%H:%M'),
    } for m in msgs]

    # Mark customer messages as read
    room.messages.filter(sender_type='customer', is_read=False).update(is_read=True)
    ChatRoom.objects.filter(pk=room.pk).update(unread_by_staff=0)

    return JsonResponse({'messages': data, 'is_closed': room.is_closed})


@staff_required
def chat_close_room(request, room_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'method'}, status=405)
    ChatRoom.objects.filter(pk=room_id).update(is_closed=True, unread_by_staff=0)
    return JsonResponse({'ok': True})
