# Continuação da configuração HTTPS

Última atualização: 01/09/2026.

## Status

Em andamento: migrando de CA interna do Caddy (exigia instalar um
certificado manualmente em cada máquina) para **certificado público** (Let's
Encrypt), validado por DNS-01 na zona `grupoflexivel.com.br` no Cloudflare.
Com isso, ninguém precisa mais instalar nada — o navegador confia
automaticamente.

Código já alterado (`caddy/Dockerfile`, `caddy/Caddyfile`,
`docker-compose.yml`, `.env.example`). Falta: criar o token no Cloudflare,
configurar `.env` no servidor e fazer o deploy.

## Por que isso é possível sem expor a aplicação à internet

A validação DNS-01 do Let's Encrypt só exige criar um registro TXT temporário
(`_acme-challenge.tv.grupoflexivel.com.br`) na zona pública do domínio — o
Caddy faz isso sozinho via API do Cloudflare. Não é necessário publicar um
registro A público, nem abrir portas 80/443 para a internet. O acesso
continua só pela rede interna, através do DNS interno (AD) que já resolve
`tv.grupoflexivel.com.br` para `10.100.100.7`.

## Passo 1 — Criar o token no Cloudflare

1. Entrar em https://dash.cloudflare.com/profile/api-tokens com a conta que
   administra `grupoflexivel.com.br`.
2. Clicar em **Create Token**.
3. Usar o template **Edit zone DNS**.
4. Em "Zone Resources", restringir a **Specific zone → grupoflexivel.com.br**
   (não deixar em "All zones").
5. Criar e copiar o token (só aparece uma vez).

## Passo 2 — Configurar no servidor

No servidor Linux (`10.100.100.7`), dentro de `~/TV-CORPORATIVA`:

```bash
git pull
```

Se ainda não existir um `.env`, copiar do modelo:

```bash
cp .env.example .env
```

Editar o `.env` e preencher:

```
CF_API_TOKEN=<token gerado no passo 1>
```

Subir a nova versão (é preciso `--build` porque o Caddy passou a ser uma
imagem customizada, com o plugin do Cloudflare):

```bash
docker compose up -d --build https-proxy
```

## Passo 3 — Validar

Acompanhar os logs até aparecer a emissão do certificado:

```bash
docker compose logs -f https-proxy
```

Esperado: `certificate obtained successfully` com `"issuer":"acme-v02.api.letsencrypt.org..."`
(em vez de `"issuer":"local"`, que era da CA interna).

Testar em qualquer computador **sem** a CA interna instalada — inclusive um
que nunca acessou o sistema antes. Deve abrir com cadeado verde/seguro sem
nenhuma instalação prévia.

## O que fazer com a CA interna já instalada nas máquinas

Nada obrigatório. Ter a CA antiga ("Caddy Local Authority") instalada não
atrapalha nem conflita com o certificado público novo — pode deixar como
está. Se quiser limpar por organização, é opcional:

```powershell
certutil -delstore "ROOT" "Caddy Local Authority - 2026 ECC Root"
```

## Renovação automática

Assim como a CA interna, o certificado público também renova sozinho em
background enquanto o container `https-proxy` estiver rodando — sem ação
manual. A diferença é que, sendo emitido pelo Let's Encrypt, tem validade de
~90 dias (bem mais folgada que a CA interna), e o Caddy renova bem antes de
expirar.

Não recriar os volumes `caddy_data`/`caddy_config`: eles guardam as chaves da
conta ACME e os certificados emitidos.

## Se falhar

Causas mais comuns:

- **Token sem permissão na zona certa**: confirmar que o token tem "Zone:DNS:Edit"
  especificamente em `grupoflexivel.com.br`.
- **`CF_API_TOKEN` vazio**: o `docker compose up` vai recusar subir e avisar
  `defina CF_API_TOKEN no .env` (validação proposital no `docker-compose.yml`).
- **Rate limit do Let's Encrypt**: evitar recriar o certificado repetidamente
  em pouco tempo durante testes; usar o mesmo container já emitido sempre que
  possível.

Registrar a saída completa de `docker compose logs -f https-proxy` ao tentar
subir, com o erro específico do Caddy/ACME.

---

## Histórico — instalação manual da CA interna (abordagem anterior)

Mantido como referência, caso seja necessário reverter para `tls internal`
temporariamente (por exemplo, se o Cloudflare ficar inacessível).

### Como instalar a CA em uma máquina Windows

Abrir o PowerShell **como Administrador** (botão direito → "Executar como
administrador"; um PowerShell aberto em `C:\Windows\system32` não é
necessariamente elevado — confirme com o comando de verificação abaixo).

Copiar o certificado do servidor:

```powershell
scp flexivel@10.100.100.7:~/TV-CORPORATIVA/tv-caddy-root.crt "$env:USERPROFILE\Downloads\tv-caddy-root.crt"
```

Confirmar que a sessão está elevada, depois instalar a CA:

```powershell
([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
certutil -addstore -f "ROOT" "$env:USERPROFILE\Downloads\tv-caddy-root.crt"
```

Fechar **completamente** o navegador (todas as janelas) e abrir de novo antes
de testar. Não usar `curl.exe` do Windows para validar CA interna: o
`schannel` dele falha com `CRYPT_E_NO_REVOCATION_CHECK`, pois a CA interna do
Caddy não expõe CRL/OCSP — isso é uma limitação do `curl`/schannel, não indica
problema real no navegador. Testar direto no Chrome/Edge.

Se o Chrome mostrar "Não seguro" mesmo com a CA instalada, mas o DevTools
(F12 → aba **Security**) mostrar o certificado como "valid and trusted", é só
estado antigo da aba (algum recurso rodou antes de a CA ficar confiável).
Fechar todas as abas do site e o navegador por completo, abrir de novo. Se
persistir, limpar os dados do site em `chrome://settings/content/all`.
