"""
TV Corporativa – Integração de KPIs
Grupo Flexível

Este script lê indicadores de arquivos Excel/CSV internos
e atualiza automaticamente o conteúdo exibido nas TVs.

Uso:
    pip install pandas openpyxl requests schedule
    python integracao_kpi.py

O script pode rodar em segundo plano e atualizar os KPIs
no intervalo configurado (padrão: a cada 5 minutos).
"""

import json
import os
import time
import logging
from datetime import datetime
from pathlib import Path

# Raiz do projeto (este script vive em integrations/)
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ── Configuração de log ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("integracao_kpi.log", encoding="utf-8")
    ]
)
log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES – edite aqui
# ═══════════════════════════════════════════════════════════════════════════════
CONFIG = {
    # Intervalo de atualização em segundos (300 = 5 minutos)
    "intervalo_segundos": 300,

    # Arquivo de conteúdo central das TVs (compartilhado com o server.py)
    "content_file": str(DATA_DIR / "content.json"),

    # Modo recomendado: None (arquivo local). O script escreve direto no
    # data/content.json que o server.py também lê — sem precisar de login.
    # OBS: o modo via API (/api/content) exige autenticação e não é usado aqui.
    "server_url": None,

    # Fontes de dados – configure conforme sua realidade
    "fontes": [
        {
            "tipo": "excel",
            # Caminho do arquivo Excel com os indicadores
            "arquivo": r"kpi_dados.xlsx",
            # Aba da planilha
            "aba": "KPIs",
            # Mapeamento: nome_coluna_excel → chave_kpi_tv
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
    ]
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
# ATUALIZAÇÃO DO CONTEÚDO
# ═══════════════════════════════════════════════════════════════════════════════
def carregar_content():
    path = CONFIG["content_file"]
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def salvar_content(data):
    # Modo servidor: envia via API
    url = CONFIG.get("server_url")
    if url:
        try:
            import requests
            r = requests.post(f"{url}/api/content", json=data, timeout=5)
            r.raise_for_status()
            log.info("Conteúdo enviado ao servidor com sucesso.")
            return True
        except Exception as e:
            log.error(f"Erro ao enviar ao servidor: {e}")
            return False

    # Modo arquivo local
    path = CONFIG["content_file"]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log.info(f"content.json atualizado.")
    return True

def atualizar_kpis(metricas):
    content = carregar_content()
    if not content:
        log.warning("content.json não encontrado. Execute o servidor ou o admin primeiro.")
        return False

    # Modelo unificado: procura o slide de KPI em todas as grades
    kpi_slide = None
    for grade in content.get("grades", []):
        kpi_slide = next((s for s in grade.get("slides", []) if s.get("type") == "kpi"), None)
        if kpi_slide:
            break
    # Compatibilidade com modelo antigo (slides na raiz)
    if not kpi_slide:
        kpi_slide = next((s for s in content.get("slides", []) if s.get("type") == "kpi"), None)
    if not kpi_slide:
        log.warning("Nenhum slide de KPI encontrado no content.json. "
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
    else:
        log.warning("⚠️  Nenhum dado coletado das fontes configuradas.")

def main():
    log.info("=" * 55)
    log.info("  TV CORPORATIVA – Integração de KPIs")
    log.info(f"  Intervalo: {CONFIG['intervalo_segundos']}s  |  {datetime.now().strftime('%d/%m/%Y')}")
    log.info("=" * 55)

    criar_arquivo_exemplo()

    # Primeira execução imediata
    executar_ciclo()

    # Loop com intervalo
    intervalo = CONFIG["intervalo_segundos"]
    log.info(f"Próxima atualização em {intervalo}s. Ctrl+C para encerrar.")
    try:
        while True:
            time.sleep(intervalo)
            executar_ciclo()
    except KeyboardInterrupt:
        log.info("Integração encerrada pelo usuário.")

if __name__ == "__main__":
    main()
