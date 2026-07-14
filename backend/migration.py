"""
Inicialização do banco e migração única dos dados legados
(JSON em data/ + arquivos em uploads/) para o Postgres.
"""
import os
import time
from datetime import datetime

import db
from config import (
    log, UPLOADS_DIR, CONTENT_FILE, USERS_FILE, PROFILES_FILE,
    SMTP_FILE, RESETS_FILE, DEFAULT_CONTENT,
)
from storage import _read_json, guess_mime, save_content

INTEGRATIONS_FILE = os.path.join(os.path.dirname(CONTENT_FILE), "integrations.json")

LEGACY_DOCS = {
    "content": CONTENT_FILE,
    "users": USERS_FILE,
    "profiles": PROFILES_FILE,
    "smtp": SMTP_FILE,
    "integrations": INTEGRATIONS_FILE,
    "password_resets": RESETS_FILE,
}


def migrate_from_files():
    """Importa, uma única vez, os dados em arquivo (JSON + uploads/) para o banco.
    Os arquivos atuais NÃO são apagados — servem de rollback."""
    if db.doc_exists("__meta_migrated"):
        return
    imported = []
    for key, path in LEGACY_DOCS.items():
        if not db.doc_exists(key) and os.path.exists(path):
            data = _read_json(path, None)
            if data is not None:
                db.doc_set(key, data)
                imported.append(key)

    n_files = 0
    if os.path.isdir(UPLOADS_DIR):
        for root, dirs, files in os.walk(UPLOADS_DIR):
            rel_root = os.path.relpath(root, UPLOADS_DIR)
            rel_root = "" if rel_root == "." else rel_root.replace(os.sep, "/")
            # pula as capturas do Grafana (transitórias, regeneradas)
            if rel_root == "captures" or rel_root.startswith("captures/"):
                continue
            for d in dirs:
                if rel_root == "" and d == "captures":
                    continue
                rel = (rel_root + "/" + d) if rel_root else d
                db.folder_add(rel)
            for fn in files:
                rel = (rel_root + "/" + fn) if rel_root else fn
                try:
                    with open(os.path.join(root, fn), "rb") as f:
                        db.media_put(rel, f.read(), guess_mime(fn))
                    n_files += 1
                except OSError as e:  # noqa: PERF203
                    log.warning("Falha ao migrar mídia %s: %s", rel, e)

    db.doc_set("__meta_migrated", {"at": datetime.utcnow().isoformat(),
                                   "docs": imported, "files": n_files})
    if imported or n_files:
        log.info("Migração p/ o banco: %d documento(s), %d arquivo(s) de mídia.",
                 len(imported), n_files)


def init_database(max_attempts=30, retry_delay=2):
    """Conecta ao Postgres (com retry), cria o schema e migra os dados legados."""
    last = None
    for attempt in range(1, max_attempts + 1):
        try:
            db.init_db()
            last = None
            break
        except Exception as e:  # noqa: BLE001
            last = e
            log.warning("Aguardando o banco de dados... (tentativa %d/%d)", attempt, max_attempts)
            time.sleep(retry_delay)
    if last is not None:
        raise last
    migrate_from_files()
    if not db.doc_exists("content"):
        save_content(DEFAULT_CONTENT)
