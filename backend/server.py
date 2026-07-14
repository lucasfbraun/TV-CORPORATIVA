"""
TV Corporativa - Servidor Central
Grupo Flexível

Ponto de entrada da aplicação: cria o app Flask, registra os blueprints
e faz o bootstrap do banco. A lógica vive nos módulos ao lado:

    config.py              caminhos, constantes, logging, conteúdo padrão
    db.py                  camada de dados PostgreSQL
    storage.py             documentos (conteúdo, usuários, perfis) e utilitários
    security.py            decoradores login_required / require_perm
    mailer.py              configuração SMTP e envio de e-mail
    migration.py           init do banco + migração dos dados legados
    grafana.py             workers de captura (Playwright)
    auth_routes.py         login, sessão, troca/redefinição de senha
    users_routes.py        usuários e perfis de acesso
    system_routes.py       SMTP e backup/restauração
    content_routes.py      conteúdo das TVs + cotações, clima e notícias
    integrations_routes.py CRUD das integrações (Grafana etc.)
    media_routes.py        upload, biblioteca e /uploads
    pages_routes.py        páginas do frontend e estáticos

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
import sys

# Garante que os módulos ao lado sejam importáveis tanto rodando
# `python backend/server.py` quanto importando `backend.server:app`
# (Vercel/WSGI), onde o diretório backend/ não está no sys.path.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask  # noqa: E402

from config import log, PORT, HOST, MAX_UPLOAD_BYTES, ON_SERVERLESS  # noqa: E402
from storage import get_secret_key, load_users  # noqa: E402
from migration import init_database  # noqa: E402
from grafana import start_all_workers  # noqa: E402

import auth_routes  # noqa: E402
import users_routes  # noqa: E402
import system_routes  # noqa: E402
import content_routes  # noqa: E402
import integrations_routes  # noqa: E402
import media_routes  # noqa: E402
import pages_routes  # noqa: E402

# ══════════════════════════════════════════════════════════════════════════════
# APP
# ══════════════════════════════════════════════════════════════════════════════
app = Flask(__name__, static_folder=None)
app.secret_key = get_secret_key()
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

app.register_blueprint(auth_routes.bp)
app.register_blueprint(users_routes.bp)
app.register_blueprint(system_routes.bp)
app.register_blueprint(content_routes.bp)
app.register_blueprint(integrations_routes.bp)
app.register_blueprint(media_routes.bp)
app.register_blueprint(pages_routes.bp)

# ══════════════════════════════════════════════════════════════════════════════
# BOOTSTRAP — roda sempre que o módulo é carregado, seja `python backend/server.py`
# (local/Docker) ou uma importação direta do objeto `app` (Vercel/serverless e
# outros WSGI). Isso é essencial em serverless: lá o bloco `if __name__ ==
# "__main__"` abaixo NUNCA executa (o servidor importa `app` e chama ele
# mesmo), então sem isso o banco nunca seria inicializado/migrado.
# ══════════════════════════════════════════════════════════════════════════════
try:
    _boot_attempts = 5 if ON_SERVERLESS else 30
    _boot_delay = 1 if ON_SERVERLESS else 2
    init_database(max_attempts=_boot_attempts, retry_delay=_boot_delay)
    load_users()
except Exception as e:  # noqa: BLE001
    log.error("Falha ao inicializar o banco de dados: %s", e)
    if not ON_SERVERLESS:
        raise  # local/Docker: falha alto e visível, como antes
    # Em serverless, deixa o app subir mesmo assim — melhor um 500 claro nas
    # rotas que dependem do banco do que a função inteira falhar ao importar
    # (o que a Vercel mostraria como erro genérico de invocação).


if __name__ == "__main__":
    log.info("=" * 60)
    log.info("  TV CORPORATIVA – Servidor Central")
    log.info("  Admin:   http://localhost:%s/admin", PORT)
    log.info("  Display: http://localhost:%s/tela/principal", PORT)
    log.info("=" * 60)

    try:
        start_all_workers()  # inicia as integrações (Grafana etc.) — só faz sentido
                              # com processo persistente (local/Docker), por isso
                              # fica de fora do bootstrap acima.
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
