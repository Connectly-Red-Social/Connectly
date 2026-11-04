"""Servicio del contexto USERS. Las funciones con `conn` participan en la transacción del llamador."""
from sqlalchemy import insert, or_, select, update
from contexts.users.models import users
from shared.db import chunks


def create_user(conn, username: str, email: str = None, user_id: int = None, status: str = 'active') -> int:
    values = {'username': username, 'email': email, 'status': status}
    if user_id is not None:
        values['id'] = user_id
    result = conn.execute(insert(users).values(**values))
    return user_id if user_id is not None else int(result.inserted_primary_key[0])


def bulk_create(conn, rows: list):
    """rows: [{'id', 'username', 'email'}]. Conserva los ids recibidos."""
    for chunk in chunks(rows):
        conn.execute(insert(users), chunk)


def find_conflict(conn, username: str, email: str = None):
    """Devuelve 'username', 'email' o None según qué dato ya está en uso."""
    cond = [users.c.username == username]
    if email:
        cond.append(users.c.email == email)
    row = conn.execute(select(users.c.username, users.c.email).where(or_(*cond)).limit(1)).first()
    if not row:
        return None
    return 'username' if (row.username or '').lower() == username.lower() else 'email'


def get_by_id(conn, user_id: int):
    return conn.execute(select(users).where(users.c.id == user_id)).mappings().first()


def set_status(conn, user_id: int, status: str):
    conn.execute(update(users).where(users.c.id == user_id).values(status=status))
