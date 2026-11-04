"""Rutas web del contexto IAM: /login, /register y /logout.

Se registran con add_url_rule para conservar los nombres de endpoint ('login', 'register',
'logout') que usan las plantillas con url_for().
"""
from flask import redirect, render_template, request, session, url_for

from application.registration import RegistrationError, register_user
from contexts.iam.service import AuthError, authenticate
from contexts.profiles.service import VALID_GENDERS, count_profiles, list_interest_names


def init_app(app, engine):
    def _start_session(user_id: int, is_admin: bool):
        session.clear()
        session['user_id'] = user_id
        session['is_admin'] = is_admin
        session.permanent = True

    def _safe_next():
        target = request.values.get('next') or ''
        # Solo rutas internas (evita redirecciones abiertas a otros sitios)
        return target if target.startswith('/') and not target.startswith('//') else ''

    def login():
        ctx = {'next_url': _safe_next(), 'user_count': count_profiles(engine)}
        if request.method == 'POST':
            try:
                identity = authenticate(engine, request.form.get('username'), request.form.get('password'),
                                        ip=request.remote_addr)
            except AuthError as exc:
                return render_template('login.html', error=str(exc), **ctx), 401
            _start_session(identity.user_id, identity.is_admin)
            if identity.is_admin:
                return redirect(url_for('admin_dashboard'))
            return redirect(ctx['next_url'] or url_for('profile', user_id=identity.user_id))
        if session.get('user_id'):
            return redirect(url_for('admin_dashboard') if session.get('is_admin') else url_for('index'))
        return render_template('login.html', **ctx)

    def register():
        ctx = {'interests': list_interest_names(engine), 'genders': VALID_GENDERS, 'form': request.form,
               'user_count': count_profiles(engine)}
        if request.method == 'POST':
            try:
                user_id = register_user(engine, request.form)
            except RegistrationError as exc:
                return render_template('register.html', error=str(exc), **ctx), 400
            except Exception:  # noqa: BLE001
                app.logger.exception('Error registrando usuario')
                return render_template('register.html',
                                       error='No se pudo completar el registro. Intenta más tarde.', **ctx), 500
            _start_session(user_id, False)
            return redirect(url_for('profile', user_id=user_id))
        return render_template('register.html', **ctx)

    def logout():
        session.clear()
        return redirect(url_for('login'))

    app.add_url_rule('/login', 'login', login, methods=['GET', 'POST'])
    app.add_url_rule('/register', 'register', register, methods=['GET', 'POST'])
    app.add_url_rule('/logout', 'logout', logout)
