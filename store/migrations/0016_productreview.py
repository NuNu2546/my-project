from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0015_coins_system'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_name', models.CharField(max_length=100, verbose_name='ชื่อผู้รีวิว')),
                ('rating', models.PositiveSmallIntegerField(verbose_name='คะแนน (1-5)')),
                ('comment', models.TextField(blank=True, max_length=1000, verbose_name='ความคิดเห็น')),
                ('is_visible', models.BooleanField(default=True, verbose_name='แสดงรีวิว')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='store.order', verbose_name='ออเดอร์')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='store.product', verbose_name='สินค้า')),
            ],
            options={
                'verbose_name': 'รีวิวสินค้า',
                'verbose_name_plural': 'รีวิวสินค้า',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='productreview',
            unique_together={('product', 'order')},
        ),
    ]
