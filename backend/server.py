"""
TV Corporativa - Servidor Central
Grupo Flexível

Servidor Flask que centraliza o conteúdo exibido nas TVs e fornece o
painel de administração protegido por login.

Uso:
    pip install -r requirements.txt
    python backend/server.py

Acesso:
    Admin:   http://localhost:8080/admin        (exige login)
    Display: http://localhost:8080/tela/<slug>  (abrir nas TVs, modo kiosk)

Para outras máquinas na rede local, use o IP deste computador:
    http://192.168.X.X:8080/tela/recepcao

Primeiro acesso (credenciais padrão — TROQUE no primeiro login):
    usuário: admin
    senha:   flexivel
"""

import os
import json
import uuid
import secrets
import logging
import time
import urllib.request
import urllib.parse
from datetime import date
from functools import wraps

from flask import (
    Flask, send_from_directory, request, jsonify,
    session, redirect, url_for, abort,
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# ── Caminhos ──────────────────────────────────────────────────────────────────
BACKEND_DIR  = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR     = os.path.dirname(BACKEND_DIR)
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
DATA_DIR     = os.path.join(ROOT_DIR, "data")
UPLOADS_DIR  = os.path.join(ROOT_DIR, "uploads")

CONTENT_FILE = os.path.join(DATA_DIR, "content.json")
USERS_FILE   = os.path.join(DATA_DIR, "users.json")
SECRET_FILE  = os.path.join(DATA_DIR, "secret.key")

PORT = int(os.environ.get("TV_PORT", 8080))
HOST = os.environ.get("TV_HOST", "0.0.0.0")

# Upload: 300 MB máximo (suporta vídeos)
MAX_UPLOAD_BYTES = 300 * 1024 * 1024
# Tipos aceitos: PNG, JPG, JPEG, MP4 e PDF
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "mp4", "pdf"}

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("tv-server")

# ── Conteúdo padrão (modelo unificado: config / tvs / grades / rodapes) ────────
DEFAULT_CONTENT = {
    "config": {
        "company_name": "GRUPO FLEXÍVEL",
        "slide_duration": 12,
        "ticker_speed": 40,
    },
    "tvs": [
        {
            "id": "tv-001", "slug": "principal", "name": "TV Principal",
            "description": "Tela principal da empresa",
            "grade_id": "grade-001", "rodape_id": "rodape-001", "active": True,
        }
    ],
    "grades": [
        {
            "id": "grade-001", "name": "Grade Principal", "slide_duration": 12,
            "slides": [
                {
                    "id": 1, "type": "announcement", "active": True,
                    "icon": "📣", "badge": "Comunicado",
                    "title": "Bem-vindos à TV Corporativa!",
                    "body": "Configure o conteúdo pelo painel de administração.",
                    "author": "Equipe de TI",
                }
            ],
        }
    ],
    "rodapes": [
        {
            "id": "rodape-001", "name": "Rodapé Padrão", "ticker_speed": 40,
            "messages": [
                "Bem-vindos ao sistema de TV Corporativa",
                "Configure o conteúdo pelo painel de administração",
            ],
        }
    ],
}

# ══════════════════════════════════════════════════════════════════════════════
# PERSISTÊNCIA
# ══════════════════════════════════════════════════════════════════════════════
def _read_json(path, fallback):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            log.error("Falha ao ler %s: %s", path, e)
    return fallback


def _write_json(path, data):
    """Escrita atômica para não corromper o arquivo se cair no meio."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def load_content():
    return _read_json(CONTENT_FILE, DEFAULT_CONTENT)


def save_content(data):
    _write_json(CONTENT_FILE, data)


def get_secret_key():
    key = _read_json(SECRET_FILE, None)
    if key:
        return key
    key = secrets.token_hex(32)
    _write_json(SECRET_FILE, key)
    return key


def load_users():
    users = _read_json(USERS_FILE, None)
    if not users:
        # Cria usuário admin padrão no primeiro arranque
        users = {
            "admin": {
                "password_hash": generate_password_hash("flexivel"),
                "name": "Administrador",
                "must_change": True,
            }
        }
        _write_json(USERS_FILE, users)
        log.warning("Usuário 'admin' criado com senha padrão 'flexivel'. TROQUE no primeiro login.")
    return users


def save_users(users):
    _write_json(USERS_FILE, users)


# ══════════════════════════════════════════════════════════════════════════════
# APP
# ══════════════════════════════════════════════════════════════════════════════
app = Flask(__name__, static_folder=None)
app.secret_key = get_secret_key()
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES


def login_required(fn):
    """Protege rotas de escrita / administração."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Não autenticado"}), 401
            return redirect(url_for("login_page", next=request.path))
        return fn(*args, **kwargs)
    return wrapper


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Autenticação ──────────────────────────────────────────────────────────────
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""
    users = load_users()
    user = users.get(username)
    if user and check_password_hash(user["password_hash"], password):
        session.permanent = True
        session["user"] = username
        return jsonify({
            "status": "ok",
            "name": user.get("name", username),
            "must_change": user.get("must_change", False),
        })
    return jsonify({"error": "Usuário ou senha inválidos"}), 401


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"status": "ok"})


@app.route("/api/session", methods=["GET"])
def api_session():
    username = session.get("user")
    if not username:
        return jsonify({"authenticated": False})
    users = load_users()
    user = users.get(username, {})
    return jsonify({
        "authenticated": True,
        "user": username,
        "name": user.get("name", username),
        "must_change": user.get("must_change", False),
    })


@app.route("/api/change-password", methods=["POST"])
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


# ── Gestão de usuários (logins) ───────────────────────────────────────────────
def _public_user(username, user):
    return {"username": username, "name": user.get("name", username)}


def _norm_username(raw):
    return (raw or "").strip().lower()


@app.route("/api/users", methods=["GET"])
@login_required
def list_users():
    users = load_users()
    data = [_public_user(u, users[u]) for u in sorted(users)]
    return jsonify(data)


@app.route("/api/users", methods=["POST"])
@login_required
def create_user():
    data = request.get_json(silent=True) or {}
    username = _norm_username(data.get("username"))
    name = (data.get("name") or "").strip() or username
    password = data.get("password") or ""

    if not username or not username.replace("_", "").replace(".", "").isalnum():
        return jsonify({"error": "Usuário inválido (use letras, números, '.' ou '_')"}), 400
    if len(password) < 6:
        return jsonify({"error": "A senha deve ter ao menos 6 caracteres"}), 400

    users = load_users()
    if username in users:
        return jsonify({"error": "Já existe um usuário com esse nome"}), 409

    users[username] = {
        "password_hash": generate_password_hash(password),
        "name": name,
        "must_change": False,
    }
    save_users(users)
    return jsonify(_public_user(username, users[username])), 201


@app.route("/api/users/<username>", methods=["PUT"])
@login_required
def update_user(username):
    username = _norm_username(username)
    data = request.get_json(silent=True) or {}
    users = load_users()
    user = users.get(username)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    if "name" in data and data["name"].strip():
        user["name"] = data["name"].strip()
    new_password = data.get("password")
    if new_password:
        if len(new_password) < 6:
            return jsonify({"error": "A senha deve ter ao menos 6 caracteres"}), 400
        user["password_hash"] = generate_password_hash(new_password)
        user["must_change"] = False

    save_users(users)
    return jsonify(_public_user(username, user))


@app.route("/api/users/<username>", methods=["DELETE"])
@login_required
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


# ── Conteúdo (leitura pública, escrita protegida) ─────────────────────────────
@app.route("/api/content", methods=["GET"])
def get_content():
    return jsonify(load_content())


RATES_FILE = os.path.join(DATA_DIR, "rates.json")
RATES_URL = "https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL"


def fetch_rates():
    """Busca USD/BRL e EUR/BRL uma vez por dia, com cache em arquivo."""
    today = date.today().isoformat()
    cached = _read_json(RATES_FILE, None)
    if cached and cached.get("date") == today and cached.get("ok"):
        return cached

    try:
        req = urllib.request.Request(RATES_URL, headers={"User-Agent": "TV-Corporativa"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        result = {
            "ok": True,
            "date": today,
            "USD": round(float(raw["USDBRL"]["bid"]), 2),
            "EUR": round(float(raw["EURBRL"]["bid"]), 2),
        }
        _write_json(RATES_FILE, result)
        return result
    except Exception as e:  # noqa: BLE001
        log.warning("Falha ao buscar cotações: %s", e)
        if cached:  # devolve o último valor conhecido
            return {**cached, "stale": True}
        return {"ok": False, "USD": None, "EUR": None, "date": today}


@app.route("/api/rates", methods=["GET"])
def get_rates():
    return jsonify(fetch_rates())


# ── Previsão do tempo (Open-Meteo, sem chave de API) ──────────────────────────
WEATHER_FILE = os.path.join(DATA_DIR, "weather.json")
WMO_ICON = {
    0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️",
    45: "🌫️", 48: "🌫️",
    51: "🌦️", 53: "🌦️", 55: "🌧️", 56: "🌧️", 57: "🌧️",
    61: "🌦️", 63: "🌧️", 65: "🌧️", 66: "🌧️", 67: "🌧️",
    71: "🌨️", 73: "🌨️", 75: "❄️", 77: "❄️",
    80: "🌦️", 81: "🌧️", 82: "⛈️", 85: "🌨️", 86: "❄️",
    95: "⛈️", 96: "⛈️", 99: "⛈️",
}


def _http_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "TV-Corporativa"})
    with urllib.request.urlopen(req, timeout=6) as resp:
        return json.loads(resp.read().decode("utf-8"))


def geocode_city(q, count=5):
    """Retorna lista de localidades que batem com o nome (cidade, estado, país)."""
    q = (q or "").strip()
    if not q:
        return []
    geo = _http_json(
        f"https://geocoding-api.open-meteo.com/v1/search?count={count}&language=pt&format=json&name="
        + urllib.parse.quote(q)
    )
    out = []
    for r in (geo.get("results") or []):
        out.append({
            "name": r.get("name", ""),
            "admin1": r.get("admin1", ""),     # estado/região
            "country": r.get("country", ""),
            "lat": r["latitude"],
            "lon": r["longitude"],
        })
    return out


def _forecast(lat, lon):
    w = _http_json(
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,weather_code"
        "&daily=temperature_2m_max,temperature_2m_min&timezone=auto&forecast_days=1"
    )
    code = int(w["current"]["weather_code"])
    return {
        "temp": round(w["current"]["temperature_2m"]),
        "tmax": round(w["daily"]["temperature_2m_max"][0]),
        "tmin": round(w["daily"]["temperature_2m_min"][0]),
        "code": code,
        "icon": WMO_ICON.get(code, "🌡️"),
    }


def fetch_weather(city="", lat=None, lon=None, label=None):
    """Clima por coordenadas (preferido, sem ambiguidade) ou por nome (fallback)."""
    cache = _read_json(WEATHER_FILE, {})
    if not isinstance(cache, dict):
        cache = {}
    now = time.time()

    if lat and lon:
        key = f"{lat},{lon}"
        disp = label or city or key
    else:
        city = (city or "").strip()
        if not city:
            return {"ok": False, "error": "cidade não informada"}
        key = city.lower()
        disp = city

    hit = cache.get(key)
    if hit and hit.get("ok") and (now - hit.get("_ts", 0) < 3 * 3600):
        return hit  # cache válido por ~3h

    try:
        if not (lat and lon):
            results = geocode_city(city, count=1)
            if not results:
                return {"ok": False, "error": "cidade não encontrada"}
            lat, lon, disp = results[0]["lat"], results[0]["lon"], results[0]["name"]
        out = {"ok": True, "_ts": now, "city": disp, "lat": lat, "lon": lon, **_forecast(lat, lon)}
        cache[key] = out
        _write_json(WEATHER_FILE, cache)
        return out
    except Exception as e:  # noqa: BLE001
        log.warning("Falha ao buscar clima (%s): %s", disp, e)
        if hit:
            return {**hit, "stale": True}
        return {"ok": False, "error": "indisponível"}


@app.route("/api/geocode", methods=["GET"])
@login_required
def get_geocode():
    try:
        return jsonify(geocode_city(request.args.get("q", "")))
    except Exception as e:  # noqa: BLE001
        log.warning("Falha no geocode: %s", e)
        return jsonify({"error": "indisponível"}), 502


@app.route("/api/weather", methods=["GET"])
def get_weather():
    return jsonify(fetch_weather(
        request.args.get("city", ""),
        request.args.get("lat"),
        request.args.get("lon"),
        request.args.get("label"),
    ))


@app.route("/api/content", methods=["POST"])
@login_required
def set_content():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "grades" not in data:
        return jsonify({"error": "Conteúdo inválido"}), 400
    save_content(data)
    return jsonify({"status": "ok"})


# ── Upload e biblioteca de mídia ──────────────────────────────────────────────
@app.route("/api/upload", methods=["POST"])
@login_required
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "Nome de arquivo vazio"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Tipo de arquivo não permitido"}), 400

    safe = secure_filename(file.filename)
    unique = f"{uuid.uuid4().hex[:8]}_{safe}"
    file.save(os.path.join(UPLOADS_DIR, unique))
    return jsonify({"status": "ok", "url": f"/uploads/{unique}", "filename": unique}), 201


@app.route("/api/uploads", methods=["GET"])
@app.route("/api/library", methods=["GET"])
@login_required
def list_library():
    items = []
    for name in sorted(os.listdir(UPLOADS_DIR)):
        path = os.path.join(UPLOADS_DIR, name)
        if os.path.isfile(path):
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            kind = "video" if ext in {"mp4", "webm", "ogg", "mov", "avi"} else "image"
            size_bytes = os.path.getsize(path)
            items.append({
                "filename": name,
                "url": f"/uploads/{name}",
                "type": kind,
                "size": size_bytes,
                "size_mb": round(size_bytes / (1024 * 1024), 2),
            })
    return jsonify(items)


@app.route("/api/library/<path:filename>", methods=["DELETE"])
@login_required
def delete_library(filename):
    safe = secure_filename(filename)
    path = os.path.join(UPLOADS_DIR, safe)
    if os.path.isfile(path):
        os.remove(path)
        return jsonify({"status": "removed"})
    return jsonify({"error": "Arquivo não encontrado"}), 404


# ── Arquivos servidos ─────────────────────────────────────────────────────────
@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOADS_DIR, filename)


@app.route("/")
def index():
    return redirect("/admin")


@app.route("/tela/<slug>")
def tela(slug):
    # URL amigável das TVs → display com o slug correspondente
    safe = secure_filename(slug) or "principal"
    return redirect(f"/display.html?tv={safe}")


@app.route("/admin")
@app.route("/admin.html")
@login_required
def admin_page():
    return send_from_directory(FRONTEND_DIR, "admin.html")


@app.route("/login")
@app.route("/login.html")
def login_page():
    return send_from_directory(FRONTEND_DIR, "login.html")


# Páginas públicas (display + documentação). admin.html é protegido acima.
PUBLIC_PAGES = {
    "display.html", "guia_player.html", "manual_usuario.html",
    "protocolo_testes.html", "relatorio_final.html", "login.html",
}


@app.route("/<path:filename>")
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


@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "Arquivo excede o limite de 300 MB"}), 413


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    load_users()
    if not os.path.exists(CONTENT_FILE):
        save_content(DEFAULT_CONTENT)

    log.info("=" * 60)
    log.info("  TV CORPORATIVA – Servidor Central")
    log.info("  Admin:   http://localhost:%s/admin", PORT)
    log.info("  Display: http://localhost:%s/tela/principal", PORT)
    log.info("=" * 60)

    try:
        from waitress import serve
        log.info("Servindo com waitress em %s:%s", HOST, PORT)
        serve(app, host=HOST, port=PORT)
    except ImportError:
        log.warning("waitress não instalado — usando servidor de desenvolvimento do Flask.")
        log.warning("Para produção: pip install waitress")
        app.run(host=HOST, port=PORT, debug=False)
