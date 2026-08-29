from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0016_productreview'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(blank=True, max_length=20, verbose_name='เบอร์โทร')),
                ('default_address', models.TextField(blank=True, verbose_name='ที่อยู่เริ่มต้น')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='userprofile',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='ผู้ใช้',
                )),
            ],
            options={
                'verbose_name': 'ข้อมูลสมาชิก',
                'verbose_name_plural': 'ข้อมูลสมาชิก',
            },
        ),
    ]
