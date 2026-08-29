# 🌱 Greenhearth — Digital Garden

แพลตฟอร์ม e-commerce และระบบเช่าแปลงผักออนไลน์ สำหรับผู้ที่รักการปลูกพืชและต้องการมีส่วนร่วมในการดูแลสิ่งแวดล้อม

---

## ✨ ฟีเจอร์ทั้งหมด

### ฝั่งลูกค้า (Customer)
- **ร้านค้าออนไลน์** — สินค้า 42 รายการใน 5 หมวด: อุปกรณ์การเกษตร, เมล็ดพันธุ์, ปุ๋ยและดินปลูก, สมุนไพร/อโรมา, ไม้ดอก
- **ตะกร้าสินค้า** — เพิ่ม/ลดสินค้า จัดการปริมาณ พร้อม session-based สำหรับลูกค้าที่ไม่ได้ login
- **ชำระเงิน PromptPay QR** — ผ่าน Opn (Omise) Payment Gateway นับถอยหลัง 10 นาที ยืนยันอัตโนมัติผ่าน Webhook
- **ระบบเช่าแปลงผัก** — เลือกแปลง 6 แปลง เลือกพืช 12 ชนิด ระบบคำนวณวันเก็บเกี่ยวและราคาให้อัตโนมัติ
- **การรับผลผลิต** — เลือกระหว่างมารับที่ฟาร์ม (Pickup) หรือจัดส่งถึงบ้าน (Shipping) พร้อมชำระค่าส่งแยก
- **ติดตามออเดอร์** — Timeline สถานะแบบ step-by-step พร้อมเลขพัสดุ
- **ติดตามการจองแปลง** — ดูสถานะการปลูกตั้งแต่ปลูก → เก็บเกี่ยว → จัดส่ง
- **ระบบ Coins** — ทุก ฿50 ที่ซื้อ = 1 Coin · นำ Coins ไปบริจาคปลูกต้นไม้จริง
- **Donation Bar** — แสดงความคืบหน้าการบริจาคของชุมชน เป้าหมาย 10,000 Coins
- **แชทสด** — ส่งข้อความถึง Staff ได้โดยตรง ไม่ต้อง Login
- **รีวิวสินค้า** — รีวิวพร้อมคะแนนดาวหลังรับสินค้าแล้ว
- **ระบบสมาชิก** — สมัคร Login ดูประวัติคำสั่งซื้อ และบันทึกที่อยู่

### ฝั่งผู้ดูแล (Staff)
- **Dashboard** — สรุปออเดอร์วันนี้ รายได้ และสถิติภาพรวม
- **จัดการออเดอร์** — ดูทุกออเดอร์ กรองตามสถานะ อัปเดตสถานะ ใส่เลขพัสดุ พิมพ์ใบจัดของ
- **จัดการแปลงผัก** — ติดตามการเจริญเติบโต อัปเดตสถานะทีละขั้น บันทึกน้ำหนักผลผลิต
- **จัดการสต๊อก** — ดู Movement log การเพิ่ม/ลดสต๊อก ระบบหักสต๊อกอัตโนมัติเมื่อชำระเงิน
- **แชทกับลูกค้า** — รับและตอบข้อความ พร้อมแจ้งเตือนข้อความที่ยังไม่อ่าน
- **ตรวจสอบรีวิว** — อนุมัติหรือซ่อนรีวิวสินค้า
- **Seed ข้อมูล Demo** — `python manage.py seed_demo --reset`

---

## 🛠 Tech Stack

| ส่วน | เทคโนโลยี |
|------|-----------|
| Backend | Python 3.14 · Django 6.0.1 |
| Database | SQLite (dev) |
| Static Files | WhiteNoise 6.12 |
| Payment | Opn/Omise · PromptPay QR · Webhook |
| Frontend | Vanilla HTML/CSS/JavaScript |
| Env Management | python-dotenv |

---

## 🚀 วิธีติดตั้งและรันโปรเจกต์

### 1. Clone repository

```bash
git clone https://github.com/<your-username>/greenhearth.git
cd greenhearth
```

### 2. สร้าง Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. ติดตั้ง dependencies

```bash
pip install -r requirements.txt
```

### 4. ตั้งค่า Environment Variables

```bash
cp .env.example .env
```

เปิดไฟล์ `.env` แล้วใส่ค่าจริง:

```env
DJANGO_SECRET_KEY=your-secret-key-here
OMISE_SECRET_KEY=skey_test_xxxxxxxxxxxxxxxx
OMISE_PUBLIC_KEY=pkey_test_xxxxxxxxxxxxxxxx
NGROK_URL=                          # ใส่ถ้าจะทดสอบ webhook
```

สร้าง Django Secret Key ใหม่:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Migrate ฐานข้อมูล

```bash
python manage.py migrate
```

### 6. สร้าง Superuser (Staff)

```bash
python manage.py createsuperuser
```

### 7. Seed ข้อมูลสินค้าและแปลงผัก

```bash
python manage.py seed_products
python manage.py seed_plots
python manage.py set_thai_prices   # ตั้งราคาเป็นบาท
```

### 8. รัน Development Server

```bash
python manage.py runserver
```

เปิด http://localhost:8000 ในเบราว์เซอร์

---

## 🔗 การทดสอบ Webhook (PromptPay)

Opn Payment Webhook ต้องการ URL สาธารณะ — ใช้ **ngrok** ในขณะ development:

```bash
# ติดตั้ง ngrok จาก https://ngrok.com
ngrok http 8000
```

1. คัดลอก HTTPS URL ที่ได้ (เช่น `https://abc123.ngrok-free.app`)
2. ใส่ hostname (ไม่มี `https://`) ในไฟล์ `.env`:
   ```
   NGROK_URL=abc123.ngrok-free.app
   ```
3. รัน server ใหม่เพื่อให้ settings โหลดค่า
4. ไปที่ [Opn Dashboard](https://dashboard.omise.co/) → Settings → Webhooks
5. ตั้ง Webhook URL เป็น `https://abc123.ngrok-free.app/webhook/opn/`

> **Demo ออฟไลน์:** ถ้าไม่มี internet หรือ Opn ไม่ตอบสนอง ใช้คำสั่งนี้แทน:
> ```bash
> python manage.py mark_order_paid <order_id>
> python manage.py mark_order_paid <booking_id> --booking
> ```

---

## ⚠️ หมายเหตุเกี่ยวกับ Assets

ไฟล์กราฟิกบางส่วนใน `static/images/game/` เป็น asset ที่ซื้อมาภายใต้เงื่อนไข license ที่ **ไม่อนุญาตให้แจกจ่ายต่อ** จึงไม่ได้รวมอยู่ใน repository นี้

หากต้องการใช้งานฟีเจอร์ที่เกี่ยวข้อง กรุณาติดต่อทีมพัฒนาเพื่อขอรับไฟล์แยกต่างหาก

---

## 👥 ทีมพัฒนา

| ชื่อ | บทบาท |
|------|-------|
| Kritsada Phothong | Lead Developer & System Architect |
| Wutthichai Chanthsom | Co-developer & Project Management |
| Supakorn Sooksabuy | System Analyst |
| Wichairat Matarat | Documentation |
| Pimchanok Tamboon | QA & Presentation |

---

## 📄 License

โปรเจกต์นี้พัฒนาเพื่อการศึกษา สงวนลิขสิทธิ์โดยทีมพัฒนา
