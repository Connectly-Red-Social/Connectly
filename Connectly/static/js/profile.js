/* Connectly - página de perfil: segundo interés, filtros, contadores y modal de seguidores */
(function () {
    'use strict';
    const C = window.Connectly;
    const PROFILE_ID = window.PROFILE_ID;
    const IS_OWN = window.IS_OWN_PROFILE;
    const $ = (sel, root) => (root || document).querySelector(sel);

    // ---------- segundo interés ----------
    async function loadSecondInterest() {
        const span = $('#secondInterest span');
        if (!span) return;
        try {
            const data = await C.api('/get_second_interest/' + PROFILE_ID, { method: 'GET' });
            span.textContent = data.second_interest;
        } catch (e) {
            span.textContent = 'No disponible';
        }
    }

    // ---------- filtros (género / país) ----------
    async function loadFilterCounts() {
        const gender = $('#genderFilter'), country = $('#countryFilter');
        if (!gender || !country) return;
        try {
            const data = await C.api('/get_filter_counts_for_profile/' + PROFILE_ID, { method: 'GET' });
            const fill = (select, counts) => Object.entries(counts || {}).sort().forEach(([k, n]) => {
                const option = document.createElement('option');
                option.value = k;
                option.textContent = k + ' (' + n + ')';
                select.appendChild(option);
            });
            fill(gender, data.gender_counts);
            fill(country, data.country_counts);
        } catch (e) { /* los filtros quedan en "Todos" */ }
    }

    function userCard(u) {
        const wrap = document.createElement('div');
        wrap.className = 'bg-white p-6 rounded-lg shadow-lg text-center card';
        const link = document.createElement('a');
        link.href = '/profile/' + u.user_id;
        const img = document.createElement('img');
        img.src = u.profile_image || '/static/images/user1.png';
        img.alt = 'Foto de perfil de ' + u.name;
        img.setAttribute('data-avatar', '');
        img.className = 'w-16 h-16 mx-auto rounded-full object-cover border-2 border-blue-500 mb-3';
        link.appendChild(img);
        const name = document.createElement('p');
        name.className = 'text-gray-800 font-bold truncate';
        name.textContent = u.name;
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'follow-btn follow-link';
        btn.dataset.userId = u.user_id;
        btn.dataset.following = u.is_following ? 'true' : 'false';
        wrap.append(link, name, btn);
        return wrap;
    }

    async function applyFilters() {
        const container = $('#filteredUsersContainer');
        const params = new URLSearchParams({ profile_user_id: PROFILE_ID });
        const gender = $('#genderFilter').value, country = $('#countryFilter').value;
        if (gender) params.append('gender', gender);
        if (country) params.append('country', country);
        try {
            const data = await C.api('/filter_users?' + params, { method: 'GET' });
            container.innerHTML = '';
            if (!data.filtered_users.length) {
                container.innerHTML = '<p class="text-gray-500 col-span-full">No se encontraron usuarios.</p>';
            } else {
                data.filtered_users.forEach(u => container.appendChild(userCard(u)));
                C.initFollowButtons(container);
            }
            $('#similarCount').textContent = '· ' + data.filtered_users.length;
        } catch (err) {
            C.toast(err.message, 'error');
        }
    }

    // ---------- modal de seguidores / seguidos ----------
    window.openFollowModal = async function (type) {
        const modal = $('#followModal');
        const content = $('#followModalContent');
        content.textContent = 'Cargando...';
        modal.classList.add('is-open');
        document.body.classList.add('modal-open');
        try {
            const response = await fetch('/' + type + '/' + PROFILE_ID + '?modal=1', { headers: { 'X-Requested-With': 'fetch' } });
            if (!response.ok) throw new Error('No se pudo cargar la lista.');
            content.innerHTML = await response.text();   // HTML generado por el servidor (ya escapado por Jinja)
            C.initFollowButtons(content);
        } catch (err) {
            content.textContent = err.message;
        }
    };

    // ---------- contadores en vivo ----------
    document.addEventListener('connectly:follow', function (e) {
        const { userId, following, followerCount } = e.detail;
        if (userId === PROFILE_ID && followerCount != null) {
            $('#followerCount').textContent = followerCount;       // seguidores del perfil visitado
        } else if (IS_OWN && userId !== PROFILE_ID) {
            const el = $('#followingCount');                       // en mi perfil, "seguidos" sube o baja
            el.textContent = Math.max(0, parseInt(el.textContent, 10) + (following ? 1 : -1));
        }
    });

    document.addEventListener('DOMContentLoaded', function () {
        loadSecondInterest();
        loadFilterCounts();
        const g = $('#genderFilter'), c = $('#countryFilter');
        if (g) g.addEventListener('change', applyFilters);
        if (c) c.addEventListener('change', applyFilters);
        const count = document.querySelectorAll('#filteredUsersContainer > div').length;
        if ($('#similarCount') && count) $('#similarCount').textContent = '· ' + count;
    });
})();
