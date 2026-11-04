"""Migración de bases antiguas donde `social_media_users` era una tabla real.

Copia sus filas a USERS/IAM/PROFILES conservando los UserID, reapunta las FK de posts,
likes, comentarios, follows y mensajes a `users`, y deja la tabla vieja como
`legacy_social_media_users` (copia de seguridad; no se borra).
"""
from sqlalchemy import func, select, text

from contexts.profiles.models import profiles
from shared.schema import COMPAT_VIEW
from shared.seed import insert_people, parse_date, parse_interests
from contexts.iam import service as iam
from contexts.profiles import service as profiles_service

BACKUP_TABLE = 'legacy_social_media_users'


def is_legacy_users_table(engine) -> bool:
    with engine.connect() as conn:
        kind = conn.execute(text(
            "SELECT TABLE_TYPE FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t"), {'t': COMPAT_VIEW}).scalar()
    return kind == 'BASE TABLE'


def _people_from_legacy(rows) -> list:
    people, usernames, emails = [], set(), set()
    for r in rows:
        uid = int(r['UserID'])
        username = (r.get('username') or f'user{uid}').strip()
        if username.lower() in usernames:
            username = f'{username}_{uid}'
        usernames.add(username.lower())

        email = (r.get('email') or '').strip().lower() or None
        if email in emails:
            email = None
        if email:
            emails.add(email)

        stored = r.get('password')
        people.append({
            'id': uid, 'username': username, 'email': email,
            'password_hash': iam.to_hash(stored) if stored else None,
            'display_name': r.get('Name') or username, 'gender': r.get('Gender'),
            'birth_date': parse_date(r.get('DOB')), 'city': r.get('City'), 'country': r.get('Country'),
            'avatar_url': r.get('profile_image') or profiles_service.default_avatar(r.get('Gender'), uid),
            'interests': parse_interests(r.get('Interests')),
        })
    return people


def migrate(engine):
    """Precondición: las tablas nuevas ya existen (schema.create_tables)."""
    # 1) Copiar datos (una sola transacción: o entra todo o nada, y es reintentable)
    with engine.begin() as conn:
        if not conn.execute(select(func.count()).select_from(profiles)).scalar():
            rows = conn.execute(text(f'SELECT * FROM {COMPAT_VIEW}')).mappings().all()
            n = insert_people(conn, _people_from_legacy([dict(r) for r in rows]))
            print(f'[legacy] {n} usuarios migrados a users/credentials/profiles.')

    # 2) Soltar las FK que apuntan a la tabla vieja y apartarla
    with engine.begin() as conn:
        fks = conn.execute(text(
            "SELECT TABLE_NAME, CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE "
            "WHERE TABLE_SCHEMA = DATABASE() AND REFERENCED_TABLE_NAME = :t"), {'t': COMPAT_VIEW}).all()
        for table, constraint in fks:
            conn.execute(text(f'ALTER TABLE `{table}` DROP FOREIGN KEY `{constraint}`'))
        conn.execute(text(f'RENAME TABLE {COMPAT_VIEW} TO {BACKUP_TABLE}'))
    print(f'[legacy] Tabla antigua conservada como {BACKUP_TABLE}.')
