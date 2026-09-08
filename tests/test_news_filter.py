"""
Testes do filtro de palavras proibidas nas notícias.

Roda sem servidor e sem rede:  python tests/test_news_filter.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import news_filter as nf  # noqa: E402

CFG_USUARIO = {
    "news_blocklist": "politica, lula, bolsonaro, flavio bolsonaro, renan santos, "
                      "zema,apologia, drogas, racismo,augusto cury",
}

falhas = []


def check(cond, msg):
    if not cond:
        falhas.append(msg)


def bloqueia(titulo, terms, fonte=""):
    return nf.is_blocked({"title": titulo, "source": fonte}, terms)


# ── 1. Normalização ───────────────────────────────────────────────────────────
check(nf.news_norm("Política!") == "politica", "acento/pontuação não normalizados")
check(nf.news_norm("SÃO PAULO — Ação") == "sao paulo acao", "normalização composta falhou")

# ── 2. A lista digitada pelo usuário agora casa mesmo com acento/maiúscula ────
so_usuario = nf.block_terms({**CFG_USUARIO, "news_block_politics": False})
check(bloqueia("Governo discute a Política de preços", so_usuario),
      "'politica' não pegou 'Política' (era exatamente o bug relatado)")
check(bloqueia("LULA anuncia aporte para o Mercosul", so_usuario),
      "'lula' não pegou 'LULA'")
check(bloqueia("Polícia apreende droga em rodovia", so_usuario),
      "'drogas' não pegou o singular 'droga'")
check(not bloqueia("Drogaria abre nova filial em Curitiba", so_usuario),
      "'drogas' não pode pegar 'Drogaria' (palavra diferente)")
check(bloqueia("Cidade proibe apologia ao crime", so_usuario),
      "'apologia' colado por virgula sem espaco nao foi lido")

# ── 3. Política por assunto — as manchetes reais que estavam passando ─────────
terms = nf.block_terms(CFG_USUARIO)
reais_politicas = [
    ("Suprema Corte rejeita plano de Trump que restringe cidadania por nascimento", "CNN Brasil"),
    ("Lula anuncia aporte de US$ 100 milhões para fundo do Mercosul", "Brasil 247"),
    ("Nunes Marques dá quarto voto para liberação mais ampla de penduricalhos", "G1"),
    ("Motta recebe de Lula projeto do governo sobre aumento do limite do MEI", "Portal da Câmara dos Deputados"),
    ("Caiado deve anunciar Kassab como vice na disputa pela Presidência", "CNN Brasil"),
    ("Trabalhadores vão às ruas nesta 3ª feira pelo fim da 6 X 1", "Poder360"),
]
for titulo, fonte in reais_politicas:
    check(bloqueia(titulo, terms, fonte), "política passou: " + titulo[:60])

# ── 4. Não pode barrar o que não é política ──────────────────────────────────
reais_ok = [
    ("Colômbia fura defesa da RD Congo no final e se classifica na Copa do Mundo", "Terra"),
    ("Brasil x Escócia: horário e onde assistir ao jogo da Copa do Mundo", "G1"),
    ("Artilharia da Copa 2026: Messi lidera seguido por Haaland e Mbappé", "GE"),
    ("Mãe resgatada com bebê de 18 dias após terremoto na Venezuela", "BBC"),
    ("Velório de Ricardo Bocão é na escola de surfe que fundou, na Rocinha", "O Globo"),
    ("TRT e MP sugerem trégua na greve dos rodoviários", "G1"),
    ("Vasco ainda pode vender a SAF após Justiça afastar Pedrinho? Entenda", "ge"),
]
for titulo, fonte in reais_ok:
    check(not bloqueia(titulo, terms, fonte), "bloqueou indevidamente: " + titulo[:60])

# ── 5. O toggle desliga o bloqueio de política, mantendo a lista digitada ─────
sem_politica = nf.block_terms({**CFG_USUARIO, "news_block_politics": False})
check(not bloqueia("Suprema Corte rejeita plano de imigração", sem_politica),
      "toggle desligado ainda bloqueou política")
check(bloqueia("Bolsonaro se pronuncia", sem_politica),
      "toggle desligado quebrou a lista digitada")

# ── 6. Configuração vazia não bloqueia nada além de política ─────────────────
check(nf.block_terms({}) == sorted(set(nf.POLITICS_TERMS)),
      "config vazia deveria cair no padrão (só política)")
check(nf.block_terms({"news_block_politics": False}) == [],
      "sem lista e sem política, nada pode ser bloqueado")

# ── 7. filter_items conta certo ──────────────────────────────────────────────
itens = [{"title": t, "source": f} for t, f in reais_politicas + reais_ok]
kept, blocked = nf.filter_items(itens, terms)
check(blocked == len(reais_politicas), "contagem de bloqueadas errada: %d" % blocked)
check(len(kept) == len(reais_ok), "sobraram %d aprovadas" % len(kept))
check(nf.filter_items(itens, [])[0] == itens, "sem termos, nada pode ser removido")

if falhas:
    print("FALHOU (%d):" % len(falhas))
    for f in falhas:
        print("  -", f)
    sys.exit(1)
print("OK — todos os testes do filtro de notícias passaram.")
