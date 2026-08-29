/* One-time cleanup: remove garden widget storage left from a previous version */
try { localStorage.removeItem('gdn-widget-v1'); } catch (_) {}

/* ==========================================================================
   ส่วนที่ 0: GLOBAL LOADING STATES — Progress bar · Loading button · Img lazy
   ========================================================================== */
(function () {
    'use strict';

    /* ── Progress bar (page navigation) ── */
    var bar = document.createElement('div');
    bar.id  = 'gh-progress';
    (document.body || document.documentElement).prepend(bar);

    var _pt, _pw = 0;

    function progStart() {
        _pw = 0;
        bar.style.width = '0';
        bar.classList.add('active');
        clearInterval(_pt);
        _pt = setInterval(function () {
            _pw += _pw < 20 ? 5 : _pw < 60 ? 2.5 : _pw < 85 ? 0.6 : 0;
            bar.style.width = _pw + '%';
        }, 80);
    }

    function progDone() {
        clearInterval(_pt);
        bar.style.width = '100%';
        setTimeout(function () {
            bar.classList.remove('active');
            bar.style.width = '0';
        }, 260);
    }

    /* Intercept internal link navigation */
    document.addEventListener('click', function (e) {
        var a = e.target.closest('a[href]');
        if (!a) return;
        var h = a.getAttribute('href');
        if (!h || h === '#' || h.startsWith('#') ||
            h.startsWith('javascript') || h.startsWith('mailto') ||
            h.startsWith('tel') || a.target === '_blank' || a.download) return;
        try {
            var u = new URL(h, location.href);
            if (u.origin !== location.origin) return;
        } catch (_) { return; }
        progStart();
    });

    /* Form submissions that cause page navigation */
    document.addEventListener('submit', function (e) {
        if (e.defaultPrevented) return;
        progStart();
    }, true);

    window.addEventListener('pageshow', progDone);

    /* ── Loading button — prevent double-submit on all <form> ── */
    document.addEventListener('submit', function (e) {
        if (e.defaultPrevented) return;
        var btn = e.target.querySelector('[type="submit"]:not(.no-loading)');
        if (!btn) return;
        /* Delay one tick so browser validation runs first */
        setTimeout(function () {
            if (e.defaultPrevented) return;
            btn.classList.add('btn-loading');
            btn.disabled = true;
            /* Safety re-enable after 12 s */
            setTimeout(function () {
                btn.classList.remove('btn-loading');
                btn.disabled = false;
            }, 12000);
        }, 0);
    });

    /* ── Image lazy-load skeleton ── */
    function applyImgSkeleton(img) {
        if (img.complete && img.naturalHeight > 0) return;
        img.classList.add('img-lazy');
        img.addEventListener('load',  function () {
            img.classList.remove('img-lazy');
            img.classList.add('img-loaded');
        }, { once: true });
        img.addEventListener('error', function () {
            img.classList.remove('img-lazy');
        }, { once: true });
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('img[loading="lazy"]').forEach(applyImgSkeleton);
    });

}());

/* ==========================================================================
   ส่วนที่ 1: GLOBAL VARIABLES
   ========================================================================== */
let currentProduct = {};


/* ==========================================================================
   ส่วนที่ 2: DOM CONTENT LOADED
   ========================================================================== */
document.addEventListener('DOMContentLoaded', () => {
    updateCartBadge();

    // --- Profile Menu ---
    const profileMenu = document.getElementById('profileMenu');
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.profile-container')) {
            if (profileMenu) profileMenu.classList.remove('active');
        }
    });

    // Chat widget is handled by _chat_widget.html inline script
});


/* ==========================================================================
   ส่วนที่ 3: GLOBAL FUNCTIONS (เรียกใช้จาก HTML onclick)
   ========================================================================== */

/* --- 3.0 Profile Menu Toggle --- */
function toggleProfileMenu() {
    const profileMenu = document.getElementById('profileMenu');
    if (profileMenu) profileMenu.classList.toggle('active');
}

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
    if (modalPrice) {
        const pNum = parseFloat(price);
        modalPrice.innerText = '฿' + (Number.isInteger(pNum) ? pNum.toLocaleString('th-TH') : pNum.toLocaleString('th-TH', {minimumFractionDigits:2}));
    }

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

