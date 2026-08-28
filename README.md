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

Pronto. Acesse o painel em:

- **https://tv.grupoflexivel.com.br/admin** (HTTPS, porta 443)
- **http://localhost:8080/admin** (acesso local direto, mantido para suporte)

O proxy Caddy emite e renova automaticamente um certificado pela CA interna dele.
O DNS interno de `tv.grupoflexivel.com.br` deve apontar para o IP do servidor e
as portas TCP 80/443 precisam estar liberadas na máquina. Libere também UDP 443
caso queira disponibilizar HTTP/3.

Como o nome existe apenas no DNS interno, instale a CA raiz do Caddy como uma
autoridade confiável nos computadores das TVs e dos administradores. Depois da
primeira inicialização, execute como Administrador no servidor Windows:

```bat
docker compose cp https-proxy:/data/caddy/pki/authorities/local/root.crt "%TEMP%\tv-caddy-root.crt"
certutil -addstore -f "ROOT" "%TEMP%\tv-caddy-root.crt"
```

Distribua o mesmo arquivo `tv-caddy-root.crt` para os players (de preferência
por Política de Grupo) e instale-o em **Autoridades de Certificação Raiz
Confiáveis**. Sem isso, o navegador avisará que o certificado não é confiável.

Se no futuro o domínio for publicado no DNS da internet e 80/443 forem
encaminhadas externamente para este servidor, remova a linha `tls internal` de
`caddy/Caddyfile`; o Caddy passará a usar uma autoridade pública automaticamente.


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
https://tv.grupoflexivel.com.br/tela/recepcao
https://tv.grupoflexivel.com.br/tela/producao
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
- O **admin** salva no servidor; as **TVs** buscam do servidor e atualizam sozinhas.
- A integração de KPIs autentica na API e atualiza o slide de KPI.

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
