"""
Persistência de documentos da aplicação (conteúdo, usuários, perfis,
tokens de reset) e utilitários de arquivo/MIME.

Os dados de verdade vivem no Postgres (db.py); os arquivos JSON em data/
são apenas caches locais e legado da migração.
"""
import os
import json
import secrets

from werkzeug.security import generate_password_hash

import db
from config import (
    log, ON_SERVERLESS, SECRET_FILE, DEFAULT_CONTENT,
    PERM_AREAS, ALL_PERMS, ADMIN_PROFILE_ID,
)


def _read_json(path, fallback):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            log.error("Falha ao ler %s: %s", path, e)
    return fallback


def _write_json(path, data):
    """Escrita atômica para não corromper o arquivo se cair no meio.
    Em filesystem somente leitura (serverless) apenas loga e segue — esses
    arquivos são caches locais (cotações, clima, notícias, secret.key de
    fallback); os dados que importam ficam no Postgres."""
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except OSError as e:
        log.warning("Não foi possível gravar %s (filesystem somente leitura?): %s", path, e)


# ── Conteúdo (TVs / grades / rodapés) ─────────────────────────────────────────
def load_content():
    data = db.doc_get("content")
    return data if data is not None else DEFAULT_CONTENT


def save_content(data):
    db.doc_set("content", data)


# ── Chave de sessão do Flask ──────────────────────────────────────────────────
def get_secret_key():
    """Chave de sessão do Flask. Prioridade:
    1) variável de ambiente TV_SECRET_KEY — obrigatória em serverless (Vercel),
       pois lá não há disco persistente entre cold starts: sem isso, a cada
       novo cold start uma chave nova seria gerada e todo mundo seria
       deslogado.
    2) arquivo data/secret.key (uso local/Docker, onde o disco é persistente).
    3) gera uma chave em memória como último recurso (funciona, mas invalida
       sessões a cada reinício — evite em produção sem disco persistente).
    """
    env_key = os.environ.get("TV_SECRET_KEY", "").strip()
    if env_key:
        return env_key
    key = _read_json(SECRET_FILE, None)
    if key:
        return key
    key = secrets.token_hex(32)
    if ON_SERVERLESS:
        log.warning("TV_SECRET_KEY não definida em ambiente serverless — usando chave "
                     "temporária (sessões serão invalidadas a cada cold start). "
                     "Defina TV_SECRET_KEY nas variáveis de ambiente da Vercel.")
    _write_json(SECRET_FILE, key)
    return key


# ── Perfis de acesso ──────────────────────────────────────────────────────────
def load_profiles():
    profiles = db.doc_get("profiles")
    if not profiles:
        profiles = {
            ADMIN_PROFILE_ID: {"name": "Administrador", "perms": list(ALL_PERMS)},
            "operador":       {"name": "Operador", "perms": ["grade", "biblioteca", "rodape"]},
        }
        db.doc_set("profiles", profiles)
    # Garante que o perfil administrador exista e tenha todas as permissões
    adm = profiles.get(ADMIN_PROFILE_ID)
    if not adm:
        profiles[ADMIN_PROFILE_ID] = {"name": "Administrador", "perms": list(ALL_PERMS)}
        db.doc_set("profiles", profiles)
    elif set(adm.get("perms", [])) != set(ALL_PERMS):
        adm["perms"] = list(ALL_PERMS)
        db.doc_set("profiles", profiles)
    return profiles


def save_profiles(profiles):
    db.doc_set("profiles", profiles)


def profile_perms(profile_id):
    prof = load_profiles().get(profile_id or "")
    if not prof:
        return []
    return [p for p in prof.get("perms", []) if p in PERM_AREAS]


# ── Usuários ──────────────────────────────────────────────────────────────────
def load_users():
    users = db.doc_get("users")
    migrated = False
    if not users:
        # Cria usuário admin padrão no primeiro arranque
        users = {
            "admin": {
                "password_hash": generate_password_hash("flexivel"),
                "name": "Administrador",
                "email": "",
                "profile": ADMIN_PROFILE_ID,
                "must_change": True,
            }
        }
        db.doc_set("users", users)
        log.warning("Usuário 'admin' criado com senha padrão 'flexivel'. TROQUE no primeiro login.")
        return users
    # Migração: usuários antigos sem perfil viram administrador; garante campo email
    for uname, u in users.items():
        if "profile" not in u or not u.get("profile"):
            u["profile"] = ADMIN_PROFILE_ID
            migrated = True
        if "email" not in u:
            u["email"] = ""
            migrated = True
    if migrated:
        db.doc_set("users", users)
    return users


def save_users(users):
    db.doc_set("users", users)


# ── Tokens de redefinição de senha ────────────────────────────────────────────
def load_resets():
    return db.doc_get("password_resets") or {}


def save_resets(d):
    db.doc_set("password_resets", d)


# ── MIME ──────────────────────────────────────────────────────────────────────
_MIME = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
         "gif": "image/gif", "webp": "image/webp", "svg": "image/svg+xml",
         "mp4": "video/mp4", "webm": "video/webm", "ogg": "video/ogg",
         "pdf": "application/pdf"}


def guess_mime(name):
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return _MIME.get(ext, "application/octet-stream")
