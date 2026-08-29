from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0014_chatroom_chatmessage'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # session_key on Order
        migrations.AddField(
            model_name='order',
            name='session_key',
            field=models.CharField(blank=True, db_index=True, max_length=40),
        ),
        # session_key on PlotBooking
        migrations.AddField(
            model_name='plotbooking',
            name='session_key',
            field=models.CharField(blank=True, db_index=True, max_length=40),
        ),
        # CoinWallet
        migrations.CreateModel(
            name='CoinWallet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(db_index=True, max_length=40, unique=True)),
                ('balance', models.IntegerField(default=0)),
                ('total_earned', models.IntegerField(default=0)),
                ('total_donated', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='coin_wallet', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'กระเป๋า Coins',
                'verbose_name_plural': 'กระเป๋า Coins',
            },
        ),
        # CoinTransaction
        migrations.CreateModel(
            name='CoinTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField()),
                ('reason', models.CharField(choices=[('purchase', 'ได้จากการสั่งซื้อ'), ('donate', 'บริจาคปลูกต้นไม้'), ('adjust', 'ปรับโดยแอดมิน')], max_length=20)),
                ('note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('wallet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='store.coinwallet')),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='coin_transactions', to='store.order')),
                ('booking', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='coin_transactions', to='store.plotbooking')),
            ],
            options={
                'verbose_name': 'รายการ Coins',
                'verbose_name_plural': 'รายการ Coins',
                'ordering': ['-created_at'],
            },
        ),
        # TreeDonation
        migrations.CreateModel(
            name='TreeDonation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_coins_donated', models.IntegerField(default=0)),
                ('goal', models.IntegerField(default=10000)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'ยอดบริจาคปลูกต้นไม้',
            },
        ),
    ]
