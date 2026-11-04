"""Contexto IAM: autenticación, credenciales, roles y auditoría de accesos."""
from sqlalchemy import (BigInteger, Boolean, Column, DateTime, ForeignKey, Index, Integer,
                        String, Table, text, func)
from shared.metadata import TABLE_OPTS, metadata

credentials = Table(
    'credentials', metadata,
    Column('user_id', BigInteger, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('password_hash', String(255), nullable=False),
    Column('updated_at', DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'),
           onupdate=func.current_timestamp()),
    **TABLE_OPTS,
)

roles = Table(
    'roles', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', String(50), nullable=False, unique=True),
    Column('description', String(255)),
    **TABLE_OPTS,
)

user_roles = Table(
    'user_roles', metadata,
    Column('user_id', BigInteger, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    **TABLE_OPTS,
)

login_attempts = Table(
    'login_attempts', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('username', String(255), nullable=False),
    Column('user_id', BigInteger, ForeignKey('users.id', ondelete='SET NULL')),
    Column('ip_address', String(45)),
    Column('success', Boolean, nullable=False, server_default=text('0')),
    Column('attempted_at', DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP')),
    Index('idx_login_attempts_user_time', 'username', 'attempted_at'),
    **TABLE_OPTS,
)
