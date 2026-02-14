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