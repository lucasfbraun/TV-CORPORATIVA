"""
Filtro de palavras proibidas nas notícias.

Módulo separado (e sem dependência de Flask) de propósito: a regra de "esta
manchete pode ir ao ar?" é a parte que precisa de teste, e o teste não deve
precisar subir o servidor.

A filtragem roda no SERVIDOR, não só no display. Assim vale para qualquer TV,
inclusive as que estão com JavaScript antigo em cache, e não depende de o
navegador ter recebido a configuração.
"""
import re
import unicodedata


def news_norm(text):
    """Minúsculas, sem acentos e sem pontuação — base para comparar palavras.

    Sem isso, "politica" (como se digita na configuração) nunca casava com
    "política" (como vem escrito na manchete).
    """
    t = unicodedata.normalize("NFD", (text or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


# Termos de política, usados quando config.news_block_politics está ligado
# (o padrão). Uma lista escrita à mão pelo usuário ("politica, lula, ...") não
# segura manchete como "Suprema Corte rejeita...", "Nunes Marques dá quarto
# voto..." ou "Motta recebe projeto do governo..." — nenhuma delas contém as
# palavras da lista. Por isso o bloqueio de política é por assunto, não só por
# nome de político.
POLITICS_RAW = [
    # assunto / processo político
    "politica", "politico", "politicagem", "eleicao", "eleitoral", "eleitor",
    "candidato", "candidatura", "campanha eleitoral", "urna eletronica",
    "votacao", "pesquisa eleitoral", "coligacao", "partido", "bancada",
    "oposicao", "reeleicao", "mandato", "impeachment", "cassacao",
    "inelegivel", "inelegibilidade", "anistia", "tentativa de golpe",
    "golpe de estado", "projeto de lei", "medida provisoria",
    "reforma administrativa", "reforma tributaria", "orcamento secreto",
    "bolsonarista", "petista", "lulista", "esquerdista", "direitista",
    # instituições
    "stf", "supremo tribunal federal", "suprema corte", "stj", "tse", "tcu",
    "pgr", "procuradoria geral", "advocacia geral da uniao",
    "congresso nacional", "camara dos deputados", "senado federal", "senado",
    "planalto", "palacio do planalto", "casa civil", "governo federal",
    "presidencia da republica", "primeira dama",
    # cargos
    "deputado", "deputada", "senador", "senadora", "vereador", "vereadora",
    "parlamentar", "governador", "governadora", "prefeito", "prefeita",
    "ministro", "ministra", "presidente da republica", "vice presidente",
    "primeiro ministro", "procurador geral",
    # siglas partidárias
    "pt", "pl", "psdb", "mdb", "psol", "psd", "pdt", "psb", "republicanos",
    "uniao brasil", "avante", "solidariedade",
    # nomes recorrentes (nacionais). Sobrenome sozinho também entra: manchete
    # escreve "Caiado deve anunciar Kassab como vice", não o nome completo.
    "lula", "bolsonaro", "moraes", "gilmar mendes", "flavio dino",
    "nunes marques", "toffoli", "barroso", "fachin", "zanin", "alcolumbre",
    "pacheco", "arthur lira", "haddad", "alckmin", "tarcisio de freitas",
    "ratinho junior", "caiado", "zema", "kassab", "boulos", "ciro gomes",
    "marina silva", "sergio moro", "renan calheiros", "eduardo paes",
    "pablo marcal", "presidenciavel",
    # nomes recorrentes (internacionais)
    "trump", "milei", "maduro", "putin", "biden", "macron", "netanyahu",
    "zelensky", "casa branca", "kremlin", "otan",
    # veículos abertamente políticos (o filtro também olha a fonte)
    "poder360", "congresso em foco", "brasil 247", "camara dos deputados",
]
POLITICS_TERMS = [t for t in (news_norm(x) for x in POLITICS_RAW) if t]


def block_terms(cfg):
    """Lista final de termos bloqueados: os digitados na tela + política."""
    cfg = cfg or {}
    typed = (cfg.get("news_blocklist") or "").split(",")
    terms = [t for t in (news_norm(x) for x in typed) if t]
    if cfg.get("news_block_politics", True):   # padrão: bloquear política
        terms += POLITICS_TERMS
    return sorted(set(terms))


def _term_rx(term):
    """Regex de palavra inteira, indiferente a singular/plural.

    O usuário digita "drogas" e a manchete escreve "droga" (ou o contrário):
    tira-se o "s" final do termo e devolve-se ele como opcional. As bordas
    impedem o termo de virar pedaço de outra palavra — "droga" não pode
    derrubar uma notícia sobre "drogaria".
    """
    stem = term[:-1] if term.endswith("s") and len(term) > 3 else term
    # news_norm já reduziu tudo a [a-z0-9 ]: não sobra metacaractere para escapar.
    return re.compile(r"(?<![a-z0-9])" + re.escape(stem) + r"s?(?![a-z0-9])")


_RX_CACHE = {}


def is_blocked(item, terms):
    """A manchete (título + fonte) contém alguma palavra proibida?"""
    text = news_norm((item.get("title") or "") + " " + (item.get("source") or ""))
    for t in terms:
        rx = _RX_CACHE.get(t)
        if rx is None:
            rx = _RX_CACHE[t] = _term_rx(t)
        if rx.search(text):
            return True
    return False


def filter_items(items, terms):
    """Devolve (aprovadas, quantidade_bloqueada)."""
    if not terms:
        return list(items), 0
    kept = [i for i in items if not is_blocked(i, terms)]
    return kept, len(items) - len(kept)
