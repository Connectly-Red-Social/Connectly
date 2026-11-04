/* Connectly - interacción con publicaciones (home y perfil): likes, comentarios, imágenes, borrar, reportar */
(function () {
    'use strict';
    const C = window.Connectly;
    const $ = (sel, root) => (root || document).querySelector(sel);
    let currentPostId = null;

    // ---------- texto largo: "Ver más / Ver menos" ----------
    function initExpanders(root) {
        (root || document).querySelectorAll('.post-body').forEach(p => {
            const btn = p.parentElement.querySelector('[data-action="expand"]');
            if (!btn) return;
            // clamp activo => si el contenido real es más alto que lo visible, mostrar el botón
            btn.classList.toggle('hidden', !(p.scrollHeight > p.clientHeight + 1 || p.classList.contains('is-expanded')));
        });
    }

    // ---------- modales ----------
    function openModal(el) { el.classList.add('is-open'); document.body.classList.add('modal-open'); }
    function closeModal(el) {
        el.classList.remove('is-open');
        if (!document.querySelector('.modal-backdrop.is-open')) document.body.classList.remove('modal-open');
    }

    function openImage(src) {
        const modal = $('#imageModal');
        if (!modal) return;
        $('#modalImage').src = src;
        openModal(modal);
    }

    function cardOf(postId) { return document.querySelector('[data-post-card][data-post-id="' + postId + '"]'); }

    function openComments(card) {
        const modal = $('#commentModal');
        if (!modal || !card) return;
        currentPostId = card.dataset.postId;

        const img = card.dataset.image;
        const imgWrap = $('#postImageWrap');
        imgWrap.classList.toggle('hidden', !img);
        $('#postImage').src = img || '';

        $('#postAuthor').textContent = card.dataset.authorName;
        $('#postInterest').textContent = card.dataset.interest || '';
        $('#postContent').textContent = $('.post-body', card).textContent.trim();
        $('#postProfileImage').src = card.dataset.authorImage;
        $('#postProfileLink').href = '/profile/' + card.dataset.authorId;
        $('#commentInput').value = '';
        $('#charCount').textContent = $('#commentInput').maxLength;

        syncModalLike(card);
        openModal(modal);
        const pc = $('#postContent'), tb = $('#toggleContentButton');
        pc.classList.add('line-clamp-3');
        tb.textContent = 'Ver más';
        tb.classList.toggle('hidden', !(pc.scrollHeight > pc.clientHeight + 1));
        loadComments(currentPostId);
        setTimeout(() => $('#commentInput').focus(), 50);
    }

    function syncModalLike(card) {
        const btn = $('[data-action="like"]', card);
        if (!btn) return;
        $('#modalLikeIcon').className = 'bi text-xl mr-1 text-red-500 ' + (btn.getAttribute('aria-pressed') === 'true' ? 'bi-heart-fill' : 'bi-heart');
        $('#modalLikeCount').textContent = $('.like-count', card).textContent;
    }

    // ---------- comentarios (todo con textContent: sin XSS) ----------
    function commentNode(c) {
        const row = document.createElement('div');
        row.className = 'comment-item flex items-start gap-3';

        const link = document.createElement('a');
        link.href = '/profile/' + c.UserID;
        const avatar = document.createElement('img');
        avatar.src = c.profile_image || '/static/images/user1.png';
        avatar.alt = '';
        avatar.setAttribute('data-avatar', '');
        avatar.className = 'w-10 h-10 rounded-full border border-gray-300 flex-shrink-0';
        link.appendChild(avatar);

        const body = document.createElement('div');
        body.className = 'min-w-0 flex-1';
        const head = document.createElement('div');
        head.className = 'flex items-center gap-2 flex-wrap';
        const name = document.createElement('a');
        name.href = link.href;
        name.className = 'text-sm font-semibold text-gray-800 hover:underline';
        name.textContent = c.Name || 'Usuario';
        head.appendChild(name);
        if (c.interest) {
            const tag = document.createElement('span');
            tag.className = 'interest-tag';
            tag.textContent = c.interest;
            head.appendChild(tag);
        }
        const text = document.createElement('p');
        text.className = 'text-sm text-gray-600';
        text.style.whiteSpace = 'pre-line';
        text.textContent = c.Content || '';
        const when = document.createElement('p');
        when.className = 'text-xs text-gray-500';
        when.textContent = C.timeAgo(c.CommentDate);

        body.append(head, text, when);
        row.append(link, body);
        return row;
    }

    async function loadComments(postId) {
        const box = $('#commentsContainer');
        box.innerHTML = '<p class="text-sm text-gray-400">Cargando comentarios...</p>';
        try {
            const comments = await C.api('/get_comments/' + postId, { method: 'GET' });
            if (String(postId) !== String(currentPostId)) return;  // se cerró o cambió de post
            box.innerHTML = '';
            if (!comments.length) {
                box.innerHTML = '<p class="text-sm text-gray-400">Todavía no hay comentarios. ¡Sé el primero!</p>';
                return;
            }
            comments.forEach(c => box.appendChild(commentNode(c)));
            box.scrollTop = box.scrollHeight;
        } catch (err) {
            box.innerHTML = '';
            C.toast(err.message, 'error');
        }
    }

    async function submitComment(event) {
        event.preventDefault();
        const input = $('#commentInput');
        const content = input.value.trim();
        if (!content || !currentPostId) return;
        const button = event.target.querySelector('button[type="submit"]');
        button.disabled = true;
        try {
            const data = await C.api('/add_comment/' + currentPostId, { body: C.form({ comment_content: content }) });
            input.value = '';
            $('#charCount').textContent = input.maxLength;
            const card = cardOf(currentPostId);
            if (card && data.comment_count != null) $('.comment-count', card).textContent = data.comment_count;
            await loadComments(currentPostId);
        } catch (err) {
            C.toast(err.message, 'error');
        } finally {
            button.disabled = false;
        }
    }

    // ---------- likes ----------
    async function toggleLike(btn) {
        const card = btn.closest('[data-post-card]');
        const liked = btn.getAttribute('aria-pressed') === 'true';
        btn.disabled = true;
        try {
            const data = await C.api('/' + (liked ? 'unlike' : 'like') + '_post/' + card.dataset.postId);
            btn.setAttribute('aria-pressed', liked ? 'false' : 'true');
            $('.like-icon', btn).className = 'like-icon bi text-xl mr-1 text-red-500 ' + (liked ? 'bi-heart' : 'bi-heart-fill');
            $('.like-count', btn).textContent = data.like_count;
            if (currentPostId === card.dataset.postId) syncModalLike(card);
        } catch (err) {
            C.toast(err.message, 'error');
        } finally {
            btn.disabled = false;
        }
    }

    // ---------- borrar ----------
    async function deletePost(btn) {
        const card = btn.closest('[data-post-card]');
        if (!window.confirm('¿Estás seguro de que deseas eliminar esta publicación?')) return;
        btn.disabled = true;
        try {
            await C.api('/delete_post/' + card.dataset.postId);
            card.style.transition = 'opacity .3s, transform .3s';
            card.style.opacity = '0';
            card.style.transform = 'scale(0.97)';
            setTimeout(() => {
                card.remove();
                document.querySelectorAll('[data-post-count]').forEach(el => { el.textContent = Math.max(0, parseInt(el.textContent, 10) - 1); });
                document.dispatchEvent(new CustomEvent('connectly:posts-changed'));
            }, 300);
            C.toast('Publicación eliminada.', 'success');
        } catch (err) {
            btn.disabled = false;
            C.toast(err.message, 'error');
        }
    }

    // ---------- cargar más (feed) ----------
    async function loadMore(btn) {
        btn.disabled = true;
        const original = btn.textContent;
        btn.textContent = 'Cargando...';
        try {
            const data = await C.api('/home?partial=1&offset=' + btn.dataset.offset, { method: 'GET' });
            const list = document.getElementById('post-list');
            list.insertAdjacentHTML('beforeend', data.html);
            C.initTimes(list); initExpanders(list);
            btn.dataset.offset = data.next_offset;
            if (!data.has_more) btn.remove(); else { btn.disabled = false; btn.textContent = original; }
        } catch (err) {
            btn.disabled = false; btn.textContent = original;
            C.toast(err.message, 'error');
        }
    }

    // ---------- eventos ----------
    document.addEventListener('click', function (e) {
        const target = e.target.closest('[data-action]');
        if (!target) {
            if (e.target.classList && e.target.classList.contains('modal-backdrop')) closeModal(e.target);
            return;
        }
        const action = target.dataset.action;
        const card = target.closest('[data-post-card]');
        if (action === 'like') toggleLike(target);
        else if (action === 'comments') openComments(card);
        else if (action === 'image') openImage(target.dataset.src);
        else if (action === 'delete') deletePost(target);
        else if (action === 'report-post') C.reportTarget('post', card.dataset.postId, 'esta publicación');
        else if (action === 'load-more') loadMore(target);
        else if (action === 'close-modal') closeModal(target.closest('.modal-backdrop'));
        else if (action === 'expand') {
            const p = $('.post-body', card);
            const expanded = p.classList.toggle('line-clamp-4') === false;
            p.classList.toggle('is-expanded', expanded);
            target.textContent = expanded ? 'Ver menos' : 'Ver más';
        } else if (action === 'toggle-modal-content') {
            const p = $('#postContent');
            const expanded = p.classList.toggle('line-clamp-3') === false;
            target.textContent = expanded ? 'Ver menos' : 'Ver más';
        }
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') document.querySelectorAll('.modal-backdrop.is-open').forEach(closeModal);
    });

    document.addEventListener('DOMContentLoaded', function () {
        initExpanders();
        const form = $('#commentForm');
        if (form) form.addEventListener('submit', submitComment);
        const input = $('#commentInput');
        if (input) input.addEventListener('input', () => { $('#charCount').textContent = input.maxLength - input.value.length; });

        // Abrir una publicación desde una notificación: /profile/<id>?post=<id>
        const wanted = new URLSearchParams(location.search).get('post');
        if (wanted) {
            const card = cardOf(wanted);
            if (card) { card.scrollIntoView({ block: 'center' }); openComments(card); }
        }
    });
    window.addEventListener('load', () => initExpanders());
})();
