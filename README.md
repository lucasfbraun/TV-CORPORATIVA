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
│   ├── server.py             ← ponto de entrada (cria o app e registra as rotas)
│   ├── config.py             ← caminhos, constantes e conteúdo padrão
│   ├── db.py                 ← camada de dados (PostgreSQL)
│   ├── storage.py            ← documentos: conteúdo, usuários, perfis
│   ├── security.py           ← autenticação e permissões
│   ├── mailer.py             ← SMTP e envio de e-mail
│   ├── migration.py          ← init do banco + migração de dados legados
│   ├── grafana.py            ← workers de captura (Playwright)
│   └── *_routes.py           ← rotas por área (auth, users, system, content,
│                                integrations, media, pages)
├── frontend/
│   ├── login.html            ← tela de login do admin
│   ├── reset.html            ← redefinição de senha
│   ├── admin.html/.css/.js   ← painel de administração
│   ├── display.html/.css/.js ← tela exibida nas TVs
│   └── assets/               ← logo e imagens fixas
├── integrations/
│   └── integracao_kpi.py     ← atualiza KPIs a partir de Excel/CSV (via API)
├── tests/
│   └── teste_carga.py        ← teste de carga (várias TVs simultâneas)
├── scripts/
│   └── setup_tv.bat          ← configura uma TV em modo quiosque
├── docs/                     ← documento mestre, cronograma, guias e manuais
├── data/                     ← (gerado) caches locais e chave de sessão
└── uploads/                  ← (gerado) capturas do Grafana e mídia legada
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
  Excel/CSV ──► integracao_kpi.py ──┐ (login + POST)
                                    ▼
   Admin (login) ──POST /api/content──►  PostgreSQL  ◄──┐
                                    ▲                     │
                                    └──GET /api/content───┘
                                              ▲
                          TVs (display) ──────┘  (sincroniza a cada 60s)
```

- O **banco PostgreSQL** é a fonte única de verdade (conteúdo, usuários, mídias).
- O **admin** salva no servidor; 