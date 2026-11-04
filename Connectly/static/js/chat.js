/* Connectly - chat en tiempo real (Socket.IO). Todo el contenido se inserta con textContent. */
(function () {
    'use strict';
    const C = window.Connectly;
    const root = document.getElementById('chat-root');
    if (!root) return;

    const me = Number(root.dataset.me);
    const peerId = root.dataset.selected ? Number(root.dataset.selected) : null;
    const peerImage = root.dataset.peerImage || '/static/images/user1.png';
    const box = document.getElementById('chat-box');
    if (!peerId || !box) return;

    const input = document.getElementById('message-input');
    const fileInput = document.getElementById('image-input');
    const previewBox = document.getElementById('image-preview-container');
    const preview = document.getElementById('image-preview');
    const sendBtn = document.getElementById('send-btn');
    const clock = iso => new Date(iso).toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' });

    function scrollDown() { box.scrollTop = box.scrollHeight; }

    function appendMessage(msg) {
        const empty = document.getElementById('no-messages');
        if (empty) empty.remove();
        const mine = msg.sender_id === me;

        const row = document.createElement('div');
        row.className = 'flex items-end gap-2 ' + (mine ? 'justify-end' : 'justify-start');
        if (!mine) {
            const avatar = document.createElement('img');
            avatar.src = msg.profile_image || peerImage;
            avatar.alt = '';
            avatar.setAttribute('data-avatar', '');
            avatar.className = 'w-8 h-8 rounded-full object-cover flex-shrink-0';
            row.appendChild(avatar);
        }
        const bubble = document.createElement('div');
        bubble.className = 'p-3 rounded-2xl max-w-[75%] break-words ' + (mine ? 'bg-blue-100 text-gray-800' : 'bg-gray-100 text-gray-700');
        if (msg.content) {
            const span = document.createElement('span');
            span.className = 'whitespace-pre-line';
            span.textContent = msg.content;
            bubble.appendChild(span);
        }
        if (msg.image) {
            const img = document.createElement('img');
            img.src = msg.image;
            img.alt = 'Imagen del mensaje';
            img.className = 'mt-2 w-64 max-w-full h-auto rounded-md cursor-pointer';
            img.dataset.chatImage = msg.image;
            bubble.appendChild(img);
        }
        const time = document.createElement('small');
        time.className = 'block text-xs text-gray-500 mt-1';
        time.textContent = clock(msg.sent_at);
        bubble.appendChild(time);
        row.appendChild(bubble);
        box.appendChild(row);
        scrollDown();
    }

    // ---------- imagen adjunta ----------
    function clearImage() {
        fileInput.value = '';
        preview.removeAttribute('src');
        previewBox.classList.add('hidden');
    }
    fileInput.addEventListener('change', function () {
        const file = fileInput.files[0];
        if (!file) return clearImage();
        if (file.size > 8 * 1024 * 1024) { C.toast('La imagen supera el máximo de 8 MB.', 'error'); return clearImage(); }
        const reader = new FileReader();
        reader.onload = e => { preview.src = e.target.result; previewBox.classList.remove('hidden'); };
        reader.readAsDataURL(file);
    });
    document.getElementById('remove-image').addEventListener('click', clearImage);

    // ---------- enviar ----------
    document.getElementById('chat-form').addEventListener('submit', async function (e) {
        e.preventDefault();
        const content = input.value.trim();
        const file = fileInput.files[0];
        if (!content && !file) return;

        const data = new FormData();
        data.append('content', content);
        data.append('receiver_id', peerId);
        if (file) data.append('image', file);

        sendBtn.disabled = true;
        try {
            await C.api('/send_message', { body: data });   // el mensaje vuelve por el socket
            input.value = '';
            clearImage();
        } catch (err) {
            C.toast(err.message, 'error');
        } finally {
            sendBtn.disabled = false;
            input.focus();
        }
    });

    // ---------- tiempo real ----------
    const socket = io();
    socket.on('connect', () => socket.emit('join', { selected_user_id: peerId }));   // también tras reconectar
    socket.on('receive_message', function (msg) {
        appendMessage(msg);
        if (msg.sender_id === peerId) fetch('/chat/read/' + peerId, { method: 'POST', headers: { 'X-Requested-With': 'fetch' } });
    });

    // ---------- imágenes ampliadas ----------
    box.addEventListener('click', function (e) {
        const img = e.target.closest('[data-chat-image]');
        if (!img) return;
        document.getElementById('chatModalImage').src = img.dataset.chatImage;
        document.getElementById('chatImageModal').classList.add('is-open');
    });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') document.getElementById('chatImageModal').classList.remove('is-open'); });

    document.querySelectorAll('[data-clock]').forEach(el => { el.textContent = clock(el.dataset.clock); });
    scrollDown();
    window.addEventListener('load', scrollDown);
    input.focus();
})();
