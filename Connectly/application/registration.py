"""Caso de uso: registrar una cuenta nueva.

Coordina tres contextos en UNA transacción: USERS (cuenta), IAM (credenciales + rol)
y PROFILES (perfil + intereses). Si algo falla, no queda nada a medias.
"""
import re

from sqlalchemy.exc import IntegrityError

from contexts.iam import service as iam
from contexts.profiles import service as profiles
from contexts.users import service as users

USERNAME_RE = re.compile(r'^[A-Za-z0-9_.]{3,30}$')
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
MIN_PASSWORD_LEN = 8
RESERVED_USERNAMES = {'admin', 'administrator', 'root', 'support'}


class RegistrationError(Exception):
    """Error de validación mostrable al usuario."""


def validate_registration(form) -> dict:
    data = {
        'name': (form.get('name') or '').strip(),
        'username': (form.get('username') or '').strip(),
        'email': (form.get('email') or '').strip().lower(),
        'gender': (form.get('gender') or '').strip(),
        'interest': (form.get('interest') or '').strip(),
        'country': (form.get('country') or '').strip() or 'Unknown',
        'password': form.get('password') or '',
    }
    confirm = form.get('confirm_password') or ''

    required = ('name', 'username', 'email', 'gender', 'interest', 'password')
    if any(not data[k] for k in required) or not confirm:
        raise RegistrationError('Todos los campos obligatorios deben completarse.')
    if not USERNAME_RE.match(data['username']):
        raise RegistrationError('El usuario debe tener 3-30 caracteres (letras, números, "_" o ".").')
    if not EMAIL_RE.match(data['email']) or len(data['email']) > 255:
        raise RegistrationError('El correo electrónico no es válido.')
    if data['gender'] not in profiles.VALID_GENDERS:
        raise RegistrationError('Género no válido.')
    if len(data['password']) < MIN_PASSWORD_LEN:
        raise RegistrationError(f'La contraseña debe tener al menos {MIN_PASSWORD_LEN} caracteres.')
    if data['password'] != confirm:
        raise RegistrationError('Las contraseñas no coinciden.')
    if data['username'].lower() in RESERVED_USERNAMES:
        raise RegistrationError('Ese nombre de usuario no está disponible.')
    return data


def register_user(engine, form) -> int:
    """Valida y crea usuario + credenciales + rol + perfil. Devuelve el nuevo user_id."""
    data = validate_registration(form)
    try:
        with engine.begin() as conn:
            conflict = users.find_conflict(conn, data['username'], data['email'])
            if conflict == 'username':
                raise RegistrationError('Ese nombre de usuario ya está en uso.')
            if conflict == 'email':
                raise RegistrationError('Ese correo electrónico ya está registrado.')

            user_id = users.create_user(conn, data['username'], data['email'])
            iam.set_password(conn, user_id, data['password'])
            iam.assign_role(conn, user_id, iam.ROLE_MEMBER)
            profiles.create_profile(
                conn, user_id, data['name'], [data['interest']],
                gender=data['gender'], country=data['country'],
                avatar_url=profiles.default_avatar(data['gender'], user_id),
            )
    except IntegrityError:  # carrera entre dos registros simultáneos
        raise RegistrationError('Ese usuario o correo ya está registrado.')
    return user_id
