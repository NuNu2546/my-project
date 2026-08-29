from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0009_remove_game'),
    ]

    operations = [
        # Extend status max_length to accommodate 'awaiting_shipping_payment' (26 chars)
        migrations.AlterField(
            model_name='plotbooking',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending',                   'รอชำระเงิน'),
                    ('paid',                      'ยืนยันการจอง'),
                    ('growing',                   'กำลังปลูก'),
                    ('ready_to_harvest',          'พร้อมเก็บเกี่ยว'),
                    ('harvested',                 'เก็บเกี่ยวแล้ว รอเลือกวิธีรับ'),
                    ('awaiting_shipping_payment', 'รอชำระค่าจัดส่ง'),
                    ('preparing',                 'กำลังแพ็คผลผลิต'),
                    ('shipped',                   'จัดส่งแล้ว'),
                    ('delivered',                 'ได้รับผลผลิตแล้ว'),
                    ('ready_for_pickup',          'รอรับที่สวน'),
                    ('completed',                 'เสร็จสิ้น'),
                    ('cancelled',                 'ยกเลิก'),
                    ('expired',                   'หมดอายุ'),
                ],
                default='pending', max_length=30, verbose_name='สถานะ',
            ),
        ),
        migrations.AlterField(
            model_name='plotbookingstatushistory',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending',                   'รอชำระเงิน'),
                    ('paid',                      'ยืนยันการจอง'),
                    ('growing',                   'กำลังปลูก'),
                    ('ready_to_harvest',          'พร้อมเก็บเกี่ยว'),
                    ('harvested',                 'เก็บเกี่ยวแล้ว รอเลือกวิธีรับ'),
                    ('awaiting_shipping_payment', 'รอชำระค่าจัดส่ง'),
                    ('preparing',                 'กำลังแพ็คผลผลิต'),
                    ('shipped',                   'จัดส่งแล้ว'),
                    ('delivered',                 'ได้รับผลผลิตแล้ว'),
                    ('ready_for_pickup',          'รอรับที่สวน'),
                    ('completed',                 'เสร็จสิ้น'),
                    ('cancelled',                 'ยกเลิก'),
                    ('expired',                   'หมดอายุ'),
                ],
                max_length=30,
            ),
        ),
        # New fields on PlotBooking
        migrations.AddField(
            model_name='plotbooking',
            name='delivery_method',
            field=models.CharField(
                blank=True,
                choices=[('pickup', 'มารับเองที่สวน'), ('shipping', 'จัดส่งถึงบ้าน')],
                max_length=10,
                verbose_name='วิธีรับผลผลิต',
            ),
        ),
        migrations.AddField(
            model_name='plotbooking',
            name='shipping_address',
            field=models.TextField(blank=True, verbose_name='ที่อยู่จัดส่ง'),
        ),
        migrations.AddField(
            model_name='plotbooking',
            name='shipping_fee',
            field=models.DecimalField(decimal_places=2, default=50, max_digits=8, verbose_name='ค่าจัดส่ง (฿)'),
        ),
        migrations.AddField(
            model_name='plotbooking',
            name='shipping_charge_id',
            field=models.CharField(blank=True, max_length=100, verbose_name='Charge ID ค่าส่ง'),
        ),
        migrations.AddField(
            model_name='plotbooking',
            name='tracking_number',
            field=models.CharField(blank=True, max_length=100, verbose_name='เลขพัสดุ'),
        ),
        migrations.AddField(
            model_name='plotbooking',
            name='shipping_carrier',
            field=models.CharField(
                blank=True,
                choices=[
                    ('kerry', 'Kerry Express'), ('flash', 'Flash Express'),
                    ('jnt', 'J&T Express'), ('thailand_post', 'ไปรษณีย์ไทย'), ('other', 'อื่นๆ'),
                ],
                max_length=20,
                verbose_name='ขนส่ง',
            ),
        ),
        migrations.AddField(
            model_name='plotbooking',
            name='harvest_weight',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=7,
                null=True, verbose_name='น้ำหนักผลผลิต (กก.)',
            ),
        ),
        migrations.AddField(
            model_name='plotbooking',
            name='pickup_deadline',
            field=models.DateField(blank=True, null=True, verbose_name='วันสุดท้ายที่ต้องมารับ'),
        ),
    ]
