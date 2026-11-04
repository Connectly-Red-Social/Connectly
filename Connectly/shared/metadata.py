"""MetaData único del esquema. Cada bounded context registra aquí sus tablas."""
from sqlalchemy import BigInteger, Integer, MetaData

metadata = MetaData()

TABLE_OPTS = {
    'mysql_engine': 'InnoDB',
    'mysql_charset': 'utf8mb4',
    'mysql_collate': 'utf8mb4_unicode_ci',
}

# BIGINT autoincremental en MySQL (INTEGER en SQLite para que autoincremente).
ID_TYPE = BigInteger().with_variant(Integer, 'sqlite')
