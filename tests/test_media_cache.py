"""
Testes do cache em disco da mídia (/uploads) e da invalidação dele.

Roda sem Postgres e sem servidor:  python tests/test_media_cache.py
Requer Flask instalado (o mesmo do requirements.txt).

O que precisa continuar valendo depois da otimização:
  - o arquivo servido é byte a byte o mesmo de antes;
  - Range (206) continua funcionando — é do que o <video> das TVs depende;
  - o banco é lido UMA vez por arquivo, não uma vez por pedaço;
  - apagar/mover/substituir no admin derruba o cache na hora;
  - se não der para gravar em disco, tudo volta ao caminho antigo.
"""
import os
import sys
import types
import shutil
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "..", "backend"))

TMP = tempfile.mkdtemp(prefix="tvtest-")
UPLOADS = os.path.join(TMP, "uploads")
os.makedirs(UPLOADS, exist_ok=True)

import config  # noqa: E402
config.DATA_DIR = TMP
config.UPLOADS_DIR = UPLOADS

# 'db' de mentira: guarda a mídia em memória e conta quantos SELECTs aconteceram.
BANCO = {}
LEITURAS = {"n": 0}

fake_db = types.ModuleType("db")


def _media_get(path):
    if path not in BANCO:
        return None
    LEITURAS["n"] += 1
    return BANCO[path]


import media_cache  # noqa: E402


def _media_put(path, data, mime=None):
    BANCO[path] = (data, mime)
    media_cache.invalidate(path)          # espelha o que backend/db.py faz


def _media_delete(path):
    BANCO.pop(path, None)
    media_cache.invalidate(path)


def _media_move(old, new):
    BANCO[new] = BANCO.pop(old)
    media_cache.invalidate(old)
    media_cache.invalidate(new)


fake_db.media_get = _media_get
fake_db.media_put = _media_put
fake_db.media_delete = _media_delete
fake_db.media_move = _media_move
fake_db.media_exists = lambda p: p in BANCO
fake_db.media_list = lambda: [{"path": p, "mime": v[1], "size": len(v[0])} for p, v in BANCO.items()]
fake_db.media_delete_prefix = lambda pref: [
    (BANCO.pop(p), media_cache.invalidate(p)) for p in list(BANCO) if p.startswith(pref)
]
fake_db.folders_all = lambda: []
fake_db.doc_get = lambda k, d=None: d
fake_db.doc_set = lambda k, v: None
sys.modules["db"] = fake_db

from flask import Flask  # noqa: E402
import media_routes  # noqa: E402

app = Flask(__name__)
app.register_blueprint(media_routes.bp)
cli = app.test_client()

falhas = []


def check(cond, msg):
    if not cond:
        falhas.append(msg)


VIDEO = bytes(range(256)) * 400          # ~100 KB, com bytes previsíveis
BANCO["videos/aula.mp4"] = (VIDEO, "video/mp4")

# ── 1. Primeiro acesso: vem do banco, fica em disco ──────────────────────────
LEITURAS["n"] = 0
r = cli.get("/uploads/videos/aula.mp4")
check(r.status_code == 200, "1o acesso nao retornou 200: %s" % r.status_code)
check(r.data == VIDEO, "1o acesso devolveu bytes diferentes")
check(r.headers.get("Content-Type", "").startswith("video/mp4"),
      "mime errado: %r" % r.headers.get("Content-Type"))
check(LEITURAS["n"] == 1, "esperava 1 leitura do banco, houve %d" % LEITURAS["n"])

# ── 2. Acessos seguintes NAO tocam mais o banco ──────────────────────────────
for _ in range(5):
    r = cli.get("/uploads/videos/aula.mp4")
    check(r.status_code == 200 and r.data == VIDEO, "acesso repetido divergiu")
check(LEITURAS["n"] == 1, "banco foi lido de novo (%d leituras) — cache nao pegou" % LEITURAS["n"])

# ── 3. Range (206): o que o <video> da TV usa. Nao pode ler o blob de novo ───
r = cli.get("/uploads/videos/aula.mp4", headers={"Range": "bytes=100-199"})
check(r.status_code == 206, "Range nao devolveu 206: %s" % r.status_code)
check(r.data == VIDEO[100:200], "Range devolveu o pedaco errado")
check(r.headers.get("Content-Range") == "bytes 100-199/%d" % len(VIDEO),
      "Content-Range errado: %r" % r.headers.get("Content-Range"))
r2 = cli.get("/uploads/videos/aula.mp4", headers={"Range": "bytes=50000-50099"})
check(r2.data == VIDEO[50000:50100], "segundo Range divergiu")
check(LEITURAS["n"] == 1, "cada Range voltou a ler o blob inteiro (%d leituras)" % LEITURAS["n"])

# ── 4. Revalidacao barata: ETag -> 304 (antes nao existia ETag) ──────────────
etag = r.headers.get("ETag")
check(bool(etag), "sem ETag: o navegador rebaixa o arquivo inteiro a cada 5 min")
if etag:
    r = cli.get("/uploads/videos/aula.mp4", headers={"If-None-Match": etag})
    check(r.status_code == 304, "If-None-Match nao deu 304: %s" % r.status_code)

# ── 5. ?download=1 continua forcando o anexo ─────────────────────────────────
r = cli.get("/uploads/videos/aula.mp4?download=1")
check("attachment" in (r.headers.get("Content-Disposition") or ""),
      "download=1 nao virou attachment: %r" % r.headers.get("Content-Disposition"))
check("aula.mp4" in (r.headers.get("Content-Disposition") or ""), "nome do arquivo sumiu")

# ── 6. Substituir o arquivo no admin invalida o cache ────────────────────────
NOVO = b"conteudo novo" * 100
fake_db.media_put("videos/aula.mp4", NOVO, "video/mp4")
r = cli.get("/uploads/videos/aula.mp4")
check(r.data == NOVO, "apos substituir, ainda servia o arquivo antigo (cache furado)")

# ── 7. Apagar invalida ───────────────────────────────────────────────────────
fake_db.media_delete("videos/aula.mp4")
r = cli.get("/uploads/videos/aula.mp4")
check(r.status_code == 404, "arquivo apagado ainda era servido: %s" % r.status_code)

# ── 8. Mover invalida os dois caminhos ───────────────────────────────────────
BANCO["a/foto.png"] = (b"PNGDATA" * 50, "image/png")
check(cli.get("/uploads/a/foto.png").status_code == 200, "foto nao foi servida")
fake_db.media_move("a/foto.png", "b/foto.png")
check(cli.get("/uploads/a/foto.png").status_code == 404, "caminho antigo continuou servindo")
r = cli.get("/uploads/b/foto.png")
check(r.status_code == 200 and r.data == b"PNGDATA" * 50, "caminho novo nao serviu")

# ── 9. Arquivo inexistente continua 404 ──────────────────────────────────────
check(cli.get("/uploads/nao/existe.png").status_code == 404, "inexistente deveria ser 404")

# ── 10. Capturas do Grafana continuam vindo do disco, sem passar pelo cache ──
os.makedirs(os.path.join(UPLOADS, "captures"), exist_ok=True)
with open(os.path.join(UPLOADS, "captures", "intg-grafana.png"), "wb") as fh:
    fh.write(b"PRINT")
r = cli.get("/uploads/captures/intg-grafana.png")
check(r.status_code == 200 and r.data == b"PRINT", "captura do Grafana quebrou: %s" % r.status_code)

# ── 11. Sem poder gravar em disco, volta ao caminho antigo (nada quebra) ─────
BANCO["z/doc.pdf"] = (b"%PDF-fake", "application/pdf")
_store_real = media_cache.store
media_cache.store = lambda rel, data, mime: None   # simula disco cheio/somente leitura
try:
    r = cli.get("/uploads/z/doc.pdf")
    check(r.status_code == 200 and r.data == b"%PDF-fake", "fallback sem cache quebrou")
    r = cli.get("/uploads/z/doc.pdf", headers={"Range": "bytes=0-3"})
    check(r.status_code == 206 and r.data == b"%PDF", "fallback perdeu o suporte a Range")
finally:
    media_cache.store = _store_real

# ── 12. O cache nao pode escapar da propria pasta ────────────────────────────
check(media_cache._paths("../../etc/passwd") == (None, None), "traversal aceito no cache")
check(media_cache._paths("") == (None, None), "caminho vazio aceito no cache")

# ── 13. invalidate_prefix e clear_all ────────────────────────────────────────
BANCO["pasta/1.png"] = (b"um", "image/png")
BANCO["pasta/2.png"] = (b"dois", "image/png")
cli.get("/uploads/pasta/1.png")
cli.get("/uploads/pasta/2.png")
check(media_cache.local("pasta/1.png")[0] is not None, "deveria estar em cache")
media_cache.invalidate_prefix("pasta/")
check(media_cache.local("pasta/1.png")[0] is None, "invalidate_prefix nao limpou")
check(media_cache.local("pasta/2.png")[0] is None, "invalidate_prefix deixou sobra")
cli.get("/uploads/pasta/1.png")
media_cache.clear_all()
check(media_cache.local("pasta/1.png")[0] is None, "clear_all nao limpou")

# ── 14. Os ganchos de invalidacao existem no db.py de verdade ────────────────
# (o modulo real nao pode ser importado aqui porque exige psycopg2/Postgres)
with open(os.path.join(BASE, "..", "backend", "db.py"), encoding="utf-8") as fh:
    fonte_db = fh.read()
for trecho in ("media_cache.invalidate(path)",
               "media_cache.invalidate_prefix(prefix)",
               "media_cache.invalidate(old_path)",
               "media_cache.invalidate(new_path)"):
    check(trecho in fonte_db, "db.py sem o gancho de invalidacao: %s" % trecho)
check("POOL_MAX" in fonte_db and "ThreadedConnectionPool(1, POOL_MAX" in fonte_db,
      "pool do Postgres continua fixo em 12 — nao acompanha TV_THREADS")

with open(os.path.join(BASE, "..", "backend", "server.py"), encoding="utf-8") as fh:
    fonte_srv = fh.read()
check("threads=threads" in fonte_srv and 'TV_THREADS' in fonte_srv,
      "waitress continua com as 4 threads padrao")

shutil.rmtree(TMP, ignore_errors=True)

if falhas:
    print("FALHOU (%d):" % len(falhas))
    for f in falhas:
        print("  -", f)
    sys.exit(1)
print("OK - cache de midia: mesmos bytes, Range, 304, invalidacao e fallback.")
