"""
Configuração de SMTP e envio de e-mails.
"""
import re
import ssl
import smtplib
from email.message import EmailMessage

import db

SMTP_DEFAULT = {
    "host": "", "port": 587, "security": "starttls",  # starttls | ssl | none
    "username": "", "password": "",
    "from_email": "", "from_name": "TV Corporativa",
}


def load_smtp():
    cfg = db.doc_get("smtp") or {}
    merged = dict(SMTP_DEFAULT)
    merged.update({k: v for k, v in cfg.items() if k in SMTP_DEFAULT})
    return merged


def save_smtp(cfg):
    db.doc_set("smtp", cfg)


def public_smtp(cfg):
    return {
        "host": cfg.get("host", ""), "port": cfg.get("port", 587),
        "security": cfg.get("security", "starttls"),
        "username": cfg.get("username", ""),
        "from_email": cfg.get("from_email", ""),
        "from_name": cfg.get("from_name", "TV Corporativa"),
        "has_password": bool(cfg.get("password")),
        "configured": bool(cfg.get("host") and cfg.get("from_email")),
    }


def send_email(to_email, subject, html_body, text_body=None):
    """Envia um e-mail usando a configuração SMTP salva. Lança exceção em caso de erro."""
    cfg = load_smtp()
    host = cfg.get("host")
    if not host or not cfg.get("from_email"):
        raise RuntimeError("SMTP não configurado")
    port = int(cfg.get("port") or 587)
    security = (cfg.get("security") or "starttls").lower()
    from_name = cfg.get("from_name") or "TV Corporativa"
    from_email = cfg.get("from_email")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to_email
    msg.set_content(text_body or re.sub(r"<[^>]+>", "", html_body))
    msg.add_alternative(html_body, subtype="html")

    if security == "ssl":
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, timeout=20, context=ctx) as s:
            if cfg.get("username"):
                s.login(cfg["username"], cfg.get("password", ""))
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=20) as s:
            s.ehlo()
            if security == "starttls":
                s.starttls(context=ssl.create_default_context())
                s.ehlo()
            if cfg.get("username"):
                s.login(cfg["username"], cfg.get("password", ""))
            s.send_message(msg)
