"""Contexto PROFILES: lo que otros ven de una persona (datos públicos e intereses)."""
from sqlalchemy import (BigInteger, Column, Date, DateTime, ForeignKey, Integer, SmallInteger,
                        String, Table, text, func)
from shared.metadata import TABLE_OPTS, metadata

profiles = Table(
    'profiles', metadata,
    Column('user_id', BigInteger, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('display_name', String(255), nullable=False),
    Column('bio', String(500)),
    Column('gender', String(20)),
    Column('birth_date', Date),
    Column('city', String(255)),
    Column('country', String(255)),
    Column('avatar_url', String(255)),
    Column('updated_at', DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'),
           onupdate=func.current_timestamp()),
    **TABLE_OPTS,
)

interests = Table(
    'interests', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', String(100), nullable=False, unique=True),
    **TABLE_OPTS,
)

# position = 0 es el interés principal (el que usa el grafo de comunidades)
profile_interests = Table(
    'profile_interests', metadata,
    Column('user_id', BigInteger, ForeignKey('profiles.user_id', ondelete='CASCADE'), primary_key=True),
    Column('interest_id', Integer, ForeignKey('interests.id', ondelete='CASCADE'), primary_key=True),
    Column('position', SmallInteger, nullable=False, server_default='0'),
    **TABLE_OPTS,
)
