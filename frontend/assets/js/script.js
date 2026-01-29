document.addEventListener('DOMContentLoaded', () => {
    /* =========================================
       1. ระบบ CHAT WIDGET
       ========================================= */
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

    // Event Listeners สำหรับ Chat
    chatButton.addEventListener('click', toggleChat);
    closeChatHeader.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleChat();
    });

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

    // กดปุ่มส่ง หรือ กด Enter
    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });


    /* =========================================
       2. ระบบ PROFILE MENU (Dropdown)
       ========================================= */
    const profileBtn = document.querySelector('.profile-trigger');
    const profileMenu = document.getElementById('profileMenu');

    // ฟังก์ชันสลับเมนู (ใช้ร่วมกับ onclick ใน HTML หรือใช้ Event Listener ตรงนี้ก็ได้)
    // เพื่อความชัวร์ เราจะผูก Event Listener ใหม่เลย
    if (profileBtn && profileMenu) {
        // ลบ onclick เดิมออกจาก HTML (ถ้ามี) หรือปล่อยไว้ก็ได้ แต่ JS นี้จะทำงาน
        window.toggleProfileMenu = function() { // เผื่อ HTML เรียกใช้
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