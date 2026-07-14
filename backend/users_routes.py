"""
Rotas de gestão de usuários (logins) e perfis de acesso.
"""
import re

from flask import Blueprint, request, session, jsonify
from werkzeug.security import generate_password_hash

from config import PERM_AREAS, ALL_PERMS, ADMIN_PROFILE_ID, EMAIL_RE
from storage import load_users, save_users, load_profiles, save_profiles
from security import require_perm

bp = Blueprint("users", __name__)


# ── Usuários ──────────────────────────────────────────────────────────────────
def _public_user(username, user):
    profiles = load_profiles()
    pid = user.get("profile", ADMIN_PROFILE_ID)
    return {
        "username": username,
        "name": user.get("name", username),
        "email": user.get("email", ""),
        "profile": pid,
        "profile_name": profiles.get(pid, {}).get("name", pid),
    }


def _norm_username(raw):
    return (raw or "").strip().lower()


@bp.route("/api/users", methods=["GET"])
@require_perm("sistema")
def list_users():
    users = load_users()
    data = [_public_user(u, users[u]) for u in sorted(users)]
    return jsonify(data)


@bp.route("/api/users", methods=["POST"])
@require_perm("sistema")
def create_user():
    data = request.get_json(silent=True) or {}
    username = _norm_username(data.get("username"))
    name = (data.get("name") or "").strip() or username
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    profile = (data.get("profile") or ADMIN_PROFILE_ID).strip()

    if not username or not username.replace("_", "").replace(".", "").isalnum():
        return jsonify({"error": "Usuário inválido (use letras, números, '.' ou '_')"}), 400
    if not email or not EMAIL_RE.match(email):
        return jsonify({"error": "Informe um e-mail válido"}), 400
    if len(password) < 6:
        return jsonify({"error": "A senha deve ter ao menos 6 caracteres"}), 400
    if profile not in load_profiles():
        return jsonify({"error": "Perfil de acesso inválido"}), 400

    users = load_users()
    if username in users:
        return jsonify({"error": "Já existe um usuário com esse nome"}), 409

    users[username] = {
        "password_hash": generate_password_hash(password),
        "name": name,
        "email": email,
        "profile": profile,
        "must_change": False,
    }
    save_users(users)
    return jsonify(_public_user(username, users[username])), 201


@bp.route("/api/users/<username>", methods=["PUT"])
@require_perm("sistema")
def update_user(username):
    username = _norm_username(username)
    data = request.get_json(silent=True) or {}
    users = load_users()
    user = users.get(username)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    if "name" in data and data["name"].strip():
        user["name"] = data["name"].strip()
    if data.get("email"):
        email = data["email"].strip().lower()
        if not EMAIL_RE.match(email):
            return jsonify({"error": "Informe um e-mail válido"}), 400
        user["email"] = email
    if "profile" in data and data["profile"]:
        if data["profile"] not in load_profiles():
            return jsonify({"error": "Perfil de acesso inválido"}), 400
        user["profile"] = data["profile"]
    new_password = data.get("password")
    if new_password:
        if len(new_password) < 6:
            return jsonify({"error": "A senha deve ter ao menos 6 caracteres"}), 400
        user["password_hash"] = generate_password_hash(new_password)
        user["must_change"] = False

    save_users(users)
    return jsonify(_public_user(username, user))


@bp.route("/api/users/<username>", methods=["DELETE"])
@require_perm("sistema")
def delete_user(username):
    username = _norm_username(username)
    users = load_users()
    if username not in users:
        return jsonify({"error": "Usuário não encontrado"}), 404
    if username == session.get("user"):
        return jsonify({"error": "Você não pode remover o próprio usuário"}), 400
    if len(users) <= 1:
        return jsonify({"error": "Não é possível remover o último usuário"}), 400
    del users[username]
    save_users(users)
    return jsonify({"status": "removed"})


# ── Perfis de acesso (CRUD) ───────────────────────────────────────────────────
def _profile_id(raw):
    pid = re.sub(r"[^a-z0-9_]+", "_", (raw or "").strip().lower()).strip("_")
    return pid


@bp.route("/api/perm-areas", methods=["GET"])
@require_perm("sistema")
def list_perm_areas():
    return jsonify(PERM_AREAS)


@bp.route("/api/profiles", methods=["GET"])
@require_perm("sistema")
def list_profiles():
    profiles = load_profiles()
    users = load_users()
    out = []
    for pid in sorted(profiles):
        p = profiles[pid]
        in_use = sum(1 for u in users.values() if u.get("profile") == pid)
        out.append({
            "id": pid, "name": p.get("name", pid),
            "perms": [a for a in p.get("perms", []) if a in PERM_AREAS],
            "in_use": in_use,
            "locked": pid == ADMIN_PROFILE_ID,
        })
    return jsonify(out)


@bp.route("/api/profiles", methods=["POST"])
@require_perm("sistema")
def create_profile():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    pid = _profile_id(data.get("id") or name)
    perms = [a for a in (data.get("perms") or []) if a in PERM_AREAS]
    if not name:
        return jsonify({"error": "Informe o nome do perfil"}), 400
    if not pid:
        return jsonify({"error": "Identificador de perfil inválido"}), 400
    profiles = load_profiles()
    if pid in profiles:
        return jsonify({"error": "Já existe um perfil com esse identificador"}), 409
    profiles[pid] = {"name": name, "perms": perms}
    save_profiles(profiles)
    return jsonify({"id": pid, "name": name, "perms": perms}), 201


@bp.route("/api/profiles/<pid>", methods=["PUT"])
@require_perm("sistema")
def update_profile(pid):
    data = request.get_json(silent=True) or {}
    profiles = load_profiles()
    prof = profiles.get(pid)
    if not prof:
        return jsonify({"error": "Perfil não encontrado"}), 404
    if "name" in data and data["name"].strip():
        prof["name"] = data["name"].strip()
    if "perms" in data:
        perms = [a for a in (data.get("perms") or []) if a in PERM_AREAS]
        # O perfil administrador sempre mantém todas as permissões
        if pid == ADMIN_PROFILE_ID:
            perms = list(ALL_PERMS)
        prof["perms"] = perms
    save_profiles(profiles)
    return jsonify({"id": pid, "name": prof["name"], "perms": prof["perms"]})


@bp.route("/api/profiles/<pid>", methods=["DELETE"])
@require_perm("sistema")
def delete_profile(pid):
    if pid == ADMIN_PROFILE_ID:
        return jsonify({"error": "O perfil Administrador não pode ser removido"}), 400
    profiles = load_profiles()
    if pid not in profiles:
        return jsonify({"error": "Perfil não encontrado"}), 404
    users = load_users()
    if any(u.get("profile") == pid for u in users.values()):
        return jsonify({"error": "Há usuários usando este perfil. Reatribua-os antes de remover."}), 400
    del profiles[pid]
    save_profiles(profiles)
    return jsonify({"status": "removed"})
