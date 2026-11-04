"""Rutas web del contexto SOCIAL (bloqueos, notificaciones y reportes)."""
from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from contexts.social import service as social

bp = Blueprint('social', __name__)
_engine = None


def init_app(app, engine):
    global _engine
    _engine = engine
    app.register_blueprint(bp)


def _current_user():
    return session.get('user_id') if isinstance(session.get('user_id'), int) else None


@bp.route('/block/<int:user_id>', methods=['POST'])
def block(user_id):
    me = _current_user()
    if not me:
        return jsonify(success=False, error='No autenticado.'), 401
    try:
        social.block_user(_engine, me, user_id)
    except social.SocialError as exc:
        return jsonify(success=False, error=str(exc)), 400
    return jsonify(success=True)


@bp.route('/unblock/<int:user_id>', methods=['POST'])
def unblock(user_id):
    me = _current_user()
    if not me:
        return jsonify(success=False, error='No autenticado.'), 401
    social.unblock_user(_engine, me, user_id)
    return jsonify(success=True)


@bp.route('/report', methods=['POST'])
def report():
    me = _current_user()
    if not me:
        return jsonify(success=False, error='No autenticado.'), 401
    try:
        social.create_report(_engine, me, request.form.get('target_type'),
                             request.form.get('target_id', type=int) or 0, request.form.get('reason'))
    except social.SocialError as exc:
        return jsonify(success=False, error=str(exc)), 400
    return jsonify(success=True)


@bp.route('/notifications', methods=['GET'])
def notifications():
    me = _current_user()
    if not me:
        return jsonify(error='No autenticado.'), 401
    return jsonify(unread=social.unread_count(_engine, me), items=social.list_notifications(_engine, me))


@bp.route('/notifications/read', methods=['POST'])
def notifications_read():
    me = _current_user()
    if not me:
        return jsonify(success=False, error='No autenticado.'), 401
    social.mark_notifications_read(_engine, me)
    return jsonify(success=True)


@bp.route('/admin/reports', methods=['GET'])
def admin_reports():
    if not session.get('is_admin'):
        return jsonify(error='Prohibido.'), 403
    return jsonify(social.list_open_reports(_engine))


@bp.route('/admin_reports', methods=['GET'])
def admin_reports_page():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    status = request.args.get('status', 'open')
    if status not in ('open', 'reviewed', 'dismissed', 'all'):
        status = 'open'
    return render_template('admin_reports.html', reports=social.list_reports_detailed(_engine, status), status=status)


@bp.route('/admin/reports/<int:report_id>/resolve', methods=['POST'])
def admin_resolve_report(report_id):
    if not session.get('is_admin'):
        return jsonify(success=False, error='Prohibido.'), 403
    try:
        social.resolve_report(_engine, report_id, session['user_id'], request.form.get('status'))
    except social.SocialError as exc:
        return jsonify(success=False, error=str(exc)), 400
    return jsonify(success=True)
