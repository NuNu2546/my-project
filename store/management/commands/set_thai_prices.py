"""
Management command: python manage.py set_thai_prices
อัปเดตราคาสินค้า / ค่าเช่าแปลง / seed_price ให้เป็นราคาตลาดไทยที่สมจริง
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from store.models import Product, Plot, Plant


# ──────────────────────────────────────────────────────
#  PRODUCT PRICES  (id → new price in ฿)
# ──────────────────────────────────────────────────────
PRODUCT_PRICES = {
    # tools — ชิ้นกลาง
    1:  Decimal('290'),   # บัวรดน้ำ
    2:  Decimal('89'),    # ถุงขยะสวน (ชิ้นเล็ก)
    3:  Decimal('79'),    # ป้ายชื่อต้นไม้ (ชิ้นเล็กมาก)
    4:  Decimal('190'),   # กระถาง & ถาดเพาะเมล็ด (ชุดเล็ก)
    5:  Decimal('390'),   # สายยางพร้อมหัวฉีด (ชิ้นกลาง-พรีเมียม)
    6:  Decimal('390'),   # กรรไกรตัดกิ่งยาว (ชิ้นกลาง-คม)
    7:  Decimal('129'),   # พลั่ว
    8:  Decimal('149'),   # คราด
    9:  Decimal('89'),    # ถุงมือทำสวน (ชิ้นเล็ก)

    # seeds — เมล็ดทั่วไป/พรีเมียม
    10: Decimal('29'),    # เมล็ดมะเขือเทศ
    11: Decimal('69'),    # เมล็ดลาเวนเดอร์ (นำเข้า-พรีเมียม)
    12: Decimal('39'),    # เมล็ดดอกไม้ป่า (ชุดรวม)
    13: Decimal('25'),    # เมล็ดโหระพาหวาน
    14: Decimal('79'),    # เมล็ดสตรอว์เบอร์รี่ (พรีเมียม)
    15: Decimal('45'),    # เมล็ดผักกาดหอมกูร์เมต์
    16: Decimal('29'),    # เมล็ดทานตะวัน
    17: Decimal('29'),    # เมล็ดแครอท
    18: Decimal('25'),    # เมล็ดมะเขือยาว
    19: Decimal('25'),    # เมล็ดพริก
    20: Decimal('29'),    # เมล็ดแตงกวา
    21: Decimal('35'),    # เมล็ดฟักทอง

    # essential oils — 10ml
    22: Decimal('199'),   # เปปเปอร์มินต์
    23: Decimal('290'),   # คาโมมายล์ (rare)
    24: Decimal('350'),   # กุหลาบ (premium)
    25: Decimal('250'),   # หญ้าแฝก (vetiver)
    26: Decimal('229'),   # ลาเวนเดอร์ (popular)
    27: Decimal('320'),   # ไม้จันทน์หอม (premium)
    28: Decimal('199'),   # ตะไคร้หอม
    29: Decimal('189'),   # ส้มหวาน

    # aroma diffusers
    30: Decimal('890'),   # ทรงกรวย เขียวมะกอก
    31: Decimal('790'),   # ทรงสูง เทาดำ
    32: Decimal('990'),   # ทรงกระบอก ดำขาว (two-tone premium)
    33: Decimal('690'),   # ทรงลูกบาศก์ ขาวนวล
    34: Decimal('790'),   # ทรงกระบอก ขาวไม้
    35: Decimal('990'),   # ทรงสี่เหลี่ยม กรมท่า (premium)

    # dried flowers / herbs
    36: Decimal('159'),   # ดอกสแตติสแห้ง
    37: Decimal('149'),   # ดอกยิปโซฟิลลาแห้ง
    38: Decimal('159'),   # ดอกสตอร์วฟลาวเวอร์แห้ง
    39: Decimal('179'),   # ลาเวนเดอร์แห้ง
    40: Decimal('199'),   # กุหลาบแห้ง
    41: Decimal('229'),   # ไฮเดรนเยียแห้ง (ช่อใหญ่-พิเศษ)
    42: Decimal('149'),   # โรสแมรี่แห้ง
}


# ──────────────────────────────────────────────────────
#  PLOT PRICES  (code → new price_per_day in ฿)
#  คำนวณจาก area_sqm × rate/sqm/month ÷ 30 วัน
#  ≤100 sqm: ฿5/sqm/mo, ≥300 sqm: ฿4/sqm/mo
# ──────────────────────────────────────────────────────
PLOT_PRICES = {
    'A12': Decimal('16'),   # 100 sqm  (100×5÷30 ≈16)
    'B04': Decimal('15'),   # 96 sqm   (96×5÷30 =16, ปัดลง)
    'C21': Decimal('5'),    # 25 sqm   (25×5÷30 ≈4.2, ปัดขึ้น=5 ตามตัวอย่าง)
    'D08': Decimal('15'),   # 96 sqm
    'E15': Decimal('16'),   # 100 sqm
    'F01': Decimal('40'),   # 300 sqm  (300×4÷30=40)
}

# แปลงขนาด string → ตร.ม.
PLOT_AREA = {
    'A12': 100,   # 10x10
    'B04': 96,    # 8x12
    'C21': 25,    # 5x5
    'D08': 96,    # 12x8
    'E15': 100,   # 10x10
    'F01': 300,   # 20x15
}


# ──────────────────────────────────────────────────────
#  PLANT SEED PRICES  (name → seed_price in ฿)
# ──────────────────────────────────────────────────────
PLANT_SEED_PRICES = {
    # โตเร็ว / ผักใบ ≤45 วัน → ฿30
    'ผักบุ้งจีน':   Decimal('30'),
    'กวางตุ้ง':     Decimal('30'),
    'กะเพรา':       Decimal('30'),
    'โหระพา':       Decimal('30'),
    'ต้นหอม':       Decimal('35'),
    'ผักชี':        Decimal('35'),

    # ผักทั่วไป 45-70 วัน → ฿40-50
    'ผักกาดหอม':    Decimal('40'),
    'คะน้า':        Decimal('40'),
    'ทานตะวัน':     Decimal('40'),
    'แตงกวา':       Decimal('45'),
    'หัวผักกาด':    Decimal('45'),
    'ถั่วฝักยาว':   Decimal('45'),
    'กะหล่ำปลี':   Decimal('50'),
    'ข้าวโพด':      Decimal('50'),
    'ข้าวโพดหวาน':  Decimal('50'),

    # ผักระยะกลาง-ยาว 75-90 วัน → ฿55-70
    'แครอท':        Decimal('55'),
    'พริกขี้หนู':   Decimal('55'),
    'ฟักทอง':       Decimal('55'),
    'พริกหวาน':     Decimal('60'),
    'มะเขือเทศ':    Decimal('60'),
    'มะเขือม่วง':   Decimal('60'),
    'มะเขือเปราะ':  Decimal('60'),
    'แตงโม':        Decimal('65'),
    'ข้าวสาลี':     Decimal('60'),

    # ต้องดูแลนาน / ต้นทุนสูง → ฿80
    'มันฝรั่ง':     Decimal('80'),
    'บลูเบอร์รี่':  Decimal('80'),
    'ราสป์เบอร์รี่': Decimal('80'),

    # สตรอว์เบอร์รี — แพงที่สุด
    'สตรอว์เบอร์รี': Decimal('150'),
}


class Command(BaseCommand):
    help = 'อัปเดตราคาสินค้า, แปลง, และค่าเมล็ดพันธุ์ให้เป็นราคาตลาดไทยที่สมจริง'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== อัปเดตราคาสินค้า ==='))
        prod_ok = prod_skip = 0
        for product in Product.objects.all().order_by('id'):
            new_price = PRODUCT_PRICES.get(product.id)
            if new_price is None:
                self.stdout.write(self.style.WARNING(f'  ⚠ ไม่พบราคาสำหรับ product #{product.id} "{product.name}"'))
                prod_skip += 1
                continue
            old = product.price
            product.price = new_price
            product.save(update_fields=['price'])
            self.stdout.write(f'  ✓ #{product.id} {product.name}: ฿{old} → ฿{new_price}')
            prod_ok += 1

        self.stdout.write(self.style.MIGRATE_HEADING('\n=== อัปเดตราคาแปลง ==='))
        for plot in Plot.objects.all().order_by('code'):
            new_ppd = PLOT_PRICES.get(plot.code)
            if new_ppd is None:
                self.stdout.write(self.style.WARNING(f'  ⚠ ไม่พบราคาสำหรับแปลง {plot.code}'))
                continue
            old = plot.price_per_day
            plot.price_per_day = new_ppd
            plot.save(update_fields=['price_per_day'])
            sqm = PLOT_AREA.get(plot.code, '?')
            monthly = new_ppd * 30
            self.stdout.write(f'  ✓ {plot.code} {plot.name} ({sqm} ตร.ม.): ฿{old}/วัน → ฿{new_ppd}/วัน (฿{monthly}/เดือน)')

        self.stdout.write(self.style.MIGRATE_HEADING('\n=== อัปเดต seed_price พืช ==='))
        seed_ok = seed_skip = 0
        for plant in Plant.objects.all().order_by('name'):
            new_sp = PLANT_SEED_PRICES.get(plant.name)
            if new_sp is None:
                self.stdout.write(self.style.WARNING(f'  ⚠ ไม่พบ seed_price สำหรับ "{plant.name}" — ใช้ค่าตั้งต้น ฿50'))
                seed_skip += 1
                continue
            old = plant.seed_price
            plant.seed_price = new_sp
            plant.save(update_fields=['seed_price'])
            self.stdout.write(f'  ✓ {plant.name} ({plant.grow_days} วัน): ฿{old} → ฿{new_sp}')
            seed_ok += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nเสร็จสิ้น: สินค้า {prod_ok} รายการ, แปลง {len(PLOT_PRICES)} แปลง, '
            f'พืช {seed_ok} ชนิด (ข้ามไป {seed_skip})'
        ))
