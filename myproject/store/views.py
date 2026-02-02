from django.shortcuts import render
from django.http import Http404

ALL_PRODUCTS = [
    {
        'id': 1,
        'name': 'บัวรดน้ำ',
        'price': 6.00,
        'description': 'บัวรดน้ำคุณภาพดี ทนทาน น้ำไหลสม่ำเสมอ เหมาะสำหรับพืชทุกชนิด...',
        'image': 'images/grow_kits/watering_can.png',
        'category': 'tools'
    },
    {
        'id': 2,
        'name': 'ถุงขยะสวน',
        'price': 6.00,
        'description': 'ถุงเก็บเศษใบไม้ จุของได้เยอะ พับเก็บได้ ทำความสะอาดง่าย...',
        'image': 'images/grow_kits/garden_waste_bags.png',
        'category': 'tools'
    },
    {
        'id': 3,
        'name': 'ป้ายชื่อต้นไม้',
        'price': 2.00,
        'description': 'ป้าย',
        'image': 'images/grow_kits/plant_labels.png',
        'category': 'tools'
    },

]


def home(request):
    return render(request, 'home.html')

def shop(request):
    # ส่งข้อมูลสินค้าทั้งหมดไปที่หน้า Shop
    return render(request, 'shop.html', {'products': ALL_PRODUCTS})

def product_detail(request, product_id):
    # ค้นหาสินค้าจาก ID ใน list ข้างบน
    product = next((item for item in ALL_PRODUCTS if item['id'] == product_id), None)
    
    if product is None:
        raise Http404("ไม่พบสินค้านี้")

    # (Optional) หาสินค้าแนะนำ โดยเอาตัวอื่นที่ไม่ใช่ตัวปัจจุบัน
    related_products = [p for p in ALL_PRODUCTS if p['id'] != product_id][:4]

    context = {
        'product': product,
        'related_products': related_products
    }
    return render(request, 'product_detail.html', context)

# --- Views อื่นๆ คงเดิม ---
def veggie_plots(request):
    return render(request, 'veggie_plots.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')