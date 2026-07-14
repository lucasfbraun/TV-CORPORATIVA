"""
Configuração central da TV Corporativa: caminhos, constantes, logging
e conteúdo padrão. Todos os módulos importam daqui.
"""
import os
import re
import logging

# ── Caminhos ──────────────────────────────────────────────────────────────────
BACKEND_DIR  = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR     = os.path.dirname(BACKEND_DIR)
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
DATA_DIR     = os.path.join(ROOT_DIR, "data")
UPLOADS_DIR  = os.path.join(ROOT_DIR, "uploads")

CONTENT_FILE  = os.path.join(DATA_DIR, "content.json")
USERS_FILE    = os.path.join(DATA_DIR, "users.json")
PROFILES_FILE = os.path.join(DATA_DIR, "profiles.json")
SMTP_FILE     = os.path.join(DATA_DIR, "smtp.json")
RESETS_FILE   = os.path.join(DATA_DIR, "password_resets.json")
SECRET_FILE   = os.path.join(DATA_DIR, "secret.key")

PORT = int(os.environ.get("TV_PORT", 8080))
HOST = os.environ.get("TV_HOST", "0.0.0.0")

# Upload: 300 MB máximo (suporta vídeos)
MAX_UPLOAD_BYTES = 300 * 1024 * 1024
# Tipos aceitos: PNG, JPG, JPEG, MP4 e PDF
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "mp4", "pdf"}

# Ambientes serverless (ex.: Vercel) rodam com filesystem somente leitura,
# exceto /tmp, e sem processo persistente entre requisições. Detecta isso pra
# desligar automaticamente o que depende de disco gravável / threads em segundo
# plano (a Vercel define a variável de ambiente VERCEL=1).
ON_SERVERLESS = bool(os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"))

try:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(UPLOADS_DIR, exist_ok=True)
except OSError:
    # Filesystem somente leitura (ex.: Vercel). Os dados de verdade estão no
    # Postgres (db.py); os arquivos em DATA_DIR/UPLOADS_DIR são só caches
    # locais e mídia legada — seguem sem funcionar, sem derrubar o app.
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("tv-server")
if ON_SERVERLESS:
    log.info("Ambiente serverless detectado (VERCEL) — workers em segundo "
             "plano e cache em disco ficam desativados.")

# ── Perfis de acesso (permissões por área) ────────────────────────────────────
# Áreas que um perfil pode liberar. 'sistema' = gerir usuários, perfis, SMTP e integrações.
PERM_AREAS = {
    "grade":      "Montar grade / TVs / grades",
    "biblioteca": "Biblioteca e mídias",
    "rodape":     "Barra inferior (rodapé)",
    "sistema":    "Usuários, perfis, SMTP e integrações",
}
ALL_PERMS = list(PERM_AREAS.keys())
ADMIN_PROFILE_ID = "administrador"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

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
