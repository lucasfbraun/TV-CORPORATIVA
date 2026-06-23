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
import threading
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


# ── Notícias por categoria (Google News RSS, sempre atual, sem chave) ──────────
NEWS_FILE = os.path.join(DATA_DIR, "news.json")
NEWS_LABELS = {
    "TOP": "Principais", "WORLD": "Mundo", "NATION": "Brasil",
    "BUSINESS": "Economia", "TECHNOLOGY": "Tecnologia", "SPORTS": "Esportes",
    "SCIENCE": "Ciência", "HEALTH": "Saúde", "ENTERTAINMENT": "Entretenimento",
}


# Chave opcional do GNews (gnews.io) — se definida, garante imagens de verdade.
NEWS_API_KEY = os.environ.get("TV_NEWS_API_KEY", "").strip()
GNEWS_CAT = {
    "TOP": "general", "WORLD": "world", "NATION": "nation", "BUSINESS": "business",
    "TECHNOLOGY": "technology", "SPORTS": "sports", "SCIENCE": "science",
    "HEALTH": "health", "ENTERTAINMENT": "entertainment",
}


def _og_image(url):
    """Tenta extrair a imagem principal (og:image) da página da matéria."""
    import re
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (TV-Corporativa)"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            html = resp.read(160000).decode("utf-8", "replace")
        m = re.search(r'<meta[^>]+(?:property|name)=["\']og:image["\'][^>]+content=["\']([^"\']+)', html, re.I)
        if not m:
            m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']og:image', html, re.I)
        return m.group(1) if m else None
    except Exception:  # noqa: BLE001
        return None


def _news_gnews(cat):
    import urllib.error
    url = (f"https://gnews.io/api/v4/top-headlines?category={GNEWS_CAT.get(cat, 'general')}"
           f"&lang=pt&country=br&max=10&apikey={NEWS_API_KEY}")
    try:
        data = _http_json(url)
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "replace")[:300]
        except Exception:
            pass
        raise RuntimeError(f"HTTP {e.code}: {body}")
    items = []
    for a in data.get("articles", []):
        items.append({
            "title": (a.get("title") or "").strip(),
            "source": ((a.get("source") or {}).get("name") or "").strip(),
            "image": a.get("image") or None,
        })
    return items


def _news_google(cat):
    import re
    url = ("https://news.google.com/rss?hl=pt-BR&gl=BR&ceid=BR:pt-419" if cat == "TOP"
           else f"https://news.google.com/rss/headlines/section/topic/{cat}?hl=pt-BR&gl=BR&ceid=BR:pt-419")
    req = urllib.request.Request(url, headers={"User-Agent": "TV-Corporativa"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        xml_text = resp.read().decode("utf-8", "replace")

    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_text)
    items = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        src_el = it.find("source")
        source = (src_el.text or "").strip() if src_el is not None else ""
        image = None
        media = it.find("{http://search.yahoo.com/mrss/}content")
        if media is None:
            media = it.find("{http://search.yahoo.com/mrss/}thumbnail")
        if media is not None:
            image = media.get("url")
        if not image:
            m = re.search(r'<img[^>]+src=["\']([^"\']+)', it.findtext("description") or "", re.I)
            if m:
                image = m.group(1)
        if " - " in title:
            head, tail = title.rsplit(" - ", 1)
            title, source = head.strip(), source or tail.strip()
        if title:
            items.append({"title": title, "source": source, "image": image, "_link": link})
        if len(items) >= 10:
            break

    # Enriquecimento de imagem (og:image) para os que não têm, em paralelo
    missing = [i for i in items if not i.get("image") and i.get("_link")]
    if missing:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=6) as ex:
            for it, img in zip(missing, ex.map(lambda i: _og_image(i["_link"]), missing)):
                it["image"] = img
    for i in items:
        i.pop("_link", None)
    return items


def fetch_news(category):
    cat = (category or "TOP").upper()
    if cat not in NEWS_LABELS:
        cat = "TOP"
    cache = _read_json(NEWS_FILE, {})
    if not isinstance(cache, dict):
        cache = {}
    hit = cache.get(cat)
    now = time.time()
    if hit and hit.get("ok"):
        age = now - hit.get("_ts", 0)
        # GNews fica em cache por 30 min (poupa o limite diário da chave).
        # Se caiu no plano B (Google News, sem imagem), expira em 2 min para retentar o GNews logo.
        fresh_for = 1800 if hit.get("provider") == "gnews" else 120
        if age < fresh_for:
            return hit

    provider = "google"
    gnews_error = None
    try:
        if NEWS_API_KEY:
            try:
                items = _news_gnews(cat)
                provider = "gnews"
            except Exception as e:  # noqa: BLE001
                gnews_error = str(e)
                log.warning("GNews falhou (%s) — usando Google News como reserva. %s", cat, e)
                items = _news_google(cat)
        else:
            items = _news_google(cat)
        with_image = sum(1 for i in items if i.get("image"))
        out = {"ok": True, "_ts": now, "category": cat,
               "label": NEWS_LABELS.get(cat, "Notícias"),
               "provider": provider, "key_set": bool(NEWS_API_KEY),
               "gnews_error": gnews_error,
               "with_image": with_image, "total": len(items), "items": items}
        cache[cat] = out
        _write_json(NEWS_FILE, cache)
        return out
    except Exception as e:  # noqa: BLE001
        log.warning("Falha ao buscar notícias (%s): %s", cat, e)
        if hit:
            return {**hit, "stale": True}
        return {"ok": False, "category": cat, "label": NEWS_LABELS.get(cat, "Notícias"), "items": []}


@app.route("/api/news", methods=["GET"])
def get_news():
    return jsonify(fetch_news(request.args.get("category", "TOP")))


# ── Integrações com login (ex.: Grafana): login + print periódico ─────────────
CAPTURES_DIR = os.path.join(UPLOADS_DIR, "captures")
INTEGRATIONS_FILE = os.path.join(DATA_DIR, "integrations.json")
_intg_threads = {}  # id -> {"stop": Event, "thread": Thread, "status": str}


def load_integrations():
    d = _read_json(INTEGRATIONS_FILE, {})
    return d if isinstance(d, dict) else {}


def save_integrations(d):
    _write_json(INTEGRATIONS_FILE, d)


def _public_integration(iid, c):
    return {
        "id": iid, "type": c.get("type", "grafana"), "name": c.get("name", ""),
        "url": c.get("url", ""), "username": c.get("username", ""),
        "interval": c.get("interval", 20), "active": c.get("active", True),
        "has_password": bool(c.get("password")),
        "status": (_intg_threads.get(iid, {}) or {}).get("status", "parado"),
    }


# Grafana fixo (nativo) — só as credenciais são editáveis pelo usuário
GRAFANA_URL = ("https://monitoramento.techmaster.inf.br/d/SKHAi2oGz/incidentes"
               "?orgId=4&from=now-6h&to=now&timezone=America%2FSao_Paulo"
               "&var-GRUPO=$__all&var-HOST=$__all&refresh=30s")
GRAFANA_PLAYLIST = "FLEXIVEL"
GRAFANA_AUTH_FILE = os.path.join(DATA_DIR, "grafana_auth.json")


def ensure_grafana_integration():
    """Garante a integração nativa 'grafana' (mantém credenciais; URL/playlist são fixos)."""
    d = load_integrations()
    g = d.get("grafana", {})
    g["type"] = "grafana"
    g.setdefault("name", "Grafana")
    g["url"] = GRAFANA_URL
    g["playlist"] = GRAFANA_PLAYLIST
    g.setdefault("interval", 20)
    g.setdefault("username", "")
    g.setdefault("password", "")
    g.setdefault("active", True)
    d["grafana"] = g
    save_integrations(d)
    return g


def _looks_login(page):
    if "/login" in page.url.lower():
        return True
    try:
        return page.locator('input[type="password"]').count() > 0
    except Exception:
        return False


def _grafana_login(page, base, username, password):
    """Login no Grafana (mesmos seletores do script do cliente)."""
    if "/login" not in page.url.lower():
        page.goto(base + "/login", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector('input[name="user"], input[name="username"]', timeout=15000)
    page.fill('input[name="user"], input[name="username"]', username)
    page.fill('input[name="password"], input[type="password"]', password)
    for sel in ('button[type="submit"]', 'button:has-text("Log in")',
                'button:has-text("Entrar")', 'button[aria-label="Login button"]'):
        try:
            page.click(sel, timeout=2500)
            break
        except Exception:
            continue
    page.wait_for_timeout(5000)
    if _looks_login(page):
        raise RuntimeError("login falhou — verifique usuário/senha")


def _grafana_start_playlist(page, base, name):
    """Inicia a playlist. 1º tenta via API (robusto); senão, clica na interface."""
    try:
        resp = page.context.request.get(base + "/api/playlists")
        if resp.ok:
            for pl in resp.json():
                if (pl.get("name") or "").strip().lower() == (name or "").strip().lower():
                    key = pl.get("uid") or pl.get("id")
                    page.goto(f"{base}/playlists/play/{key}?kiosk", wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(4000)
                    return True
    except Exception as e:  # noqa: BLE001
        log.warning("Grafana playlists API: %s", e)
    # Fallback: navegação pela interface (igual ao script original)
    try:
        page.goto(base + "/playlists", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2500)
        for sel in (f'button:has-text("Start {name}")', 'button:has-text("Start playlist")',
                    'button[aria-label*="Start"]', 'a:has-text("Start")'):
            try:
                page.click(sel, timeout=4000)
                page.wait_for_timeout(3500)
                return True
            except Exception:
                continue
    except Exception as e:  # noqa: BLE001
        log.warning("Grafana playlist UI: %s", e)
    return False


def integration_worker(iid, stop):
    from playwright.sync_api import sync_playwright
    from urllib.parse import urlparse
    out = os.path.join(CAPTURES_DIR, f"intg-{iid}.png")
    os.makedirs(CAPTURES_DIR, exist_ok=True)
    while not stop.is_set():
        cfg = load_integrations().get(iid)
        if not cfg or not cfg.get("active", True):
            time.sleep(5)
            continue
        is_grafana = cfg.get("type", "grafana") == "grafana"
        url = GRAFANA_URL if is_grafana else cfg.get("url", "")
        interval = max(5, int(cfg.get("interval") or 20))
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
                opts = {"viewport": {"width": 1920, "height": 1080}, "ignore_https_errors": True,
                        "locale": "pt-BR", "timezone_id": "America/Sao_Paulo"}
                if is_grafana and os.path.isfile(GRAFANA_AUTH_FILE):
                    opts["storage_state"] = GRAFANA_AUTH_FILE  # reaproveita a sessão salva
                ctx = browser.new_context(**opts)
                page = ctx.new_page()
                base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(2500)
                if _looks_login(page):
                    if iid in _intg_threads:
                        _intg_threads[iid]["status"] = "logando"
                    _grafana_login(page, base, cfg.get("username", ""), cfg.get("password", ""))
                    if is_grafana:
                        ctx.storage_state(path=GRAFANA_AUTH_FILE)  # salva a sessão p/ próximos boots
                if is_grafana:
                    _grafana_start_playlist(page, base, cfg.get("playlist") or GRAFANA_PLAYLIST)
                page.wait_for_timeout(5000)
                if iid in _intg_threads:
                    _intg_threads[iid]["status"] = "ok"
                # Mantém a sessão aberta e tira prints (acompanha a rotação da playlist)
                while not stop.is_set():
                    cur = load_integrations().get(iid)
                    if not cur or not cur.get("active", True):
                        break
                    # Sessão expirou (token caiu) → o Grafana volta pro /login.
                    # Refaz o login e reabre a playlist em vez de "fotografar" a tela de login.
                    if is_grafana and _looks_login(page):
                        if iid in _intg_threads:
                            _intg_threads[iid]["status"] = "religando"
                        _grafana_login(page, base, cur.get("username", ""), cur.get("password", ""))
                        ctx.storage_state(path=GRAFANA_AUTH_FILE)
                        _grafana_start_playlist(page, base, cur.get("playlist") or GRAFANA_PLAYLIST)
                        page.wait_for_timeout(4000)
                        if iid in _intg_threads:
                            _intg_threads[iid]["status"] = "ok"
                    tmp = out + ".tmp.png"
                    page.screenshot(path=tmp)
                    os.replace(tmp, out)
                    interval = max(5, int(cur.get("interval") or interval))
                    for _ in range(interval):
                        if stop.is_set():
                            break
                        time.sleep(1)
                browser.close()
        except Exception as e:  # noqa: BLE001
            log.warning("Integração %s: %s", iid, e)
            if iid in _intg_threads:
                _intg_threads[iid]["status"] = f"erro: {str(e)[:120]}"
            time.sleep(20)


def start_worker(iid):
    old = _intg_threads.get(iid)
    if old:
        old["stop"].set()
    stop = threading.Event()
    t = threading.Thread(target=integration_worker, args=(iid, stop), daemon=True)
    _intg_threads[iid] = {"stop": stop, "thread": t, "status": "iniciando"}
    t.start()


def stop_worker(iid):
    st = _intg_threads.pop(iid, None)
    if st:
        st["stop"].set()


def start_all_workers():
    ensure_grafana_integration()  # garante a integração nativa do Grafana
    for iid, cfg in load_integrations().items():
        if cfg.get("active", True):
            start_worker(iid)


@app.route("/api/integrations", methods=["GET"])
@login_required
def list_integrations():
    d = load_integrations()
    return jsonify([_public_integration(i, c) for i, c in d.items()])


@app.route("/api/integrations", methods=["POST"])
@login_required
def create_integration():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    url = (data.get("url") or "").strip()
    if not name or not url.startswith(("http://", "https://")):
        return jsonify({"error": "Nome e URL (http/https) são obrigatórios"}), 400
    iid = "intg-" + uuid.uuid4().hex[:8]
    d = load_integrations()
    d[iid] = {
        "type": data.get("type", "grafana"), "name": name, "url": url,
        "username": data.get("username", ""), "password": data.get("password", ""),
        "interval": int(data.get("interval") or 20), "active": True,
    }
    save_integrations(d)
    start_worker(iid)
    return jsonify(_public_integration(iid, d[iid])), 201


@app.route("/api/integrations/<iid>", methods=["PUT"])
@login_required
def update_integration(iid):
    d = load_integrations()
    c = d.get(iid)
    if not c:
        return jsonify({"error": "Integração não encontrada"}), 404
    data = request.get_json(silent=True) or {}
    keys = ("name", "username", "active", "type") if iid == "grafana" else ("name", "url", "username", "active", "type")
    for k in keys:
        if k in data:
            c[k] = data[k]
    if "interval" in data:
        c["interval"] = int(data.get("interval") or 20)
    if data.get("password"):  # só troca a senha se uma nova for enviada
        c["password"] = data["password"]
    save_integrations(d)
    if iid == "grafana":  # credenciais podem ter mudado → descarta a sessão salva
        try:
            os.remove(GRAFANA_AUTH_FILE)
        except OSError:
            pass
    start_worker(iid) if c.get("active", True) else stop_worker(iid)
    return jsonify(_public_integration(iid, c))


@app.route("/api/integrations/<iid>", methods=["DELETE"])
@login_required
def delete_integration(iid):
    d = load_integrations()
    if iid not in d:
        return jsonify({"error": "Integração não encontrada"}), 404
    del d[iid]
    save_integrations(d)
    stop_worker(iid)
    return jsonify({"status": "removed"})


@app.route("/api/content", methods=["POST"])
@login_required
def set_content():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "grades" not in data:
        return jsonify({"error": "Conteúdo inválido"}), 400
    save_content(data)
    return jsonify({"status": "ok"})


# ── Upload e biblioteca de mídia (com pastas) ─────────────────────────────────
def safe_rel_path(rel):
    """Sanitiza um caminho relativo dentro de uploads/ (impede '..' e traversal)."""
    rel = (rel or "").replace("\\", "/").strip().strip("/")
    parts = []
    for seg in rel.split("/"):
        seg = secure_filename(seg)
        if seg and seg not in (".", ".."):
            parts.append(seg)
    return "/".join(parts)


def uploads_abs(rel):
    """Retorna (caminho_relativo_seguro, caminho_absoluto) garantindo que fica dentro de uploads/."""
    safe = safe_rel_path(rel)
    full = os.path.abspath(os.path.join(UPLOADS_DIR, safe))
    root = os.path.abspath(UPLOADS_DIR)
    if full != root and not full.startswith(root + os.sep):
        return None, None
    return safe, full


def _file_kind(name):
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext in {"mp4", "webm", "ogg", "mov", "avi"}:
        return "video"
    if ext == "pdf":
        return "pdf"
    return "image"


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

    safe_dir, dest_dir = uploads_abs(request.form.get("path", ""))
    if dest_dir is None:
        safe_dir, dest_dir = "", UPLOADS_DIR
    os.makedirs(dest_dir, exist_ok=True)

    safe_name = secure_filename(file.filename)
    unique = f"{uuid.uuid4().hex[:8]}_{safe_name}"
    file.save(os.path.join(dest_dir, unique))
    rel_url = (safe_dir + "/" + unique).strip("/")
    return jsonify({"status": "ok", "url": f"/uploads/{rel_url}", "filename": unique, "path": safe_dir}), 201


@app.route("/api/uploads", methods=["GET"])
@app.route("/api/library", methods=["GET"])
@login_required
def list_library():
    safe, base = uploads_abs(request.args.get("path", ""))
    if base is None or not os.path.isdir(base):
        safe, base = "", UPLOADS_DIR
    folders, files = [], []
    for name in sorted(os.listdir(base), key=str.lower):
        full = os.path.join(base, name)
        relpath = (safe + "/" + name).strip("/")
        if os.path.isdir(full):
            try:
                count = len(os.listdir(full))
            except OSError:
                count = 0
            folders.append({"name": name, "path": relpath, "count": count})
        elif os.path.isfile(full):
            size_bytes = os.path.getsize(full)
            files.append({
                "filename": name,
                "path": relpath,
                "url": f"/uploads/{relpath}",
                "type": _file_kind(name),
                "size": size_bytes,
                "size_mb": round(size_bytes / (1024 * 1024), 2),
            })
    return jsonify({"path": safe, "folders": folders, "files": files})


@app.route("/api/library/folder", methods=["POST"])
@login_required
def create_folder():
    data = request.get_json(silent=True) or {}
    name = secure_filename((data.get("name") or "").strip())
    if not name:
        return jsonify({"error": "Nome de pasta inválido"}), 400
    rel = (safe_rel_path(data.get("path", "")) + "/" + name).strip("/")
    safe, full = uploads_abs(rel)
    if full is None:
        return jsonify({"error": "Caminho inválido"}), 400
    if os.path.exists(full):
        return jsonify({"error": "Já existe uma pasta com esse nome"}), 409
    os.makedirs(full)
    return jsonify({"status": "ok", "path": safe}), 201


@app.route("/api/library/folder", methods=["DELETE"])
@login_required
def delete_folder():
    safe, full = uploads_abs(request.args.get("path", ""))
    if not safe or full is None or not os.path.isdir(full):
        return jsonify({"error": "Pasta não encontrada"}), 404
    import shutil
    shutil.rmtree(full)
    return jsonify({"status": "removed"})


@app.route("/api/library/<path:filename>", methods=["DELETE"])
@login_required
def delete_library(filename):
    safe, full = uploads_abs(filename)
    if full is None or not os.path.isfile(full):
        return jsonify({"error": "Arquivo não encontrado"}), 404
    os.remove(full)
    return jsonify({"status": "removed"})


def _replace_url_everywhere(obj, old, new):
    """Atualiza recursivamente qualquer URL antiga para a nova no conteúdo."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and v == old:
                obj[k] = new
            else:
                _replace_url_everywhere(v, old, new)
    elif isinstance(obj, list):
        for item in obj:
            _replace_url_everywhere(item, old, new)


@app.route("/api/library/move", methods=["POST"])
@login_required
def move_file():
    data = request.get_json(silent=True) or {}
    src_rel, src_full = uploads_abs(data.get("from", ""))
    if src_full is None or not os.path.isfile(src_full):
        return jsonify({"error": "Arquivo não encontrado"}), 404
    dst_rel, dst_full = uploads_abs(data.get("to", ""))
    if dst_full is None:
        return jsonify({"error": "Pasta de destino inválida"}), 400
    os.makedirs(dst_full, exist_ok=True)

    name = os.path.basename(src_full)
    target = os.path.join(dst_full, name)
    if os.path.exists(target):  # não sobrescreve: gera nome único
        base, ext = os.path.splitext(name)
        name = f"{base}_{uuid.uuid4().hex[:4]}{ext}"
        target = os.path.join(dst_full, name)

    import shutil
    shutil.move(src_full, target)
    new_rel = (dst_rel + "/" + name).strip("/")

    # Mantém os slides apontando para o novo local
    content = load_content()
    _replace_url_everywhere(content, f"/uploads/{src_rel}", f"/uploads/{new_rel}")
    save_content(content)

    return jsonify({"status": "ok", "url": f"/uploads/{new_rel}", "path": new_rel})


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
        start_all_workers()  # inicia as integrações (Grafana etc.)
    except Exception as e:  # noqa: BLE001
        log.warning("Não foi possível iniciar integrações: %s", e)

    try:
        from waitress import serve
        log.info("Servindo com waitress em %s:%s", HOST, PORT)
        serve(app, host=HOST, port=PORT)
    except ImportError:
        log.warning("waitress não instalado — usando servidor de desenvolvimento do Flask.")
        log.warning("Para produção: pip install waitress")
        app.run(host=HOST, port=PORT, debug=False)
