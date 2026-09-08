"""
Integrações com login (ex.: Grafana): navegador headless (Playwright) que
autentica, abre a playlist e tira capturas periódicas para exibição nas TVs.
"""
import os
import time
import threading

import db
from config import log, DATA_DIR, UPLOADS_DIR

CAPTURES_DIR = os.path.join(UPLOADS_DIR, "captures")
_intg_threads = {}  # id -> {"stop": Event, "thread": Thread, "status": str}

# Grafana fixo (nativo) — só as credenciais são editáveis pelo usuário
GRAFANA_URL = ("https://monitoramento.techmaster.inf.br/d/SKHAi2oGz/incidentes"
               "?orgId=4&from=now-6h&to=now&timezone=America%2FSao_Paulo"
               "&var-GRUPO=$__all&var-HOST=$__all&refresh=30s")
GRAFANA_PLAYLIST = "FLEXIVEL"
GRAFANA_ZOOM = 1.0  # zoom padrão (legado) — o valor por integração vem do campo 'zoom' (%)
GRAFANA_REFRESH = "30s"  # auto-refresh dos painéis no navegador (mantém os dados atuais)
GRAFANA_AUTH_FILE = os.path.join(DATA_DIR, "grafana_auth.json")

# Argumentos do Chromium. Sem eles, o headless no Linux cai no rasterizador por
# software e fica desenhando com a CPU, além de subir uma porção de serviços de
# fundo (sincronização, telemetria, atualização de componentes) que não servem
# para nada em um navegador que só tira print de um painel.
CHROMIUM_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-software-rasterizer",
    "--disable-extensions",
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-client-side-phishing-detection",
    "--disable-default-apps",
    "--disable-sync",
    "--disable-breakpad",
    "--metrics-recording-only",
    "--no-first-run",
    "--mute-audio",
    "--hide-scrollbars",
]

# Quando nenhuma TV pede a captura há um tempo, o painel não está na tela de
# ninguém: não faz sentido continuar fotografando a cada 10s.
OCIOSO_APOS = 180      # segundos sem ninguém pedir a imagem
INTERVALO_OCIOSO = 60  # cadência enquanto ninguém está olhando
_ultimo_pedido = {}    # id da integração -> quando a imagem foi pedida pela última vez


def note_capture_request(rel):
    """Registra que uma TV pediu a captura (chamado ao servir /uploads/captures/…).

    É o que permite o worker desacelerar quando o slide não está em cena e
    voltar ao ritmo normal assim que alguma TV mostra o painel de novo.
    """
    nome = os.path.basename(rel or "")
    if nome.startswith("intg-") and "." in nome:
        _ultimo_pedido[nome[len("intg-"):].rsplit(".", 1)[0]] = time.time()


def load_integrations():
    d = db.doc_get("integrations", {})
    return d if isinstance(d, dict) else {}


def save_integrations(d):
    db.doc_set("integrations", d)


def public_integration(iid, c):
    return {
        "id": iid, "type": c.get("type", "grafana"), "name": c.get("name", ""),
        "url": c.get("url", ""), "username": c.get("username", ""),
        "interval": c.get("interval", 20), "zoom": c.get("zoom", 100),
        "active": c.get("active", True),
        "has_password": bool(c.get("password")),
        "status": (_intg_threads.get(iid, {}) or {}).get("status", "parado"),
    }


def ensure_grafana_integration():
    """Garante a integração nativa 'grafana' (mantém credenciais; URL/playlist são fixos)."""
    d = load_integrations()
    g = d.get("grafana", {})
    g["type"] = "grafana"
    g.setdefault("name", "Grafana")
    g["url"] = GRAFANA_URL
    g["playlist"] = GRAFANA_PLAYLIST
    g.setdefault("interval", 10)
    g.setdefault("zoom", 100)
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
                    page.goto(f"{base}/playlists/play/{key}?kiosk&refresh={GRAFANA_REFRESH}",
                              wait_until="domcontentloaded", timeout=60000)
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


def integration_worker(iid, stop, anterior=None):
    from playwright.sync_api import sync_playwright
    from urllib.parse import urlparse
    # Cada "Salvar" nas Integrações troca o worker. Sem esperar o antigo sair,
    # ficavam dois Chromium vivos ao mesmo tempo — o antigo ainda fechando, o
    # novo já carregando o painel.
    if anterior is not None and anterior.is_alive():
        anterior.join(timeout=30)
    out = os.path.join(CAPTURES_DIR, f"intg-{iid}.png")
    os.makedirs(CAPTURES_DIR, exist_ok=True)
    espera_erro = 20   # backoff: se o Grafana está fora, não adianta relançar o
                       # navegador inteiro a cada 20s — só queima CPU à toa.

    # A configuração vinha do Postgres a cada volta do laço (a cada ~10s, por
    # integração). Ela quase nunca muda; 5s de cache tiram essa consulta do
    # caminho quente sem atrasar de forma perceptível uma edição no admin.
    _cache = {"quando": 0.0, "valor": None}

    def config_atual():
        agora = time.time()
        if agora - _cache["quando"] > 5:
            _cache["valor"] = load_integrations().get(iid)
            _cache["quando"] = agora
        return _cache["valor"]

    while not stop.is_set():
        cfg = config_atual()
        if not cfg or not cfg.get("active", True):
            time.sleep(5)
            continue
        is_grafana = cfg.get("type", "grafana") == "grafana"
        url = GRAFANA_URL if is_grafana else cfg.get("url", "")
        interval = max(5, int(cfg.get("interval") or 10))
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(args=CHROMIUM_ARGS)
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
                espera_erro = 20   # chegou até aqui: o backoff pode recomeçar do início
                # Mantém a sessão aberta e tira prints (acompanha a rotação da playlist)
                while not stop.is_set():
                    cur = config_atual()
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
                    # Zoom da captura (config. no painel): <100% "afasta a câmera"
                    # e mostra mais conteúdo; >100% aproxima. Continua sendo
                    # verificado a cada ciclo (navegações da playlist resetam o
                    # estilo), mas só é ESCRITO quando está diferente: atribuir
                    # zoom força um relayout da página inteira, e fazer isso a
                    # cada 10s num painel do Grafana não é barato.
                    try:
                        z = max(25, min(200, int(cur.get("zoom") or 100)))
                        page.evaluate(
                            "(z) => { const e = document.documentElement;"
                            " if (e.style.zoom !== z) e.style.zoom = z; }",
                            str(z / 100))
                    except Exception:  # noqa: BLE001
                        pass
                    tmp = out + ".tmp.png"
                    page.screenshot(path=tmp)
                    os.replace(tmp, out)
                    interval = max(5, int(cur.get("interval") or interval))

                    # Ninguém pediu a imagem há um tempo → o painel não está em
                    # cena. Espaça as capturas e volta ao ritmo assim que uma TV
                    # pedir de novo (o display recarrega a imagem a cada 10s
                    # enquanto o slide está visível, então ele se acerta sozinho).
                    ocioso = (time.time() - _ultimo_pedido.get(iid, 0)) > OCIOSO_APOS
                    espera = INTERVALO_OCIOSO if ocioso else interval
                    for _ in range(espera):
                        if stop.is_set():
                            break
                        if ocioso and (time.time() - _ultimo_pedido.get(iid, 0)) <= OCIOSO_APOS:
                            break   # alguém voltou a olhar: acorda agora
                        time.sleep(1)
                browser.close()
        except Exception as e:  # noqa: BLE001
            log.warning("Integração %s: %s (nova tentativa em %ds)", iid, e, espera_erro)
            if iid in _intg_threads:
                _intg_threads[iid]["status"] = f"erro: {str(e)[:120]}"
            for _ in range(espera_erro):
                if stop.is_set():
                    break
                time.sleep(1)
            espera_erro = min(espera_erro * 2, 300)


def start_worker(iid):
    old = _intg_threads.get(iid)
    anterior = None
    if old:
        old["stop"].set()
        anterior = old.get("thread")
    stop = threading.Event()
    # 'anterior' é esperado DENTRO da thread nova, não aqui: start_worker é
    # chamado no meio de uma requisição do admin ("Salvar" nas Integrações) e
    # ela não pode ficar pendurada esperando um navegador fechar.
    t = threading.Thread(target=integration_worker, args=(iid, stop, anterior), daemon=True)
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
