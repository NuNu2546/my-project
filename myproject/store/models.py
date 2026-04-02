from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="ชื่อสินค้า")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ราคา")
    
    # เก็บชื่อไฟล์ เช่น "pot.png"
    image = models.CharField(max_length=200, default='default.png') 
    
    # ลบบรรทัด description = models.TextField() อันที่ซ้ำออก ให้เหลืออันเดียว
    description = models.TextField(verbose_name="รายละเอียด", blank=True)
    
    category = models.CharField(max_length=100, blank=True, verbose_name="หมวดหมู่") 

    def __str__(self):
        return self.name
    from django.db import models
from django.contrib.auth.models import User # ต้อง import User มาด้วยเพื่อผูกประวัติ

# --- (โมเดล Product เดิมของคุณ เอาไว้เหมือนเดิม) ---
class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="ชื่อสินค้า")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ราคา")
    image = models.CharField(max_length=200, default='default.png') 
    description = models.TextField(verbose_name="รายละเอียด", blank=True)
    category = models.CharField(max_length=100, blank=True, verbose_name="หมวดหมู่") 

    def __str__(self):
        return self.name

# ==========================================
# ส่วนที่เพิ่มใหม่: ตารางสำหรับเก็บประวัติต่างๆ
# ==========================================

# 1. ตารางเก็บประวัติการจองแปลงผัก
class VeggiePlotBooking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ผู้จอง")
    plot_name = models.CharField(max_length=100, verbose_name="ชื่อ/โซนแปลงผัก")
    status = models.CharField(max_length=50, default="กำลังปลูก (รอเก็บเกี่ยว)", verbose_name="สถานะ")
    booking_date = models.DateTimeField(auto_now_add=True, verbose_name="วันที่จอง")

    def __str__(self):
        return f"{self.user.username} - {self.plot_name}"

# 2. ตารางเก็บประวัติการสั่งซื้อสินค้า (บิลหลัก)
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ผู้สั่งซื้อ")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ราคารวม")
    status = models.CharField(max_length=50, default="รอดำเนินการ", verbose_name="สถานะการจัดส่ง")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่สั่งซื้อ")

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"