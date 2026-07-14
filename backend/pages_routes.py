"""
Páginas do frontend: admin (protegido), login, reset, display das TVs
e arquivos estáticos.
"""
import os

from flask import Blueprint, jsonify, redirect, send_from_directory, abort
from werkzeug.utils import secure_filename

from config import FRONTEND_DIR
from security import login_required

bp = Blueprint("pages", __name__)

# Páginas públicas. admin.html é protegido; a documentação vive em docs/
# e não é servida pelo servidor.
PUBLIC_PAGES = {"display.html", "login.html", "reset.html"}


@bp.route("/")
def index():
    return redirect("/admin")


@bp.route("/tela/<slug>")
def tela(slug):
    # URL amigável das TVs → display com o slug correspondente
    safe = secure_filename(slug) or "principal"
    return redirect(f"/display.html?tv={safe}")


@bp.route("/admin")
@bp.route("/admin.html")
@login_required
def admin_page():
    return send_from_directory(FRONTEND_DIR, "admin.html")


@bp.route("/login")
@bp.route("/login.html")
def login_page():
    return send_from_directory(FRONTEND_DIR, "login.html")


@bp.route("/reset")
@bp.route("/reset.html")
def reset_page():
    return send_from_directory(FRONTEND_DIR, "reset.html")


@bp.route("/<path:filename>")
def static_files(filename):
    base = filename.split("/")[0]
    if base == "admin.html":
        return redirect("/admin")
    if filename in PUBLIC_PAGES or filename.endswith((".css", ".js", ".png", ".jpg",
                                                       ".svg", ".ico", ".woff", ".woff2")):
        full = os.path.join(FRONTEND_DIR, filename)
        if os.path.isfile(full):
            return send_from_directory(FRONTEND_DIR, filename)
    abort(404)


@bp.app_errorhandler(413)
def too_large(e):
    return jsonify({"error": "Arquivo excede o limite de 300 MB"}), 413
