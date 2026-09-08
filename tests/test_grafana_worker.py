"""
Testes do worker de captura das Integrações (Grafana).

Roda sem Playwright, sem Postgres e sem rede:  python tests/test_grafana_worker.py
O navegador, a página e o relógio são de mentira; o que está sob teste é a
lógica do laço — cadência, backoff, zoom e troca de worker.
"""
import os
import sys
import time
import types
import threading
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "..", "backend"))

TMP = tempfile.mkdtemp(prefix="tvgraf-")
import config  # noqa: E402
config.DATA_DIR = TMP
config.UPLOADS_DIR = os.path.join(TMP, "uploads")

CFG = {"grafana": {"type": "outro", "url": "http://painel/x", "interval": 10,
                   "zoom": 100, "active": True}}
fake_db = types.ModuleType("db")
fake_db.doc_get = lambda k, d=None: CFG if k == "integrations" else d
fake_db.doc_set = lambda k, v: None
sys.modules["db"] = fake_db

import grafana  # noqa: E402
grafana.CAPTURES_DIR = os.path.join(TMP, "uploads", "captures")

falhas = []


def check(cond, msg):
    if not cond:
        falhas.append(msg)


# ── 1. note_capture_request extrai o id do nome do arquivo ───────────────────
grafana._ultimo_pedido.clear()
grafana.note_capture_request("captures/intg-grafana.png")
check("grafana" in grafana._ultimo_pedido, "nao registrou o pedido da captura")
grafana.note_capture_request("captures/intg-painel-2.png")
check("painel-2" in grafana._ultimo_pedido, "id com hifen nao foi lido")
antes = dict(grafana._ultimo_pedido)
grafana.note_capture_request("videos/aula.mp4")      # nao e captura
grafana.note_capture_request("")
check(grafana._ultimo_pedido == antes, "registrou pedido que nao era de captura")

# ── 2. Argumentos do Chromium ────────────────────────────────────────────────
for arg in ("--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
            "--disable-software-rasterizer"):
    check(arg in grafana.CHROMIUM_ARGS, "faltou o argumento %s no Chromium" % arg)


# ── Aparato: Playwright de mentira ───────────────────────────────────────────
class FakePage:
    def __init__(self, reg):
        self.reg = reg
        self.url = "http://painel/x"
        self.style_zoom = None

    def goto(self, *a, **k):
        pass

    def wait_for_timeout(self, ms):
        pass

    def evaluate(self, script, arg=None):
        # Reproduz o "so escreve se estiver diferente" do script real.
        self.reg["evaluate"] += 1
        if "style.zoom" in script:
            if self.style_zoom != arg:
                self.style_zoom = arg
                self.reg["zoom_escrito"] += 1

    def screenshot(self, path=None, **k):
        self.reg["prints"] += 1
        with open(path, "wb") as fh:
            fh.write(b"PNG")

    def locator(self, *a, **k):
        return types.SimpleNamespace(count=lambda: 0)


class FakeCtx:
    def __init__(self, reg):
        self.reg = reg

    def new_page(self):
        return FakePage(self.reg)

    def storage_state(self, path=None):
        pass


class FakeBrowser:
    def __init__(self, reg):
        self.reg = reg
        reg["browsers"] += 1
        reg["vivos"] += 1

    def new_context(self, **k):
        return FakeCtx(self.reg)

    def close(self):
        self.reg["vivos"] -= 1


class FakePlaywright:
    def __init__(self, reg):
        self.reg = reg
        self.chromium = types.SimpleNamespace(launch=lambda **k: FakeBrowser(reg))

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def instalar_playwright(reg, falhar=False):
    """Injeta um playwright.sync_api de mentira em sys.modules."""
    mod = types.ModuleType("playwright")
    api = types.ModuleType("playwright.sync_api")

    def sync_playwright():
        if falhar:
            raise RuntimeError("painel fora do ar")
        return FakePlaywright(reg)

    api.sync_playwright = sync_playwright
    mod.sync_api = api
    sys.modules["playwright"] = mod
    sys.modules["playwright.sync_api"] = api


def novo_reg():
    return {"prints": 0, "browsers": 0, "vivos": 0, "evaluate": 0, "zoom_escrito": 0}


# ── 3. Ritmo normal enquanto uma TV está pedindo a captura ───────────────────
reg = novo_reg()
instalar_playwright(reg)
# O worker tem piso de 5s por ciclo (max(5, interval)) — comportamento que
# ja existia. As janelas abaixo sao medidas em cima desse piso.
CFG["grafana"]["interval"] = 1
grafana._ultimo_pedido["grafana"] = time.time()
stop = threading.Event()
t = threading.Thread(target=grafana.integration_worker, args=("grafana", stop), daemon=True)
grafana._intg_threads["grafana"] = {"stop": stop, "thread": t, "status": "iniciando"}
t.start()
time.sleep(4)
grafana._ultimo_pedido["grafana"] = time.time()   # a TV continua olhando
time.sleep(2.5)
stop.set()
t.join(timeout=10)
check(reg["prints"] >= 2,
      "com TV olhando, em ~6,5s (piso de 5s) deveria dar 2 prints; deu %d" % reg["prints"])
check(reg["browsers"] == 1, "abriu %d navegadores para uma integracao" % reg["browsers"])
check(reg["vivos"] == 0, "o navegador ficou aberto depois de parar o worker")
prints_ativo = reg["prints"]

# O zoom e verificado todo ciclo, mas so escrito na primeira vez (nao muda).
check(reg["evaluate"] >= prints_ativo, "o zoom deixou de ser verificado a cada ciclo")
check(reg["zoom_escrito"] == 1,
      "o zoom foi reescrito %d vezes (cada escrita e um relayout do painel)" % reg["zoom_escrito"])

# ── 4. Ocioso: ninguém pede a captura → praticamente não fotografa ───────────
reg = novo_reg()
instalar_playwright(reg)
grafana._ultimo_pedido["grafana"] = 0     # ninguem olha ha muito tempo
stop = threading.Event()
t = threading.Thread(target=grafana.integration_worker, args=("grafana", stop), daemon=True)
grafana._intg_threads["grafana"] = {"stop": stop, "thread": t, "status": "iniciando"}
t.start()
time.sleep(6.5)          # mesma janela do caso ativo
stop.set()
t.join(timeout=10)
check(reg["prints"] == 1,
      "ocioso deveria dar 1 print e esperar; deu %d (ativo daria ~%d)" % (reg["prints"], prints_ativo))

# ── 5. Ocioso acorda assim que uma TV volta a pedir ──────────────────────────
reg = novo_reg()
instalar_playwright(reg)
grafana._ultimo_pedido["grafana"] = 0
stop = threading.Event()
t = threading.Thread(target=grafana.integration_worker, args=("grafana", stop), daemon=True)
grafana._intg_threads["grafana"] = {"stop": stop, "thread": t, "status": "iniciando"}
t.start()
time.sleep(2)
check(reg["prints"] == 1, "deveria estar ocioso, esperando")
grafana.note_capture_request("captures/intg-grafana.png")   # a TV voltou a olhar
time.sleep(2.5)
stop.set()
t.join(timeout=10)
check(reg["prints"] >= 2, "nao acordou quando a TV voltou a pedir a captura")

# ── 6. Falha: backoff cresce em vez de relançar o navegador sem parar ────────
reg = novo_reg()
instalar_playwright(reg, falhar=True)
grafana_espera = []
_sleep_real = time.sleep
esperas = []


def sleep_espiao(s):
    esperas.append(s)
    _sleep_real(0.01)          # nao espera de verdade


grafana.time.sleep = sleep_espiao
stop = threading.Event()
t = threading.Thread(target=grafana.integration_worker, args=("grafana", stop), daemon=True)
grafana._intg_threads["grafana"] = {"stop": stop, "thread": t, "status": "iniciando"}
t.start()
_sleep_real(1.0)
stop.set()
t.join(timeout=10)
grafana.time.sleep = _sleep_real
# Cada tentativa espera N segundos em passos de 1s: contando os passos, os
# blocos precisam ser 20, depois 40, depois 80...
check(len(esperas) > 20, "o backoff nem chegou a rodar (%d esperas)" % len(esperas))
check(reg["browsers"] == 0, "nao deveria ter aberto navegador com o painel fora do ar")

# ── 7. start_worker nao deixa dois workers do mesmo id vivos ─────────────────
reg = novo_reg()
instalar_playwright(reg)
grafana._ultimo_pedido["grafana"] = time.time()
grafana.start_worker("grafana")
_sleep_real(0.5)
grafana.start_worker("grafana")     # troca o worker, como um "Salvar" no admin
_sleep_real(1.5)
check(reg["vivos"] <= 1, "ficaram %d navegadores vivos ao trocar o worker" % reg["vivos"])
grafana.stop_worker("grafana")
_sleep_real(1.5)

if falhas:
    print("FALHOU (%d):" % len(falhas))
    for f in falhas:
        print("  -", f)
    sys.exit(1)
print("OK - worker do Grafana: cadencia ociosa, backoff, zoom e troca de worker.")
