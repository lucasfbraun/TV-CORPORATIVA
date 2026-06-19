"""
TV Corporativa – Teste de Carga e Estabilidade
Grupo Flexível

Simula múltiplas TVs acessando o servidor simultaneamente.
Mede tempo de resposta, taxa de erros e estabilidade.

Uso:
    pip install requests
    python teste_carga.py

    # Ou especificando IP e quantidade de telas:
    python teste_carga.py --ip 192.168.1.10 --telas 20 --duracao 60
"""

import argparse
import time
import threading
import statistics
from datetime import datetime
from collections import defaultdict

try:
    import requests
except ImportError:
    print("Instale o requests:  pip install requests")
    raise

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ═══════════════════════════════════════════════════════════════════════════════
DEFAULT_IP       = "localhost"
DEFAULT_PORT     = 8080
DEFAULT_TELAS    = 10       # número de TVs simuladas
DEFAULT_DURACAO  = 60       # duração do teste em segundos
DEFAULT_INTERVALO = 5       # segundos entre requisições por TV (simula refresh)

# ═══════════════════════════════════════════════════════════════════════════════
# COLETORES DE RESULTADO
# ═══════════════════════════════════════════════════════════════════════════════
lock = threading.Lock()
resultados = defaultdict(list)   # endpoint → [tempos em ms]
erros      = defaultdict(int)    # endpoint → contagem de erros
total_reqs = 0
stop_event = threading.Event()

ENDPOINTS = [
    "/display.html?tv=principal",   # o que as TVs realmente abrem
    "/api/content",                 # conteúdo central (leitura pública)
    "/login",                       # admin é protegido; testamos a tela de login
]

def fazer_requisicao(base_url, endpoint, tv_id):
    global total_reqs
    url = base_url + endpoint
    try:
        t0 = time.time()
        r = requests.get(url, timeout=10)
        elapsed_ms = (time.time() - t0) * 1000
        ok = r.status_code < 400
    except requests.exceptions.ConnectionError:
        elapsed_ms = 10000
        ok = False
    except requests.exceptions.Timeout:
        elapsed_ms = 10000
        ok = False
    except Exception:
        elapsed_ms = 10000
        ok = False

    with lock:
        resultados[endpoint].append(elapsed_ms)
        if not ok:
            erros[endpoint] += 1
        total_reqs += 1

def simular_tv(tv_id, base_url, intervalo, duracao):
    """Simula uma TV fazendo requisições periodicamente."""
    fim = time.time() + duracao
    # Cada TV começa em momento ligeiramente diferente (evita spike inicial)
    time.sleep(tv_id * 0.2)
    while not stop_event.is_set() and time.time() < fim:
        # TV principal faz mais requisições ao display e content
        fazer_requisicao(base_url, "/display.html", tv_id)
        fazer_requisicao(base_url, "/api/content",  tv_id)
        time.sleep(intervalo)

def barra_progresso(atual, total, largura=30):
    pct = atual / total
    preenchido = int(pct * largura)
    return "[" + "█" * preenchido + "░" * (largura - preenchido) + f"] {pct*100:.0f}%"

# ═══════════════════════════════════════════════════════════════════════════════
# RELATÓRIO
# ═══════════════════════════════════════════════════════════════════════════════
def imprimir_relatorio(duracao, n_telas):
    sep = "=" * 62
    print(f"\n{sep}")
    print("  RELATÓRIO DE TESTE DE CARGA – TV CORPORATIVA")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(sep)
    print(f"  TVs simuladas : {n_telas}")
    print(f"  Duração       : {duracao}s")
    print(f"  Total de reqs : {total_reqs}")
    print(sep)

    aprovado = True
    for ep, tempos in sorted(resultados.items()):
        if not tempos:
            continue
        p50  = statistics.median(tempos)
        p95  = sorted(tempos)[int(len(tempos) * 0.95)]
        p99  = sorted(tempos)[int(len(tempos) * 0.99)]
        media = statistics.mean(tempos)
        errs  = erros.get(ep, 0)
        taxa_erro = errs / len(tempos) * 100 if tempos else 0

        status = "✅ OK"
        if p95 > 2000 or taxa_erro > 5:
            status = "⚠️  ATENÇÃO"
            aprovado = False
        if p95 > 5000 or taxa_erro > 20:
            status = "❌ CRÍTICO"
            aprovado = False

        print(f"\n  Endpoint: {ep}")
        print(f"    Requisições : {len(tempos)}")
        print(f"    Média       : {media:.0f} ms")
        print(f"    P50 (mediana): {p50:.0f} ms")
        print(f"    P95         : {p95:.0f} ms")
        print(f"    P99         : {p99:.0f} ms")
        print(f"    Erros       : {errs} ({taxa_erro:.1f}%)")
        print(f"    Status      : {status}")

    print(f"\n{sep}")
    if aprovado:
        print("  ✅ RESULTADO FINAL: APROVADO")
        print("     Sistema suporta a carga simulada com boa performance.")
    else:
        print("  ⚠️  RESULTADO FINAL: REQUER ATENÇÃO")
        print("     Verifique os endpoints com P95 > 2s ou taxa de erro > 5%.")
    print(sep)

    # Salvar relatório em arquivo
    nome = f"resultado_teste_carga_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    linhas = [
        "RELATÓRIO DE TESTE DE CARGA – TV CORPORATIVA",
        f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        f"TVs simuladas: {n_telas} | Duração: {duracao}s | Total reqs: {total_reqs}",
        "",
    ]
    for ep, tempos in sorted(resultados.items()):
        if not tempos:
            continue
        p95  = sorted(tempos)[int(len(tempos) * 0.95)]
        media = statistics.mean(tempos)
        errs  = erros.get(ep, 0)
        taxa_erro = errs / len(tempos) * 100 if tempos else 0
        linhas.append(f"{ep}: média={media:.0f}ms P95={p95:.0f}ms erros={errs}({taxa_erro:.1f}%)")
    linhas.append("")
    linhas.append("RESULTADO: " + ("APROVADO" if aprovado else "REQUER ATENÇÃO"))
    with open(nome, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
    print(f"\n  Relatório salvo em: {nome}")

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description="Teste de carga – TV Corporativa")
    parser.add_argument("--ip",       default=DEFAULT_IP,        help="IP do servidor")
    parser.add_argument("--porta",    default=DEFAULT_PORT,      type=int)
    parser.add_argument("--telas",    default=DEFAULT_TELAS,     type=int, help="Nº de TVs simuladas")
    parser.add_argument("--duracao",  default=DEFAULT_DURACAO,   type=int, help="Duração em segundos")
    parser.add_argument("--intervalo",default=DEFAULT_INTERVALO, type=int, help="Intervalo entre reqs (s)")
    args = parser.parse_args()

    base_url = f"http://{args.ip}:{args.porta}"
    print(f"\n{'='*62}")
    print("  TESTE DE CARGA – TV CORPORATIVA – GRUPO FLEXÍVEL")
    print(f"{'='*62}")
    print(f"  Servidor  : {base_url}")
    print(f"  TVs       : {args.telas}")
    print(f"  Duração   : {args.duracao}s")
    print(f"  Intervalo : {args.intervalo}s por TV")
    print(f"{'='*62}\n")

    # Verificar se servidor está acessível
    print("  Verificando servidor...")
    try:
        r = requests.get(base_url + "/api/content", timeout=5)
        print(f"  ✅ Servidor OK (status {r.status_code})\n")
    except Exception as e:
        print(f"  ❌ Servidor inacessível em {base_url}")
        print(f"     Erro: {e}")
        print("  Certifique-se de que o server.py está rodando.")
        return

    # Lançar threads (uma por TV)
    threads = []
    for i in range(args.telas):
        t = threading.Thread(
            target=simular_tv,
            args=(i, base_url, args.intervalo, args.duracao),
            daemon=True
        )
        threads.append(t)

    print(f"  Iniciando {args.telas} TVs simuladas...\n")
    inicio = time.time()
    for t in threads:
        t.start()

    # Barra de progresso
    try:
        while time.time() - inicio < args.duracao:
            elapsed = time.time() - inicio
            with lock:
                reqs = total_reqs
            print(f"\r  {barra_progresso(elapsed, args.duracao)} | {reqs} reqs", end="", flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n  Interrompido pelo usuário.")

    stop_event.set()
    for t in threads:
        t.join(timeout=5)

    print()
    imprimir_relatorio(args.duracao, args.telas)

if __name__ == "__main__":
    main()
