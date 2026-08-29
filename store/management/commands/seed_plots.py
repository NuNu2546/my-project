from django.core.management.base import BaseCommand
from store.models import Plot, Plant


class Command(BaseCommand):
    help = 'Seed 6 plots and 12 plants from the original hardcoded data'

    def handle(self, *args, **options):
        plots = [
            dict(code='A12', name='มุมแดดสบาย', size='10x10m', sun_type='แดดจัดเต็มวัน',
                 price_per_day=5, image='images/Veggie_Plots/Veggie_Plots_A12.png',
                 description='แปลงมุมที่โดนแดดเต็มวัน เหมาะสำหรับผักและดอกไม้ที่ชอบแสงแดดจัด เช่น มะเขือเทศ พริก หรือดอกทานตะวัน ดินเป็นดินออร์แกนิกคุณภาพดี ช่วยให้ต้นไม้เจริญเติบโตอย่างแข็งแรง'),
            dict(code='B04', name='มุมน่ารัก', size='8x12m', sun_type='ดินปลอดสาร',
                 price_per_day=6, image='images/Veggie_Plots/Veggie_Plots_B04.png',
                 description='แปลงขนาดเล็ก อบอุ่น เหมาะสำหรับปลูกผักสวนครัวหรือสมุนไพร'),
            dict(code='C21', name='เนินดอกไม้', size='5x5m', sun_type='ร่มบางเวลา',
                 price_per_day=3, image='images/Veggie_Plots/Veggie_Plots_C21.png',
                 description='แปลงบนเนินเล็ก ดอกไม้บานสะพรั่ง เหมาะสำหรับทำสวนประดับ'),
            dict(code='D08', name='ทุ่งเล็ก', size='12x8m', sun_type='แดดจัดเต็มวัน',
                 price_per_day=7, image='images/Veggie_Plots/Veggie_Plots_D08.png',
                 description='แปลงพื้นที่เปิด โล่งโปร่งสบาย ปลูกผักได้หลากหลายชนิด'),
            dict(code='E15', name='แปลงสดชื่น', size='10x10m', sun_type='ใกล้แหล่งน้ำ',
                 price_per_day=5, image='images/Veggie_Plots/Veggie_Plots_E15.png',
                 description='แปลงที่ดูแลง่าย ใกล้แหล่งน้ำ เหมาะสำหรับผู้เริ่มต้น'),
            dict(code='F01', name='โอเอซิสเขียว', size='20x15m', sun_type='ร่มรื่น',
                 price_per_day=9, image='images/Veggie_Plots/Veggie_Plots_F01.png',
                 description='แปลงขนาดใหญ่ ร่มรื่น เหมาะสำหรับกลุ่มเพื่อนหรือครอบครัว'),
        ]
        for p in plots:
            obj, created = Plot.objects.update_or_create(code=p['code'], defaults=p)
            status = 'created' if created else 'updated'
            self.stdout.write(f'  Plot {p["code"]} — {status}')

        plants = [
            dict(name='มะเขือเทศ',    grow_days=75,  image='images/Veggie_Plots/plot_detail/Tomato.png'),
            dict(name='แครอท',         grow_days=75,  image='images/Veggie_Plots/plot_detail/Carrot.png'),
            dict(name='ผักกาดหอม',     grow_days=37,  image='images/Veggie_Plots/plot_detail/Lettuce.png'),
            dict(name='พริกหวาน',      grow_days=75,  image='images/Veggie_Plots/plot_detail/Bell_pepper.png'),
            dict(name='แตงกวา',        grow_days=52,  image='images/Veggie_Plots/plot_detail/Cucumber.png'),
            dict(name='ข้าวโพด',       grow_days=75,  image='images/Veggie_Plots/plot_detail/Corn.png'),
            dict(name='ทานตะวัน',      grow_days=75,  image='images/Veggie_Plots/plot_detail/Sunflower.png'),
            dict(name='มันฝรั่ง',      grow_days=105, image='images/Veggie_Plots/plot_detail/Potato.png'),
            dict(name='โหระพาไทย',    grow_days=24,  image='images/Veggie_Plots/plot_detail/Thai_basil.png'),
            dict(name='สตรอว์เบอร์รี', grow_days=105, image='images/Veggie_Plots/plot_detail/Strawberry.png'),
            dict(name='บลูเบอร์รี่',   grow_days=912, image='images/Veggie_Plots/plot_detail/Blueberry.png'),
            dict(name='ราสป์เบอร์รี่', grow_days=547, image='images/Veggie_Plots/plot_detail/Raspberry.png'),
        ]
        for p in plants:
            obj, created = Plant.objects.update_or_create(name=p['name'], defaults=p)
            status = 'created' if created else 'updated'
            self.stdout.write(f'  Plant {p["name"]} — {status}')

        self.stdout.write(self.style.SUCCESS('Seed complete: 6 plots, 12 plants'))
