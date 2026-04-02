from django.contrib import admin
from .models import Product, VeggiePlotBooking, Order

# นำตารางไปลงทะเบียนให้แสดงในหน้าแอดมิน
admin.site.register(Product)
admin.site.register(VeggiePlotBooking)
admin.site.register(Order)