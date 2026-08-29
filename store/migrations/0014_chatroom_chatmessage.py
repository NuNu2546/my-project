import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0013_order_staff_fields'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatRoom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(blank=True, db_index=True, max_length=40)),
                ('customer_name', models.CharField(blank=True, max_length=100, verbose_name='ชื่อลูกค้า')),
                ('phone', models.CharField(blank=True, max_length=20, verbose_name='เบอร์โทร')),
                ('is_closed', models.BooleanField(default=False, verbose_name='ปิดเคสแล้ว')),
                ('unread_by_staff', models.PositiveIntegerField(default=0)),
                ('unread_by_customer', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chat_rooms', to=settings.AUTH_USER_MODEL)),
                ('related_order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chat_rooms', to='store.order', verbose_name='ออเดอร์ที่เกี่ยวข้อง')),
            ],
            options={
                'verbose_name': 'ห้องแชท',
                'verbose_name_plural': 'ห้องแชท',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sender_type', models.CharField(choices=[('customer', 'ลูกค้า'), ('staff', 'เจ้าหน้าที่')], max_length=10)),
                ('sender_name', models.CharField(blank=True, max_length=100)),
                ('message', models.CharField(max_length=500)),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='store.chatroom')),
            ],
            options={
                'verbose_name': 'ข้อความแชท',
                'verbose_name_plural': 'ข้อความแชท',
                'ordering': ['created_at'],
            },
        ),
    ]
