import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0011_product_stock_slug'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StockMovement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('change', models.IntegerField(verbose_name='จำนวนเปลี่ยนแปลง (+/-)')),
                ('reason', models.CharField(
                    choices=[
                        ('sale',    'ขาย'),
                        ('return',  'คืนสต๊อก'),
                        ('restock', 'เติมสต๊อก'),
                        ('adjust',  'ปรับยอด'),
                    ],
                    max_length=20,
                    verbose_name='เหตุผล',
                )),
                ('note', models.TextField(blank=True, verbose_name='หมายเหตุ')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='store.order',
                    verbose_name='ออเดอร์',
                )),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='movements',
                    to='store.product',
                    verbose_name='สินค้า',
                )),
                ('staff', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='สต๊าฟ',
                )),
            ],
            options={
                'verbose_name': 'ความเคลื่อนไหวสต๊อก',
                'verbose_name_plural': 'ความเคลื่อนไหวสต๊อก',
                'ordering': ['-created_at'],
            },
        ),
    ]
