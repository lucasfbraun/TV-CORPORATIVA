"""
Autenticação via Active Directory / LDAP.

Duas operações bem separadas:
  - ldap_authenticate(ad_username, password): faz bind DIRETO como o próprio
    usuário — é o login de verdade. Confirma a senha E que a conta não está
    desabilitada no AD. Qualquer falha (senha errada, conta desabilitada, AD
    fora do ar) retorna None — nunca cai para uma senha local.
  - ldap_search_user(username): busca com a conta de serviço, SEM a senha do
    usuário. Não autentica ninguém; serve só para o admin validar/pré-conferir
    um vínculo antes de salvar (evita digitar o usuário errado).

Nunca loga senha nenhuma (nem a da conta de serviço, nem a de usuários).
"""
import os

from ldap3 import Server, Connection, SUBTREE
from ldap3.core.exceptions import LDAPException
from ldap3.utils.conv import escape_filter_chars

import db
from config import log

LDAP_DEFAULT = {
    "enabled": False,
    "server": "", "port": 389, "use_tls": False,
    "domain": "", "base_dn": "",
    "bind_user": "", "bind_password": "",
}

ACCOUNTDISABLE = 0x2  # bit "conta desabilitada" em userAccountControl (Active Directory)


def load_ldap():
    """Configuração do LDAP/AD. Vive no banco (editável pela tela de admin),
    igual ao SMTP. Na primeira execução, semeia a partir de variáveis de
    ambiente (LDAP_*) — depois disso o banco manda; o .env deixa de ser lido."""
    cfg = db.doc_get("ldap")
    if cfg is None:
        cfg = {
            "enabled": os.environ.get("LDAP_ENABLED", "").strip().lower() == "true",
            "server": os.environ.get("LDAP_SERVER", "").strip(),
            "port": int(os.environ.get("LDAP_PORT", "389") or 389),
            "use_tls": os.environ.get("LDAP_USE_TLS", "").strip().lower() == "true",
            "domain": os.environ.get("LDAP_DOMAIN", "").strip(),
            "base_dn": os.environ.get("LDAP_BASE_DN", "").strip(),
            "bind_user": os.environ.get("LDAP_BIND_USER", "").strip(),
            "bind_password": os.environ.get("LDAP_BIND_PASSWORD", ""),
        }
        db.doc_set("ldap", cfg)
    merged = dict(LDAP_DEFAULT)
    merged.update({k: v for k, v in cfg.items() if k in LDAP_DEFAULT})
    return merged


def save_ldap(cfg):
    db.doc_set("ldap", cfg)


def public_ldap(cfg):
    """Versão segura para expor na tela de admin — nunca devolve a senha da
    conta de serviço, só se ela está preenchida."""
    return {
        "enabled": bool(cfg.get("enabled")),
        "server": cfg.get("server", ""), "port": cfg.get("port", 389),
        "use_tls": bool(cfg.get("use_tls")),
        "domain": cfg.get("domain", ""), "base_dn": cfg.get("base_dn", ""),
        "bind_user": cfg.get("bind_user", ""),
        "has_bind_password": bool(cfg.get("bind_password")),
        "configured": bool(cfg.get("server") and cfg.get("domain") and cfg.get("base_dn")),
    }


def is_account_disabled(user_account_control):
    try:
        return bool(int(user_account_control) & ACCOUNTDISABLE)
    except (TypeError, ValueError):
        return False


def _connect(cfg, user, password):
    """Abre a conexão e faz bind; aplica StartTLS antes do bind se configurado.
    Levanta LDAPException/Exception em qualquer falha de conexão — quem chama
    decide o que fazer (aqui sempre tratamos como 'acesso negado')."""
    server = Server(cfg["server"], port=int(cfg.get("port") or 389), use_ssl=False, connect_timeout=5)
    conn = Connection(server, user=user, password=password, receive_timeout=8)
    conn.open()
    if cfg.get("use_tls"):
        if not conn.start_tls():
            raise LDAPException(f"StartTLS falhou: {conn.result}")
    if not conn.bind():
        return None
    return conn


def ldap_authenticate(ad_username, password, cfg=None):
    """Login de verdade: bind direto como o usuário. Retorna {"name","email"}
    em caso de sucesso, ou None (credenciais erradas, conta desabilitada, ou
    AD inacessível — sempre nega o acesso, por design: é assim que 'desligou
    no AD, perde acesso aqui' funciona)."""
    cfg = cfg or load_ldap()
    if not cfg.get("enabled") or not ad_username or not password:
        return None
    if not cfg.get("server") or not cfg.get("domain") or not cfg.get("base_dn"):
        log.warning("Login via AD tentado com LDAP mal configurado (faltam server/domain/base_dn).")
        return None
    upn = f"{ad_username}@{cfg['domain']}"
    try:
        conn = _connect(cfg, upn, password)
        if conn is None:
            return None
        try:
            safe_user = escape_filter_chars(ad_username)
            conn.search(
                search_base=cfg["base_dn"],
                search_filter=f"(sAMAccountName={safe_user})",
                search_scope=SUBTREE,
                attributes=["displayName", "mail", "userAccountControl"],
            )
            # A senha já bateu (bind acima), mas só confirmamos "conta habilitada" se
            # conseguirmos LER o registro e o atributo userAccountControl de verdade.
            # Sem essa confirmação positiva, nega por padrão (fail-closed) — não
            # assume "habilitada" só porque não achou motivo pra recusar.
            if not conn.entries:
                log.warning("Login via AD negado para '%s': bind OK mas a busca de confirmação não "
                            "encontrou o registro (confira o Base DN nas configurações do LDAP).", ad_username)
                return None
            entry = conn.entries[0]
            if "userAccountControl" not in entry:
                log.warning("Login via AD negado para '%s': não foi possível ler userAccountControl "
                            "para confirmar que a conta está habilitada.", ad_username)
                return None
            if is_account_disabled(entry.userAccountControl.value):
                log.warning("Login via AD negado para '%s': conta desabilitada no AD.", ad_username)
                return None
            name = entry.displayName.value if "displayName" in entry and entry.displayName.value else ad_username
            email = entry.mail.value if "mail" in entry and entry.mail.value else ""
            return {"name": name, "email": email}
        finally:
            conn.unbind()
    except LDAPException as e:
        log.warning("Falha ao autenticar '%s' via AD: %s", ad_username, e)
        return None
    except Exception as e:  # noqa: BLE001 — erro de rede/conexão também nega o acesso
        log.warning("Erro de conexão com o AD ao autenticar '%s': %s", ad_username, e)
        return None


def ldap_search_user(username, cfg=None):
    """Busca um usuário no AD com a conta de serviço (sem senha do usuário).
    Não autentica ninguém — só valida que o usuário existe, para o admin
    conferir antes de vincular ou testar a conexão. Retorna
    {"sam","name","email","enabled"} ou None se não encontrar (ou a conta de
    serviço/config estiver errada).

    Propositalmente NÃO depende de cfg["enabled"]: é assim que dá pra testar a
    conexão/buscar um usuário ANTES de ligar o interruptor "Habilitar login via
    AD" — o interruptor só controla se o LOGIN de verdade (ldap_authenticate)
    passa a usar o AD, não a busca de validação."""
    cfg = cfg or load_ldap()
    if not cfg.get("bind_user") or not username:
        return None
    if not cfg.get("server") or not cfg.get("base_dn"):
        return None
    try:
        conn = _connect(cfg, cfg["bind_user"], cfg.get("bind_password", ""))
        if conn is None:
            log.warning("Conta de serviço do LDAP não autenticou (verifique usuário/senha nas configurações).")
            return None
        try:
            safe_user = escape_filter_chars(username)
            conn.search(
                search_base=cfg["base_dn"],
                search_filter=f"(sAMAccountName={safe_user})",
                search_scope=SUBTREE,
                attributes=["displayName", "mail", "userAccountControl", "sAMAccountName"],
            )
            if not conn.entries:
                return None
            entry = conn.entries[0]
            uac = entry.userAccountControl.value if "userAccountControl" in entry else None
            return {
                "sam": entry.sAMAccountName.value if "sAMAccountName" in entry else username,
                "name": entry.displayName.value if "displayName" in entry and entry.displayName.value else username,
                "email": entry.mail.value if "mail" in entry and entry.mail.value else "",
                "enabled": (not is_account_disabled(uac)) if uac is not None else True,
            }
        finally:
            conn.unbind()
    except LDAPException as e:
        log.warning("Falha ao buscar '%s' no AD: %s", username, e)
        return None
    except Exception as e:  # noqa: BLE001
        log.warning("Erro de conexão com o AD ao buscar '%s': %s", username, e)
        return None
