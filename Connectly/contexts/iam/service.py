"""Servicio IAM: contraseñas, autenticación, bloqueo por intentos y roles."""
import os
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import func, insert, or_, select, update
from werkzeug.security import check_password_hash, generate_password_hash

from contexts.iam.models import credentials, login_attempts, roles, user_roles
from contexts.users.models import users
from contexts.users import service as users_service
from shared.db import chunks
from shared.timeutil import utc_now

try:
    from werkzeug.security import DEFAULT_PBKDF2_ITERATIONS
except ImportError:  # versiones antiguas de werkzeug
    DEFAULT_PBKDF2_ITERATIONS = 600_000

ROLE_MEMBER = 'member'
ROLE_ADMIN = 'admin'
ROLES = {ROLE_MEMBER: 'Usuario normal', ROLE_ADMIN: 'Administrador de la plataforma'}

MAX_FAILED_ATTEMPTS = 5
LOCK_WINDOW = timedelta(minutes=15)
GENERIC_ERROR = 'Usuario o contraseña incorrectos.'
LOCKED_ERROR = 'Demasiados intentos fallidos. Intenta de nuevo en unos minutos.'

# Hash barato SOLO para cuentas de demostración sembradas en lote; se mejora en el primer login.
_CHEAP_METHOD = 'pbkdf2:sha256:1000'


class AuthError(Exception):
    """Fallo de autenticación mostrable al usuario."""


@dataclass(frozen=True)
class Identity:
    user_id: int
    username: str
    roles: tuple

    @property
    def is_admin(self) -> bool:
        return ROLE_ADMIN in self.roles


# ---------- contraseñas ----------
def hash_password(password: str, cheap: bool = False) -> str:
    return generate_password_hash(password, method=_CHEAP_METHOD if cheap else 'pbkdf2:sha256')


def to_hash(stored: str) -> str:
    """Datos heredados: conserva un hash existente o convierte texto plano en hash."""
    if stored.startswith(('pbkdf2:', 'scrypt:')):
        return stored
    return hash_password(stored, cheap=True)


def needs_rehash(password_hash: str) -> bool:
    if password_hash.startswith('scrypt:'):
        return False
    try:
        return int(password_hash.split('$', 1)[0].split(':')[2]) < DEFAULT_PBKDF2_ITERATIONS
    except (IndexError, ValueError):
        return True


def set_password(conn, user_id: int, password: str):
    conn.execute(insert(credentials).values(user_id=user_id, password_hash=hash_password(password)))


def bulk_set_credentials(conn, rows: list):
    """rows: [{'user_id', 'password_hash'}]."""
    for chunk in chunks(rows):
        conn.execute(insert(credentials), chunk)


# ---------- roles ----------
def ensure_roles(engine):
    with engine.begin() as conn:
        existing = {r[0] for r in conn.execute(select(roles.c.name))}
        missing = [{'name': n, 'description': d} for n, d in ROLES.items() if n not in existing]
        if missing:
            conn.execute(insert(roles), missing)


def _role_id(conn, role_name: str) -> int:
    return conn.execute(select(roles.c.id).where(roles.c.name == role_name)).scalar_one()


def assign_role(conn, user_id: int, role_name: str):
    bulk_assign_role(conn, [user_id], role_name)


def bulk_assign_role(conn, user_ids: list, role_name: str):
    role_id = _role_id(conn, role_name)
    rows = [{'user_id': uid, 'role_id': role_id} for uid in user_ids]
    for chunk in chunks(rows):
        conn.execute(insert(user_roles), chunk)


def get_roles(conn, user_id: int) -> tuple:
    q = select(roles.c.name).join(user_roles, user_roles.c.role_id == roles.c.id).where(user_roles.c.user_id == user_id)
    return tuple(r[0] for r in conn.execute(q))


# ---------- autenticación ----------
def authenticate(engine, identifier: str, password: str, ip: str = None) -> Identity:
    """Valida usuario (o correo) y contraseña. Lanza AuthError si falla."""
    identifier = (identifier or '').strip()
    if not identifier or not password:
        raise AuthError(GENERIC_ERROR)

    key = identifier.lower()[:255]
    now = utc_now()
    error, identity = None, None

    with engine.begin() as conn:
        failures = conn.execute(
            select(func.count()).select_from(login_attempts).where(
                login_attempts.c.username == key,
                login_attempts.c.success == False,  # noqa: E712
                login_attempts.c.attempted_at > now - LOCK_WINDOW,
            )
        ).scalar()

        if failures >= MAX_FAILED_ATTEMPTS:
            error = LOCKED_ERROR
        else:
            row = conn.execute(
                select(users.c.id, users.c.username, users.c.status, credentials.c.password_hash)
                .select_from(users.outerjoin(credentials, credentials.c.user_id == users.c.id))
                .where(or_(users.c.username == identifier, users.c.email == key))
                .limit(1)
            ).first()

            ok = bool(row and row.password_hash and row.status == 'active'
                      and check_password_hash(row.password_hash, password))
            conn.execute(insert(login_attempts).values(
                username=key, user_id=row.id if row else None, ip_address=ip, success=ok, attempted_at=now))

            if ok:
                if needs_rehash(row.password_hash):
                    conn.execute(update(credentials).where(credentials.c.user_id == row.id)
                                 .values(password_hash=hash_password(password)))
                identity = Identity(int(row.id), row.username, get_roles(conn, row.id))
            else:
                error = GENERIC_ERROR

    if error:  # se lanza fuera del bloque para que el intento quede registrado
        raise AuthError(error)
    return identity


# ---------- administrador inicial ----------
def ensure_admin(engine):
    """Garantiza que exista al menos un administrador (credenciales por variables de entorno)."""
    with engine.begin() as conn:
        role_id = _role_id(conn, ROLE_ADMIN)
        if conn.execute(select(func.count()).select_from(user_roles).where(user_roles.c.role_id == role_id)).scalar():
            return
        username = os.getenv('ADMIN_USERNAME', 'admin')
        password = os.getenv('ADMIN_PASSWORD')
        if not password:
            password = 'admin'
            print('[iam] ADMIN_PASSWORD no definida: se usa la contraseña por defecto "admin". Defínela en producción.')
        if users_service.find_conflict(conn, username):
            print(f'[iam] No se creó el administrador: el usuario "{username}" ya existe.')
            return
        admin_id = users_service.create_user(conn, username)
        set_password(conn, admin_id, password)
        assign_role(conn, admin_id, ROLE_ADMIN)
        print(f'[iam] Administrador "{username}" creado.')


# ---------- cambio de contraseña ----------
MIN_PASSWORD_LEN = 8


def change_password(engine, user_id: int, current_password: str, new_password: str):
    """Cambia la contraseña verificando la actual. Lanza AuthError con un mensaje mostrable."""
    if len(new_password or '') < MIN_PASSWORD_LEN:
        raise AuthError(f'La nueva contraseña debe tener al menos {MIN_PASSWORD_LEN} caracteres.')
    with engine.begin() as conn:
        current = conn.execute(select(credentials.c.password_hash).where(credentials.c.user_id == user_id)).scalar()
        if not current or not check_password_hash(current, current_password or ''):
            raise AuthError('La contraseña actual no es correcta.')
        conn.execute(update(credentials).where(credentials.c.user_id == user_id)
                     .values(password_hash=hash_password(new_password)))
