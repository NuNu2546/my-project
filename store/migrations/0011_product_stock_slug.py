from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0010_plotbooking_harvest_delivery'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='slug',
            field=models.SlugField(blank=True, max_length=220, verbose_name='Slug'),
        ),
        migrations.AddField(
            model_name='product',
            name='stock_quantity',
            field=models.PositiveIntegerField(default=0, verbose_name='สต๊อก'),
        ),
        migrations.AddField(
            model_name='product',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='เปิดขาย'),
        ),
        migrations.AddField(
            model_name='product',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='product',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.CharField(
                blank=True,
                choices=[
                    ('tools',   'เครื่องมือทำสวน'),
                    ('seeds',   'เมล็ดพันธุ์'),
                    ('natural', 'ผลิตภัณฑ์ธรรมชาติ'),
                    ('aroma',   'อโรมาเธอราพี'),
                    ('flowers', 'ดอกไม้แห้ง'),
                ],
                max_length=20,
                verbose_name='หมวดหมู่',
            ),
        ),
        migrations.AlterField(
            model_name='product',
            name='image',
            field=models.CharField(default='default.png', max_length=200, verbose_name='รูปภาพ'),
        ),
    ]
