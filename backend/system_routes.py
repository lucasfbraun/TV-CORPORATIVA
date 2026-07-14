"""
Rotas de sistema: configuração SMTP e backup/restauração do banco.
"""
import os
import tempfile
import subprocess
import urllib.parse
from datetime import datetime

from flask import Blueprint, request, session, jsonify, send_file, after_this_request

import db
from config import EMAIL_RE, log
from storage import load_users
from security import require_perm
from mailer import load_smtp, save_smtp, public_smtp, send_email

bp = Blueprint("system", __name__)


# ── Configuração de SMTP (envio de e-mail) ────────────────────────────────────
@bp.route("/api/smtp", methods=["GET"])
@require_perm("sistema")
def get_smtp():
    return jsonify(public_smtp(load_smtp()))


@bp.route("/api/smtp", methods=["PUT"])
@require_perm("sistema")
def set_smtp():
    data = request.get_json(silent=True) or {}
    cfg = load_smtp()
    cfg["host"] = (data.get("host") or "").strip()
    try:
        cfg["port"] = int(data.get("port") or 587)
    except (TypeError, ValueError):
        cfg["port"] = 587
    sec = (data.get("security") or "starttls").lower()
    cfg["security"] = sec if sec in ("starttls", "ssl", "none") else "starttls"
    cfg["username"] = (data.get("username") or "").strip()
    cfg["from_email"] = (data.get("from_email") or "").strip()
    cfg["from_name"] = (data.get("from_name") or "TV Corporativa").strip()
    # Só troca a senha se enviada (campo vazio = manter a atual)
    if data.get("password"):
        cfg["password"] = data["password"]
    if data.get("clear_password"):
        cfg["password"] = ""
    save_smtp(cfg)
    return jsonify(public_smtp(cfg))


@bp.route("/api/smtp/test", methods=["POST"])
@require_perm("sistema")
def test_smtp():
    data = request.get_json(silent=True) or {}
    to = (data.get("to") or "").strip().lower()
    if not to:
        # manda para o e-mail do próprio usuário logado
        user = load_users().get(session.get("user"), {})
        to = (user.get("email") or "").strip().lower()
    if not to or not EMAIL_RE.match(to):
        return jsonify({"error": "Informe um e-mail de destino válido (ou cadastre o seu)"}), 400
    try:
        send_email(
            to, "Teste de SMTP — TV Corporativa",
            "<p>Este é um e-mail de teste do painel <b>TV Corporativa</b>.</p>"
            "<p>Se você recebeu esta mensagem, o envio de e-mails está funcionando.</p>",
        )
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": f"Falha ao enviar: {e}"}), 502
    return jsonify({"status": "ok", "sent_to": to})


# ── Backup e restauração do banco (pg_dump / pg_restore) ──────────────────────
def _pg_env():
    """Monta as variáveis PG* a partir da DATABASE_URL para o pg_dump/pg_restore."""
    u = urllib.parse.urlparse(os.environ.get("DATABASE_URL", ""))
    env = dict(os.environ)
    env["PGHOST"] = u.hostname or "db"
    env["PGPORT"] = str(u.port or 5432)
    env["PGUSER"] = u.username or "tvcorp"
    env["PGPASSWORD"] = u.password or ""
    dbname = (u.path or "/tvcorporativa").lstrip("/")
    return env, dbname


@bp.route("/api/backup", methods=["GET"])
@require_perm("sistema")
def backup_download():
    env, dbname = _pg_env()
    fd, path = tempfile.mkstemp(suffix=".dump")
    os.close(fd)

    @after_this_request
    def _cleanup(resp):
        try:
            os.remove(path)
        except OSError:
            pass
        return resp

    try:
        proc = subprocess.run(
            ["pg_dump", "-Fc", "--no-owner", "--no-privileges", "-f", path, dbname],
            env=env, capture_output=True, timeout=1800,
        )
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": f"Falha ao gerar backup: {e}"}), 500
    if proc.returncode != 0:
        return jsonify({"error": proc.stderr.decode("utf-8", "ignore")[:400] or "pg_dump falhou"}), 500
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return send_file(path, as_attachment=True,
                     download_name=f"tvcorporativa-backup-{ts}.dump",
                     mimetype="application/octet-stream")


def _do_restore(req):
    if "file" not in req.files:
        return jsonify({"error": "Envie o arquivo de backup"}), 400
    f = req.files["file"]
    if not f or f.filename == "":
        return jsonify({"error": "Arquivo de backup vazio"}), 400
    env, dbname = _pg_env()
    fd, path = tempfile.mkstemp(suffix=".dump")
    os.close(fd)
    f.save(path)
    try:
        proc = subprocess.run(
            ["pg_restore", "--clean", "--if-exists", "--no-owner", "--no-privileges",
             "-d", dbname, path],
            env=env, capture_output=True, timeout=1800,
        )
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": f"Falha ao restaurar: {e}"}), 500
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    db.reset_pool()  # reconecta após a troca dos dados
    if proc.returncode != 0:
        return jsonify({"error": proc.stderr.decode("utf-8", "ignore")[:400] or "pg_restore falhou"}), 500
    log.warning("Banco de dados RESTAURADO a partir de um backup enviado.")
    return jsonify({"status": "ok"})


@bp.route("/api/restore", methods=["POST"])
@require_perm("sistema")
def restore_authenticated():
    return _do_restore(request)


@bp.route("/api/restore-login", methods=["POST"])
def restore_from_login():
    """Restauração pela tela de login (sem chave, a pedido do operador).
    ATENÇÃO: rota sem autenticação — qualquer pessoa com acesso à rede pode
    substituir o banco inteiro. Proteger com TV_RESTORE_KEY ou remover."""
    return _do_restore(request)
