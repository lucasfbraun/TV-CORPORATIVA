# DOCUMENTO MESTRE DO PROJETO
# Plataforma Corporativa de Comunicação Visual por URL Interna

**Versão:** 1.0  
**Status:** Documento consolidado para início de arquitetura, planejamento e desenvolvimento  
**Formato recomendado para uso com agentes:** Markdown  
**Objetivo do arquivo:** Servir como fonte única de contexto para agentes de IA, Product Owner, Arquitetura, Backend, Frontend, Banco de Dados, QA, UX/UI e DevOps.

---

## 1. Resumo Executivo

Este projeto tem como objetivo desenvolver uma plataforma web interna para comunicação visual corporativa em televisões, monitores e painéis da empresa.

A solução permitirá que usuários administrativos criem grades de programação dinâmicas, adicionem conteúdos multimídia, definam tempo de exibição por item, simulem a grade antes da publicação, configurem barras informativas, insiram widgets como clima, cotação do dólar, logo, data e hora, integrem notícias por categoria, capturem prints de URLs e exibam postagens de redes sociais, como Facebook.

A principal premissa técnica é que **não haverá player instalado na TV**. A TV funcionará como um navegador acessando uma **URL interna da rede corporativa**.

Exemplo:

```text
http://display-server/tela/recepcao
http://display-server/tela/producao
http://display-server/tela/refeitorio
```

As URLs de exibição **não precisam de token**, pois o sistema será utilizado apenas dentro da rede interna da empresa.

---

## 2. Premissas Fundamentais do Projeto

1. A plataforma será utilizada dentro da rede corporativa.
2. As TVs acessarão URLs internas.
3. Não haverá aplicativo instalado na TV.
4. Não haverá player nativo instalado.
5. A exibição será feita por navegador web.
6. A TV deverá funcionar preferencialmente em modo quiosque, ou kiosk mode.
7. Cada tela terá uma URL amigável baseada em slug.
8. As URLs de exibição não terão token.
9. O controle de acesso administrativo ocorrerá apenas no painel de administração.
10. O painel administrativo exigirá autenticação.
11. A grade de programação deverá ser dinâmica e reutilizável.
12. O usuário deverá ter autonomia para montar grades, barras e widgets.
13. O sistema deverá permitir simular a programação antes da publicação.
14. O sistema deverá exibir o tempo total da grade.
15. O sistema deverá permitir integração com fontes externas, mas sem deixar a TV dependente diretamente dessas fontes.
16. O backend deverá preparar, cachear e entregar os dados para a URL de exibição.
17. O sistema deverá ser preparado para evolução futura, mas o foco inicial é ambiente interno.

---

## 3. Objetivo do Produto

Desenvolver uma plataforma web que permita transformar televisões da empresa em canais de comunicação visual corporativa, utilizando apenas URLs internas acessadas por navegador.

A plataforma deverá permitir:

- Criar e gerenciar telas.
- Criar e gerenciar grupos de telas.
- Criar grades de programação dinâmicas.
- Inserir imagens, vídeos, textos, URLs, dashboards, notícias e posts sociais.
- Definir a duração individual de cada conteúdo.
- Calcular automaticamente o tempo total da grade.
- Simular a grade antes de publicar.
- Reutilizar uma mesma grade em várias telas.
- Criar barras informativas personalizadas.
- Permitir que o usuário configure a posição da barra.
- Inserir logo na barra.
- Exibir previsão do tempo.
- Exibir cotação do dólar.
- Exibir data e hora.
- Exibir notícias por categoria, apenas com resumo.
- Exibir postagens do Facebook.
- Capturar print de uma URL e exibir como conteúdo.
- Monitorar telas online e offline.
- Registrar logs de uso, publicação, falhas e exibição.

---

## 4. Problema a Ser Resolvido

A empresa precisa comunicar informações internas em TVs corporativas de forma padronizada, dinâmica e centralizada.

Problemas atuais que o produto resolve:

- Atualização manual de TVs.
- Falta de padronização visual.
- Dificuldade para reutilizar programações em múltiplas telas.
- Dependência de pessoas técnicas para mudar conteúdos.
- Falta de autonomia para usuários de comunicação, RH, produção ou gestão.
- Dificuldade para exibir informações dinâmicas como clima, dólar, notícias e dashboards.
- Dificuldade para exibir painéis web que não possuem integração direta.
- Ausência de simulação antes da publicação.
- Ausência de monitoramento sobre o que está sendo exibido.

---

## 5. Visão do Funcionamento

Fluxo principal:

```text
Usuário Administrador
        ↓
Painel Administrativo
        ↓
Cadastro de Conteúdos
        ↓
Criação da Grade Dinâmica
        ↓
Configuração de Layout, Barra e Widgets
        ↓
Simulação da Exibição
        ↓
Publicação
        ↓
URL Interna da Tela
        ↓
TV acessando a URL no navegador
```

Exemplo prático:

1. O usuário cria a tela chamada `Recepção`.
2. O sistema gera a URL interna `/tela/recepcao`.
3. O usuário cadastra conteúdos: vídeo institucional, imagem de campanha, notícias químicas e painel solar.
4. O usuário monta uma grade:
   - Vídeo institucional: 120 segundos.
   - Imagem campanha RH: 30 segundos.
   - Print do painel solar: 60 segundos.
   - Notícia sobre produtos químicos: 45 segundos.
   - Postagem do Facebook: 45 segundos.
5. O sistema calcula o tempo total da grade.
6. O usuário simula a exibição.
7. O usuário publica a grade.
8. A TV da recepção abre `http://display-server/tela/recepcao`.
9. A grade passa a rodar automaticamente em loop.

---

## 6. Escopo do Produto

O produto será composto por:

- Painel Administrativo Web.
- Página de Exibição por URL Interna.
- API Backend.
- Banco de Dados.
- Serviço de Armazenamento de Mídias.
- Serviço de Captura de URL.
- Serviço de Notícias.
- Serviço de Integrações.
- Serviço de Widgets.
- Serviço de Monitoramento.
- Serviço de Logs e Auditoria.

---

## 7. Fora do Escopo Inicial

Os seguintes itens não fazem parte do MVP, mas podem entrar no roadmap:

- Aplicativo Android TV nativo.
- Aplicativo desktop instalado.
- Marketplace de widgets.
- Multiempresa SaaS completo.
- White label avançado.
- Inteligência artificial para gerar campanhas automaticamente.
- Integração com Instagram, LinkedIn, YouTube e TikTok.
- Editor visual avançado com múltiplas zonas complexas.
- Aprovação editorial avançada.
- Automação via MQTT ou OPC-UA.
- Integrações industriais avançadas.

---

## 8. Stakeholders

### Usuários Internos

- Comunicação interna.
- RH.
- Marketing.
- Produção.
- Gestão.
- TI.
- Segurança do trabalho.
- Operações.

### Papéis do Projeto

- Product Owner.
- Analista de requisitos.
- Arquiteto de software.
- Desenvolvedor backend.
- Desenvolvedor frontend.
- Designer UX/UI.
- Analista QA.
- DevOps.
- Administrador de infraestrutura.
- Usuário-chave para homologação.

---

## 9. Glossário

**Tela:** Ponto lógico de exibição, como recepção, refeitório ou produção.

**URL de Exibição:** Link interno acessado pela TV para mostrar a programação.

**Grade:** Sequência ordenada de conteúdos com duração individual.

**Item da Grade:** Um conteúdo específico dentro da grade.

**Layout:** Estrutura visual da tela, com zonas, barra e área principal.

**Barra Informativa:** Faixa superior, inferior ou lateral exibindo informações como logo, clima, dólar, data, hora e notícias.

**Widget:** Componente reutilizável que exibe uma informação específica.

**Captura de URL:** Recurso que acessa uma página web, tira um print e exibe esse print na grade.

**Notícia Dinâmica:** Conteúdo que busca notícias por categoria e exibe apenas resumo.

**Modo Kiosk:** Forma de executar a TV em tela cheia, sem menus e sem interação manual.

**Heartbeat:** Comunicação periódica da tela com o servidor para informar que está online.

---

# 10. Módulo de Usuários e Autenticação

## 10.1 Objetivo

Permitir que usuários autorizados acessem o painel administrativo e executem ações conforme seu perfil de permissão.

## 10.2 Perfis de Usuário

### Administrador

Acesso total ao sistema.

Pode:

- Cadastrar usuários.
- Gerenciar telas.
- Gerenciar grupos.
- Gerenciar conteúdos.
- Criar e publicar grades.
- Configurar layouts.
- Configurar barras e widgets.
- Configurar integrações.
- Visualizar logs.
- Gerenciar permissões.

### Editor

Foco em conteúdos e grades.

Pode:

- Cadastrar conteúdos.
- Criar grades.
- Editar grades.
- Simular grades.
- Salvar rascunhos.
- Publicar, se autorizado.

### Operador

Foco em operação e monitoramento.

Pode:

- Visualizar telas.
- Ver status online/offline.
- Consultar logs operacionais.
- Reiniciar exibição via interface, se implementado.

### Visualizador

Acesso somente leitura.

Pode:

- Visualizar telas cadastradas.
- Visualizar grades.
- Visualizar conteúdos.
- Visualizar monitoramento.

## 10.3 Regras de Negócio

- O painel administrativo deve exigir login.
- As URLs de exibição das TVs não exigem login.
- Usuários devem ter permissões por perfil.
- Ações críticas devem gerar logs.
- Senhas devem ser armazenadas com hash seguro.
- Sessões administrativas devem expirar após período configurável.

---

# 11. Módulo de Telas

## 11.1 Objetivo

Gerenciar os pontos de exibição da empresa.

Uma tela representa uma TV, monitor ou painel que abrirá uma URL interna no navegador.

## 11.2 Exemplos de Telas

- Recepção.
- Produção.
- Refeitório.
- RH.
- Comercial.
- Diretoria.
- Sala de reunião.
- Expedição.
- Almoxarifado.

## 11.3 Campos da Tela

- ID.
- Nome.
- Slug.
- Descrição.
- Localização.
- Grupo principal.
- Grupos adicionais.
- Grade associada.
- Layout associado.
- Status.
- Última comunicação.
- Resolução detectada.
- Navegador detectado.
- Data de criação.
- Data de atualização.

## 11.4 URL da Tela

A URL será baseada no slug da tela.

Exemplo:

```text
Nome: Recepção
Slug: recepcao
URL: http://display-server/tela/recepcao
```

Outros exemplos:

```text
http://display-server/tela/producao
http://display-server/tela/refeitorio
http://display-server/tela/rh
http://display-server/tela/comercial
```

## 11.5 Regras de Negócio

- O slug deve ser único.
- A URL não precisa de token.
- A URL não exige autenticação.
- A URL deve funcionar apenas na rede interna.
- Se uma tela estiver desativada, a URL deve exibir mensagem de tela indisponível.
- Se não houver grade publicada associada, a URL deve exibir uma tela padrão.
- Se não houver layout associado, deve ser usado um layout padrão.
- A tela deve informar heartbeat periodicamente.
- A tela deve carregar automaticamente a grade publicada mais recente.
- Quando a grade publicada for alterada, a tela deve atualizar a exibição automaticamente.

---

# 12. Modo Kiosk

## 12.1 Objetivo

Permitir que a TV funcione como uma tela dedicada à comunicação corporativa.

## 12.2 Características

- Exibição em tela cheia.
- Sem barra de endereço visível.
- Sem menus do navegador.
- Sem interação do usuário.
- Inicialização automática ao ligar a TV ou dispositivo.
- Reconexão automática.
- Atualização automática.
- Recuperação após falha.

## 12.3 Regras

- A página de exibição deve ser preparada para tela cheia.
- A interface da URL da tela não deve exibir menus administrativos.
- A página deve tentar reconectar caso perca conexão com o backend.
- Caso não consiga carregar dados novos, deve manter a última grade válida em cache quando possível.
- Deve haver uma tela de fallback para falhas graves.

---

# 13. Módulo de Grupos de Telas

## 13.1 Objetivo

Permitir organizar telas em grupos para facilitar a aplicação de grades e layouts.

## 13.2 Exemplos de Grupos

- Recepção.
- Produção.
- RH.
- Comercial.
- Refeitório.
- Filial SC.
- Filial SP.
- Segurança do trabalho.
- Diretoria.

## 13.3 Regras

- Uma tela pode pertencer a um ou mais grupos.
- Uma grade pode ser aplicada a um grupo inteiro.
- Um layout pode ser aplicado a um grupo inteiro.
- Quando uma grade for aplicada a um grupo, todas as telas do grupo devem receber a grade.
- Deve ser possível sobrescrever a grade em uma tela específica, se necessário.

---

# 14. Biblioteca de Conteúdos

## 14.1 Objetivo

Centralizar todos os conteúdos que poderão ser utilizados nas grades.

## 14.2 Tipos de Conteúdo

- Imagem.
- Vídeo.
- PDF.
- Texto.
- URL.
- Captura de URL.
- Notícias dinâmicas.
- Facebook.
- Dashboard.
- Widget.
- API externa.

## 14.3 Campos Gerais do Conteúdo

- ID.
- Nome.
- Tipo.
- Descrição.
- Categoria.
- Tags.
- Status.
- Arquivo ou URL.
- Duração sugerida.
- Validade inicial.
- Validade final.
- Criado por.
- Data de criação.
- Data de atualização.

## 14.4 Regras Gerais

- Conteúdos podem ser ativos ou inativos.
- Conteúdos inativos não devem ser exibidos em novas publicações.
- Se um conteúdo ativo em grade for desativado, a grade deve alertar inconsistência.
- Conteúdo com validade expirada não deve ser exibido.
- O sistema deve permitir pré-visualizar conteúdos.
- O sistema deve permitir organizar conteúdos por categorias e tags.

---

# 15. Conteúdo do Tipo Imagem

## 15.1 Formatos Recomendados

- JPG.
- PNG.
- WEBP.

## 15.2 Regras

- Imagem deve ter duração obrigatória quando inserida na grade.
- O sistema deve validar tamanho máximo de upload.
- O sistema pode otimizar imagem automaticamente.
- A imagem deve se adaptar ao layout configurado.
- Deve haver opções de ajuste: conter, preencher, centralizar ou cortar.

---

# 16. Conteúdo do Tipo Vídeo

## 16.1 Formatos Recomendados

- MP4.
- WEBM.

## 16.2 Regras

- O sistema deve tentar identificar a duração original do vídeo.
- O usuário pode usar a duração original.
- O usuário pode sobrescrever a duração na grade.
- Se a duração configurada for menor que a duração do vídeo, o vídeo poderá ser cortado no tempo definido.
- Se a duração configurada for maior que a duração do vídeo, o sistema poderá repetir o vídeo ou avançar para o próximo item, conforme configuração.
- O sistema deve validar tamanho máximo de upload.
- O sistema deve recomendar compressão de vídeos pesados.

---

# 17. Conteúdo do Tipo Texto

## 17.1 Objetivo

Permitir que usuários criem mensagens simples sem precisar subir imagem.

## 17.2 Campos

- Título.
- Mensagem.
- Cor de fundo.
- Cor do texto.
- Tamanho da fonte.
- Alinhamento.
- Duração sugerida.

## 17.3 Regras

- Texto deve ter duração obrigatória na grade.
- Deve respeitar o layout da tela.
- Pode ser usado em barra, widget ou conteúdo principal.

---

# 18. Conteúdo do Tipo URL

## 18.1 Objetivo

Permitir exibir uma página web diretamente dentro da grade.

## 18.2 Regras

- O usuário deve informar uma URL.
- A URL deve usar HTTP ou HTTPS.
- O sistema deve validar a URL.
- O usuário deve definir a duração de exibição.
- A URL pode ser exibida diretamente quando for compatível com iframe/navegador.
- Caso a URL não seja adequada para exibição direta, recomenda-se usar Captura de URL.

---

# 19. Captura de URL

## 19.1 Objetivo

Permitir que o usuário informe uma URL e o sistema capture um print da página para exibir na grade.

Esse recurso é importante para casos como:

- Painel solar.
- Dashboard de produção.
- Power BI.
- Grafana.
- GLPI.
- ERP.
- CRM.
- Portal interno.
- Relatórios web.
- Indicadores de operação.

## 19.2 Funcionamento

1. O usuário cadastra uma URL.
2. O sistema valida a URL.
3. O backend agenda uma captura.
4. Um serviço com navegador headless abre a página.
5. O serviço aguarda o tempo configurado.
6. O serviço tira um screenshot.
7. A imagem é salva no storage.
8. O conteúdo da grade exibe o último screenshot válido.
9. O screenshot é atualizado conforme a frequência configurada.

## 19.3 Tecnologia Recomendada

- Playwright.

Alternativas:

- Puppeteer.
- Selenium.

## 19.4 Configurações

- URL.
- Duração na grade.
- Frequência de atualização.
- Resolução da captura.
- Delay antes da captura.
- Zoom.
- Captura da tela visível.
- Captura da página inteira.
- Recorte da imagem.
- Headers customizados.
- Timeout.
- Usar último print válido em caso de erro.

## 19.5 Regras de Negócio

- O sistema deve exibir o último print válido se a nova captura falhar.
- O player web da TV não deve capturar a URL diretamente.
- A captura deve ocorrer no backend ou em worker dedicado.
- A captura deve ser assíncrona.
- A captura não deve travar a exibição da grade.
- Se nunca houver captura válida, o sistema deve exibir uma mensagem de indisponibilidade.
- O usuário deve poder forçar uma nova captura manualmente.
- O sistema deve registrar logs de captura.

## 19.6 Segurança da Captura

Mesmo em rede interna, a funcionalidade de captura de URL precisa de controle.

Regras:

- Permitir apenas HTTP e HTTPS.
- Bloquear `file://`.
- Bloquear `ftp://`.
- Bloquear `localhost`.
- Bloquear `127.0.0.1`.
- Bloquear endereços de metadados de cloud.
- Permitir acesso a URLs internas somente se estiverem em allowlist configurada pela TI.
- Permitir domínios internos autorizados, como painéis, ERPs e dashboards corporativos.
- Definir timeout obrigatório.
- Registrar tentativas de captura com falha.

---

# 20. Notícias Dinâmicas por Categoria

## 20.1 Objetivo

Permitir exibir notícias relacionadas a temas específicos dentro da grade, trazendo uma notícia nova a cada passagem ou conforme regra configurada.

Exemplo solicitado:

- Categoria: Produtos Químicos.
- Palavras-chave: produtos químicos, indústria química, segurança química.

## 20.2 Fontes Possíveis

- RSS.
- API de notícias.
- Portal próprio.
- Integrações futuras com provedores de conteúdo.

## 20.3 Dados Exibidos

A exibição deve mostrar apenas resumo da notícia, nunca a matéria completa.

Campos exibidos:

- Título.
- Resumo curto.
- Fonte.
- Data de publicação.
- Imagem de capa, se disponível e permitida.
- Categoria.
- QR Code opcional para acessar a notícia completa.

## 20.4 Regras de Negócio

- O sistema não deve copiar a matéria completa.
- O sistema deve exibir apenas título, resumo, fonte, data e imagem permitida.
- O usuário pode configurar categoria.
- O usuário pode configurar palavras-chave.
- O usuário pode configurar fontes.
- O sistema pode buscar uma nova notícia a cada execução da grade.
- O sistema pode evitar repetição.
- O sistema deve manter cache de notícias.
- A TV não deve depender diretamente do portal de notícias.
- Se não houver notícia nova, pode exibir a última válida ou pular o item, conforme configuração.
- Notícias podem ter validade máxima, como últimas 24 horas, 7 dias ou 30 dias.
- Deve ser possível ocultar notícia específica.
- Aprovação manual pode ser adicionada em versão futura.

## 20.5 Modos de Exibição

- Mais recente.
- Aleatória.
- Próxima da fila.
- Próxima sem repetir.

## 20.6 Frequência de Atualização

- A cada exibição.
- A cada X minutos.
- A cada X horas.
- Manual.

## 20.7 Repetição

Configurações:

- Permitir repetição.
- Não permitir repetição.
- Repetir somente após esgotar todas as notícias disponíveis.

---

# 21. Integração com Facebook

## 21.1 Objetivo

Permitir que postagens de uma página corporativa do Facebook sejam exibidas na grade.

## 21.2 Dados Exibidos

- Texto da postagem.
- Imagem da postagem.
- Data da publicação.
- Nome da página.
- Link ou QR Code opcional para a postagem original.

## 21.3 Integração Recomendada

- API oficial da Meta/Facebook.

Os detalhes de permissões, autenticação e limites devem ser validados na documentação vigente da Meta no momento da implementação.

## 21.4 Regras de Negócio

- O sistema deve autenticar a integração administrativa com Facebook.
- O usuário deve selecionar a página a ser usada.
- O sistema deve buscar postagens recentes.
- O sistema deve manter cache local das postagens.
- A TV não deve depender diretamente do Facebook em tempo real.
- Se a integração falhar, o sistema deve exibir o último post válido ou pular o item.
- O usuário pode ocultar posts específicos.
- O usuário pode configurar moderação automática ou manual.
- A cada execução na grade, pode exibir próximo post, post aleatório ou post mais recente.

## 21.5 Modos de Exibição

- Próximo post.
- Aleatório.
- Mais recente.

## 21.6 Moderação

- Automática.
- Manual.

---

# 22. Grade de Programação Dinâmica

## 22.1 Objetivo

Permitir que o usuário monte uma sequência dinâmica de conteúdos para exibição nas telas.

A grade é o coração do sistema.

## 22.2 Operações da Grade

- Criar.
- Editar.
- Clonar.
- Duplicar.
- Arquivar.
- Excluir.
- Salvar como rascunho.
- Validar.
- Simular.
- Publicar.

## 22.3 Estrutura da Grade

Campos principais:

- ID.
- Nome.
- Descrição.
- Status.
- Versão.
- Loop ativo.
- Tempo total.
- Quantidade de itens.
- Criado por.
- Publicado por.
- Data de criação.
- Data de publicação.

## 22.4 Estrutura do Item da Grade

Cada item da grade deve conter:

- ID.
- Grade ID.
- Conteúdo ID.
- Tipo de conteúdo.
- Ordem.
- Duração em segundos.
- Configurações específicas.
- Status.

## 22.5 Exemplo de Grade

| Ordem | Conteúdo | Tipo | Duração |
|---|---|---|---|
| 1 | Vídeo Institucional | Vídeo | 120s |
| 2 | Campanha RH | Imagem | 30s |
| 3 | Painel Solar | Captura de URL | 60s |
| 4 | Notícias Produtos Químicos | Notícias Dinâmicas | 45s |
| 5 | Facebook Empresa | Post Social | 45s |

Tempo total da grade: 300 segundos, ou 5 minutos.

## 22.6 Regras de Negócio da Grade

- Não permitir publicar grade vazia.
- Todo item deve possuir duração.
- Conteúdo inválido impede publicação.
- Conteúdo inativo deve gerar alerta.
- Conteúdo expirado deve gerar alerta.
- Tempo total deve ser recalculado automaticamente.
- Quantidade de itens deve ser recalculada automaticamente.
- Tempo médio por item deve ser recalculado automaticamente.
- O usuário pode alterar a ordem dos itens.
- O usuário pode remover itens.
- O usuário pode duplicar itens.
- O usuário pode clonar a grade.
- Uma grade clonada deve ser independente da original.
- Uma grade pode ser reutilizada em várias telas.
- Uma grade pode ser aplicada a grupos de telas.
- Alterações devem ficar em rascunho até publicação.
- A publicação deve ser explícita.
- Ao publicar, as telas associadas devem atualizar a programação.
- A grade deve rodar em loop, salvo configuração diferente.

## 22.7 Estados da Grade

- Rascunho.
- Em validação.
- Publicada.
- Arquivada.
- Inativa.

## 22.8 Loop da Grade

Por padrão, a grade deverá reiniciar automaticamente ao chegar ao fim.

Configurações futuras:

- Reiniciar automaticamente.
- Parar no fim.
- Chamar outra grade.
- Entrar em grade padrão.

---

# 23. Simulador de Grade

## 23.1 Objetivo

Permitir que o usuário visualize como a programação ficará antes de publicar.

## 23.2 Funcionalidades

- Simular ordem dos conteúdos.
- Respeitar duração de cada item.
- Mostrar tempo total da grade.
- Mostrar tempo decorrido.
- Mostrar tempo restante do item atual.
- Mostrar próximo conteúdo.
- Mostrar barra de progresso.
- Mostrar layout.
- Mostrar barra informativa.
- Mostrar widgets.
- Permitir play, pause, próximo, anterior e reiniciar.

## 23.3 Regras

- O simulador deve usar a mesma lógica da URL de exibição.
- O simulador deve alertar se houver conteúdo inválido.
- O simulador deve permitir testar a grade antes da publicação.
- A simulação não publica automaticamente a grade.
- A simulação deve ser acessível no painel administrativo.

---

# 24. Layouts

## 24.1 Objetivo

Definir a estrutura visual da tela.

O layout define onde o conteúdo principal, barras, widgets e elementos visuais serão exibidos.

## 24.2 Zonas

- Zona principal.
- Zona superior.
- Zona inferior.
- Zona esquerda.
- Zona direita.
- Overlay.

## 24.3 Resoluções Suportadas

- Full HD.
- 2K.
- 4K.
- Ultrawide.

## 24.4 Regras

- Toda tela deve possuir um layout.
- Se nenhuma configuração for definida, usar layout padrão.
- O layout deve ser responsivo.
- Uma grade pode ser exibida em layouts diferentes.
- Layouts podem ser clonados.
- Layouts clonados devem ser independentes.
- Alterações em layout publicado devem passar por rascunho e publicação.

---

# 25. Barra Informativa Personalizável

## 25.1 Objetivo

Permitir que o usuário crie uma barra de informações com autonomia, escolhendo onde ela ficará e quais dados serão exibidos.

## 25.2 Posições

- Superior.
- Inferior.
- Lateral esquerda.
- Lateral direita.

## 25.3 Configurações Visuais

- Cor de fundo.
- Cor do texto.
- Fonte.
- Tamanho da fonte.
- Transparência.
- Altura.
- Largura.
- Espaçamento.
- Velocidade de rolagem.
- Logo.
- Ordem dos widgets.

## 25.4 Conteúdos da Barra

- Logo da empresa.
- Clima.
- Cotação do dólar.
- Data.
- Hora.
- Notícias.
- Texto livre.
- Comunicados.
- Indicadores.
- QR Code.
- APIs externas.

## 25.5 Regras

- A barra pode ser associada a um layout ou grade.
- A barra deve poder ser reutilizada.
- A barra deve poder ser clonada.
- A barra clonada deve ser independente.
- O usuário deve poder escolher a posição da barra.
- O usuário deve poder inserir logo.
- O usuário deve poder ordenar widgets.
- A barra não deve prejudicar a exibição do conteúdo principal.
- A barra deve se adaptar à resolução da tela.

---

# 26. Sistema de Widgets

## 26.1 Objetivo

Permitir que informações dinâmicas sejam adicionadas à barra ou ao layout.

## 26.2 Widgets Nativos

- Logo.
- Relógio.
- Data.
- Clima.
- Cotação do dólar.
- Cotação do euro.
- Bitcoin.
- Texto livre.
- Texto rolante.
- RSS.
- QR Code.
- Indicador.
- Imagem.
- API externa.

## 26.3 Regras

- Widgets podem ser adicionados à barra.
- Widgets podem ser removidos.
- Widgets podem ser reordenados.
- Widgets podem ter configurações próprias.
- Widgets devem usar cache quando dependerem de fonte externa.
- Se uma fonte externa falhar, o widget deve exibir último dado válido ou estado de indisponibilidade.

---

# 27. Widget de Clima

## 27.1 Dados

- Temperatura.
- Sensação térmica.
- Umidade.
- Previsão.
- Cidade.
- Ícone climático.

## 27.2 Regras

- O usuário deve configurar a cidade.
- O sistema deve atualizar automaticamente.
- O sistema deve usar cache.
- Se a API falhar, exibir último dado válido.

---

# 28. Widget de Cotação

## 28.1 Moedas

- Dólar.
- Euro.
- Bitcoin.

## 28.2 Regras

- O sistema deve buscar cotações automaticamente.
- O usuário pode escolher quais moedas exibir.
- O sistema deve usar cache.
- Se a API falhar, exibir último dado válido.

---

# 29. Widget API Externa

## 29.1 Objetivo

Permitir ao usuário criar widgets baseados em APIs personalizadas.

## 29.2 Configurações

- URL.
- Método HTTP.
- Headers.
- Token.
- Corpo da requisição, se necessário.
- JSONPath para extrair valor.
- Nome do campo.
- Sufixo ou prefixo.
- Frequência de atualização.

## 29.3 Regras

- O sistema deve validar a configuração.
- O sistema deve executar a requisição no backend.
- A TV não deve chamar APIs externas diretamente.
- O resultado deve ser cacheado.
- Falhas devem ser registradas.
- Tokens devem ser armazenados de forma segura.

---

# 30. Dashboards Corporativos

## 30.1 Objetivo

Permitir exibição de painéis e indicadores de sistemas corporativos.

## 30.2 Exemplos

- Painel solar.
- Power BI.
- Grafana.
- Metabase.
- Looker Studio.
- GLPI.
- ERP.
- CRM.
- N8N.
- Sistemas internos.

## 30.3 Formas de Exibição

- URL direta.
- Captura de URL.
- Widget API.
- Imagem exportada.

## 30.4 Regras

- Preferir captura de URL quando o painel não for adequado para iframe.
- Preferir widget API quando o objetivo for exibir apenas indicadores.
- Usar cache para reduzir carga nos sistemas internos.

---

# 31. Campanhas

## 31.1 Objetivo

Permitir que conteúdos tenham período de validade.

## 31.2 Campos

- Nome.
- Descrição.
- Data inicial.
- Data final.
- Conteúdos associados.
- Prioridade.
- Status.

## 31.3 Regras

- Conteúdo de campanha só deve ser exibido dentro do período configurado.
- Após a data final, o conteúdo deve ser removido automaticamente da exibição.
- Campanhas podem ser usadas para eventos, comunicados e ações temporárias.
- Campanhas podem ter prioridade normal, alta ou emergencial.

---

# 32. Prioridade de Conteúdo

## 32.1 Níveis

- Normal.
- Alta.
- Emergencial.

## 32.2 Regras

- Conteúdo normal segue a grade padrão.
- Conteúdo de alta prioridade pode aparecer com destaque ou mais frequência.
- Conteúdo emergencial interrompe a programação.

---

# 33. Conteúdo Emergencial

## 33.1 Objetivo

Permitir interromper todas as grades para exibir uma mensagem urgente.

## 33.2 Exemplos

- Incêndio.
- Evacuação.
- Acidente.
- Parada de produção.
- Alerta de segurança.
- Comunicado crítico.

## 33.3 Regras

- Conteúdo emergencial tem prioridade máxima.
- Deve substituir imediatamente a programação normal.
- Pode ser aplicado a todas as telas ou grupos específicos.
- Deve ter controle de ativação e desativação.
- Deve registrar logs de ativação e encerramento.

---

# 34. Página de Exibição por URL Interna

## 34.1 Objetivo

Substituir o conceito de player instalado.

A página de exibição é a aplicação web acessada pela TV.

## 34.2 Exemplo

```text
http://display-server/tela/recepcao
```

## 34.3 Responsabilidades

- Carregar a tela pelo slug.
- Buscar layout publicado.
- Buscar grade publicada.
- Exibir conteúdo em loop.
- Exibir barra informativa.
- Exibir widgets.
- Enviar heartbeat.
- Atualizar programação quando houver nova publicação.
- Tratar falhas de conexão.
- Usar cache local quando possível.

## 34.4 Regras

- Não exibir menus administrativos.
- Não exigir login.
- Não usar token.
- Deve funcionar em tela cheia.
- Deve se adaptar à resolução detectada.
- Deve manter exibição mesmo com instabilidade temporária.
- Deve exibir fallback se não houver grade.

---

# 35. Monitoramento

## 35.1 Objetivo

Permitir acompanhar quais telas estão online e o que estão exibindo.

## 35.2 Heartbeat

Cada tela deve enviar periodicamente informações ao backend.

Dados enviados:

- Tela ID.
- Slug.
- Status online.
- Data/hora da última comunicação.
- Resolução.
- Navegador.
- Grade ativa.
- Layout ativo.
- Item atual da grade.
- Erros recentes.

## 35.3 Dashboard de Monitoramento

Exibir:

- Total de telas.
- Telas online.
- Telas offline.
- Última comunicação.
- Grade atual.
- Layout atual.
- Erros de sincronização.
- Erros de captura.
- Erros de integração.

## 35.4 Regras

- Se uma tela não enviar heartbeat dentro do tempo configurado, marcar como offline.
- O histórico de status deve ser registrado.
- O operador deve conseguir filtrar por grupo.
- O operador deve conseguir ver a última grade publicada em cada tela.

---

# 36. Logs e Auditoria

## 36.1 Eventos a Registrar

- Login.
- Logout.
- Criação de usuário.
- Alteração de permissão.
- Criação de tela.
- Alteração de tela.
- Criação de conteúdo.
- Alteração de conteúdo.
- Upload de arquivo.
- Criação de grade.
- Alteração de grade.
- Publicação de grade.
- Clonagem de grade.
- Criação de layout.
- Alteração de layout.
- Criação de barra.
- Alteração de widget.
- Captura de URL.
- Falha de captura.
- Busca de notícia.
- Falha em fonte de notícia.
- Sincronização com Facebook.
- Falha de integração.
- Ativação de conteúdo emergencial.
- Desativação de conteúdo emergencial.

## 36.2 Regras

- Logs críticos devem ter usuário, data, hora e entidade afetada.
- Logs operacionais devem ser consultáveis pelo painel.
- Logs técnicos podem ser enviados para ferramenta de observabilidade.

---

# 37. Requisitos Funcionais

## Usuários e Permissões

RF001 - O sistema deve permitir login no painel administrativo.
RF002 - O sistema deve permitir logout.
RF003 - O sistema deve permitir cadastro de usuários.
RF004 - O sistema deve permitir edição de usuários.
RF005 - O sistema deve permitir desativação de usuários.
RF006 - O sistema deve permitir perfis de acesso.
RF007 - O sistema deve controlar permissões por perfil.

## Telas

RF008 - O sistema deve permitir cadastrar telas.
RF009 - O sistema deve permitir editar telas.
RF010 - O sistema deve permitir desativar telas.
RF011 - O sistema deve permitir configurar slug da tela.
RF012 - O sistema deve gerar URL interna baseada no slug.
RF013 - O sistema deve permitir associar grade à tela.
RF014 - O sistema deve permitir associar layout à tela.
RF015 - O sistema deve permitir visualizar status da tela.

## Grupos

RF016 - O sistema deve permitir criar grupos de telas.
RF017 - O sistema deve permitir editar grupos.
RF018 - O sistema deve permitir associar telas a grupos.
RF019 - O sistema deve permitir aplicar grade a um grupo.
RF020 - O sistema deve permitir aplicar layout a um grupo.

## Conteúdos

RF021 - O sistema deve permitir upload de imagens.
RF022 - O sistema deve permitir upload de vídeos.
RF023 - O sistema deve permitir cadastro de textos.
RF024 - O sistema deve permitir cadastro de URLs.
RF025 - O sistema deve permitir cadastro de conteúdo do tipo captura de URL.
RF026 - O sistema deve permitir cadastro de conteúdo do tipo notícias dinâmicas.
RF027 - O sistema deve permitir cadastro de conteúdo do tipo Facebook.
RF028 - O sistema deve permitir categorizar conteúdos.
RF029 - O sistema deve permitir definir tags.
RF030 - O sistema deve permitir pré-visualizar conteúdos.

## Grade

RF031 - O sistema deve permitir criar grades.
RF032 - O sistema deve permitir editar grades.
RF033 - O sistema deve permitir clonar grades.
RF034 - O sistema deve permitir arquivar grades.
RF035 - O sistema deve permitir excluir grades não publicadas.
RF036 - O sistema deve permitir salvar grade como rascunho.
RF037 - O sistema deve permitir inserir conteúdos na grade.
RF038 - O sistema deve permitir definir duração por item.
RF039 - O sistema deve permitir reordenar itens.
RF040 - O sistema deve permitir duplicar itens.
RF041 - O sistema deve permitir remover itens.
RF042 - O sistema deve calcular tempo total da grade.
RF043 - O sistema deve calcular quantidade de itens.
RF044 - O sistema deve calcular tempo médio dos itens.
RF045 - O sistema deve validar grade antes da publicação.
RF046 - O sistema deve permitir publicar grade.
RF047 - O sistema deve permitir reutilizar grade em várias telas.
RF048 - O sistema deve permitir associar grade a grupos.

## Simulador

RF049 - O sistema deve permitir simular uma grade.
RF050 - O simulador deve respeitar ordem dos itens.
RF051 - O simulador deve respeitar duração dos itens.
RF052 - O simulador deve exibir tempo total.
RF053 - O simulador deve exibir tempo restante do item atual.
RF054 - O simulador deve exibir próximo item.
RF055 - O simulador deve exibir barra de progresso.
RF056 - O simulador deve permitir play, pause, próximo, anterior e reiniciar.

## Layouts e Barras

RF057 - O sistema deve permitir criar layouts.
RF058 - O sistema deve permitir editar layouts.
RF059 - O sistema deve permitir clonar layouts.
RF060 - O sistema deve permitir configurar zonas.
RF061 - O sistema deve permitir criar barra informativa.
RF062 - O sistema deve permitir escolher posição da barra.
RF063 - O sistema deve permitir configurar aparência da barra.
RF064 - O sistema deve permitir inserir logo na barra.
RF065 - O sistema deve permitir adicionar widgets à barra.
RF066 - O sistema deve permitir reordenar widgets.

## Widgets

RF067 - O sistema deve permitir widget de relógio.
RF068 - O sistema deve permitir widget de data.
RF069 - O sistema deve permitir widget de clima.
RF070 - O sistema deve permitir widget de cotação do dólar.
RF071 - O sistema deve permitir widget de texto livre.
RF072 - O sistema deve permitir widget de RSS.
RF073 - O sistema deve permitir widget de QR Code.
RF074 - O sistema deve permitir widget de API externa.

## Captura de URL

RF075 - O sistema deve permitir informar URL para captura.
RF076 - O sistema deve capturar print automaticamente.
RF077 - O sistema deve permitir configurar frequência de captura.
RF078 - O sistema deve permitir configurar resolução da captura.
RF079 - O sistema deve permitir configurar delay antes da captura.
RF080 - O sistema deve armazenar a imagem capturada.
RF081 - O sistema deve exibir último print válido em caso de falha.
RF082 - O sistema deve registrar falhas de captura.

## Notícias

RF083 - O sistema deve permitir configurar fontes de notícias.
RF084 - O sistema deve permitir filtrar notícias por categoria.
RF085 - O sistema deve permitir filtrar notícias por palavra-chave.
RF086 - O sistema deve exibir apenas resumo da notícia.
RF087 - O sistema deve alternar notícia a cada execução, se configurado.
RF088 - O sistema deve evitar repetição, se configurado.
RF089 - O sistema deve armazenar cache de notícias.

## Facebook

RF090 - O sistema deve permitir configurar integração com Facebook.
RF091 - O sistema deve permitir selecionar página.
RF092 - O sistema deve buscar postagens recentes.
RF093 - O sistema deve exibir texto, imagem, data e página.
RF094 - O sistema deve alternar posts conforme configuração.
RF095 - O sistema deve armazenar cache de postagens.
RF096 - O sistema deve permitir ocultar posts específicos.

## Exibição por URL

RF097 - O sistema deve disponibilizar URL interna para cada tela.
RF098 - A URL deve carregar a grade publicada.
RF099 - A URL deve carregar o layout publicado.
RF100 - A URL deve exibir conteúdos em loop.
RF101 - A URL deve exibir barra e widgets.
RF102 - A URL deve enviar heartbeat.
RF103 - A URL deve atualizar programação após nova publicação.
RF104 - A URL deve exibir fallback quando não houver grade.

## Monitoramento e Logs

RF105 - O sistema deve exibir dashboard de telas online/offline.
RF106 - O sistema deve registrar heartbeat das telas.
RF107 - O sistema deve registrar logs administrativos.
RF108 - O sistema deve registrar logs de exibição.
RF109 - O sistema deve registrar logs de integração.
RF110 - O sistema deve registrar logs de erros.

## Emergência

RF111 - O sistema deve permitir criar conteúdo emergencial.
RF112 - O sistema deve permitir ativar conteúdo emergencial.
RF113 - O sistema deve interromper programação normal durante emergência.
RF114 - O sistema deve permitir aplicar emergência a todas as telas ou grupos.
RF115 - O sistema deve permitir desativar emergência.

---

# 38. Requisitos Não Funcionais

RNF001 - O painel administrativo deve exigir autenticação.
RNF002 - A URL de exibição não deve exigir autenticação.
RNF003 - A URL de exibição deve funcionar apenas na rede interna.
RNF004 - O sistema deve usar HTTPS sempre que possível, mesmo em rede interna.
RNF005 - O sistema deve possuir controle de permissões.
RNF006 - Senhas devem ser armazenadas com hash seguro.
RNF007 - Tokens de integrações devem ser armazenados de forma segura.
RNF008 - O sistema deve respeitar LGPD.
RNF009 - O sistema deve possuir logs de auditoria.
RNF010 - O sistema deve possuir cache para dados externos.
RNF011 - O sistema deve possuir cache para a última grade válida.
RNF012 - A TV não deve depender diretamente de APIs externas.
RNF013 - O sistema deve ter timeout para integrações externas.
RNF014 - O sistema deve ter timeout para captura de URL.
RNF015 - O sistema deve otimizar imagens.
RNF016 - O sistema deve limitar tamanho de upload.
RNF017 - O sistema deve ser responsivo para diferentes resoluções.
RNF018 - A página de exibição deve ser leve.
RNF019 - A página de exibição deve suportar execução contínua.
RNF020 - A página de exibição deve tratar perda de conexão.
RNF021 - A página de exibição deve tentar reconectar automaticamente.
RNF022 - O sistema deve suportar centenas de telas simultâneas no ambiente interno.
RNF023 - O backend deve separar operações pesadas em filas.
RNF024 - Capturas de URL devem ser assíncronas.
RNF025 - Atualizações de notícias devem ser assíncronas.
RNF026 - Integrações sociais devem ser assíncronas.
RNF027 - O sistema deve permitir backup periódico.
RNF028 - O sistema deve permitir restauração de dados.
RNF029 - O sistema deve possuir logs técnicos centralizados.
RNF030 - A disponibilidade alvo deve ser 99,9% no ambiente interno.

---

# 39. Regras de Negócio Consolidadas

## Regras de URLs Internas

RN-URL-001 - Cada tela terá uma URL interna baseada em slug.
RN-URL-002 - A URL não terá token.
RN-URL-003 - A URL não exigirá login.
RN-URL-004 - O acesso será controlado pela rede interna.
RN-URL-005 - Slugs devem ser únicos.
RN-URL-006 - Tela inativa deve exibir aviso de indisponibilidade.
RN-URL-007 - Tela sem grade deve exibir fallback.
RN-URL-008 - Tela sem layout deve usar layout padrão.

## Regras de Grade

RN-GRD-001 - Grade vazia não pode ser publicada.
RN-GRD-002 - Todo item precisa de duração.
RN-GRD-003 - Duração deve ser informada em segundos.
RN-GRD-004 - O sistema deve recalcular tempo total automaticamente.
RN-GRD-005 - Alterações ficam em rascunho até publicação.
RN-GRD-006 - Publicação deve ser ação explícita.
RN-GRD-007 - Grade pode ser reutilizada em várias telas.
RN-GRD-008 - Grade pode ser aplicada a grupos.
RN-GRD-009 - Clonagem cria entidade independente.
RN-GRD-010 - Conteúdo inválido impede publicação.
RN-GRD-011 - Conteúdo expirado impede ou alerta publicação.
RN-GRD-012 - Grade publicada deve ter versão.
RN-GRD-013 - Deve ser possível restaurar versão em roadmap futuro.

## Regras de Conteúdo

RN-CON-001 - Imagem precisa de duração na grade.
RN-CON-002 - Vídeo pode usar duração original.
RN-CON-003 - Vídeo pode ter duração sobrescrita.
RN-CON-004 - URL direta precisa de duração.
RN-CON-005 - Captura de URL precisa de última imagem válida para exibição.
RN-CON-006 - Notícias exibem somente resumo.
RN-CON-007 - Facebook deve usar cache.
RN-CON-008 - Conteúdos inativos não devem ser usados em novas publicações.
RN-CON-009 - Conteúdo vencido não deve ser exibido.

## Regras de Barra

RN-BAR-001 - Barra pode ficar no topo, rodapé, lateral esquerda ou lateral direita.
RN-BAR-002 - Barra deve aceitar logo.
RN-BAR-003 - Barra deve aceitar widgets.
RN-BAR-004 - Usuário pode ordenar widgets.
RN-BAR-005 - Barra pode ser clonada.
RN-BAR-006 - Barra clonada deve ser independente.
RN-BAR-007 - Barra deve se adaptar à resolução.

## Regras de Widgets

RN-WDG-001 - Widgets externos devem usar cache.
RN-WDG-002 - Falha externa deve exibir último dado válido quando possível.
RN-WDG-003 - Widget API deve ser executado pelo backend.
RN-WDG-004 - A TV não deve chamar API externa diretamente.
RN-WDG-005 - Tokens devem ser protegidos.

## Regras de Captura de URL

RN-CAP-001 - Captura deve ocorrer no backend ou worker.
RN-CAP-002 - Captura deve usar Playwright ou tecnologia similar.
RN-CAP-003 - Captura deve ser assíncrona.
RN-CAP-004 - Falha de captura não deve travar a grade.
RN-CAP-005 - Sistema deve exibir último print válido.
RN-CAP-006 - URLs internas só devem ser permitidas via allowlist.
RN-CAP-007 - Bloquear protocolos inseguros.
RN-CAP-008 - Registrar logs de captura.

## Regras de Notícias

RN-NOT-001 - Exibir apenas resumo.
RN-NOT-002 - Não exibir matéria completa.
RN-NOT-003 - Permitir categoria.
RN-NOT-004 - Permitir palavras-chave.
RN-NOT-005 - Permitir fonte RSS ou API.
RN-NOT-006 - Permitir nova notícia a cada execução.
RN-NOT-007 - Permitir evitar repetição.
RN-NOT-008 - Usar cache.
RN-NOT-009 - Exibir última notícia válida em falha, se configurado.

## Regras de Facebook

RN-FBK-001 - Usar API oficial sempre que possível.
RN-FBK-002 - Buscar posts recentes da página configurada.
RN-FBK-003 - Exibir texto, imagem, data e página.
RN-FBK-004 - Usar cache.
RN-FBK-005 - Permitir ocultar posts.
RN-FBK-006 - Permitir moderação automática ou manual.
RN-FBK-007 - Falha no Facebook não deve travar a exibição.

## Regras de Emergência

RN-EMG-001 - Conteúdo emergencial tem prioridade máxima.
RN-EMG-002 - Conteúdo emergencial interrompe grade normal.
RN-EMG-003 - Pode ser aplicado a todas as telas ou grupos.
RN-EMG-004 - Deve ter ativação e desativação manual.
RN-EMG-005 - Deve gerar logs.

---

# 40. Modelo Conceitual de Dados

## Entidades Principais

- User.
- Role.
- Screen.
- ScreenGroup.
- Content.
- Schedule.
- ScheduleItem.
- Layout.
- LayoutZone.
- InfoBar.
- Widget.
- Campaign.
- NewsSource.
- NewsItem.
- FacebookIntegration.
- FacebookPost.
- UrlCapture.
- EmergencyContent.
- Heartbeat.
- AuditLog.
- IntegrationLog.

## User

Campos:

- id.
- name.
- email.
- password_hash.
- role_id.
- status.
- created_at.
- updated_at.

## Role

Campos:

- id.
- name.
- permissions.

## Screen

Campos:

- id.
- name.
- slug.
- description.
- location.
- status.
- layout_id.
- schedule_id.
- last_heartbeat_at.
- detected_resolution.
- detected_browser.
- created_at.
- updated_at.

## ScreenGroup

Campos:

- id.
- name.
- description.
- created_at.
- updated_at.

Relacionamento:

- Screen N:N ScreenGroup.

## Content

Campos:

- id.
- name.
- description.
- type.
- category.
- tags.
- status.
- file_url.
- external_url.
- suggested_duration.
- valid_from.
- valid_until.
- metadata.
- created_by.
- created_at.
- updated_at.

## Schedule

Campos:

- id.
- name.
- description.
- status.
- version.
- loop_enabled.
- total_duration_seconds.
- items_count.
- average_item_duration.
- published_at.
- published_by.
- created_by.
- created_at.
- updated_at.

## ScheduleItem

Campos:

- id.
- schedule_id.
- content_id.
- order_index.
- duration_seconds.
- item_config.
- status.
- created_at.
- updated_at.

## Layout

Campos:

- id.
- name.
- description.
- status.
- resolution_target.
- config_json.
- created_at.
- updated_at.

## InfoBar

Campos:

- id.
- name.
- position.
- style_config.
- status.
- created_at.
- updated_at.

## Widget

Campos:

- id.
- name.
- type.
- config_json.
- refresh_interval_seconds.
- cache_ttl_seconds.
- status.
- created_at.
- updated_at.

## UrlCapture

Campos:

- id.
- content_id.
- url.
- resolution_width.
- resolution_height.
- delay_seconds.
- zoom.
- crop_config.
- refresh_interval_seconds.
- last_capture_url.
- last_success_at.
- last_error.
- status.
- created_at.
- updated_at.

## NewsSource

Campos:

- id.
- name.
- type.
- url.
- category.
- keywords.
- refresh_interval_seconds.
- status.
- created_at.
- updated_at.

## NewsItem

Campos:

- id.
- source_id.
- title.
- summary.
- source_name.
- image_url.
- original_url.
- published_at.
- category.
- keywords.
- display_count.
- last_displayed_at.
- status.
- created_at.
- updated_at.

## FacebookIntegration

Campos:

- id.
- page_id.
- page_name.
- access_token_encrypted.
- refresh_config.
- status.
- created_at.
- updated_at.

## FacebookPost

Campos:

- id.
- integration_id.
- post_external_id.
- text.
- image_url.
- original_url.
- published_at.
- display_count.
- last_displayed_at.
- status.
- created_at.
- updated_at.

## EmergencyContent

Campos:

- id.
- title.
- message.
- media_url.
- target_type.
- target_ids.
- active.
- activated_at.
- deactivated_at.
- created_by.
- created_at.
- updated_at.

## Heartbeat

Campos:

- id.
- screen_id.
- status.
- current_schedule_id.
- current_layout_id.
- current_item_id.
- browser.
- resolution.
- error_message.
- created_at.

## AuditLog

Campos:

- id.
- user_id.
- action.
- entity_type.
- entity_id.
- before_data.
- after_data.
- ip_address.
- created_at.

---

# 41. Arquitetura Técnica Recomendada

## 41.1 Frontend Administrativo

Recomendado:

- React.
- Next.js.
- TypeScript.
- TailwindCSS ou Material UI.

Responsabilidades:

- Login.
- Dashboard.
- CRUD de telas.
- CRUD de conteúdos.
- Editor de grade.
- Simulador.
- Editor de barra.
- Editor de widgets.
- Configuração de integrações.
- Monitoramento.

## 41.2 Página de Exibição

Pode usar o mesmo projeto Next.js ou aplicação separada.

Responsabilidades:

- Rota `/tela/[slug]`.
- Renderização em tela cheia.
- Execução da grade.
- Renderização de layout, barra e widgets.
- Heartbeat.
- Atualização automática.
- Cache local.

## 41.3 Backend

Recomendado:

- NestJS.
- API REST.
- WebSocket ou Server-Sent Events para atualização de telas.

Responsabilidades:

- Autenticação.
- Regras de negócio.
- CRUDs.
- Publicação de grades.
- Integrações.
- Capturas.
- Cache.
- Logs.

## 41.4 Banco de Dados

Recomendado:

- PostgreSQL.

## 41.5 Cache

Recomendado:

- Redis.

Usos:

- Dados de widgets.
- Notícias.
- Cotações.
- Clima.
- Facebook.
- Última grade publicada.
- Status de telas.

## 41.6 Storage

Recomendado para ambiente interno:

- MinIO.

Alternativas:

- S3.
- Storage local gerenciado.

Usos:

- Imagens.
- Vídeos.
- Prints de URL.
- Assets de layout.
- Logos.

## 41.7 Filas

Recomendado:

- BullMQ com Redis.

Jobs:

- Capturar URL.
- Atualizar notícias.
- Atualizar clima.
- Atualizar cotações.
- Sincronizar Facebook.
- Processar vídeos.
- Gerar thumbnails.

## 41.8 Captura de URL

Recomendado:

- Playwright em worker isolado.

## 41.9 Infraestrutura

Recomendado:

- Docker.
- Docker Compose para MVP.
- Nginx ou Traefik como proxy.
- PostgreSQL.
- Redis.
- MinIO.
- Serviço backend.
- Serviço frontend.
- Worker de capturas.

---

# 42. APIs Sugeridas

## Autenticação

```text
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
```

## Usuários

```text
GET    /api/users
POST   /api/users
GET    /api/users/:id
PATCH  /api/users/:id
DELETE /api/users/:id
```

## Telas

```text
GET    /api/screens
POST   /api/screens
GET    /api/screens/:id
PATCH  /api/screens/:id
DELETE /api/screens/:id
GET    /api/screens/slug/:slug/public-state
POST   /api/screens/:id/heartbeat
```

## Grupos

```text
GET    /api/screen-groups
POST   /api/screen-groups
PATCH  /api/screen-groups/:id
DELETE /api/screen-groups/:id
POST   /api/screen-groups/:id/apply-schedule
POST   /api/screen-groups/:id/apply-layout
```

## Conteúdos

```text
GET    /api/contents
POST   /api/contents
GET    /api/contents/:id
PATCH  /api/contents/:id
DELETE /api/contents/:id
POST   /api/contents/upload
```

## Grades

```text
GET    /api/schedules
POST   /api/schedules
GET    /api/schedules/:id
PATCH  /api/schedules/:id
DELETE /api/schedules/:id
POST   /api/schedules/:id/items
PATCH  /api/schedules/:id/items/:itemId
DELETE /api/schedules/:id/items/:itemId
POST   /api/schedules/:id/clone
POST   /api/schedules/:id/validate
POST   /api/schedules/:id/publish
GET    /api/schedules/:id/simulation
```

## Layouts

```text
GET    /api/layouts
POST   /api/layouts
GET    /api/layouts/:id
PATCH  /api/layouts/:id
DELETE /api/layouts/:id
POST   /api/layouts/:id/clone
```

## Barras

```text
GET    /api/info-bars
POST   /api/info-bars
GET    /api/info-bars/:id
PATCH  /api/info-bars/:id
DELETE /api/info-bars/:id
POST   /api/info-bars/:id/widgets
```

## Widgets

```text
GET    /api/widgets
POST   /api/widgets
GET    /api/widgets/:id
PATCH  /api/widgets/:id
DELETE /api/widgets/:id
POST   /api/widgets/:id/test
```

## Captura de URL

```text
POST /api/url-captures
POST /api/url-captures/:id/run
GET  /api/url-captures/:id/status
GET  /api/url-captures/:id/latest
```

## Notícias

```text
GET  /api/news-sources
POST /api/news-sources
POST /api/news-sources/:id/sync
GET  /api/news-items
POST /api/news-items/:id/hide
```

## Facebook

```text
GET  /api/integrations/facebook
POST /api/integrations/facebook/connect
POST /api/integrations/facebook/sync
GET  /api/integrations/facebook/posts
POST /api/integrations/facebook/posts/:id/hide
```

## Emergência

```text
GET  /api/emergency
POST /api/emergency
POST /api/emergency/:id/activate
POST /api/emergency/:id/deactivate
```

## Monitoramento

```text
GET /api/monitoring/screens
GET /api/monitoring/screens/:id
GET /api/monitoring/logs
```

---

# 43. Telas do Painel Administrativo

## 43.1 Login

- Email.
- Senha.
- Esqueci minha senha, se implementado.

## 43.2 Dashboard Inicial

Mostrar:

- Total de telas.
- Telas online.
- Telas offline.
- Grades publicadas.
- Erros recentes.
- Próximas campanhas.

## 43.3 Gestão de Telas

Funcionalidades:

- Listar telas.
- Criar tela.
- Editar tela.
- Ver URL interna.
- Copiar URL.
- Associar grade.
- Associar layout.
- Ver status.

## 43.4 Gestão de Grupos

Funcionalidades:

- Criar grupo.
- Associar telas.
- Aplicar grade ao grupo.
- Aplicar layout ao grupo.

## 43.5 Biblioteca de Conteúdos

Funcionalidades:

- Upload.
- Cadastro de URL.
- Cadastro de captura de URL.
- Cadastro de notícia dinâmica.
- Cadastro de Facebook.
- Categorização.
- Tags.
- Pré-visualização.

## 43.6 Editor de Grade

Áreas sugeridas:

1. Biblioteca de conteúdos.
2. Linha do tempo ou lista ordenada.
3. Painel de propriedades.
4. Resumo de tempo total.
5. Botão simular.
6. Botão publicar.

## 43.7 Simulador

Elementos:

- Preview da TV.
- Conteúdo atual.
- Próximo conteúdo.
- Tempo restante.
- Tempo total.
- Barra de progresso.
- Controles.

## 43.8 Editor de Layout

Funcionalidades:

- Selecionar zonas.
- Definir área principal.
- Escolher barra.
- Visualizar responsividade.

## 43.9 Editor de Barra

Funcionalidades:

- Escolher posição.
- Configurar visual.
- Adicionar logo.
- Adicionar widgets.
- Reordenar widgets.
- Pré-visualizar.

## 43.10 Integrações

Funcionalidades:

- Configurar clima.
- Configurar cotações.
- Configurar RSS.
- Configurar Facebook.
- Configurar APIs externas.
- Testar conexão.

## 43.11 Monitoramento

Funcionalidades:

- Ver telas online/offline.
- Ver última comunicação.
- Ver grade ativa.
- Ver layout ativo.
- Ver erros.

## 43.12 Emergência

Funcionalidades:

- Criar alerta emergencial.
- Selecionar destino.
- Ativar.
- Desativar.
- Ver histórico.

---

# 44. Interface da URL de Exibição

A URL de exibição deve carregar uma interface limpa, sem botões administrativos.

## Elementos

- Área principal de conteúdo.
- Barra superior, inferior ou lateral, se configurada.
- Widgets.
- Overlay emergencial, se ativo.
- Fallback de erro.

## Comportamentos

- Iniciar automaticamente.
- Rodar grade em loop.
- Respeitar duração dos itens.
- Trocar conteúdo sem intervenção.
- Atualizar grade publicada.
- Manter heartbeat.
- Recuperar de falhas.

---

# 45. Estratégia de Cache

## Cache no Backend

Usar Redis para:

- Estado publicado da tela.
- Dados de clima.
- Cotações.
- Notícias.
- Posts do Facebook.
- Último print de URL.

## Cache no Navegador da TV

Usar localStorage, IndexedDB ou Cache API para:

- Último estado válido da grade.
- Assets essenciais.
- Configuração de layout.

## Regras

- Cache não deve impedir atualização após publicação.
- Deve haver versão da grade para invalidar cache.
- Em falha temporária, usar último estado válido.

---

# 46. Estratégia de Atualização das Telas

Opções:

1. Polling periódico.
2. WebSocket.
3. Server-Sent Events.

Para MVP, polling é mais simples.

Recomendação inicial:

- A URL da tela consulta alterações a cada 30 segundos.
- Heartbeat enviado a cada 15 ou 30 segundos.
- Em versão futura, usar WebSocket ou SSE.

---

# 47. Segurança

## Painel Administrativo

- Login obrigatório.
- Senhas com hash seguro.
- RBAC.
- Logs de auditoria.
- Sessão com expiração.

## URLs de Exibição

- Sem login.
- Sem token.
- Acesso restrito pela rede interna.
- Recomenda-se firewall, VLAN ou regras de rede.

## Captura de URL

- Allowlist para domínios internos.
- Timeout obrigatório.
- Bloqueio de protocolos inseguros.
- Logs de falha.

## Integrações

- Tokens criptografados.
- Execução no backend.
- Nunca expor tokens na URL da TV.

---

# 48. PMBOK - Estrutura de Gestão do Projeto

## 48.1 Termo de Abertura

Nome do projeto:

Plataforma Corporativa de Comunicação Visual por URL Interna.

Objetivo:

Criar uma plataforma para gestão e exibição de conteúdos corporativos em TVs internas por meio de URLs locais.

Justificativa:

Centralizar a comunicação visual da empresa, reduzir atualizações manuais e permitir autonomia operacional para diferentes áreas.

Principais entregas:

- Painel administrativo.
- Gestão de telas.
- Gestão de conteúdos.
- Editor de grade dinâmica.
- Simulador.
- URL de exibição.
- Barra informativa.
- Widgets.
- Captura de URL.
- Notícias dinâmicas.
- Monitoramento.
- Logs.

## 48.2 Gerenciamento do Escopo

Escopo principal:

- Criar sistema web interno.
- Permitir criação de grades.
- Permitir exibição via URL.
- Permitir widgets e integrações.
- Permitir simulação antes da publicação.

Controle de mudanças:

- Toda nova funcionalidade deve ser registrada.
- Toda alteração de escopo deve ser avaliada por impacto em prazo, custo e arquitetura.

## 48.3 EAP - Estrutura Analítica do Projeto

1. Planejamento
   - Levantamento de requisitos.
   - Definição do MVP.
   - Definição de arquitetura.
   - Planejamento de cronograma.

2. UX/UI
   - Protótipo do painel.
   - Protótipo do editor de grade.
   - Protótipo do simulador.
   - Protótipo da URL de exibição.
   - Protótipo da barra.

3. Backend
   - Autenticação.
   - Usuários e permissões.
   - Telas e grupos.
   - Conteúdos.
   - Grades.
   - Layouts.
   - Barras e widgets.
   - Captura de URL.
   - Notícias.
   - Facebook.
   - Monitoramento.
   - Logs.

4. Frontend Administrativo
   - Login.
   - Dashboard.
   - CRUD de telas.
   - Biblioteca de conteúdos.
   - Editor de grade.
   - Simulador.
   - Editor de barra.
   - Monitoramento.

5. URL de Exibição
   - Rota por slug.
   - Renderização de grade.
   - Renderização de layout.
   - Barra e widgets.
   - Heartbeat.
   - Atualização automática.
   - Fallback.

6. Integrações
   - Clima.
   - Dólar.
   - RSS.
   - Captura de URL.
   - Facebook.

7. Testes
   - Testes unitários.
   - Testes de integração.
   - Testes da URL de exibição.
   - Testes de simulação.
   - Testes de captura.
   - Testes de monitoramento.

8. Implantação
   - Docker.
   - Banco.
   - Redis.
   - MinIO.
   - Proxy.
   - Ambiente de homologação.
   - Ambiente de produção interna.

9. Treinamento e Encerramento
   - Manual do usuário.
   - Treinamento.
   - Homologação.
   - Termo de aceite.

## 48.4 Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| Internet ou rede interna instável | Alto | Cache local e reconexão |
| TV sair do navegador | Médio | Modo kiosk |
| Vídeos muito pesados | Médio | Compressão e limites |
| Captura de URL falhar | Médio | Último print válido |
| Fonte de notícias indisponível | Baixo/Médio | Cache |
| Facebook alterar regras | Médio/Alto | Cache e validar documentação |
| Grade inválida publicada | Alto | Validação obrigatória |
| Usuário errar configuração | Médio | Simulador e pré-visualização |
| APIs internas lentas | Médio | Filas e cache |
| Falha no servidor | Alto | Backup e monitoramento |

## 48.5 Qualidade

Critérios de qualidade:

- Interface simples para usuários não técnicos.
- Grade não pode travar.
- A URL deve carregar rapidamente.
- A simulação deve refletir a exibição real.
- As integrações não devem interromper a programação.
- Logs devem permitir diagnóstico.

## 48.6 Comunicação

Ritos sugeridos:

- Reunião inicial.
- Reunião semanal de acompanhamento.
- Validação de protótipo.
- Validação do MVP.
- Homologação com usuários-chave.
- Revisão pós-implantação.

---

# 49. MVP - Versão Inicial

## 49.1 Entregas Obrigatórias

- Login administrativo.
- Perfis básicos.
- Cadastro de telas.
- URL interna por tela.
- Cadastro de grupos.
- Upload de imagens.
- Upload de vídeos.
- Cadastro de texto.
- Cadastro de URL.
- Captura de URL.
- Editor de grade dinâmica.
- Duração por item.
- Cálculo do tempo total.
- Reordenação de itens.
- Simulador básico.
- Publicação de grade.
- Associação de grade com tela.
- Associação de grade com grupo.
- Layout padrão.
- Barra inferior.
- Logo na barra.
- Widget de relógio.
- Widget de data.
- Widget de clima.
- Widget de dólar.
- Notícias via RSS com resumo.
- URL de exibição em loop.
- Heartbeat.
- Dashboard online/offline.
- Logs básicos.

## 49.2 Fora do MVP

- Facebook pode entrar na V2 se o MVP precisar ser menor.
- Editor drag and drop avançado.
- Múltiplas barras simultâneas.
- Histórico completo de versões.
- Aprovação editorial.
- Instagram, LinkedIn e YouTube.
- IA para resumo.
- Aplicativo nativo.

---

# 50. Roadmap

## V1 - MVP

Foco:

- Fluxo completo de conteúdo para URL da tela.
- Grade dinâmica.
- Simulador.
- Barra básica.
- Widgets básicos.
- Captura de URL.
- Notícias RSS.
- Monitoramento.

## V2

Foco:

- Integração com Facebook.
- Templates de layout.
- Editor drag and drop melhorado.
- Histórico de versões.
- Aprovação de conteúdo.
- Barra lateral.

## V3

Foco:

- Integrações com Power BI, Grafana e GLPI.
- Widget API avançado.
- Instagram.
- LinkedIn.
- YouTube.
- Relatórios de exibição.

## V4

Foco:

- Marketplace interno de widgets.
- IA para resumir notícias.
- IA para sugerir grade.
- White label.
- Multiempresa, se o produto evoluir para SaaS.

---

# 51. Backlog Inicial por Épicos

## Épico 1 - Autenticação e Usuários

Histórias:

- Como administrador, quero fazer login para acessar o painel.
- Como administrador, quero cadastrar usuários para delegar acesso.
- Como administrador, quero definir perfis para controlar permissões.

## Épico 2 - Telas e Grupos

Histórias:

- Como administrador, quero cadastrar uma tela para gerar sua URL interna.
- Como administrador, quero definir um slug para acessar a tela pela rede.
- Como administrador, quero agrupar telas para aplicar grades em lote.

## Épico 3 - Conteúdos

Histórias:

- Como editor, quero enviar imagens para usar nas grades.
- Como editor, quero enviar vídeos para usar nas grades.
- Como editor, quero cadastrar uma URL para exibir um portal.
- Como editor, quero cadastrar uma captura de URL para exibir um print atualizado.

## Épico 4 - Grade Dinâmica

Histórias:

- Como editor, quero criar uma grade para montar a programação.
- Como editor, quero inserir conteúdos na grade.
- Como editor, quero definir a duração de cada conteúdo.
- Como editor, quero ver o tempo total da grade.
- Como editor, quero reordenar os itens da grade.
- Como editor, quero publicar a grade para que apareça na TV.

## Épico 5 - Simulador

Histórias:

- Como editor, quero simular a grade antes de publicar.
- Como editor, quero ver o conteúdo atual e próximo conteúdo.
- Como editor, quero ver tempo restante e tempo total.

## Épico 6 - Layout e Barra

Histórias:

- Como editor, quero configurar uma barra inferior.
- Como editor, quero inserir logo na barra.
- Como editor, quero escolher widgets para a barra.

## Épico 7 - Widgets

Histórias:

- Como editor, quero exibir data e hora.
- Como editor, quero exibir clima.
- Como editor, quero exibir cotação do dólar.
- Como editor, quero exibir texto livre.

## Épico 8 - Notícias

Histórias:

- Como editor, quero configurar notícias por categoria.
- Como editor, quero buscar notícias sobre produtos químicos.
- Como editor, quero exibir apenas resumo da notícia.
- Como editor, quero evitar repetição de notícias.

## Épico 9 - Facebook

Histórias:

- Como editor, quero conectar uma página do Facebook.
- Como editor, quero exibir postagens recentes.
- Como editor, quero alternar posts na grade.

## Épico 10 - Exibição por URL

Histórias:

- Como operador, quero abrir uma URL interna na TV.
- Como usuário, quero que a TV exiba a grade publicada automaticamente.
- Como operador, quero que a TV reconecte em caso de falha.

## Épico 11 - Monitoramento

Histórias:

- Como operador, quero ver telas online e offline.
- Como operador, quero ver a última comunicação da tela.
- Como operador, quero ver qual grade está ativa.

## Épico 12 - Emergência

Histórias:

- Como administrador, quero ativar um alerta emergencial.
- Como administrador, quero interromper todas as grades.
- Como administrador, quero encerrar o alerta e voltar à programação normal.

---

# 52. Critérios de Aceite do Produto

O produto será considerado aceito quando:

1. O administrador conseguir acessar o painel.
2. O administrador conseguir cadastrar telas.
3. Cada tela possuir uma URL interna sem token.
4. A URL da tela conseguir exibir uma grade publicada.
5. O editor conseguir cadastrar imagens.
6. O editor conseguir cadastrar vídeos.
7. O editor conseguir cadastrar textos.
8. O editor conseguir cadastrar URL.
9. O editor conseguir cadastrar captura de URL.
10. O sistema conseguir capturar print de uma URL configurada.
11. O editor conseguir criar uma grade dinâmica.
12. O editor conseguir inserir conteúdos na grade.
13. O editor conseguir definir duração por item.
14. O sistema calcular o tempo total da grade.
15. O editor conseguir simular a grade.
16. O editor conseguir publicar a grade.
17. A grade publicada rodar em loop na URL da tela.
18. A mesma grade poder ser usada em várias telas.
19. A mesma grade poder ser aplicada a grupo.
20. A barra informativa ser exibida na tela.
21. A barra permitir logo.
22. A barra permitir widgets.
23. O widget de relógio funcionar.
24. O widget de clima funcionar com cache.
25. O widget de dólar funcionar com cache.
26. Notícias por categoria exibirem apenas resumo.
27. O sistema conseguir alternar notícias conforme configuração.
28. O sistema conseguir registrar heartbeat das telas.
29. O dashboard mostrar telas online e offline.
30. Logs básicos serem registrados.
31. Conteúdo emergencial conseguir interromper a programação normal.

---

# 53. Recomendações Para os Agentes de Desenvolvimento

## Agente Product Owner

Responsável por:

- Refinar backlog.
- Priorizar MVP.
- Validar regras de negócio.
- Criar histórias de usuário.
- Definir critérios de aceite por sprint.

## Agente Arquitetura

Responsável por:

- Definir arquitetura modular.
- Validar stack.
- Projetar comunicação entre frontend, backend, workers e storage.
- Definir estratégia de cache.
- Definir estratégia de atualização das telas.

## Agente Backend

Responsável por:

- Criar APIs.
- Implementar regras de negócio.
- Criar filas.
- Integrar Redis.
- Integrar MinIO.
- Implementar captura de URL.
- Implementar notícias e widgets.

## Agente Frontend Admin

Responsável por:

- Criar painel administrativo.
- Criar editor de grade.
- Criar simulador.
- Criar editor de barra.
- Criar dashboard de monitoramento.

## Agente Frontend Exibição

Responsável por:

- Criar rota `/tela/[slug]`.
- Renderizar grade.
- Renderizar layout.
- Renderizar barra e widgets.
- Controlar loop e duração.
- Enviar heartbeat.
- Tratar reconexão.

## Agente Banco de Dados

Responsável por:

- Criar modelo relacional.
- Criar migrations.
- Definir índices.
- Otimizar consultas.
- Garantir integridade.

## Agente QA

Responsável por:

- Criar plano de testes.
- Testar grade dinâmica.
- Testar cálculo de tempo total.
- Testar simulação.
- Testar URL de exibição.
- Testar captura de URL.
- Testar widgets.
- Testar notícias.
- Testar monitoramento.

## Agente DevOps

Responsável por:

- Criar Docker Compose.
- Configurar Nginx ou Traefik.
- Configurar PostgreSQL.
- Configurar Redis.
- Configurar MinIO.
- Configurar workers.
- Configurar backups.
- Configurar logs.

---

# 54. Definition of Done

Uma funcionalidade será considerada pronta quando:

- Código implementado.
- Testes básicos executados.
- Regras de negócio atendidas.
- Validações de erro implementadas.
- Logs relevantes registrados.
- Interface validada.
- Funcionalidade documentada.
- Critérios de aceite atendidos.
- Não houver impacto negativo na URL de exibição.

---

# 55. Observações Finais

Este projeto deve ser tratado como uma plataforma corporativa de comunicação visual baseada em URLs internas.

A decisão mais importante do projeto é: **a TV não executa um player instalado; ela apenas abre uma URL interna no navegador**.

Isso simplifica implantação, reduz manutenção e permite que a empresa gerencie toda a comunicação visual por meio de um painel central.

A funcionalidade central é a **grade dinâmica com duração por item, cálculo de tempo total, simulação e publicação**.

Os diferenciais do produto são:

- URL interna por tela.
- Autonomia para o usuário montar grades.
- Simulador antes da publicação.
- Barra informativa configurável.
- Widgets de clima, dólar, data, hora e logo.
- Captura automática de prints de URL.
- Notícias dinâmicas por categoria com resumo.
- Integração com Facebook.
- Reutilização de grades em múltiplas telas.
- Monitoramento online/offline.
- Conteúdo emergencial.

Este documento deve ser usado como base única para iniciar a arquitetura, modelagem do banco, criação do backlog, prototipação, desenvolvimento e testes.

