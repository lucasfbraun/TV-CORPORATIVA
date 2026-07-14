"""
Camada de dados (PostgreSQL) da TV Corporativa.

Guarda TUDO no banco:
  - app_documents : documentos JSON (config/TVs/grades/rodapés, usuários, perfis, SMTP, integrações)
  - media         : imagens, vídeos e PDFs (bytea)
  - media_folders : pastas da biblioteca (inclusive vazias)

Projetado para um futuro multi-inquilino (SaaS): basta adicionar uma coluna
tenant_id às tabelas e um filtro nas funções abaixo.
"""
import os
import threading
from contextlib import contextmanager

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import Json

DATABASE_URL = os.environ.get("DATABASE_URL", "")

_pool = None
_lock = threading.Lock()


def _get_pool():
    global _pool
    if _pool is None:
        with _lock:
            if _pool is None:
                if not DATABASE_URL:
                    raise RuntimeError("DATABASE_URL não configurada")
                _pool = ThreadedConnectionPool(1, 12, dsn=DATABASE_URL)
    return _pool


def reset_pool():
    """Fecha o pool (usado após restaurar o banco, p/ reconectar do zero)."""
    global _pool
    with _lock:
        if _pool is not None:
            try:
                _pool.closeall()
            except Exception:
                pass
            _pool = None


@contextmanager
def get_conn():
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def init_db():
    """Cria as tabelas se ainda não existirem."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_documents (
                key        TEXT PRIMARY KEY,
                value      JSONB NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            CREATE TABLE IF NOT EXISTS media (
                path       TEXT PRIMARY KEY,
                data       BYTEA NOT NULL,
                mime       TEXT,
                size       BIGINT,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            CREATE TABLE IF NOT EXISTS media_folders (
                path       TEXT PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            """
        )


# ── Documentos JSON ───────────────────────────────────────────────────────────
def doc_get(key, default=None):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT value FROM app_documents WHERE key = %s", (key,))
        row = cur.fetchone()
        return row[0] if row else default


def doc_set(key, value):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO app_documents (key, value, updated_at)
            VALUES (%s, %s, now())
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now()
            """,
            (key, Json(value)),
        )


def doc_exists(key):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM app_documents WHERE key = %s", (key,))
        return cur.fetchone() is not None


# ── Mídia (bytea) ─────────────────────────────────────────────────────────────
def media_put(path, data, mime=None):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO media (path, data, mime, size, updated_at)
            VALUES (%s, %s, %s, %s, now())
            ON CONFLICT (path) DO UPDATE
              SET data = EXCLUDED.data, mime = EXCLUDED.mime,
                  size = EXCLUDED.size, updated_at = now()
            """,
            (path, psycopg2.Binary(data), mime, len(data)),
        )


def media_get(path):
    """Retorna (bytes, mime) ou None."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT data, mime FROM media WHERE path = %s", (path,))
        row = cur.fetchone()
        if not row:
            return None
        return bytes(row[0]), row[1]


def media_exists(path):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM media WHERE path = %s", (path,))
        return cur.fetchone() is not None


def media_delete(path):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM media WHERE path = %s", (path,))


def media_delete_prefix(prefix):
    """Remove todos os arquivos sob uma pasta (prefixo terminado em '/')."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM media WHERE path LIKE %s", (prefix + "%",))


def media_list():
    """Lista todos os arquivos: [{path, mime, size}]."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT path, mime, size FROM media ORDER BY path")
        return [{"path": p, "mime": m, "size": s} for (p, m, s) in cur.fetchall()]


def media_move(old_path, new_path):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("UPDATE media SET path = %s, updated_at = now() WHERE path = %s",
                    (new_path, old_path))


# ── Pastas da biblioteca ──────────────────────────────────────────────────────
def folder_add(path):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO media_folders (path) VALUES (%s) ON CONFLICT (path) DO NOTHING",
            (path,),
        )


def folder_delete(path):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM media_folders WHERE path = %s", (path,))


def folder_delete_prefix(prefix):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM media_folders WHERE path = %s OR path LIKE %s",
                    (prefix.rstrip("/"), prefix + "%"))


def folders_all():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT path FROM media_folders ORDER BY path")
        return [r[0] for r in cur.fetchall()]
