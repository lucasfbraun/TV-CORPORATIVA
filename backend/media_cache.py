"""
Cache em disco da mídia guardada no Postgres.

Motivo: cada GET /uploads/<arquivo> fazia um SELECT do blob inteiro e o
carregava duas vezes na memória (buffer do psycopg2 + cópia do bytes()). Um
vídeo de 300 MB — o teto de upload — custava ~600 MB de RAM por requisição. E
o <video> das TVs pede o arquivo em pedaços (HTTP Range): cada pedaço refazia
o SELECT do arquivo COMPLETO. Com as threads do servidor ocupadas nisso, o
site inteiro parecia travar.

Aqui o arquivo é gravado em disco no primeiro acesso e servido de lá dali em
diante: o Werkzeug faz streaming, Range (206) e 304 sem carregar nada inteiro
na memória, e o banco só é consultado uma vez por arquivo.

O cache é descartável: apagar a pasta só faz o próximo acesso rebuscar do
banco. Se não der para gravar (disco cheio, filesystem somente leitura), as
funções devolvem None e quem chamou segue pelo caminho antigo, em memória —
mais lento, mas idêntico ao que já funcionava.
"""
import os
import shutil
import threading

from config import DATA_DIR, log

CACHE_DIR = os.path.join(DATA_DIR, "media-cache")
_BLOBS = os.path.join(CACHE_DIR, "blob")   # o arquivo em si
_METAS = os.path.join(CACHE_DIR, "meta")   # o mime, num arquivo ao lado

# Escape de emergência: TV_MEDIA_CACHE=0 desliga tudo e volta ao comportamento antigo.
ENABLED = os.environ.get("TV_MEDIA_CACHE", "1").strip() not in ("0", "false", "no")

_locks = {}
_locks_guard = threading.Lock()
_warned = False


def _lock_for(rel):
    """Um cadeado por arquivo: duas TVs pedindo o mesmo vídeo ao mesmo tempo
    não podem virar dois SELECTs do blob inteiro."""
    with _locks_guard:
        lk = _locks.get(rel)
        if lk is None:
            lk = _locks[rel] = threading.Lock()
        return lk


def _paths(rel):
    """(arquivo, meta) dentro do cache, ou (None, None) se o caminho escapar dele."""
    rel = (rel or "").replace("\\", "/").strip("/")
    if not rel:
        return None, None
    blob = os.path.abspath(os.path.join(_BLOBS, rel))
    meta = os.path.abspath(os.path.join(_METAS, rel)) + ".mime"
    # Cinto de segurança contra '..' — o chamador já sanitiza, mas o cache
    # também é alimentado pela migração, que varre o disco.
    if not blob.startswith(os.path.abspath(_BLOBS) + os.sep):
        return None, None
    return blob, meta


def _warn_once(e):
    global _warned
    if not _warned:
        _warned = True
        log.warning("Cache de mídia indisponível (%s) — servindo direto do banco.", e)


def local(rel):
    """(caminho_em_disco, mime) se o arquivo já está no cache; senão (None, None)."""
    if not ENABLED:
        return None, None
    blob, meta = _paths(rel)
    if not blob:
        return None, None
    try:
        if os.path.isfile(blob) and os.path.isfile(meta):
            with open(meta, encoding="utf-8") as fh:
                mime = fh.read().strip()
            return blob, (mime or None)
    except OSError as e:
        _warn_once(e)
    return None, None


def store(rel, data, mime):
    """Grava no cache e devolve o caminho; None se não deu (o chamador segue sem cache)."""
    if not ENABLED:
        return None
    blob, meta = _paths(rel)
    if not blob:
        return None
    with _lock_for(rel):
        existente, _ = local(rel)
        if existente:                      # outra thread gravou enquanto esperávamos
            return existente
        try:
            os.makedirs(os.path.dirname(blob), exist_ok=True)
            os.makedirs(os.path.dirname(meta), exist_ok=True)
            # O mime é o ÚLTIMO a ser gravado, e 'local()' exige o par completo.
            # Assim, se a gravação do arquivo falhar no meio, o que sobra em
            # disco não tem mime e vira um "miss" — nunca um arquivo velho
            # servido como se fosse o novo.
            tmp = blob + ".tmp"
            with open(tmp, "wb") as fh:
                fh.write(data)
            os.replace(tmp, blob)
            with open(meta, "w", encoding="utf-8") as fh:
                fh.write(mime or "")
            return blob
        except OSError as e:
            _warn_once(e)
            invalidate(rel)   # não deixa meia-entrada para trás
            return None


def invalidate(rel):
    """Descarta um arquivo do cache (chamado quando o banco muda).

    O mime sai primeiro. Se a remoção do arquivo em si falhar (no Windows,
    enquanto uma resposta ainda o mantém aberto), o que resta em disco já não
    tem par — 'local()' devolve miss e o conteúdo vem do banco. Em nenhum
    cenário de falha parcial se serve conteúdo desatualizado.
    """
    blob, meta = _paths(rel)
    if not blob:
        return
    for p in (meta, blob, blob + ".tmp"):
        try:
            os.remove(p)
        except OSError:
            pass


def invalidate_prefix(prefix):
    """Descarta uma pasta inteira do cache."""
    prefix = (prefix or "").replace("\\", "/").strip("/")
    if not prefix:
        return
    for base in (_BLOBS, _METAS):
        alvo = os.path.abspath(os.path.join(base, prefix))
        if alvo.startswith(os.path.abspath(base) + os.sep):
            shutil.rmtree(alvo, ignore_errors=True)


def clear_all():
    """Zera o cache (usado depois de restaurar o banco)."""
    shutil.rmtree(CACHE_DIR, ignore_errors=True)
