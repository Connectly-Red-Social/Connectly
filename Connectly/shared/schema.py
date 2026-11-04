"""Creación y evolución automática del esquema (todas las tablas de todos los contextos)."""
from sqlalchemy import inspect, text
from sqlalchemy.schema import AddConstraint, CreateColumn

from shared.metadata import metadata

# Importar los modelos registra sus tablas en `metadata`.
import contexts.users.models      # noqa: F401
import contexts.iam.models        # noqa: F401
import contexts.profiles.models   # noqa: F401
import contexts.social.models     # noqa: F401

COMPAT_VIEW = 'social_media_users'


def create_tables(engine):
    """Crea lo que falte y añade columnas nuevas a tablas ya existentes (solo aditivo)."""
    metadata.create_all(engine)  # checkfirst: no toca lo que ya existe
    _ensure_columns(engine)


def _ensure_columns(engine):
    prep = engine.dialect.identifier_preparer
    inspector = inspect(engine)
    for table in metadata.sorted_tables:
        existing = {c['name'] for c in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name not in existing:
                ddl = str(CreateColumn(column).compile(dialect=engine.dialect))
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE {prep.format_table(table)} ADD COLUMN {ddl}"))
                print(f"[schema] Columna añadida: {table.name}.{column.name}")


def ensure_foreign_keys(engine):
    """Añade las FK que falten (p. ej. en tablas creadas antes de existir `users`)."""
    inspector = inspect(engine)
    for table in metadata.sorted_tables:
        existing = {(tuple(fk['constrained_columns']), fk['referred_table'])
                    for fk in inspector.get_foreign_keys(table.name)}
        for fkc in table.foreign_key_constraints:
            key = (tuple(c.name for c in fkc.columns), fkc.referred_table.name)
            if key in existing:
                continue
            try:
                with engine.begin() as conn:
                    conn.execute(AddConstraint(fkc))
                print(f"[schema] FK añadida: {table.name}{list(key[0])} -> {key[1]}")
            except Exception as exc:  # noqa: BLE001  (p. ej. filas huérfanas)
                print(f"[schema] No se pudo añadir la FK {table.name}{list(key[0])} -> {key[1]}: {exc}")


def create_compat_view(engine):
    """Vista de SOLO LECTURA con la forma de la antigua tabla `social_media_users`.

    Es el modelo de lectura que consumen el grafo de comunidades y las recomendaciones
    (contexts/community) mientras sus consultas se migran a las tablas de cada contexto.
    """
    ddl = f"""
    CREATE OR REPLACE VIEW {COMPAT_VIEW} AS
    SELECT u.id                AS UserID,
           p.display_name      AS Name,
           p.gender            AS Gender,
           p.birth_date        AS DOB,
           COALESCE((SELECT GROUP_CONCAT(CONCAT('''', i.name, '''') ORDER BY pi.position SEPARATOR ', ')
                       FROM profile_interests pi
                       JOIN interests i ON i.id = pi.interest_id
                      WHERE pi.user_id = u.id), '') AS Interests,
           p.city              AS City,
           p.country           AS Country,
           u.username          AS username,
           p.avatar_url        AS profile_image,
           u.email             AS email
      FROM users u
      JOIN profiles p ON p.user_id = u.id
     WHERE u.status = 'active'
    """
    with engine.begin() as conn:
        conn.execute(text(ddl))
