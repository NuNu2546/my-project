document.addEventListener('DOMContentLoaded', () => {
    const chatButton = document.getElementById('chatButton');
    const chatPopup = document.getElementById('chatPopup');
    const closeChatHeader = document.getElementById('closeChatHeader');
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatMessages = document.getElementById('chatMessages');

    // ฟังก์ชัน เปิด-ปิด แชท (แบบไม่เปลี่ยนไอคอน)
    function toggleChat() {
        const isOpen = chatPopup.classList.contains('show');

        if (isOpen) {
            // ปิดแชท
            chatPopup.classList.remove('show');
            chatButton.classList.remove('active-btn');
        } else {
            // เปิดแชท
            chatPopup.classList.add('show');
            chatButton.classList.add('active-btn');
            
            // Focus ที่ช่อง input ทันทีเมื่อเปิด
            setTimeout(() => chatInput.focus(), 400);
        }
    }

    // คลิกปุ่มกลม
    chatButton.addEventListener('click', toggleChat);

    // คลิกปุ่ม X ในหัวแชท
    closeChatHeader.addEventListener('click', (e) => {
        e.stopPropagation(); 
        toggleChat();
    });

    // ฟังก์ชันส่งข้อความ (เหมือนเดิม)
    function sendMessage() {
        const text = chatInput.value.trim();
        if (text !== "") {
            const msgDiv = document.createElement('div');
            msgDiv.className = 'message user-msg';
            msgDiv.innerText = text;
            chatMessages.appendChild(msgDiv);

            chatInput.value = "";
            chatMessages.scrollTop = chatMessages.scrollHeight;

            setTimeout(() => {
                const adminDiv = document.createElement('div');
                adminDiv.className = 'message admin-msg';
                adminDiv.innerText = "รับทราบค่ะ แอดมินกำลังตรวจสอบข้อมูลให้นะคะ";
                chatMessages.appendChild(adminDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }, 1000);
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
});

function toggleProfileMenu() {
        const menu = document.getElementById("profileMenu");
        menu.classList.toggle("active");
    }

    // คลิกที่อื่นเพื่อปิดเมนู
    window.addEventListener('click', function(e) {
        const menu = document.getElementById("profileMenu");
        const btn = document.querySelector('.profile-trigger');

        // ถ้าคลิกไม่ได้อยู่ที่ปุ่ม และไม่ได้อยู่ในเมนู ให้ปิดเมนู
        if (!btn.contains(e.target) && !menu.contains(e.target)) {
            menu.classList.remove('active');
        }
    });