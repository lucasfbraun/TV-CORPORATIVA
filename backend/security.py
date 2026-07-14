"""
Decoradores de autenticação/autorização e utilidades de sessão.
"""
from functools import wraps

from flask import request, session, jsonify, redirect, url_for

from storage import load_users, profile_perms


def login_required(fn):
    """Protege rotas de escrita / administração."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Não autenticado"}), 401
            return redirect(url_for("pages.login_page", next=request.path))
        return fn(*args, **kwargs)
    return wrapper


def current_perms():
    """Permissões do usuário logado (lista de áreas)."""
    username = session.get("user")
    if not username:
        return []
    user = load_users().get(username)
    if not user:
        return []
    return profile_perms(user.get("profile"))


def require_perm(area):
    """Protege rotas que exigem uma permissão de área específica."""
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not session.get("user"):
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Não autenticado"}), 401
                return redirect(url_for("pages.login_page", next=request.path))
            if area not in current_perms():
                return jsonify({"error": "Você não tem permissão para esta ação"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return deco
