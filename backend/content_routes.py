"""
Rotas de conteúdo (grades/TVs/rodapés) e widgets públicos das TVs:
cotações, previsão do tempo e notícias.
"""
import os
import json
import time
import urllib.request
import urllib.parse
from datetime import date

from flask import Blueprint, request, jsonify

from config import DATA_DIR, log
from storage import _read_json, _write_json, load_content, save_content
from security import login_required

bp = Blueprint("content", __name__)


# ── Conteúdo (leitura pública, escrita protegida) ─────────────────────────────
@bp.route("/api/content", methods=["GET"])
def get_content():
    return jsonify(load_content())


@bp.route("/api/content", methods=["POST"])
@login_required
def set_content():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "grades" not in data:
        return jsonify({"error": "Conteúdo inválido"}), 400
    save_content(data)
    return jsonify({"status": "ok"})


# ── Cotações (USD/EUR → BRL) ──────────────────────────────────────────────────
RATES_FILE = os.path.join(DATA_DIR, "rates.json")
RATES_URL = "https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL"
RATES_TTL = 3600  # atualiza as cotações a cada 1 hora


def fetch_rates():
    """Busca USD/BRL e EUR/BRL a cada 1 hora, com cache em arquivo."""
    today = date.today().isoformat()
    now = time.time()
    cached = _read_json(RATES_FILE, None)
    if cached and cached.get("ok") and (now - cached.get("ts", 0)) < RATES_TTL:
        return cached

    try:
        req = urllib.request.Request(RATES_URL, headers={"User-Agent": "TV-Corporativa"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        result = {
            "ok": True,
            "date": today,
            "ts": now,
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


@bp.route("/api/rates", methods=["GET"])
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


@bp.route("/api/geocode", methods=["GET"])
@login_required
def get_geocode():
    try:
        return jsonify(geocode_city(request.args.get("q", "")))
    except Exception as e:  # noqa: BLE001
        log.warning("Falha no geocode: %s", e)
        return jsonify({"error": "indisponível"}), 502


@bp.route("/api/weather", methods=["GET"])
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


@bp.route("/api/news", methods=["GET"])
def get_news():
    return jsonify(fetch_news(request.args.get("category", "TOP")))
