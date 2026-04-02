from django.shortcuts import render, redirect
from django.http import Http404
from datetime import datetime, timedelta
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User 
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import VeggiePlotBooking, Order, Product
from .forms import QuantumUserEditForm, QuantumProductForm, QuantumPlotForm

# ==========================================
# 1. ข้อมูลสินค้าแบบ Static (สำหรับแสดงผลหน้า Shop)
# ==========================================
ALL_PRODUCTS = [
    {'id': 1, 'name': 'บัวรดน้ำ', 'price': 6.00, 'description': '🚿 บัวรดน้ำคุณภาพสูง รดน้ำได้แม่นยำ', 'image': 'images/grow_kits/watering_can.png', 'category': 'tools'},
    {'id': 2, 'name': 'ถุงขยะสวน', 'price': 6.00, 'description': '🗑️ ถุงขยะสวนเอนกประสงค์ วัสดุเหนียวพิเศษ', 'image': 'images/grow_kits/garden_waste_bags.png', 'category': 'tools'},
    {'id': 3, 'name': 'ป้ายชื่อต้นไม้', 'price': 2.00, 'description': '🏷️ ป้ายชื่อต้นไม้ ทนแดดทนฝน', 'image': 'images/grow_kits/plant_labels.png', 'category': 'tools'},
    {'id': 4, 'name': 'กระถาง & ถาดเพาะเมล็ด', 'price': 2.00, 'description': '🌱 ชุดเริ่มต้นความสุข คุณภาพพรีเมียม', 'image': 'images/grow_kits/pots_and_seed_trays.png', 'category': 'tools'},
    {'id': 5, 'name': 'สายยางพร้อมหัวฉีด', 'price': 12.00, 'description': '🚿 สายยางพร้อมหัวฉีดละอองละเอียด', 'image': 'images/grow_kits/hose_with_spray_nozzle.png', 'category': 'tools'},
    {'id': 6, 'name': 'กรรไกรตัดกิ่งยาว', 'price': 20.00, 'description': '✂️ กรรไกรตัดกิ่งพรีเมียม คมกริบ ผ่อนแรง', 'image': 'images/grow_kits/long_handle_pruning_shears.png', 'category': 'tools'},
    {'id': 7, 'name': 'พลั่ว', 'price': 20.00, 'description': '⛏️ พลั่วตักดินพรีเมียม แข็งแกร่ง ทนทาน', 'image': 'images/grow_kits/garden_shovel.png', 'category': 'tools'},
    {'id': 8, 'name': 'คราด', 'price': 20.00, 'description': '🍂 คราดพรวนดินพรีเมียม เตรียมหน้าดินให้พร้อม', 'image': 'images/grow_kits/garden_rake.png', 'category': 'tools'},
    {'id': 9, 'name': 'ถุงมือทำสวน', 'price': 7.00, 'description': '🧤 ถุงมือทำสวนปกป้องมือคุณ นุ่มสบาย ทนทาน', 'image': 'images/grow_kits/gardening_gloves.png', 'category': 'tools'},
    {'id': 10, 'name': 'เมล็ดมะเขือเทศ', 'price': 1.10, 'description': '🍅 เมล็ดพันธุ์มะเขือเทศ อัตราการงอกสูง', 'image': 'images/seeds/tomato_seeds.png', 'category': 'seeds'},
    # ... (สามารถเพิ่มสินค้าตัวอื่นๆ ที่เหลือของคุณต่อลงไปได้เลยครับ) ...
]

# ==========================================
# 2. ฟังก์ชันหน้าเว็บหลัก (General Views)
# ==========================================

def home(request):
    return render(request, 'home.html')

def shop(request):
    return render(request, 'shop.html', {'products': ALL_PRODUCTS})

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def veggie_plots(request):
    return render(request, 'veggie_plots.html')

def plot_detail(request):
    # ฟังก์ชันนี้ต้องมีเพื่อให้ตรงกับ urls.py
    return render(request, 'plot_detail.html')

def cart(request):
    return render(request, 'cart.html')

def product_detail(request, product_id):
    product = next((item for item in ALL_PRODUCTS if item['id'] == product_id), None)
    if product is None:
        raise Http404("ไม่พบสินค้านี้")

    # เก็บประวัติการดูสินค้าลง Session
    if 'recent_viewed' not in request.session:
        request.session['recent_viewed'] = []
    
    recent = request.session['recent_viewed']
    if product_id in recent:
        recent.remove(product_id)
    recent.insert(0, product_id)
    request.session['recent_viewed'] = recent[:4]
    request.session.modified = True

    related_products = [p for p in ALL_PRODUCTS if p['id'] != product_id][:4]
    return render(request, 'product_detail.html', {'product': product, 'related_products': related_products})

# ==========================================
# 3. ระบบสมาชิกและการยืนยันตัวตน (Authentication)
# ==========================================

def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            # ถ้าเป็นแอดมินให้ไป Dashboard ทันที
            if user.is_superuser or user.is_staff:
                return redirect('admin_dashboard')
            return redirect('home')
        else:
            messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
    return render(request, 'login.html')

def register_view(request):
    if request.method == 'POST':
        u, e, p1, p2 = request.POST.get('username'), request.POST.get('email'), request.POST.get('password'), request.POST.get('confirm_password')
        if p1 != p2:
            messages.error(request, 'รหัสผ่านไม่ตรงกัน')
        elif User.objects.filter(username=u).exists():
            messages.error(request, 'ชื่อผู้ใช้นี้มีคนใช้แล้ว')
        else:
            User.objects.create_user(username=u, email=e, password=p1)
            messages.success(request, 'สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบ')
            return redirect('login')
    return render(request, 'register.html')

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required(login_url='login')
def profile_view(request):
    plot_bookings = VeggiePlotBooking.objects.filter(user=request.user).order_by('-booking_date')
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    recent_ids = request.session.get('recent_viewed', [])
    recent_products = []
    for pid in recent_ids:
        prod = next((item for item in ALL_PRODUCTS if item['id'] == pid), None)
        if prod:
            recent_products.append(prod)

    context = {
        'plot_bookings': plot_bookings,
        'orders': orders,
        'recent_products': recent_products,
    }
    return render(request, 'profile.html', context)

# ==========================================
# 4. ระบบจัดการสำหรับแอดมิน (Quantum Admin)
# ==========================================

@login_required(login_url='login')
def admin_dashboard_view(request):
    if not request.user.is_staff: return redirect('home')
    
    context = {
        'total_users': User.objects.filter(is_superuser=False).count(),
        'total_sales': Order.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0,
        'total_orders': Order.objects.count(),
        'total_plots': VeggiePlotBooking.objects.count(),
        'recent_orders': Order.objects.all().order_by('-created_at')[:5],
        'recent_bookings': VeggiePlotBooking.objects.all().order_by('-booking_date')[:5],
    }
    return render(request, 'admin_dashboard.html', context)

@login_required(login_url='login')
def admin_users_view(request):
    if not request.user.is_staff: return redirect('home')
    users = User.objects.filter(is_superuser=False).order_by('-date_joined')
    return render(request, 'admin_users.html', {'all_users': users})

@login_required(login_url='login')
def admin_orders_view(request):
    if not request.user.is_staff: return redirect('home')
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'admin_orders.html', {'all_orders': orders})

@login_required(login_url='login')
def admin_plots_view(request):
    if not request.user.is_staff: return redirect('home')
    plots = VeggiePlotBooking.objects.all().order_by('-booking_date')
    return render(request, 'admin_plots.html', {'all_plots': plots})

@login_required(login_url='login')
def admin_products_view(request):
    if not request.user.is_staff: return redirect('home')
    products = Product.objects.all() 
    return render(request, 'admin_products.html', {'all_products': products})

# ==========================================
# 5. ฟังก์ชันประมวลผล (Business Logic)
# ==========================================

def process_booking(request):
    if request.method == 'POST':
        plant_name = request.POST.get('selected_plant')
        start_date_str = request.POST.get('start_date')
        if plant_name and start_date_str:
            # Logic การจองของคุณ...
            return render(request, 'booking_success.html', {'plant': plant_name})
    return redirect('veggie_plots')



@login_required(login_url='login')
def admin_edit_user_view(request, user_id):
    if not request.user.is_staff: return redirect('home')
    
    user_to_edit = User.objects.get(id=user_id)
    
    if request.method == 'POST':
        form = QuantumUserEditForm(request.POST, instance=user_to_edit)
        if form.is_valid():
            form.save()
            messages.success(request, f"NODE_{user_id} : ข้อมูลถูกอัปเดตเข้าระบบแล้ว")
            return redirect('admin_users')
    else:
        form = QuantumUserEditForm(instance=user_to_edit)
    
    return render(request, 'admin_edit_user.html', {
        'form': form,
        'edit_user': user_to_edit
    })

# ส่วนบนของ views.py


# --- ฟังก์ชันจัดการแบบรวมศูนย์ (ใช้หน้าเดียวแก้ได้ทุกอย่าง) ---

# --- ฟังก์ชันลบข้อมูล ---
@login_required
def admin_delete_handler(request, model_type, item_id):
    if not request.user.is_staff: return redirect('home')
    
    if model_type == 'user': model, red = User, 'admin_users'
    elif model_type == 'product': model, red = Product, 'admin_products'
    elif model_type == 'plot': model, red = VeggiePlotBooking, 'admin_plots'
    
    model.objects.get(id=item_id).delete()
    messages.warning(request, f"NODE_DELETED: ลบข้อมูลออกจากระบบแล้ว")
    return redirect(red)

@login_required
def admin_manager_view(request, model_type, item_id=None):
    if not request.user.is_staff: return redirect('home')

    # กำหนด Model และ Form ตามประเภทข้อมูล
    mapping = {
        'user': (User, QuantumUserEditForm, 'admin_users'),
        'product': (Product, QuantumProductForm, 'admin_products'),
        'plot': (VeggiePlotBooking, QuantumPlotForm, 'admin_plots'),
    }
    
    if model_type not in mapping: return redirect('admin_dashboard')
    
    model_class, form_class, redirect_url = mapping[model_type]
    instance = model_class.objects.get(id=item_id) if item_id else None

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            saved_instance = form.save()
            messages.success(request, f"QUANTUM_SYNC: [{model_type.upper()}] อัปเดตข้อมูลสำเร็จ")
            
            # เช็คว่ากดปุ่ม Save & Continue หรือไม่
            if 'save_continue' in request.POST:
                return redirect('admin_edit', model_type=model_type, item_id=saved_instance.id)
            return redirect(redirect_url)
    else:
        form = form_class(instance=instance)

    return render(request, 'admin_editor.html', {
        'form': form,
        'instance': instance,
        'model_type': model_type,
        'title': f'EDIT_{model_type.upper()}'
    })