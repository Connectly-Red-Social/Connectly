## Connectly: red social con Flask + MySQL. Composición de la aplicación: arranque de la BD, rutas web y chat en tiempo real (Flask-SocketIO).
## La lógica por contexto vive en contexts/ (users, iam, profiles, social, community) y en application/.
import os, uuid, time
from functools import wraps

from flask import (Flask, flash, g, jsonify, redirect, render_template, request, send_from_directory,
                   session, url_for)
from flask_cors import CORS
from flask_socketio import SocketIO, join_room
from dotenv import load_dotenv
from sqlalchemy import text

from shared.db import make_engine, get_db_url
from shared.bootstrap import bootstrap_database
from contexts.community.community_data import CommunityData
from contexts.iam import routes as iam_routes
from contexts.iam.service import AuthError, change_password
from contexts.profiles import service as profiles_service
from contexts.social import routes as social_routes
from contexts.social import service as social_service
from shared.seed import parse_date
from shared.timeutil import iso_utc, utc_now

# Cargar variables de entorno
load_dotenv()

## Crear la aplicación Flask
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # 8 MB por petición
CORS(app, supports_credentials=True)

# configuración de Flask-SocketIO para el manejo de mensajes en tiempo real entre seguidores
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
app.jinja_env.filters['iso_utc'] = iso_utc

# Conexión a la base de datos y creación de instancias de CommunityData
db_url = get_db_url()
engine = make_engine(db_url)
bootstrap_database(engine)  # crea tablas faltantes y siembra el dataset si la BD está vacía
community_data_instance = CommunityData(db_url)

# Rutas por bounded context (IAM: login/register/logout; SOCIAL: bloqueos, notificaciones, reportes)
iam_routes.init_app(app, engine)
social_routes.init_app(app, engine)

# Crear la carpeta de almacenamiento para las imágenes de chat y posts
STORAGE_FOLDER = os.path.join(os.path.dirname(__file__), 'storage')
os.makedirs(STORAGE_FOLDER, exist_ok=True)

ALLOWED_IMAGE_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
FEED_PAGE_SIZE = 10
MAX_POST_LEN = 2000
MAX_COMMENT_LEN = 500
MAX_MESSAGE_LEN = 2000


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def current_user_id():
    uid = session.get('user_id')
    return uid if isinstance(uid, int) else None


def wants_json():
    return request.headers.get('X-Requested-With') == 'fetch' or request.is_json


def login_required(view):
    """Páginas para miembros. Anónimos -> login (con ?next=). Administradores -> su panel."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user_id():
            if wants_json():
                return jsonify(success=False, error='Debes iniciar sesión.'), 401
            return redirect(url_for('login', next=request.full_path.rstrip('?')))
        if session.get('is_admin'):
            if wants_json():
                return jsonify(success=False, error='Los administradores no pueden usar esta función.'), 403
            return redirect(url_for('admin_dashboard'))
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapper


def save_image(file_storage, prefix):
    """Valida y guarda una imagen subida. Devuelve '/storage/<archivo>' o None si no se envió."""
    if not file_storage or not file_storage.filename:
        return None
    ext = file_storage.filename.rsplit('.', 1)[-1].lower() if '.' in file_storage.filename else ''
    if ext not in ALLOWED_IMAGE_EXT:
        raise ValueError('Formato de imagen no permitido. Usa PNG, JPG, GIF o WEBP.')
    name = f"{prefix}_{int(time.time())}_{uuid.uuid4().hex}.{ext}"
    file_storage.save(os.path.join(STORAGE_FOLDER, name))
    return f"/storage/{name}"


def delete_stored_file(url_path):
    """Borra un archivo de storage a partir de su URL pública ('/storage/x.png')."""
    if not url_path or not url_path.startswith('/storage/'):
        return
    path = os.path.join(STORAGE_FOLDER, os.path.basename(url_path))
    if os.path.isfile(path):
        os.remove(path)


def are_mutual_followers(a, b):
    return community_data_instance.is_following(a, b) and community_data_instance.is_following(b, a)


def chat_room(a, b):
    return f'chat_{min(a, b)}_{max(a, b)}'


@app.before_request
def load_logged_in_user():
    g.user = None
    if request.endpoint in (None, 'static', 'serve_image'):
        return
    user_id = session.get('user_id')
    if user_id:
        query = text("SELECT UserID, username, profile_image FROM social_media_users WHERE UserID = :user_id")
        with engine.connect() as connection:
            user = connection.execute(query, {"user_id": user_id}).fetchone()
            if user:
                g.user = {
                    "user_id": user.UserID,
                    "username": user.username,
                    "profile_image": user.profile_image
                }


@app.context_processor
def inject_sidebar_counters():
    """Mensajes sin leer para la insignia del sidebar."""
    uid = current_user_id()
    if uid and not session.get('is_admin') and request.endpoint not in (None, 'static', 'serve_image'):
        return {'unread_messages': sum(social_service.unread_by_sender(engine, uid).values())}
    return {'unread_messages': 0}


@app.errorhandler(404)
def not_found(_):
    if wants_json():
        return jsonify(success=False, error='No encontrado.'), 404
    return render_template('error.html', code=404, title='Página no encontrada',
                           message='Lo que buscas no existe o ya no está disponible.'), 404


@app.errorhandler(413)
def too_large(_):
    if wants_json():
        return jsonify(success=False, error='El archivo supera el máximo de 8 MB.'), 413
    return render_template('error.html', code=413, title='Archivo demasiado grande',
                           message='El archivo supera el máximo permitido de 8 MB.'), 413


@app.errorhandler(500)
def server_error(_):
    if wants_json():
        return jsonify(success=False, error='Error interno del servidor.'), 500
    return render_template('error.html', code=500, title='Algo salió mal',
                           message='Tuvimos un problema. Inténtalo de nuevo en unos minutos.'), 500


## Rutas de la aplicación
@app.route('/')
def home():
    if current_user_id():
        return redirect(url_for('admin_dashboard') if session.get('is_admin') else url_for('index'))
    return redirect(url_for('login'))


# ---------------------------------------------------------------------------
# Administración
# ---------------------------------------------------------------------------
@app.route('/admin_dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html', user_id=session.get('user_id'),
                           open_reports=len(social_service.list_open_reports(engine)),
                           total_users=profiles_service.count_profiles(engine))


@app.route('/view_all_users', methods=['GET'])
@admin_required
def view_all_users():
    selected_interest = request.args.get('interest', '')
    users, interests = community_data_instance.list_users(selected_interest or None)
    return render_template('view_all_users.html', users=users, interests=interests,
                           selected_interest=selected_interest)


@app.route('/admin_graph', methods=['GET'])
@admin_required
def admin_graph():
    limit = max(10, min(request.args.get('limit', 300, type=int), 1500))
    graph_file = os.path.join(STORAGE_FOLDER, "admin_graph.html")
    community_data_instance.generate_pyvis_graph(graph_file, max_nodes=limit)
    return render_template("admin_graph.html", graph_file="/storage/admin_graph.html", limit=limit)


# ---------------------------------------------------------------------------
# Perfil
# ---------------------------------------------------------------------------
@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    me = current_user_id()
    is_own_profile = (me == user_id)

    user_data, same_interest_users = community_data_instance.get_user_profile(user_id)
    blocked_by_me = (not is_own_profile) and social_service.has_blocked(engine, me, user_id)
    blocked_me = (not is_own_profile) and (not blocked_by_me) and social_service.is_blocked_between(engine, me, user_id)
    if not user_data or blocked_me:
        return render_template('error.html', code=404, title='Perfil no disponible',
                               message='Este perfil no existe o no está disponible.'), 404

    following_ids = community_data_instance.get_following_ids(me)
    profile_info = profiles_service.get_profile(engine, user_id) or {}

    user_interest = user_data['interest']
    gender_filter = request.args.get('gender')
    if gender_filter and user_interest:
        same_interest_users = community_data_instance.get_users_by_gender_and_interest(gender_filter, user_interest, me)

    # Copias con el estado de seguimiento del visitante (no se toca la caché compartida)
    similar_users = [{**u, 'is_following': u['user_id'] in following_ids}
                     for u in same_interest_users if u['user_id'] != me]

    recommended_users = community_data_instance.get_user_recommendations(user_id) if is_own_profile else []
    is_following = user_id in following_ids
    followed_by_them = (not is_own_profile) and community_data_instance.is_following(user_id, me)

    posts = [] if blocked_by_me else community_data_instance.get_feed(me, author_id=user_id, limit=30)

    return render_template(
        'profile.html',
        user=user_data,
        profile_info=profile_info,
        similar_users=similar_users,
        user_posts=posts,
        recommended_users=recommended_users,
        post_count=community_data_instance.get_post_count(user_id),
        follower_count=community_data_instance.get_follower_count(user_id),
        following_count=community_data_instance.get_following_count(user_id),
        is_own_profile=is_own_profile,
        is_following=is_following,
        can_chat=is_following and followed_by_them,
        blocked_by_me=blocked_by_me,
        me=me,
    )


@app.route('/get_second_interest/<int:user_id>', methods=['GET'])
@login_required
def get_second_interest_endpoint(user_id):
    second_interest = community_data_instance.get_second_interest(user_id)
    if second_interest:
        return jsonify({"success": True, "second_interest": second_interest})
    return jsonify({"success": False, "message": "Este usuario no tiene un segundo interés."})


## Filtra usuarios de la comunidad por género/país
@app.route('/filter_users', methods=['GET'])
@login_required
def filter_users():
    gender = request.args.get('gender')
    country = request.args.get('country')
    profile_user_id = request.args.get('profile_user_id', type=int)
    me = current_user_id()

    user_data, _ = community_data_instance.get_user_profile(profile_user_id)
    user_interest = user_data['interest'] if user_data else None
    following_ids = community_data_instance.get_following_ids(me)

    filtered_users = [
        {"user_id": u["user_id"], "name": u["name"], "profile_image": u["profile_image"],
         "is_following": u["user_id"] in following_ids}
        for u in list(community_data_instance.user_groups.values())
        if (not gender or u["gender"] == gender)
        and (not country or u.get("country") == country)
        and (not user_interest or u["interest"] == user_interest)
        and u["user_id"] not in (profile_user_id, me)
    ]
    return jsonify({"filtered_users": filtered_users})


@app.route('/get_filter_counts_for_profile/<int:profile_user_id>', methods=['GET'])
@login_required
def get_filter_counts_for_profile(profile_user_id):
    return jsonify(community_data_instance.get_filter_counts_for_profile(profile_user_id))


# ---------------------------------------------------------------------------
# Ajustes de cuenta (perfil + contraseña)
# ---------------------------------------------------------------------------
@app.route('/settings', methods=['GET'])
@login_required
def settings():
    me = current_user_id()
    return render_template('settings.html', info=profiles_service.get_profile(engine, me) or {},
                           interest_options=profiles_service.list_interest_names(engine),
                           genders=profiles_service.VALID_GENDERS)


@app.route('/settings/profile', methods=['POST'])
@login_required
def settings_profile():
    me = current_user_id()
    f = request.form
    name = (f.get('display_name') or '').strip()
    gender = (f.get('gender') or '').strip()
    chosen = [i for i in dict.fromkeys(f.getlist('interests')) if i][:3]
    valid_interests = {i.lower() for i in profiles_service.list_interest_names(engine)}

    if not name or len(name) > 255:
        flash('El nombre es obligatorio (máximo 255 caracteres).', 'error')
        return redirect(url_for('settings'))
    if gender and gender not in profiles_service.VALID_GENDERS:
        flash('Género no válido.', 'error')
        return redirect(url_for('settings'))
    if not chosen or any(i.lower() not in valid_interests for i in chosen):
        flash('Elige entre 1 y 3 intereses de la lista.', 'error')
        return redirect(url_for('settings'))

    fields = {
        'display_name': name, 'gender': gender or None,
        'bio': (f.get('bio') or '').strip()[:500] or None,
        'city': (f.get('city') or '').strip()[:255] or None,
        'country': (f.get('country') or '').strip()[:255] or None,
        'birth_date': parse_date((f.get('birth_date') or '').strip() or None),
    }
    try:
        avatar = save_image(request.files.get('avatar'), f'avatar{me}')
    except ValueError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('settings'))
    if avatar:
        old = (profiles_service.get_profile(engine, me) or {}).get('avatar_url')
        fields['avatar_url'] = avatar
        delete_stored_file(old)

    profiles_service.update_profile(engine, me, interests_list=chosen, **fields)
    community_data_instance.refresh_user(me)  # el grafo y las búsquedas ven el cambio al instante
    flash('Perfil actualizado.', 'success')
    return redirect(url_for('settings'))


@app.route('/settings/password', methods=['POST'])
@login_required
def settings_password():
    f = request.form
    if f.get('new_password') != f.get('confirm_password'):
        flash('Las contraseñas nuevas no coinciden.', 'error')
        return redirect(url_for('settings') + '#password')
    try:
        change_password(engine, current_user_id(), f.get('current_password'), f.get('new_password'))
    except AuthError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('settings') + '#password')
    flash('Contraseña actualizada.', 'success')
    return redirect(url_for('settings'))


# ---------------------------------------------------------------------------
# Publicaciones
# ---------------------------------------------------------------------------
@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    user_id = current_user_id()
    user_data, _ = community_data_instance.get_user_profile(user_id)

    if request.method == 'POST':
        content = (request.form.get('content') or '').strip()
        if not content:
            return render_template('post_form.html', error="Escribe algo para publicar.", user=user_data), 400
        if len(content) > MAX_POST_LEN:
            return render_template('post_form.html', error=f"Máximo {MAX_POST_LEN} caracteres.",
                                   user=user_data, content=content), 400
        try:
            image_path = save_image(request.files.get('image'), str(user_id))
        except ValueError as exc:
            return render_template('post_form.html', error=str(exc), user=user_data, content=content), 400
        except Exception:
            return render_template('post_form.html', error="Error al guardar la imagen. Intente nuevamente.",
                                   user=user_data, content=content), 500

        try:
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO posts (UserID, Content, Image, PostDate)
                    VALUES (:user_id, :content, :image, NOW())
                """), {"user_id": user_id, "content": content, "image": image_path})
        except Exception:
            delete_stored_file(image_path)
            return render_template('post_form.html', error="Error al crear la publicación. Intente nuevamente.",
                                   user=user_data, content=content), 500

        flash('Publicación creada.', 'success')
        return redirect(url_for('index'))

    return render_template('post_form.html', user=user_data)


@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    user_id = current_user_id()
    with engine.connect() as connection:
        post = connection.execute(text("SELECT Image, UserID FROM posts WHERE PostID = :p"), {"p": post_id}).fetchone()
    if not post:
        return jsonify(success=False, error='La publicación no existe.'), 404
    if post.UserID != user_id:
        return jsonify(success=False, error='No puedes eliminar esta publicación.'), 403

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM posts WHERE PostID = :p"), {"p": post_id})
    delete_stored_file(post.Image)
    return jsonify(success=True)


@app.route('/home')
@login_required
def index():
    me = current_user_id()
    user_data, _ = community_data_instance.get_user_profile(me)
    offset = max(0, request.args.get('offset', 0, type=int))
    posts = community_data_instance.get_feed(me, limit=FEED_PAGE_SIZE + 1, offset=offset)
    has_more = len(posts) > FEED_PAGE_SIZE
    posts = posts[:FEED_PAGE_SIZE]

    if request.args.get('partial'):  # "Cargar más": devuelve solo las tarjetas
        html = render_template('partials/post_cards.html', posts=posts, me=me)
        return jsonify(html=html, has_more=has_more, next_offset=offset + len(posts))

    return render_template('home.html', posts=posts, user=user_data, has_more=has_more,
                           next_offset=offset + len(posts), me=me)


@app.route('/get_comments/<int:post_id>', methods=['GET'])
@login_required
def get_comments(post_id):
    return jsonify(community_data_instance.get_comments_for_post(post_id))


@app.route('/like_post/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    user_id = current_user_id()
    owner_id = social_service.get_post_owner(engine, post_id)
    if not owner_id:
        return jsonify(success=False, error='La publicación no existe.'), 404
    already_liked = community_data_instance.is_post_liked(post_id, user_id)
    community_data_instance.like_post(post_id, user_id)
    if not already_liked:
        social_service.notify(engine, owner_id, user_id, 'like', 'post', post_id)
    return jsonify({"success": True, "like_count": community_data_instance.get_like_count(post_id)})


@app.route('/unlike_post/<int:post_id>', methods=['POST'])
@login_required
def unlike_post(post_id):
    community_data_instance.unlike_post(post_id, current_user_id())
    return jsonify({"success": True, "like_count": community_data_instance.get_like_count(post_id)})


@app.route('/add_comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    content = (request.form.get('comment_content') or '').strip()
    user_id = current_user_id()
    if not content:
        return jsonify(success=False, error="Escribe un comentario."), 400
    if len(content) > MAX_COMMENT_LEN:
        return jsonify(success=False, error=f"Máximo {MAX_COMMENT_LEN} caracteres."), 400
    owner_id = social_service.get_post_owner(engine, post_id)
    if not owner_id:
        return jsonify(success=False, error="La publicación no existe."), 404

    community_data_instance.add_comment(post_id, user_id, content)
    social_service.notify(engine, owner_id, user_id, 'comment', 'post', post_id)
    return jsonify({"success": True, "comment_count": len(community_data_instance.get_comments_for_post(post_id))})


# ---------------------------------------------------------------------------
# Seguidores
# ---------------------------------------------------------------------------
def _user_list_response(title, users, me, mode, owner):
    for u in users:
        u['is_following'] = community_data_instance.is_following(me, u['user_id'])
        if mode == 'followers':
            u['follows_me'] = community_data_instance.is_following(u['user_id'], me)
    ctx = dict(users=users, mode=mode, me=me, owner=owner, title=title)
    if request.args.get('modal'):
        return render_template('partials/user_list.html', **ctx)
    return render_template('user_list.html', **ctx)


@app.route('/followers/<int:user_id>')
@login_required
def followers(user_id):
    owner, _ = community_data_instance.get_user_profile(user_id)
    if not owner:
        return not_found(None)
    return _user_list_response('Seguidores', community_data_instance.get_followers(user_id, current_user_id()),
                               current_user_id(), 'followers', owner)


@app.route('/following/<int:user_id>')
@login_required
def following(user_id):
    owner, _ = community_data_instance.get_user_profile(user_id)
    if not owner:
        return not_found(None)
    return _user_list_response('Seguidos', community_data_instance.get_following(user_id, current_user_id()),
                               current_user_id(), 'following', owner)


@app.route('/follow/<int:user_id>', methods=['POST'])
@login_required
def follow(user_id):
    follower_id = current_user_id()
    if follower_id == user_id:
        return jsonify(success=False, error="No puedes seguirte a ti mismo.")
    if not community_data_instance.get_user_profile(user_id)[0]:
        return jsonify(success=False, error="El usuario no existe."), 404
    if social_service.is_blocked_between(engine, follower_id, user_id):
        return jsonify(success=False, error="No puedes seguir a este usuario.")

    if community_data_instance.follow_user(follower_id, user_id):
        social_service.notify(engine, user_id, follower_id, 'follow', 'user', follower_id)
        return jsonify(success=True, follower_count=community_data_instance.get_follower_count(user_id),
                       mutual=community_data_instance.is_following(user_id, follower_id))
    return jsonify(success=False, error="No se pudo seguir al usuario.")


@app.route('/unfollow/<int:user_id>', methods=['POST'])
@login_required
def unfollow(user_id):
    follower_id = current_user_id()
    if follower_id == user_id:
        return jsonify(success=False, error="No puedes dejar de seguirte a ti mismo.")
    if community_data_instance.unfollow_user(follower_id, user_id):
        return jsonify(success=True, follower_count=community_data_instance.get_follower_count(user_id))
    return jsonify(success=False, error="No se pudo dejar de seguir al usuario.")


# ---------------------------------------------------------------------------
# Búsqueda
# ---------------------------------------------------------------------------
@app.route('/search', methods=['GET'])
@login_required
def search():
    term = request.args.get('term', '').strip()
    me = current_user_id()
    results = []
    if term:
        following_ids = community_data_instance.get_following_ids(me)
        results = [{**u, 'is_following': u['user_id'] in following_ids}
                   for u in community_data_instance.search_users(term, exclude_id=me)]
    return render_template('search.html', term=term, results=results)


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------
@app.route('/chat')
@login_required
def chat():
    me = current_user_id()
    mutual_followers = community_data_instance.get_mutual_followers(me)
    unread = social_service.unread_by_sender(engine, me)
    for u in mutual_followers:
        u['unread'] = unread.get(u['user_id'], 0)
    mutual_followers.sort(key=lambda u: (-u['unread'], (u['name'] or '').lower()))

    selected_user_id = request.args.get('user_id', type=int)
    selected_user, messages = None, []

    if selected_user_id:
        selected_user = next((u for u in mutual_followers if u['user_id'] == selected_user_id), None)
        if not selected_user:
            flash('Solo puedes chatear con personas que se siguen mutuamente.', 'error')
            return redirect(url_for('chat'))
        social_service.mark_conversation_read(engine, me, selected_user_id)
        selected_user['unread'] = 0
        messages = community_data_instance.get_messages_between_users(me, selected_user_id)

    return render_template('chat.html', mutual_followers=mutual_followers, messages=messages,
                           selected_user=selected_user, selected_user_id=selected_user_id, me=me)


@app.route('/chat/read/<int:user_id>', methods=['POST'])
@login_required
def chat_mark_read(user_id):
    social_service.mark_conversation_read(engine, current_user_id(), user_id)
    return jsonify(success=True)


@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    sender_id = current_user_id()
    receiver_id = request.form.get('receiver_id', type=int)
    content = (request.form.get('content') or '').strip()
    image_file = request.files.get('image')

    if not receiver_id or not are_mutual_followers(sender_id, receiver_id):
        return jsonify(success=False, error="Solo puedes escribir a quienes se siguen mutuamente."), 403
    if social_service.is_blocked_between(engine, sender_id, receiver_id):
        return jsonify(success=False, error="No puedes enviar mensajes a este usuario."), 403
    if len(content) > MAX_MESSAGE_LEN:
        return jsonify(success=False, error=f"Máximo {MAX_MESSAGE_LEN} caracteres."), 400
    if not content and not (image_file and image_file.filename):
        return jsonify(success=False, error="El mensaje está vacío."), 400

    try:
        image_path = save_image(image_file, f'chat{sender_id}')
    except ValueError as exc:
        return jsonify(success=False, error=str(exc)), 400

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO messages (sender_id, receiver_id, content, image, sent_at)
            VALUES (:sender_id, :receiver_id, :content, :image, NOW())
        """), {"sender_id": sender_id, "receiver_id": receiver_id, "content": content or None, "image": image_path})

    social_service.notify(engine, receiver_id, sender_id, 'message', 'user', sender_id)

    socketio.emit('receive_message', {
        'sender_id': sender_id,
        'receiver_id': receiver_id,
        'content': content,
        'image': image_path,
        'profile_image': g.user['profile_image'] if g.user else None,
        'sent_at': iso_utc(utc_now())
    }, room=chat_room(sender_id, receiver_id))

    return jsonify(success=True)


@socketio.on('join')
def on_join(data):
    """Une al usuario autenticado a la sala de su conversación (solo con seguidores mutuos)."""
    me = current_user_id()
    other = (data or {}).get('selected_user_id')
    if me and isinstance(other, int) and are_mutual_followers(me, other):
        join_room(chat_room(me, other))


@app.route('/get_messages/<int:user_id>', methods=['GET'])
@login_required
def get_messages(user_id):
    me = current_user_id()
    if not are_mutual_followers(me, user_id):
        return jsonify({"error": "You need to follow each other to chat"}), 403
    return jsonify([
        {"sender_id": m["sender_id"], "receiver_id": m["receiver_id"], "content": m["content"],
         "image": m["image"], "sent_at": iso_utc(m["sent_at"])}
        for m in community_data_instance.get_messages_between_users(me, user_id)
    ])


@app.route('/storage/<path:filename>')
def serve_image(filename):
    return send_from_directory(STORAGE_FOLDER, filename)


if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
