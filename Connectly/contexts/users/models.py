"""Contexto USERS: la cuenta de una persona en la plataforma (identidad básica)."""
from sqlalchemy import Column, DateTime, String, Table, text, func
from shared.metadata import ID_TYPE, TABLE_OPTS, metadata

users = Table(
    'users', metadata,
    Column('id', ID_TYPE, primary_key=True, autoincrement=True),
    Column('username', String(100), nullable=False, unique=True),
    Column('email', String(255), unique=True),
    Column('status', String(20), nullable=False, server_default='active'),  # active | suspended | deleted
    Column('created_at', DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP')),
    Column('updated_at', DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'),
           onupdate=func.current_timestamp()),
    **TABLE_OPTS,
)
