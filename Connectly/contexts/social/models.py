"""Contexto SOCIAL: publicaciones, interacciones, seguimiento, mensajes y moderación.

Los nombres de las tablas/columnas heredadas (posts, post_likes, comments, user_follows,
messages) se conservan para no romper las consultas existentes.
"""
from sqlalchemy import (BigInteger, Boolean, Column, DateTime, ForeignKey, Index, Integer,
                        String, Table, Text, text, func)
from shared.metadata import TABLE_OPTS, metadata

_NOW = text('CURRENT_TIMESTAMP')
_USER = 'users.id'

posts = Table(
    'posts', metadata,
    Column('PostID', Integer, primary_key=True, autoincrement=True),
    Column('UserID', BigInteger, ForeignKey(_USER, ondelete='CASCADE'), nullable=False, index=True),
    Column('Content', Text),
    Column('Image', String(255)),
    Column('PostDate', DateTime, nullable=False),
    Column('updated_at', DateTime),
    **TABLE_OPTS,
)

post_likes = Table(
    'post_likes', metadata,
    Column('PostID', Integer, ForeignKey('posts.PostID', ondelete='CASCADE'), primary_key=True),
    Column('UserID', BigInteger, ForeignKey(_USER, ondelete='CASCADE'), primary_key=True, index=True),
    Column('LikeDate', DateTime, server_default=_NOW),
    **TABLE_OPTS,
)

comments = Table(
    'comments', metadata,
    Column('CommentID', Integer, primary_key=True, autoincrement=True),
    Column('PostID', Integer, ForeignKey('posts.PostID', ondelete='CASCADE'), nullable=False, index=True),
    Column('UserID', BigInteger, ForeignKey(_USER, ondelete='CASCADE'), nullable=False, index=True),
    Column('Content', Text, nullable=False),
    Column('CommentDate', DateTime, server_default=_NOW),
    **TABLE_OPTS,
)

user_follows = Table(
    'user_follows', metadata,
    Column('follower_id', BigInteger, ForeignKey(_USER, ondelete='CASCADE'), primary_key=True),
    Column('followed_id', BigInteger, ForeignKey(_USER, ondelete='CASCADE'), primary_key=True, index=True),
    Column('follow_date', DateTime, nullable=False, server_default=_NOW),
    **TABLE_OPTS,
)

messages = Table(
    'messages', metadata,
    Column('message_id', Integer, primary_key=True, autoincrement=True),
    Column('sender_id', BigInteger, ForeignKey(_USER, ondelete='CASCADE'), nullable=False, index=True),
    Column('receiver_id', BigInteger, ForeignKey(_USER, ondelete='CASCADE'), nullable=False, index=True),
    Column('content', Text),
    Column('image', String(255)),
    Column('sent_at', DateTime, nullable=False),
    Column('read_at', DateTime),
    **TABLE_OPTS,
)

blocks = Table(
    'blocks', metadata,
    Column('blocker_id', BigInteger, ForeignKey(_USER, ondelete='CASCADE'), primary_key=True),
    Column('blocked_id', BigInteger, ForeignKey(_USER, ondelete='CASCADE'), primary_key=True, index=True),
    Column('created_at', DateTime, nullable=False, server_default=_NOW),
    **TABLE_OPTS,
)

notifications = Table(
    'notifications', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', BigInteger, ForeignKey(_USER, ondelete='CASCADE'), nullable=False),   # destinatario
    Column('actor_id', BigInteger, ForeignKey(_USER, ondelete='CASCADE'), nullable=False),  # quien la provoca
    Column('type', String(30), nullable=False),          # follow | like | comment | message
    Column('entity_type', String(30)),                   # post | comment | user
    Column('entity_id', BigInteger),
    Column('is_read', Boolean, nullable=False, server_default=text('0')),
    Column('created_at', DateTime, nullable=False, server_default=_NOW),
    Index('idx_notifications_user_unread', 'user_id', 'is_read', 'created_at'),
    **TABLE_OPTS,
)

reports = Table(
    'reports', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('reporter_id', BigInteger, ForeignKey(_USER, ondelete='CASCADE'), nullable=False),
    Column('target_type', String(20), nullable=False),   # user | post | comment
    Column('target_id', BigInteger, nullable=False),
    Column('reason', String(255), nullable=False),
    Column('status', String(20), nullable=False, server_default='open'),  # open | reviewed | dismissed
    Column('created_at', DateTime, nullable=False, server_default=_NOW),
    Column('resolved_at', DateTime),
    Column('resolved_by', BigInteger, ForeignKey(_USER, ondelete='SET NULL')),
    Index('idx_reports_status', 'status', 'created_at'),
    **TABLE_OPTS,
)
