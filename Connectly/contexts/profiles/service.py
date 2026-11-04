"""Servicio del contexto PROFILES."""
from sqlalchemy import delete, insert, select, update

from contexts.profiles.models import interests, profile_interests, profiles
from shared.db import chunks

VALID_GENDERS = ('Male', 'Female', 'Other')
_EDITABLE = {'display_name', 'bio', 'gender', 'birth_date', 'city', 'country', 'avatar_url'}


def default_avatar(gender: str, user_id: int) -> str:
    folder = 'men' if (gender or '').lower() == 'male' else 'women'
    return f"https://randomuser.me/api/portraits/{folder}/{user_id % 99 + 1}.jpg"


def _clean(names) -> list:
    """Quita vacíos y duplicados (sin distinguir mayúsculas) conservando el orden."""
    seen, out = set(), []
    for n in names or []:
        n = (n or '').strip(" '\"")
        if n and n.lower() not in seen:
            seen.add(n.lower())
            out.append(n)
    return out


def ensure_interests(conn, names) -> dict:
    """Crea los intereses que falten. Devuelve {nombre_en_minúsculas: id}."""
    names = _clean(names)
    if not names:
        return {}
    existing = {r.name.lower(): r.id for r in conn.execute(select(interests.c.id, interests.c.name))}
    missing = [{'name': n} for n in names if n.lower() not in existing]
    for chunk in chunks(missing):
        conn.execute(insert(interests), chunk)
    if missing:
        existing = {r.name.lower(): r.id for r in conn.execute(select(interests.c.id, interests.c.name))}
    return existing


def bulk_create(conn, rows: list):
    """rows: [{'user_id','display_name','gender','birth_date','city','country','avatar_url','bio','interests':[...]}]"""
    if not rows:
        return
    profile_rows = [{k: v for k, v in r.items() if k != 'interests'} for r in rows]
    for chunk in chunks(profile_rows):
        conn.execute(insert(profiles), chunk)

    id_by_name = ensure_interests(conn, [n for r in rows for n in r.get('interests', [])])
    links = [
        {'user_id': r['user_id'], 'interest_id': id_by_name[n.lower()], 'position': pos}
        for r in rows for pos, n in enumerate(_clean(r.get('interests')))
    ]
    for chunk in chunks(links):
        conn.execute(insert(profile_interests), chunk)


def create_profile(conn, user_id: int, display_name: str, interests_list=(), **fields):
    row = {'user_id': user_id, 'display_name': display_name, 'interests': list(interests_list)}
    row.update({k: v for k, v in fields.items() if k in _EDITABLE})
    bulk_create(conn, [row])


def set_interests(conn, user_id: int, names):
    id_by_name = ensure_interests(conn, names)
    conn.execute(delete(profile_interests).where(profile_interests.c.user_id == user_id))
    links = [{'user_id': user_id, 'interest_id': id_by_name[n.lower()], 'position': pos}
             for pos, n in enumerate(_clean(names))]
    if links:
        conn.execute(insert(profile_interests), links)


def get_profile(engine, user_id: int):
    with engine.connect() as conn:
        row = conn.execute(select(profiles).where(profiles.c.user_id == user_id)).mappings().first()
        if not row:
            return None
        names = conn.execute(
            select(interests.c.name)
            .join(profile_interests, profile_interests.c.interest_id == interests.c.id)
            .where(profile_interests.c.user_id == user_id)
            .order_by(profile_interests.c.position)
        ).scalars().all()
        return {**row, 'interests': names}


def update_profile(engine, user_id: int, interests_list=None, **fields) -> bool:
    values = {k: v for k, v in fields.items() if k in _EDITABLE}
    with engine.begin() as conn:
        if values:
            conn.execute(update(profiles).where(profiles.c.user_id == user_id).values(**values))
        if interests_list is not None:
            set_interests(conn, user_id, interests_list)
    return True


def list_interest_names(engine) -> list:
    with engine.connect() as conn:
        return conn.execute(select(interests.c.name).order_by(interests.c.name)).scalars().all()


def count_profiles(engine) -> int:
    from sqlalchemy import func
    with engine.connect() as conn:
        return conn.execute(select(func.count()).select_from(profiles)).scalar()
