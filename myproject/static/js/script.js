/* ==========================================================================
   ส่วนที่ 1: GLOBAL VARIABLES & STATE
   ตัวแปรที่ต้องใช้งานร่วมกันในหลายฟังก์ชัน
   ========================================================================== */
// ตัวแปรเก็บข้อมูลสินค้าชั่วคราวขณะเปิด Modal
let currentProduct = {};


/* ==========================================================================
   ส่วนที่ 2: DOM CONTENT LOADED
   ทำงานเมื่อหน้าเว็บโหลดโครงสร้างเสร็จ (Chat Widget & Profile Menu)
   ========================================================================== */
document.addEventListener('DOMContentLoaded', () => {

    // ---------------------------------------------------
    // 2.1 ระบบ CHAT WIDGET
    // ---------------------------------------------------
    const chatButton = document.getElementById('chatButton');
    const chatPopup = document.getElementById('chatPopup');
    const closeChatHeader = document.getElementById('closeChatHeader');
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatMessages = document.getElementById('chatMessages');

    // ฟังก์ชันเปิด-ปิดแชท
    function toggleChat() {
        chatPopup.classList.toggle('show');

        // ถ้าเปิดอยู่ ให้โฟกัสที่ช่องพิมพ์
        if (chatPopup.classList.contains('show')) {
            setTimeout(() => chatInput.focus(), 300);
        }
    }

    // ฟังก์ชันสร้าง HTML ข้อความ
    function addMessage(text, className) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${className}`;
        msgDiv.innerText = text;
        chatMessages.appendChild(msgDiv);
        scrollToBottom();
    }

    // ฟังก์ชันเลื่อนแชทลงล่างสุด
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // ฟังก์ชันแสดงสถานะ "กำลังพิมพ์..."
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typingIndicator';
        typingDiv.className = 'message admin-msg typing';
        typingDiv.innerHTML = '<span>.</span><span>.</span><span>.</span>';
        chatMessages.appendChild(typingDiv);
        scrollToBottom();
    }

    // ฟังก์ชันลบสถานะ "กำลังพิมพ์..."
    function removeTypingIndicator() {
        const typingDiv = document.getElementById('typingIndicator');
        if (typingDiv) {
            typingDiv.remove();
        }
    }

    // ฟังก์ชันส่งข้อความ
    function sendMessage() {
        const text = chatInput.value.trim();

        if (text !== "") {
            // 1. เพิ่มข้อความฝั่งผู้ใช้ (User)
            addMessage(text, 'user-msg');
            chatInput.value = ""; // เคลียร์ช่องพิมพ์

            // 2. จำลอง Admin กำลังพิมพ์...
            showTypingIndicator();

            // 3. Admin ตอบกลับอัตโนมัติ (Delay 1.5 วินาที)
            setTimeout(() => {
                removeTypingIndicator();
                addMessage("รับทราบค่ะ แอดมินกำลังตรวจสอบข้อมูลให้นะคะ 🌿", 'admin-msg');
            }, 1500);
        }
    }

    // --- Chat Event Listeners ---
    if (chatButton) chatButton.addEventListener('click', toggleChat);
    
    if (closeChatHeader) {
        closeChatHeader.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleChat();
        });
    }

    if (sendBtn) sendBtn.addEventListener('click', sendMessage);
    
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }


    // ---------------------------------------------------
    // 2.2 ระบบ PROFILE MENU (Dropdown)
    // ---------------------------------------------------
    const profileBtn = document.querySelector('.profile-trigger');
    const profileMenu = document.getElementById('profileMenu');

    if (profileBtn && profileMenu) {
        // กำหนดฟังก์ชันให้ global window เพื่อให้ HTML เรียกใช้ได้ (ถ้าจำเป็น)
        window.toggleProfileMenu = function() {
            profileMenu.classList.toggle('active');
        };

        // คลิกที่อื่นเพื่อปิดเมนู
        window.addEventListener('click', function(e) {
            if (!profileBtn.contains(e.target) && !profileMenu.contains(e.target)) {
                profileMenu.classList.remove('active');
            }
        });
    }
});


/* ==========================================================================
   ส่วนที่ 3: GLOBAL FUNCTIONS (MODAL & CART)
   ฟังก์ชันที่ต้องอยู่นอก DOMContentLoaded เพื่อให้ onclick="..." ใน HTML เรียกใช้ได้
   ========================================================================== */

// 3.1 ฟังก์ชันเปิด Modal (Quick View)
function openQuickView(event, id, name, price, image) {
    // ป้องกันไม่ให้กดแล้วเด้งไปหน้า Detail
    event.preventDefault();
    event.stopPropagation();

    // เก็บข้อมูลลงตัวแปร
    currentProduct = {
        id: id,
        name: name,
        price: parseFloat(price),
        image: image,
        qty: 1
    };

    // อัปเดตหน้าตา Modal
    document.getElementById('modalImg').src = image;
    document.getElementById('modalTitle').innerText = name;
    document.getElementById('modalPrice').innerText = "$" + currentProduct.price.toFixed(2);
    document.getElementById('modalQty').value = 1;

    // แสดง Modal
    document.getElementById('quickViewModal').style.display = 'flex';
}

// 3.2 ฟังก์ชันปิด Modal
function closeModal() {
    document.getElementById('quickViewModal').style.display = 'none';
}

// Event: ปิดเมื่อกดพื้นหลังสีดำ
window.onclick = function(event) {
    const modal = document.getElementById('quickViewModal');
    if (event.target == modal) {
        closeModal();
    }
}

// 3.3 ฟังก์ชันปรับจำนวนสินค้าใน Modal
function updateModalQty(change) {
    let newQty = currentProduct.qty + change;
    if (newQty >= 1) {
        currentProduct.qty = newQty;
        document.getElementById('modalQty').value = newQty;
    }
}

// 3.4 ฟังก์ชันยืนยันการเพิ่มลงตะกร้า (Confirm Add)
function confirmAddToCart() {
    // ดึงตะกร้าเก่ามา หรือถ้าไม่มีให้สร้าง Array ว่าง
    let cart = JSON.parse(localStorage.getItem('cart')) || [];

    // เช็คว่ามีสินค้านี้ในตะกร้าอยู่แล้วไหม?
    const existingItem = cart.find(item => item.id === currentProduct.id);

    if (existingItem) {
        // ถ้ามีแล้ว ให้บวกจำนวนเพิ่ม
        existingItem.qty += currentProduct.qty;
    } else {
        // ถ้ายังไม่มี ให้เพิ่มใหม่
        cart.push(currentProduct);
    }

    // บันทึกลง LocalStorage
    localStorage.setItem('cart', JSON.stringify(cart));

    // แจ้งเตือน
    alert(`เพิ่ม "${currentProduct.name}" จำนวน ${currentProduct.qty} ชิ้น ลงตะกร้าแล้ว!`);

    // ปิด Modal
    closeModal();

    // (Optional) updateCartCount(); 
}