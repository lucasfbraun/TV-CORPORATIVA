"""
Rotas de autenticação: login, logout, sessão, troca e redefinição de senha.
"""
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from config import log, ADMIN_PROFILE_ID, EMAIL_RE
from storage import (
    load_users, save_users, load_profiles, profile_perms,
    load_resets, save_resets,
)
from security import login_required
from mailer import load_smtp, public_smtp, send_email

bp = Blueprint("auth", __name__)

RESET_TTL_MIN = 60  # validade do link de redefinição em minutos


@bp.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    ident = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""
    users = load_users()
    # Aceita login pelo nome de usuário OU pelo e-mail cadastrado
    username = ident
    user = users.get(ident)
    if not user and ident:
        for uname, u in users.items():
            if (u.get("email") or "").strip().lower() == ident:
                username, user = uname, u
                break
    if user and check_password_hash(user["password_hash"], password):
        session.permanent = True
        session["user"] = username
        return jsonify({
            "status": "ok",
            "name": user.get("name", username),
            "must_change": user.get("must_change", False),
            "profile": user.get("profile", ADMIN_PROFILE_ID),
            "perms": profile_perms(user.get("profile")),
        })
    return jsonify({"error": "Usuário ou senha inválidos"}), 401


@bp.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"status": "ok"})


@bp.route("/api/session", methods=["GET"])
def api_session():
    username = session.get("user")
    if not username:
        return jsonify({"authenticated": False})
    users = load_users()
    user = users.get(username, {})
    profiles = load_profiles()
    pid = user.get("profile", ADMIN_PROFILE_ID)
    return jsonify({
        "authenticated": True,
        "user": username,
        "name": user.get("name", username),
        "email": user.get("email", ""),
        "must_change": user.get("must_change", False),
        "profile": pid,
        "profile_name": profiles.get(pid, {}).get("name", pid),
        "perms": profile_perms(pid),
    })


@bp.route("/api/change-password", methods=["POST"])
@login_required
def api_change_password():
    data = request.get_json(silent=True) or {}
    current = data.get("current_password") or ""
    new = data.get("new_password") or ""
    if len(new) < 6:
        return jsonify({"error": "A nova senha deve ter ao menos 6 caracteres"}), 400
    users = load_users()
    username = session["user"]
    user = users.get(username)
    if not user or not check_password_hash(user["password_hash"], current):
        return jsonify({"error": "Senha atual incorreta"}), 401
    user["password_hash"] = generate_password_hash(new)
    user["must_change"] = False
    save_users(users)
    return jsonify({"status": "ok"})


# ── Esqueci a senha (token + e-mail de redefinição) ───────────────────────────
def _prune_resets(d):
    now = datetime.utcnow().timestamp()
    return {t: v for t, v in d.items() if v.get("exp", 0) > now}


@bp.route("/api/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True) or {}
    ident = (data.get("identifier") or "").strip().lower()
    users = load_users()
    # localiza por login ou por e-mail
    target = None
    if ident in users:
        target = ident
    else:
        for uname, u in users.items():
            if (u.get("email") or "").strip().lower() == ident and ident:
                target = uname
                break
    # Resposta sempre genérica (não revela se o usuário existe)
    generic = {"status": "ok",
               "message": "Se o usuário existir e tiver e-mail cadastrado, enviaremos um link de redefinição."}
    if not target:
        return jsonify(generic)
    user = users[target]
    email = (user.get("email") or "").strip()
    if not email:
        return jsonify(generic)
    if not public_smtp(load_smtp())["configured"]:
        return jsonify({"error": "Envio de e-mail não está configurado. Contate a TI."}), 503

    token = secrets.token_urlsafe(32)
    resets = _prune_resets(load_resets())
    resets[token] = {"user": target,
                     "exp": (datetime.utcnow() + timedelta(minutes=RESET_TTL_MIN)).timestamp()}
    save_resets(resets)

    base = request.host_url.rstrip("/")
    link = f"{base}/reset?token={token}"
    html = (
        f"<p>Olá, {user.get('name', target)}.</p>"
        f"<p>Recebemos um pedido para redefinir a senha do seu acesso ao painel <b>TV Corporativa</b>.</p>"
        f"<p><a href=\"{link}\">Clique aqui para criar uma nova senha</a>. "
        f"O link expira em {RESET_TTL_MIN} minutos.</p>"
        f"<p>Se você não fez este pedido, ignore este e-mail.</p>"
    )
    try:
        send_email(email, "Redefinição de senha — TV Corporativa", html)
    except Exception as e:  # noqa: BLE001
        log.warning("Falha ao enviar e-mail de redefinição: %s", e)
        return jsonify({"error": "Não foi possível enviar o e-mail. Contate a TI."}), 502
    return jsonify(generic)


@bp.route("/api/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}
    token = (data.get("token") or "").strip()
    new = data.get("new_password") or ""
    if len(new) < 6:
        return jsonify({"error": "A nova senha deve ter ao menos 6 caracteres"}), 400
    resets = _prune_resets(load_resets())
    entry = resets.get(token)
    if not entry:
        return jsonify({"error": "Link inválido ou expirado. Solicite um novo."}), 400
    users = load_users()
    user = users.get(entry["user"])
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    user["password_hash"] = generate_password_hash(new)
    user["must_change"] = False
    save_users(users)
    del resets[token]
    save_resets(resets)
    log.info("Senha redefinida via link para o usuário '%s'. Login pode ser feito com o usuário ou o e-mail.", entry["user"])
    return jsonify({"status": "ok"})
