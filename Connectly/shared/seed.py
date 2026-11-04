"""Carga inicial del dataset (idempotente) y carga masiva común a seed y migración legacy.

El CSV deja de ser una entidad: sus filas se reparten entre USERS, IAM y PROFILES.
"""
import os
from datetime import date

import pandas as pd
from sqlalchemy import func, select

from contexts.iam import service as iam
from contexts.profiles import service as profiles
from contexts.profiles.models import profiles as profiles_table
from contexts.users import service as users

SEED_LIMIT = 1500
DEFAULT_CSV = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'SocialMediaUsersDataset.csv')


def parse_interests(raw) -> list:
    """"'Movies', 'Fashion'" -> ['Movies', 'Fashion']"""
    if raw is None or (not isinstance(raw, str) and pd.isna(raw)):
        return []
    return [p.strip(" '\"") for p in str(raw).split(', ') if p.strip(" '\"")]


def parse_date(value):
    if value is None or (not isinstance(value, (str, date)) and pd.isna(value)):
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def insert_people(conn, people: list) -> int:
    """Inserta personas en USERS + IAM + PROFILES dentro de la transacción recibida.

    people: [{'id','username','email','password_hash'|None,'display_name','gender','birth_date',
              'city','country','avatar_url','interests':[...]}]
    """
    if not people:
        return 0
    users.bulk_create(conn, [{'id': p['id'], 'username': p['username'], 'email': p.get('email')} for p in people])
    iam.bulk_set_credentials(conn, [{'user_id': p['id'], 'password_hash': p['password_hash']}
                                    for p in people if p.get('password_hash')])
    iam.bulk_assign_role(conn, [p['id'] for p in people], iam.ROLE_MEMBER)
    profiles.bulk_create(conn, [{
        'user_id': p['id'], 'display_name': p['display_name'], 'gender': p.get('gender'),
        'birth_date': p.get('birth_date'), 'city': p.get('city'), 'country': p.get('country'),
        'avatar_url': p.get('avatar_url'), 'interests': p.get('interests', []),
    } for p in people])
    return len(people)


def _csv_to_people(df: pd.DataFrame) -> list:
    df = df.dropna(subset=['UserID', 'Name', 'Gender', 'Interests'])
    people = []
    for r in df.itertuples(index=False):
        uid = int(r.UserID)
        username = f"{str(r.Name).split()[0]}{uid}"
        people.append({
            'id': uid, 'username': username, 'email': None,
            # Cuentas de demostración: contraseña = usuario. Hash barato, se refuerza en el primer login.
            'password_hash': iam.hash_password(username, cheap=True),
            'display_name': r.Name, 'gender': r.Gender, 'birth_date': parse_date(r.DOB),
            'city': None if pd.isna(r.City) else r.City,
            'country': None if pd.isna(r.Country) else r.Country,
            'avatar_url': profiles.default_avatar(r.Gender, uid),
            'interests': parse_interests(r.Interests),
        })
    return people


def seed_dataset(engine, csv_path: str = None, limit: int = SEED_LIMIT) -> int:
    """Carga el CSV solo si no hay ningún perfil. Devuelve el número de personas insertadas."""
    with engine.connect() as conn:
        if conn.execute(select(func.count()).select_from(profiles_table)).scalar():
            print('[seed] Ya existen perfiles; se omite la carga del dataset.')
            return 0

    path = os.path.abspath(csv_path or os.getenv('SEED_CSV_PATH') or DEFAULT_CSV)
    if not os.path.exists(path):
        print(f'[seed] No se encontró el dataset en {path}; se omite la carga.')
        return 0

    people = _csv_to_people(pd.read_csv(path).head(limit))
    with engine.begin() as conn:
        insert_people(conn, people)
    print(f'[seed] {len(people)} personas cargadas desde {os.path.basename(path)}.')
    return len(people)
