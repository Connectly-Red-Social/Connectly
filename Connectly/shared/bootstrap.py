"""Preparación automática de la base de datos al arrancar la aplicación."""
from sqlalchemy import text

from contexts.iam import service as iam
from shared import legacy_migration, schema, seed

_LOCK_NAME = 'connectly_bootstrap'


def bootstrap_database(engine):
    """Esquema + datos iniciales. Un lock de MySQL evita carreras entre workers de gunicorn."""
    with engine.connect() as lock_conn:
        lock_conn.execute(text('SELECT GET_LOCK(:n, 120)'), {'n': _LOCK_NAME})
        try:
            _run(engine)
        finally:
            lock_conn.execute(text('SELECT RELEASE_LOCK(:n)'), {'n': _LOCK_NAME})


def _run(engine):
    legacy = legacy_migration.is_legacy_users_table(engine)   # ¿base creada con el esquema antiguo?
    schema.create_tables(engine)                              # tablas/columnas que falten
    iam.ensure_roles(engine)
    if legacy:
        legacy_migration.migrate(engine)                      # copia datos y aparta la tabla vieja
    else:
        seed.seed_dataset(engine)                             # solo si no hay perfiles
    schema.ensure_foreign_keys(engine)                        # reapunta FK a users(id)
    schema.create_compat_view(engine)                         # vista social_media_users (solo lectura)
    iam.ensure_admin(engine)
