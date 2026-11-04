/* Connectly - utilidades compartidas por todas las páginas */
(function () {
    'use strict';

    // ---------- helpers ----------
    function escapeHtml(value) {
        const div = document.createElement('div');
        div.textContent = value == null ? '' : String(value);
        return div.innerHTML;
    }

    /** fetch JSON con cabecera X-Requested-With; lanza Error con el mensaje del servidor. */
    async function api(url, options) {
        const opts = Object.assign({ method: 'POST' }, options || {});
        opts.headers = Object.assign({ 'X-Requested-With': 'fetch' }, opts.headers || {});
        let response;
        try {
            response = await fetch(url, opts);
        } catch (e) {
            throw new Error('No se pudo conectar con el servidor.');
        }
        if (response.status === 401) {
            window.location.href = '/login?next=' + encodeURIComponent(location.pathname + location.search);
            throw new Error('Debes iniciar sesión.');
        }
        let data = null;
        try { data = await response.json(); } catch (e) { /* respuesta sin JSON */ }
        if (!response.ok || (data && data.success === false)) {
            throw new Error((data && (data.error || data.message)) || 'Ocurrió un error.');
        }
        return data || {};
    }

    function form(data) {
        const fd = new FormData();
        Object.keys(data).forEach(k => fd.append(k, data[k]));
        return fd;
    }

    // ---------- toasts ----------
    function toast(message, type) {
        const root = document.getElementById('toast-root');
        if (!root) return;
        const el = document.createElement('div');
        el.className = 'toast toast-' + (type || 'info');
        el.setAttribute('role', 'status');
        el.textContent = message;
        root.appendChild(el);
        setTimeout(() => { el.style.transition = 'opacity .3s'; el.style.opacity = '0'; }, 3800);
        setTimeout(() => el.remove(), 4200);
    }

    // ---------- fechas relativas en español ----------
    const rtf = (typeof Intl !== 'undefined' && Intl.RelativeTimeFormat) ? new Intl.RelativeTimeFormat('es', { numeric: 'auto' }) : null;
    function timeAgo(iso) {
        const date = new Date(iso);
        if (isNaN(date)) return '';
        const seconds = Math.round((date.getTime() - Date.now()) / 1000);
        const units = [['year', 31536000], ['month', 2592000], ['day', 86400], ['hour', 3600], ['minute', 60]];
        if (!rtf) return date.toLocaleString('es');
        for (const [unit, size] of units) {
            if (Math.abs(seconds) >= size) return rtf.format(Math.round(seconds / size), unit);
        }
        return 'justo ahora';
    }
    function initTimes(root) {
        (root || document).querySelectorAll('[data-time]').forEach(el => {
            el.textContent = timeAgo(el.getAttribute('data-time'));
            el.title = new Date(el.getAttribute('data-time')).toLocaleString('es');
        });
    }

    // ---------- avatar de respaldo si la imagen no carga ----------
    document.addEventListener('error', function (e) {
        const img = e.target;
        if (img && img.tagName === 'IMG' && img.hasAttribute('data-avatar') && !img.dataset.fallbackApplied) {
            img.dataset.fallbackApplied = '1';
            img.src = '/static/images/user1.png';
        }
    }, true);

    // Imágenes que ya fallaron antes de que este script se cargara
    function fixBrokenAvatars() {
        document.querySelectorAll('img[data-avatar]').forEach(img => {
            if (img.complete && img.naturalWidth === 0 && !img.dataset.fallbackApplied) {
                img.dataset.fallbackApplied = '1';
                img.src = '/static/images/user1.png';
            }
        });
    }
    window.addEventListener('load', fixBrokenAvatars);

    // ---------- seguir / dejar de seguir (delegación: sirve también para HTML dinámico) ----------
    function followLabel(btn, following) {
        if (following) return 'Dejar de seguir';
        return btn.dataset.followsMe === 'true' ? 'Seguir también' : 'Seguir';
    }
    function setFollowState(userId, following) {
        document.querySelectorAll('.follow-btn[data-user-id="' + userId + '"]').forEach(btn => {
            btn.dataset.following = following ? 'true' : 'false';
            btn.textContent = followLabel(btn, following);
        });
    }
    function initFollowButtons(root) {
        (root || document).querySelectorAll('.follow-btn').forEach(btn => {
            btn.textContent = followLabel(btn, btn.dataset.following === 'true');
        });
    }
    document.addEventListener('click', async function (e) {
        const btn = e.target.closest('.follow-btn');
        if (!btn || btn.disabled) return;
        const userId = btn.dataset.userId;
        const wasFollowing = btn.dataset.following === 'true';
        btn.disabled = true;
        try {
            const data = await api('/' + (wasFollowing ? 'unfollow' : 'follow') + '/' + userId);
            setFollowState(userId, !wasFollowing);
            document.dispatchEvent(new CustomEvent('connectly:follow', {
                detail: { userId: Number(userId), following: !wasFollowing, followerCount: data.follower_count, button: btn }
            }));
        } catch (err) {
            toast(err.message, 'error');
        } finally {
            btn.disabled = false;
        }
    });

    // ---------- sidebar móvil ----------
    function toggleSidebar(forceClose) {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        if (!sidebar) return;
        const open = forceClose ? false : sidebar.classList.contains('-translate-x-full');
        sidebar.classList.toggle('-translate-x-full', !open);
        if (overlay) overlay.classList.toggle('hidden', !open);
        document.body.classList.toggle('modal-open', open && window.innerWidth < 1024);
    }

    // ---------- notificaciones ----------
    const NOTIF_TEXT = { follow: 'empezó a seguirte', like: 'le dio me gusta a tu publicación', comment: 'comentó tu publicación', message: 'te envió un mensaje' };
    function notifLink(n) {
        const me = document.body.dataset.me;
        if (n.type === 'follow') return '/profile/' + n.actor_id;
        if (n.type === 'message') return '/chat?user_id=' + n.actor_id;
        return '/profile/' + me + (n.entity_id ? '?post=' + n.entity_id : '');
    }
    function setBadge(count) {
        const badge = document.getElementById('notif-badge');
        if (!badge) return;
        badge.textContent = count > 99 ? '99+' : count;
        badge.classList.toggle('hidden', !count);
    }
    async function refreshNotifications(renderList) {
        if (!document.body.dataset.me) return;
        try {
            const data = await api('/notifications', { method: 'GET' });
            setBadge(data.unread);
            if (renderList) renderNotificationList(data.items);
        } catch (e) { /* silencioso: es sondeo en segundo plano */ }
    }
    function renderNotificationList(items) {
        const list = document.getElementById('notif-list');
        if (!list) return;
        if (!items.length) {
            list.innerHTML = '<p class="text-sm text-gray-400 p-3">Aún no tienes notificaciones.</p>';
            return;
        }
        list.innerHTML = items.map(n => (
            '<a href="' + notifLink(n) + '" class="flex items-start gap-3 p-2 rounded-md text-left hover:bg-gray-700 ' + (n.is_read ? 'opacity-70' : '') + '">' +
            '<img src="' + escapeHtml(n.actor_image || '/static/images/user1.png') + '" data-avatar class="w-9 h-9 rounded-full flex-shrink-0" alt="">' +
            '<div class="min-w-0"><p class="text-sm text-gray-100 leading-snug"><strong>' + escapeHtml(n.actor_name || 'Alguien') + '</strong> ' + NOTIF_TEXT[n.type] + '</p>' +
            '<p class="text-xs text-gray-400">' + timeAgo(n.created_at) + '</p></div>' +
            (n.is_read ? '' : '<span class="w-2 h-2 mt-2 rounded-full bg-blue-400 flex-shrink-0"></span>') + '</a>'
        )).join('');
    }
    async function toggleNotifications() {
        const panel = document.getElementById('notif-panel');
        if (!panel) return;
        const opening = panel.classList.contains('hidden');
        panel.classList.toggle('hidden', !opening);
        if (opening) {
            await refreshNotifications(true);
            try { await api('/notifications/read'); setBadge(0); } catch (e) { /* ignorar */ }
        }
    }

    // ---------- reportar / bloquear (usado desde perfil y publicaciones) ----------
    async function reportTarget(type, id, label) {
        const reason = window.prompt('¿Por qué quieres reportar ' + label + '? (obligatorio)');
        if (reason === null) return;
        if (!reason.trim()) { toast('Indica un motivo para el reporte.', 'error'); return; }
        try {
            await api('/report', { body: form({ target_type: type, target_id: id, reason: reason.trim() }) });
            toast('Gracias, revisaremos tu reporte.', 'success');
        } catch (err) { toast(err.message, 'error'); }
    }
    async function blockUser(userId, name) {
        if (!window.confirm('¿Bloquear a ' + name + '? Dejarán de seguirse y no podrán interactuar.')) return;
        try { await api('/block/' + userId); toast('Usuario bloqueado.', 'success'); setTimeout(() => location.reload(), 600); }
        catch (err) { toast(err.message, 'error'); }
    }
    async function unblockUser(userId) {
        try { await api('/unblock/' + userId); toast('Usuario desbloqueado.', 'success'); setTimeout(() => location.reload(), 600); }
        catch (err) { toast(err.message, 'error'); }
    }

    // ---------- arranque ----------
    document.addEventListener('DOMContentLoaded', function () {
        initTimes();
        initFollowButtons();
        fixBrokenAvatars();

        // Mensajes flash del servidor -> toasts
        const flashEl = document.getElementById('flash-data');
        if (flashEl) {
            try { JSON.parse(flashEl.dataset.messages || '[]').forEach(m => toast(m[1], m[0] === 'error' ? 'error' : m[0])); } catch (e) { /* ignorar */ }
        }

        // Buscador del sidebar: botón de limpiar
        const input = document.getElementById('search-input');
        const clear = document.getElementById('clear-icon');
        if (input && clear) {
            const sync = () => clear.classList.toggle('hidden', !input.value.trim());
            input.addEventListener('input', sync);
            clear.addEventListener('click', () => { input.value = ''; sync(); input.focus(); });
            sync();
        }

        document.querySelectorAll('[data-toggle-sidebar]').forEach(el => el.addEventListener('click', () => toggleSidebar()));
        const overlay = document.getElementById('sidebar-overlay');
        if (overlay) overlay.addEventListener('click', () => toggleSidebar(true));
        const bell = document.getElementById('notif-toggle');
        if (bell) bell.addEventListener('click', toggleNotifications);

        refreshNotifications(false);
        setInterval(() => { if (!document.hidden) refreshNotifications(false); }, 30000);
    });

    window.Connectly = { api, form, toast, escapeHtml, timeAgo, initTimes, initFollowButtons, setFollowState,
                         reportTarget, blockUser, unblockUser };

    /** Carrusel para Alpine v2: <div x-data="carousel(total, {base:1, sm:2, lg:3})" x-init="listen()"> */
    window.carousel = function (total, per) {
        per = per || { base: 1, sm: 2, lg: 3 };
        const pick = function () {
            const w = window.innerWidth;
            return w >= 1280 ? (per.xl || per.lg || per.sm || per.base)
                 : w >= 1024 ? (per.lg || per.sm || per.base)
                 : w >= 640 ? (per.sm || per.base) : per.base;
        };
        return {
            current: 0, total: total, perSlide: pick(),   // valor correcto desde el primer render
            listen() { window.addEventListener('resize', () => this.resize()); },
            resize() { this.perSlide = pick(); this.current = Math.min(this.current, this.pages - 1); },
            get pages() { return Math.max(1, Math.ceil(this.total / this.perSlide)); },
            next() { this.current = this.current < this.pages - 1 ? this.current + 1 : 0; },
            prev() { this.current = this.current > 0 ? this.current - 1 : this.pages - 1; }
        };
    };
})();
