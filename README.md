# TV Corporativa — Grupo Flexível

Plataforma interna de comunicação visual para TVs e monitores da empresa.
As TVs funcionam apenas como **navegador em modo quiosque** apontando para uma
URL da rede interna — **sem player instalado**. Um **servidor central** entrega o
conteúdo para todas as telas, e um **painel administrativo** (com login) permite
montar grades de slides, rodapés e indicadores.

## Estrutura do projeto

```
tv corporativa/
├── iniciar_servidor.bat      ← clique aqui para ligar o servidor (Windows)
├── requirements.txt          ← dependências Python
├── backend/
│   └── server.py             ← servidor central (Flask)
├── frontend/
│   ├── login.html            ← tela de login do admin
│   ├── admin.html            ← painel de administração
│   ├── display.html          ← tela exibida nas TVs
│   └── *.html                ← guias e documentação
├── integrations/
│   └── integracao_kpi.py     ← atualiza KPIs a partir de Excel/CSV
├── tests/
│   └── teste_carga.py        ← teste de carga (várias TVs simultâneas)
├── scripts/
│   └── setup_tv.bat          ← configura uma TV em modo quiosque
├── docs/                     ← documento mestre e cronogramas
├── data/                     ← (gerado) content.json, usuários, sessão
└── uploads/                  ← (gerado) imagens e vídeos enviados
```

> `data/` e `uploads/` são criados automaticamente na primeira execução.

## Como rodar com Docker (recomendado)

Não precisa instalar Python. Basta ter o **Docker Desktop** instalado
(https://www.docker.com/products/docker-desktop).

Abra um terminal **na pasta do projeto** e rode:

```bash
docker compose up -d --build
```

Pronto. Acesse o painel em **http://localhost:8080/admin**


Comandos úteis:

```bash
docker compose logs -f      # ver os logs do servidor
docker compose down         # parar o servidor
docker compose up -d        # ligar de novo (sem rebuild)
```

Os dados (conteúdo, usuários, senha e uploads) ficam nas pastas `data/` e
`uploads/` do seu computador, então **persistem mesmo recriando o container**.

## Como rodar sem Docker (alternativa)

1. Instale o [Python 3.10+](https://python.org) (marque *Add Python to PATH*).
2. Dê dois cliques em **`iniciar_servidor.bat`**.
   Ele instala as dependências e sobe o servidor.
3. Acesse o painel: **http://localhost:8080/admin**



## Como configurar as TVs

Em cada PC/player de TV, rode **`scripts/setup_tv.bat`** como Administrador.
Ele cria o atalho em modo quiosque, agenda ligar/desligar e impede a tela de apagar.
A TV abrirá automaticamente uma URL como:

```
http://<IP-DO-SERVIDOR>:8080/tela/recepcao
http://<IP-DO-SERVIDOR>:8080/tela/producao
```

O *slug* (`recepcao`, `producao`, ...) é definido no painel admin, em **TVs**.

## Arquitetura (como tudo se conecta)

```
  Excel/CSV ──► integracao_kpi.py ──┐
                                    ▼
   Admin (login) ──POST /api/content──►  data/content.json  ◄──┐
                                    ▲                            │
                                    └──GET /api/content──────────┘
                                              ▲
                          TVs (display) ──────┘  (sincroniza a cada 60s)
```

- O **servidor** é a fonte única de verdade (`data/content.json`).
- O **admin** salva no servidor; as **TVs** buscam do servidor e atualizam sozinhas.
- A integração de KPIs escreve direto no `data/content.json`.

## Segurança

- O painel admin e todas as rotas de escrita exigem **login** (senha com hash).
- As URLs das TVs (`/tela/...`) são públicas na rede interna, sem token — conforme
  premissa do projeto.
- Uploads aceitam apenas imagens/vídeos (whitelist) e têm limite de 300 MB.

## Testes

```
# Com o servidor rodando:
python tests/teste_carga.py --ip 192.168.1.10 --telas 20 --duracao 60
```

## Integração de KPIs (opcional)

```
set TV_KPI_USER=usuario_do_painel
set TV_KPI_PASS=senha
python integrations/integracao_kpi.py
```

Lê indicadores de um Excel/CSV e atualiza o slide de KPI **via API do servidor**
(faz login com as credenciais acima — use um usu�