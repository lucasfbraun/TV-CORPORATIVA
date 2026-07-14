"""
TV Corporativa – Integração de KPIs
Grupo Flexível

Este script lê indicadores de arquivos Excel/CSV internos e atualiza
automaticamente o slide de KPI exibido nas TVs, via API do servidor
(o conteúdo vive no PostgreSQL — não há mais escrita direta em arquivo).

Uso:
    pip install pandas openpyxl requests
    python integracao_kpi.py

Credenciais (usuário do painel com permissão de grade):
    Defina as variáveis de ambiente TV_KPI_USER e TV_KPI_PASS,
    ou preencha "usuario"/"senha" no bloco CONFIG abaixo.

O script roda em segundo plano e atualiza os KPIs no intervalo
configurado (padrão: a cada 5 minutos).
"""

import os
import time
import logging
from datetime import datetime
from pathlib import Path

# ── Configuração de log ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("integracao_kpi.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES – edite aqui
# ═══════════════════════════════════════════════════════════════════════════════
CONFIG = {
    # Intervalo de atualização em segundos (300 = 5 minutos)
    "intervalo_segundos": 300,

    # Endereço do servidor da TV Corporativa
    "server_url": os.environ.get("TV_SERVER_URL", "http://localhost:8080"),

    # Credenciais de um usuário do painel (precisa da permissão "grade").
    # Preferência: variáveis de ambiente, para não deixar senha no código.
    "usuario": os.environ.get("TV_KPI_USER", ""),
    "senha":   os.environ.get("TV_KPI_PASS", ""),

    # Fontes de dados – configure conforme sua realidade
    "fontes": [
        {
            "tipo": "excel",
            # Caminho do arquivo Excel com os indicadores
            "arquivo": r"kpi_dados.xlsx",
            # Aba da planilha
            "aba": "KPIs",
            # A planilha deve ter colunas: Indicador | Valor | Unidade | Tendencia | Direcao | Cor
            "coluna_indicador": "Indicador",
            "coluna_valor":     "Valor",
            "coluna_unidade":   "Unidade",
            "coluna_tendencia": "Tendencia",
            "coluna_direcao":   "Direcao",   # up | down | neu
            "coluna_cor":       "Cor",        # green | blue | amber | red
            "coluna_icone":     "Icone",
        },
        # Exemplo adicional – fonte CSV:
        # {
        #     "tipo": "csv",
        #     "arquivo": r"\\servidor\pasta\indicadores.csv",
        #     ...
        # }
    ],
}

# ═══════════════════════════════════════════════════════════════════════════════
# ARQUIVO DE EXEMPLO (kpi_dados.xlsx)
# ═══════════════════════════════════════════════════════════════════════════════
def criar_arquivo_exemplo():
    """Cria kpi_dados.xlsx de exemplo se não existir."""
    try:
        import pandas as pd
        dest = Path("kpi_dados.xlsx")
        if dest.exists():
            return
        df = pd.DataFrame([
            {"Indicador": "Produção Hoje",  "Valor": "1.247", "Unidade": " un",
             "Tendencia": "+8%",  "Direcao": "up",  "Cor": "green", "Icone": "🏭"},
            {"Indicador": "Meta do Mês",    "Valor": "94",    "Unidade": "%",
             "Tendencia": "+2%",  "Direcao": "up",  "Cor": "blue",  "Icone": "🎯"},
            {"Indicador": "Eficiência",     "Valor": "98,3",  "Unidade": "%",
             "Tendencia": "–0.5%","Direcao": "down","Cor": "amber", "Icone": "⚙️"},
            {"Indicador": "Qualidade",      "Valor": "99,1",  "Unidade": "%",
             "Tendencia": "+0.3%","Direcao": "up",  "Cor": "green", "Icone": "✅"},
            {"Indicador": "Colaboradores",  "Valor": "342",   "Unidade": "",
             "Tendencia": "estável","Direcao":"neu","Cor": "blue",  "Icone": "👥"},
            {"Indicador": "NPS Interno",    "Valor": "87",    "Unidade": "",
             "Tendencia": "+5 pts","Direcao": "up", "Cor": "green", "Icone": "⭐"},
        ])
        df.to_excel(dest, index=False, sheet_name="KPIs")
        log.info(f"Arquivo de exemplo criado: {dest}")
        log.info("  → Edite o arquivo com os dados reais e execute novamente.")
    except ImportError:
        log.warning("pandas não instalado. Instale com: pip install pandas openpyxl")

# ═══════════════════════════════════════════════════════════════════════════════
# LEITURA DE DADOS
# ═══════════════════════════════════════════════════════════════════════════════
def _df_para_metricas(df, cfg):
    """Converte um DataFrame em lista de métricas no formato das TVs."""
    metrics = []
    for _, row in df.iterrows():
        metrics.append({
            "label":  str(row.get(cfg["coluna_indicador"], "")),
            "value":  str(row.get(cfg["coluna_valor"], "–")),
            "unit":   str(row.get(cfg["coluna_unidade"], "")),
            "trend":  str(row.get(cfg["coluna_tendencia"], "")),
            "dir":    str(row.get(cfg["coluna_direcao"], "neu")),
            "color":  str(row.get(cfg["coluna_cor"], "blue")),
            "icon":   str(row.get(cfg["coluna_icone"], "📊")),
        })
    return metrics

def ler_excel(cfg):
    try:
        import pandas as pd
        df = pd.read_excel(cfg["arquivo"], sheet_name=cfg.get("aba", 0))
        return _df_para_metricas(df, cfg)
    except FileNotFoundError:
        log.warning(f"Arquivo não encontrado: {cfg['arquivo']}")
        return None
    except Exception as e:
        log.error(f"Erro ao ler Excel: {e}")
        return None

def ler_csv(cfg):
    try:
        import pandas as pd
        df = pd.read_csv(cfg["arquivo"])
        return _df_para_metricas(df, cfg)
    except FileNotFoundError:
        log.warning(f"Arquivo não encontrado: {cfg['arquivo']}")
        return None
    except Exception as e:
        log.error(f"Erro ao ler CSV: {e}")
        return None

def coletar_metricas():
    """Coleta KPIs de todas as fontes configuradas."""
    todas = []
    for fonte in CONFIG["fontes"]:
        tipo = fonte.get("tipo", "excel")
        if tipo == "excel":
            metricas = ler_excel(fonte)
        elif tipo == "csv":
            metricas = ler_csv(fonte)
        else:
            log.warning(f"Tipo de fonte desconhecido: {tipo}")
            metricas = None
        if metricas:
            todas.extend(metricas)
    return todas if todas else None

# ═══════════════════════════════════════════════════════════════════════════════
# COMUNICAÇÃO COM O SERVIDOR (login + leitura + escrita via API)
# ═══════════════════════════════════════════════════════════════════════════════
_session = None  # requests.Session com o cookie de login


def _api(path):
    return CONFIG["server_url"].rstrip("/") + path


def conectar():
    """Faz login no servidor e guarda a sessão (cookie). Retorna True/False."""
    global _session
    import requests
    user, pwd = CONFIG["usuario"], CONFIG["senha"]
    if not user or not pwd:
        log.error("Credenciais não configuradas. Defina TV_KPI_USER e TV_KPI_PASS "
                  "(ou preencha 'usuario'/'senha' no CONFIG).")
        return False
    s = requests.Session()
    try:
        r = s.post(_api("/api/login"), json={"username": user, "password": pwd}, timeout=10)
        if r.status_code != 200:
            log.error(f"Login falhou ({r.status_code}): {r.text[:200]}")
            return False
    except Exception as e:
        log.error(f"Não foi possível conectar ao servidor {CONFIG['server_url']}: {e}")
        return False
    _session = s
    log.info("Login efetuado no servidor.")
    return True


def carregar_content():
    """Busca o conteúdo atual do servidor (GET /api/content é público)."""
    import requests
    try:
        r = (_session or requests).get(_api("/api/content"), timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.error(f"Erro ao buscar conteúdo do servidor: {e}")
        return None


def salvar_content(data):
    """Envia o conteúdo atualizado via POST /api/content (autenticado)."""
    if _session is None and not conectar():
        return False
    r = _session.post(_api("/api/content"), json=data, timeout=10)
    if r.status_code == 401:  # sessão expirou → reloga uma vez e tenta de novo
        log.info("Sessão expirada — refazendo login...")
        if not conectar():
            return False
        r = _session.post(_api("/api/content"), json=data, timeout=10)
    if r.status_code != 200:
        log.error(f"Erro ao salvar conteúdo ({r.status_code}): {r.text[:200]}")
        return False
    log.info("Conteúdo enviado ao servidor com sucesso.")
    return True


def atualizar_kpis(metricas):
    content = carregar_content()
    if not content:
        log.warning("Não foi possível obter o conteúdo do servidor.")
        return False

    # Procura o slide de KPI em todas as grades
    kpi_slide = None
    for grade in content.get("grades", []):
        kpi_slide = next((s for s in grade.get("slides", []) if s.get("type") == "kpi"), None)
        if kpi_slide:
            break
    if not kpi_slide:
        log.warning("Nenhum slide de KPI encontrado. "
                    "Crie um slide do tipo KPI no painel admin primeiro.")
        return False

    kpi_slide["metrics"] = metricas
    kpi_slide["subtitle"] = f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    return salvar_content(content)

# ═══════════════════════════════════════════════════════════════════════════════
# CICLO PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════
def executar_ciclo():
    log.info("──── Iniciando ciclo de atualização ────")
    metricas = coletar_metricas()
    if metricas:
        ok = atualizar_kpis(metricas)
        if ok:
            log.info(f"✅ {len(metricas)} indicador(es) atualizados com sucesso.")
        else:
            log.warning("⚠️  Falha ao salvar os indicadores.")
