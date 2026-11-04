"""Servicio del contexto SOCIAL: bloqueos, notificaciones y reportes.

(Posts, likes, comentarios, follows y mensajes siguen en la clase CommunityData / app.py.)
"""
from sqlalchemy import and_, delete, func, insert, or_, select, update

from contexts.profiles.models import profiles
from shared.timeutil import iso_utc
from contexts.social.models import blocks, messages, notifications, posts, reports, user_follows

NOTIFICATION_TYPES = ('follow', 'like', 'comment', 'message')
REPORT_TARGETS = ('user', 'post', 'comment')


class SocialError(Exception):
    """Error de validación mostrable al usuario."""


# ---------- bloqueos ----------
def is_blocked_between(engine, user_a: int, user_b: int) -> bool:
    """True si cualquiera de los dos bloqueó al otro."""
    with engine.connect() as conn:
        return bool(conn.execute(
            select(func.count()).select_from(blocks).where(or_(
                and_(blocks.c.blocker_id == user_a, blocks.c.blocked_id == user_b),
                and_(blocks.c.blocker_id == user_b, blocks.c.blocked_id == user_a),
            ))
        ).scalar())


def block_user(engine, blocker_id: int, blocked_id: int):
    if blocker_id == blocked_id:
        raise SocialError('No puedes bloquearte a ti mismo.')
    with engine.begin() as conn:
        # Al bloquear se rompe cualquier relación de seguimiento en ambos sentidos.
        conn.execute(delete(user_follows).where(or_(
            and_(user_follows.c.follower_id == blocker_id, user_follows.c.followed_id == blocked_id),
            and_(user_follows.c.follower_id == blocked_id, user_follows.c.followed_id == blocker_id),
        )))
        exists = conn.execute(select(func.count()).select_from(blocks).where(
            blocks.c.blocker_id == blocker_id, blocks.c.blocked_id == blocked_id)).scalar()
        if not exists:
            conn.execute(insert(blocks).values(blocker_id=blocker_id, blocked_id=blocked_id))


def unblock_user(engine, blocker_id: int, blocked_id: int):
    with engine.begin() as conn:
        conn.execute(delete(blocks).where(blocks.c.blocker_id == blocker_id, blocks.c.blocked_id == blocked_id))


# ---------- notificaciones ----------
def notify(engine, user_id: int, actor_id: int, type_: str, entity_type: str = None, entity_id: int = None):
    """Crea una notificación (nunca para uno mismo). Un fallo aquí no debe romper la acción principal."""
    if type_ not in NOTIFICATION_TYPES or user_id == actor_id:
        return
    try:
        with engine.begin() as conn:
            conn.execute(insert(notifications).values(
                user_id=user_id, actor_id=actor_id, type=type_, entity_type=entity_type, entity_id=entity_id))
    except Exception as exc:  # noqa: BLE001
        print(f'[social] No se pudo crear la notificación: {exc}')


def list_notifications(engine, user_id: int, limit: int = 30) -> list:
    q = (select(notifications.c.id, notifications.c.type, notifications.c.entity_type, notifications.c.entity_id,
                notifications.c.is_read, notifications.c.created_at, notifications.c.actor_id,
                profiles.c.display_name.label('actor_name'), profiles.c.avatar_url.label('actor_image'))
         .select_from(notifications.outerjoin(profiles, profiles.c.user_id == notifications.c.actor_id))
         .where(notifications.c.user_id == user_id)
         .order_by(notifications.c.created_at.desc(), notifications.c.id.desc())
         .limit(limit))
    with engine.connect() as conn:
        return [{**r, 'created_at': iso_utc(r['created_at'])} for r in conn.execute(q).mappings()]


def unread_count(engine, user_id: int) -> int:
    with engine.connect() as conn:
        return conn.execute(select(func.count()).select_from(notifications).where(
            notifications.c.user_id == user_id, notifications.c.is_read == False)).scalar()  # noqa: E712


def mark_notifications_read(engine, user_id: int):
    with engine.begin() as conn:
        conn.execute(update(notifications).where(
            notifications.c.user_id == user_id, notifications.c.is_read == False).values(is_read=True))  # noqa: E712


# ---------- reportes ----------
def create_report(engine, reporter_id: int, target_type: str, target_id: int, reason: str):
    reason = (reason or '').strip()
    if target_type not in REPORT_TARGETS:
        raise SocialError('Tipo de reporte no válido.')
    if not reason:
        raise SocialError('Indica el motivo del reporte.')
    with engine.begin() as conn:
        conn.execute(insert(reports).values(
            reporter_id=reporter_id, target_type=target_type, target_id=target_id, reason=reason[:255]))


def list_open_reports(engine, limit: int = 100) -> list:
    with engine.connect() as conn:
        rows = conn.execute(select(reports).where(reports.c.status == 'open')
                            .order_by(reports.c.created_at.desc()).limit(limit)).mappings()
        return [{**r, 'created_at': r['created_at'].isoformat(), 'resolved_at': None} for r in rows]


# ---------- consultas auxiliares ----------
def get_post_owner(engine, post_id: int):
    with engine.connect() as conn:
        return conn.execute(select(posts.c.UserID).where(posts.c.PostID == post_id)).scalar()


# ---------- extras usados por el frontend ----------
def has_blocked(engine, blocker_id: int, blocked_id: int) -> bool:
    """True si `blocker_id` bloqueó a `blocked_id`."""
    with engine.connect() as conn:
        return bool(conn.execute(select(func.count()).select_from(blocks).where(
            blocks.c.blocker_id == blocker_id, blocks.c.blocked_id == blocked_id)).scalar())


def unread_by_sender(engine, user_id: int) -> dict:
    """{sender_id: mensajes_sin_leer} para el usuario."""
    with engine.connect() as conn:
        rows = conn.execute(select(messages.c.sender_id, func.count()).where(
            messages.c.receiver_id == user_id, messages.c.read_at.is_(None)).group_by(messages.c.sender_id))
        return {r[0]: r[1] for r in rows}


def mark_conversation_read(engine, me: int, other: int):
    with engine.begin() as conn:
        conn.execute(update(messages).where(
            messages.c.receiver_id == me, messages.c.sender_id == other, messages.c.read_at.is_(None)
        ).values(read_at=func.now()))
        # Las notificaciones de mensajes de esa persona dejan de estar pendientes.
        conn.execute(update(notifications).where(
            notifications.c.user_id == me, notifications.c.actor_id == other,
            notifications.c.type == 'message', notifications.c.is_read == False  # noqa: E712
        ).values(is_read=True))


def list_reports_detailed(engine, status: str = 'open', limit: int = 200) -> list:
    """Reportes con el nombre de quien reporta y del usuario/post objetivo, para el panel admin."""
    reporter = profiles.alias('reporter')
    q = (select(reports, reporter.c.display_name.label('reporter_name'))
         .select_from(reports.outerjoin(reporter, reporter.c.user_id == reports.c.reporter_id))
         .order_by(reports.c.created_at.desc()).limit(limit))
    if status != 'all':
        q = q.where(reports.c.status == status)
    with engine.connect() as conn:
        rows = [dict(r) for r in conn.execute(q).mappings()]
        for r in rows:
            r['target_label'] = None
            if r['target_type'] == 'user':
                r['target_label'] = conn.execute(select(profiles.c.display_name).where(
                    profiles.c.user_id == r['target_id'])).scalar()
                r['target_url'] = f"/profile/{r['target_id']}"
            elif r['target_type'] == 'post':
                owner = conn.execute(select(posts.c.UserID).where(posts.c.PostID == r['target_id'])).scalar()
                r['target_url'] = f"/profile/{owner}" if owner else None
            else:
                r['target_url'] = None
    return rows


def resolve_report(engine, report_id: int, admin_id: int, status: str):
    if status not in ('reviewed', 'dismissed'):
        raise SocialError('Estado no válido.')
    with engine.begin() as conn:
        conn.execute(update(reports).where(reports.c.id == report_id).values(
            status=status, resolved_at=func.now(), resolved_by=admin_id))
