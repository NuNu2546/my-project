import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0012_stockmovement'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Order: is_viewed_by_staff + staff_note
        migrations.AddField(
            model_name='order',
            name='is_viewed_by_staff',
            field=models.BooleanField(default=False, verbose_name='เปิดดูแล้ว'),
        ),
        migrations.AddField(
            model_name='order',
            name='staff_note',
            field=models.TextField(blank=True, verbose_name='หมายเหตุภายใน (staff เท่านั้น)'),
        ),
        # OrderStatusHistory: staff FK
        migrations.AddField(
            model_name='orderstatushistory',
            name='staff',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
                verbose_name='staff ที่ดำเนินการ',
            ),
        ),
        # PlotBookingStatusHistory: staff FK
        migrations.AddField(
            model_name='plotbookingstatushistory',
            name='staff',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
                verbose_name='staff ที่ดำเนินการ',
            ),
        ),
    ]
