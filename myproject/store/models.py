from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="ชื่อสินค้า")
    description = models.TextField(verbose_name="รายละเอียด", blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ราคา")
    # ต้องลง Pillow ก่อนถึงจะใช้ ImageField ได้
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name="รูปภาพ")
    
    # เพิ่ม Category เผื่อไว้ใช้จัดหมวดหมู่ในอนาคต (เช่น ผัก, อุปกรณ์)
    category = models.CharField(max_length=100, blank=True, verbose_name="หมวดหมู่") 

    def __str__(self):
        return self.name