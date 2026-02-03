/* ==========================================================================
   ส่วนที่ 1: GLOBAL VARIABLES
   ตัวแปรที่ใช้ร่วมกัน (สำคัญมาก: ห้ามลบ)
   ========================================================================== */
let currentProduct = {};


/* ==========================================================================
   ส่วนที่ 2: DOM CONTENT LOADED
   ทำงานเมื่อโหลดหน้าเว็บเสร็จ (Chat, Profile, Badge)
   ========================================================================== */
document.addEventListener('DOMContentLoaded', () => {
    // อัปเดตตัวเลขตะกร้าทันทีที่เข้าเว็บ
    updateCartBadge();

    // --- ส่วนของ Chat และ Profile Menu (ตามโค้ดเดิมของคุณ) ---
    // (ใส่โค้ด Chat / Profile ตรงนี้ได้ หรือถ้ามีอยู่แล้วก็คงไว้)
});


/* ==========================================================================
   ส่วนที่ 3: GLOBAL FUNCTIONS (เรียกใช้จาก HTML onclick)
   ต้องอยู่นอก document.addEventListener ถึงจะทำงานได้
   ========================================================================== */

/* --- 3.1 เปิด Modal (Quick View) --- */
function openQuickView(event, id, name, price, imageSrc) {
    event.preventDefault(); // ป้องกันลิงก์ทำงานซ้อน
    
    const modal = document.getElementById('quickViewModal');
    if (!modal) return;

    // 1. อัปเดตข้อมูลหน้าเว็บ (UI)
    const modalImg = document.getElementById('modalImg');
    if (modalImg) modalImg.src = imageSrc;

    const modalTitle = document.getElementById('modalTitle');
    if (modalTitle) modalTitle.innerText = name;

    const modalPrice = document.getElementById('modalPrice');
    if (modalPrice) modalPrice.innerText = '$' + price;

    const modalQty = document.getElementById('modalQty');
    if (modalQty) modalQty.value = 1;

    // 2. อัปเดตตัวแปร Global (เพื่อให้ confirmAddToCart รู้ว่าสินค้าคืออะไร)
    currentProduct = {
        id: id,
        name: name,
        price: parseFloat(price),
        image: imageSrc,
        qty: 1
    };

    // 3. แสดง Modal
    modal.style.display = 'flex';
}

/* --- 3.2 ปิด Modal --- */
function closeModal() {
    const modal = document.getElementById('quickViewModal');
    if (modal) modal.style.display = 'none';
}

/* --- 3.3 เพิ่ม/ลด จำนวนสินค้าใน Modal --- */
function updateModalQty(change) {
    const qtyInput = document.getElementById('modalQty');
    if (!qtyInput) return;

    let newQty = parseInt(qtyInput.value) + change;
    if (newQty < 1) newQty = 1; // ห้ามต่ำกว่า 1

    qtyInput.value = newQty;
    currentProduct.qty = newQty; // อัปเดตตัวแปร Global ด้วย
}

/* --- 3.4 Animation รูปบินเข้าตะกร้า --- */
/* --- 3.4 Animation รูปบินเข้าตะกร้า (ฉบับ GPU Smooth) --- */
function animateFlyToCart(sourceElement, callback) {
    const cartIcon = document.querySelector('.cart-btn-wrapper');
    if (!cartIcon || !sourceElement) {
        callback(); 
        return;
    }

    // 1. Clone รูป
    const flyImg = sourceElement.cloneNode();
    flyImg.classList.add('fly-item');
    
    // 2. หาตำแหน่งเริ่มต้น และ ปลายทาง
    const startRect = sourceElement.getBoundingClientRect();
    const endRect = cartIcon.getBoundingClientRect();

    // 3. เซตตำแหน่งเริ่มต้น (ใช้ top/left แค่ครั้งเดียวตอนเริ่ม)
    flyImg.style.position = "fixed"; 
    flyImg.style.top = startRect.top + "px";
    flyImg.style.left = startRect.left + "px";
    flyImg.style.width = startRect.width + "px";
    flyImg.style.height = startRect.height + "px";
    flyImg.style.margin = "0"; // กันค่า default
    
    document.body.appendChild(flyImg);

    // 4. คำนวณระยะทางที่จะต้องเลื่อน (Delta X, Y)
    // เป้าหมายคือ กึ่งกลางตะกร้า - กึ่งกลางรูปเริ่ม
    const destX = (endRect.left + endRect.width / 2) - (startRect.left + startRect.width / 2);
    const destY = (endRect.top + endRect.height / 2) - (startRect.top + startRect.height / 2);

    // คำนวณอัตราส่วนการย่อรูป (Scaling) เช่น ย่อเหลือ 50px
    const scaleRatio = 50 / startRect.width; 

    // 5. เริ่ม Animation (ใช้ Transform ล้วนๆ เพื่อความลื่น)
    requestAnimationFrame(() => {
        // ต้อง Delay นิดนึงเพื่อให้ Browser รู้จัก element ก่อนเริ่มขยับ
        setTimeout(() => {
            flyImg.style.transform = `translate(${destX}px, ${destY}px) scale(${scaleRatio})`;
            flyImg.style.opacity = "0.7"; 
        }, 10);
    });

    // 6. จบงาน
    setTimeout(() => {
        flyImg.remove();
        callback(); 
    }, 800); // เวลาต้องตรงกับ CSS transition
}

/* --- 3.5 ยืนยันการเพิ่มลงตะกร้า (Main Logic) --- */
function confirmAddToCart() {
    const modalImg = document.getElementById('modalImg');

    // เรียก Animation -> เมื่อเสร็จแล้วค่อยบันทึก
    animateFlyToCart(modalImg, () => {
        
        // 1. ดึงตะกร้าเดิมจาก LocalStorage
        let cart = JSON.parse(localStorage.getItem('cart')) || [];
        
        // 2. เช็คว่ามีสินค้านี้อยู่แล้วไหม
        const existingItem = cart.find(item => item.id === currentProduct.id);

        if (existingItem) {
            existingItem.qty += currentProduct.qty;
        } else {
            cart.push(currentProduct);
        }

        // 3. บันทึกกลับลง LocalStorage
        localStorage.setItem('cart', JSON.stringify(cart));

        // 4. อัปเดตตัวเลขแจ้งเตือน
        updateCartBadge();
        
        // 5. เอฟเฟกต์เด้งดึ๋งที่ปุ่มตะกร้า
        const badge = document.getElementById('cartBadge');
        if(badge) {
            badge.classList.remove('bump'); // รีเซ็ตคลาสก่อน
            void badge.offsetWidth; // บังคับ browser วาดใหม่ (Trick)
            badge.classList.add('bump');
        }
    });

    // ปิด Modal ทันทีเพื่อให้เห็น Animation ชัดๆ
    closeModal();
}

/* --- 3.6 อัปเดตตัวเลข Badge --- */
function updateCartBadge() {
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
    const totalQty = cart.reduce((sum, item) => sum + item.qty, 0);
    const badge = document.getElementById('cartBadge');

    if (badge) {
        badge.innerText = totalQty;
        if (totalQty > 0) {
            badge.classList.add('show');
        } else {
            badge.classList.remove('show');
        }
    }
}

// ปิด Modal เมื่อคลิกพื้นที่ว่างข้างนอก
window.onclick = function(event) {
    const modal = document.getElementById('quickViewModal');
    if (event.target == modal) {
        closeModal();
    }
}