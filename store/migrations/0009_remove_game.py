from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0008_garden_game'),
    ]

    operations = [
        # Remove FK-dependent models first
        migrations.DeleteModel(name='CoinTransaction'),
        migrations.DeleteModel(name='DiscountCoupon'),
        migrations.DeleteModel(name='GardenGame'),
        migrations.DeleteModel(name='PlayerWallet'),
        # Remove coupon_code field from Order
        migrations.RemoveField(model_name='order', name='coupon_code'),
    ]
