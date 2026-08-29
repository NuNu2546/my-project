# DEMO_CHECKLIST.md
# Greenhearth — Live Presentation Prep

---

## ✅ ก่อน Demo (30 นาทีก่อนขึ้นเวที)

### 1. Seed ข้อมูล demo ใหม่
```bash
python manage.py seed_demo --reset
```
สร้าง: 6 orders ทุกสถานะ · 8 bookings ทุกสถานะ · รีวิว · แชท 2 ห้อง · Donation bar 32%

### 2. เปิด server
```bash
python manage.py runserver 0.0.0.0:8000
```

### 3. (ถ้าต้องการ demo การจ่ายเงินส��) เปิด ngrok
```bash
ngrok http 8000
```
จด HTTPS URL (เช่น `https://abc123.ngrok.io`)

อัปเดต `settings.py`:
```python
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'abc123.ngrok.io']
CSRF_TRUSTED_ORIGINS = ['https://abc123.ngrok.io']
```

อัปเดต Opn dashboard → Webhook URL:
```
https://abc123.ngrok.io/webhook/opn/
```

### 4. ตรวจสอบหน้าหลัก
- [ ] http://localhost:8000/ — Home + donation bar ขย��บ
- [ ] http://localhost:8000/shop/ — สินค้าแสดงครบ
- [ ] http://localhost:8000/veggie-plots/ — แปลงผัก 6 แปลง
- [ ] http://localhost:8000/staff/ — Staff panel เข้าได้

---

## 🎬 แนะนำลำดับการ Demo

### 1. หน้า Home
- Donation bar (3,200/10,000 coins = 32%)
- Product slider
- Veggie plot rental section

### 2. Shop �� Cart → Payment
- เลือกสินค้า → ใส่ตะกร้า → checkout
- กรอกชื่อ-ที่อยู่ → กด "สั่งซื้อ" → QR PromptPay ขึ้น
- **ถ้าออฟไลน์:** เปิด terminal ���ีกอ��น → `python manage.py mark_order_paid <id>`

### 3. Staff Panel → Orders
- แสดง orders ทุกสถานะ (pending / paid / shipped / ฯลฯ)
- เปิด order ที่ถูก seed → แสดงรายละเอียด

### 4. Staff Panel → Veggie Plot Bookings
- Bookings ครบทุกสถานะรวมถึง harvested/shipped

### 5. Staff Chat
- แสดง 2 ห้องแ���ท: ��ีจุดแดง unread (2 + 1)
- ตอบข้อความสดใน demo

### 6. Veggie Plots → ทำ booking ใหม่
- เลือกแปลง → เลือกพืช → เลือกวันเร��่มปลูก → ���่ายเงิน

### 7. My Orders / Track
- Login ด้วย demo@digitalgarden.th / Demo1234!
- แสดง order history + ติดตามพัสดุ

### 8. Coins
- ดู coin wallet ห���ัง login
- บริจาค coins ��� donation bar ขยับ

---

## 🔌 ช���ระเงินออฟไลน์ (ไม่มี internet / Opn ล่ม)

```bash
# Order (���ั่งซื้อสินค้า)
python manage.py mark_order_paid <order_id>

# Booking (จองแปลง)
python manage.py mark_order_paid <booking_id> --booking

# ค���าจัดส่งหลัง��ก็บเกี่ยว
python manage.py mark_order_paid <booking_id> --shipping
```

ผล: สถานะอัปเดต · สต๊อกหัก · Coins เพิ่ม · History บันทึก (เหมือน webhook จริง)

---

## 🆘 Troubleshooting

| ปัญหา | วิธีแก้ |
|-------|---------|
| หน้าค้างตอนจ่ายเงิน | Opn ไม่ตอบสนอง ���ช้ `mark_order_paid` แทน |
| ฟอนต์ไม่ใช่ Sarabun | ปกติถ้าออฟไลน์ — fallback font ทำงานต่อได้ |
| CSRF verification failed | เพิ่ม ngrok URL ใน `CSRF_TRUSTED_ORIGINS` |
| 500 error | ���ู terminal ที่รัน `runserver` |
| ข้อมูล demo หาย | `python manage.py seed_demo --reset` |
| Staff login ไม่ได้ | `python manage.py createsuperuser` |
| Port 8000 ถูกใช้ | `python manage.py runserver 8080` แล้วแก้ ngrok |

---

## 🔐 Credentials

| Role | Email / Username | Password |
|------|-----------------|---------|
| Customer (demo) | demo@digitalgarden.th | Demo1234! |
| Staff / Admin | สร้างด้วย `createsuperuser` | ตามที่กำหนด |

---

## 📦 Demo Data Summary

| ประเภท | จำนวน | รายละเอียด |
|--------|-------|-----------|
| Orders | 6 | pending, paid, shipped, in_transit, delivered, cancelled |
| Bookings | 8 | pending, growing, ready_to_harvest, harvested(pickup), ready_for_pickup, awaiting_shipping_payment, shipped, completed |
| Reviews | 2–4 | สำหรับ delivered orders |
| Chat rooms | 2 | unread 2 + 1 |
| Donation | 3,200 coins | 32% of goal (10,000) |

---

## ⚡ Quick Commands

```bash
# รัน server
python manage.py runserver 0.0.0.0:8000

# seed ใหม่ทั้งหมด
python manage.py seed_demo --reset

# จ่ายออเดอร์ออฟไลน์
python manage.py mark_order_paid <id>
python manage.py mark_order_paid <id> --booking
python manage.py mark_order_paid <id> --shipping

# ดู order IDs ที่ pending
python manage.py shell -c "from store.models import Order; [print(o.id, o.customer_name, o.status) for o in Order.objects.all()[:10]]"
```
