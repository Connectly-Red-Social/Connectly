"""Fábrica central del engine de SQLAlchemy (driver PyMySQL, pool resiliente)."""
import os
from sqlalchemy import create_engine

# Respaldo para desarrollo local; en Render se define DATABASE_URL.
LOCAL_DB_URL = 'mysql+pymysql://root:Nicolas20@localhost:3306/connectly'


def normalize_db_url(url: str) -> str:
    """Convierte cualquier URL MySQL a la sintaxis mysql+pymysql://."""
    for prefix in ('mysql+mysqlconnector://', 'mysql://'):
        if url.startswith(prefix):
            return 'mysql+pymysql://' + url[len(prefix):]
    return url


def get_db_url() -> str:
    return normalize_db_url(os.getenv('DATABASE_URL') or LOCAL_DB_URL)


def make_engine(db_url: str = None):
    # pool_pre_ping: verifica la conexión antes de usarla (evita error 2013).
    # pool_recycle: renueva conexiones antes de que el servidor las cierre.
    return create_engine(
        normalize_db_url(db_url or get_db_url()),
        pool_pre_ping=True,
        pool_recycle=280,
        # init_command: toda sesión en UTC, así NOW() es igual en local y en Render
        connect_args={'charset': 'utf8mb4', 'init_command': "SET time_zone='+00:00'"},
    )


def chunks(items, size=500):
    for i in range(0, len(items), size):
        yield items[i:i + size]
