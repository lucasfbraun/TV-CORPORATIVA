# Continuação da configuração HTTPS

Última atualização: 01/09/2026.

## Status

Concluído. Acesso via `https://tv.grupoflexivel.com.br` validado de ponta a
ponta em um computador Windows, com certificado confiável (sem `-k` e sem
aviso do navegador). Falta apenas distribuir a CA para as demais máquinas
(veja "Distribuir para outras máquinas" abaixo).

## Estado confirmado

- Servidor da aplicação: `10.100.100.7` (`flexivel-VMware20-1`).
- DNS interno: `tv.grupoflexivel.com.br` resolve corretamente para
  `10.100.100.7`.
- O Apache já utiliza a porta TCP 80 do servidor.
- O Caddy publica somente TCP/UDP 443 e encaminha as requisições para
  `tv-corporativa:8080`.
- Os containers `tv-corporativa-db`, `tv-corporativa` e
  `tv-corporativa-https` estão em execução.
- A CA do Caddy foi exportada no servidor para
  `~/TV-CORPORATIVA/tv-caddy-root.crt`.

O mapeamento `80:80` foi removido do Compose porque causava conflito com o
Apache. Não interromper o Apache sem antes verificar as outras aplicações que
ele atende.

## Testes que passaram

No servidor, o acesso local forçando o nome TLS retornou `HTTP/2 302`, com os
cabeçalhos `Via: 1.1 Caddy` e `Location: /login.html?next=/admin`.

Em um computador Windows da rede:

- `Resolve-DnsName tv.grupoflexivel.com.br` retornou `10.100.100.7`;
- `Test-NetConnection tv.grupoflexivel.com.br -Port 443` retornou
  `TcpTestSucceeded: True`;
- `curl.exe -k -I https://tv.grupoflexivel.com.br/admin` retornou
  `302 Found` por meio do Caddy.

Isso confirma que aplicação, DNS, rota, porta 443 e proxy estão funcionando.
O parâmetro `-k` ignora a validação do certificado, portanto o ponto de parada
é a confiança da CA interna no Windows.

## Como instalar a CA em uma máquina Windows

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
de testar. Não usar `curl.exe` do Windows para validar: o `schannel` dele
falha com `CRYPT_E_NO_REVOCATION_CHECK`, pois a CA interna do Caddy não expõe
CRL/OCSP — isso é uma limitação do `curl`/schannel, não indica problema real
no navegador. Testar direto no Chrome/Edge.

### Se o Chrome mostrar "Não seguro" mesmo com a CA instalada

Se o DevTools (F12 → aba **Security**) mostrar o certificado como "valid and
trusted" mas ainda assim aparecer "This page isn't secure (broken HTTPS)" com
o motivo "Resources - active content with certificate errors", é só estado
antigo da aba: algum recurso da página rodou antes de a CA ficar confiável, e
o Chrome guarda esse aviso para a navegação atual. Basta fechar todas as abas
do site, fechar o navegador por completo e abrir de novo. Se persistir, limpar
os dados do site em `chrome://settings/content/all` e recarregar.

O aviso "Certificate expires soon" no DevTools é esperado e não exige ação: a
CA interna do Caddy emite certificados de vida curta e o Caddy os renova
sozinho em background (ver "Renovação automática" abaixo).

## Renovação automática

O Caddy renova os certificados-folha automaticamente enquanto o container
`https-proxy` estiver rodando e os volumes `caddy_data`/`caddy_config`
existirem — não precisa de nenhuma ação manual. Não recriar esses volumes:
eles guardam a CA raiz e as chaves usadas pelo Caddy; recriá-los gera uma CA
nova e invalida a confiança já instalada em todas as máquinas.

A CA raiz em si tem validade de vários anos. Só será necessário redistribuir
um novo `tv-caddy-root.crt` (repetindo os passos acima em cada máquina) se ela
expirar ou se os volumes forem recriados.

## Distribuir para outras máquinas

Repetir "Como instalar a CA em uma máquina Windows" em cada computador que
precisa acessar a aplicação, e nos players/TVs. Para várias máquinas de uma
vez, prefira publicar `tv-caddy-root.crt` via Política de Grupo (GPO) em vez
de instalar manualmente uma por uma.

## Se falhar

Registrar a saída completa do `certutil`, o texto do DevTools (aba Security) e
o código exato mostrado pelo navegador, por exemplo
`NET::ERR_CERT_AUTHORITY_INVALID`.

Para conferir se o arquivo copiado é exatamente o mesmo, comparar os hashes:

No servidor Linux:

```bash
sha256sum ~/TV-CORPORATIVA/tv-caddy-root.crt
```

No Windows:

```powershell
Get-FileHash "$env:USERPROFILE\Downloads\tv-caddy-root.crt" -Algorithm SHA256
```
