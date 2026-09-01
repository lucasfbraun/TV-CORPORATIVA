# Continuação da configuração HTTPS

Última atualização: 28/08/2026.

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

## Próximo passo

No computador Windows que não abre a aplicação, abrir o PowerShell como
Administrador.

Se o certificado ainda não estiver no computador, copiá-lo do servidor:

```powershell
scp flexivel@10.100.100.7:/home/flexivel/TV-CORPORATIVA/tv-caddy-root.crt "$env:USERPROFILE\Downloads\tv-caddy-root.crt"
```

Instalar e confirmar a CA:

```powershell
Test-Path "$env:USERPROFILE\Downloads\tv-caddy-root.crt"
certutil -addstore -f "ROOT" "$env:USERPROFILE\Downloads\tv-caddy-root.crt"
certutil -store "ROOT" | Select-String "Caddy" -Context 2,2
```

Fechar completamente o navegador, abri-lo novamente e testar sem `-k`:

```powershell
curl.exe -I https://tv.grupoflexivel.com.br/admin
```

Resultado esperado: `302 Found`, sem erro de certificado. Em seguida, abrir:

```text
https://tv.grupoflexivel.com.br/admin
```

## Se ainda falhar

Registrar a saída completa do `certutil` e do `curl.exe` sem `-k`, além do código
exato mostrado pelo navegador, por exemplo `NET::ERR_CERT_AUTHORITY_INVALID`.
Não recriar os volumes `tv-corporativa_caddy_data` e
`tv-corporativa_caddy_config`: eles guardam a CA e as chaves usadas pelo Caddy.

Para conferir se o arquivo copiado é exatamente o mesmo, comparar os hashes:

No servidor Linux:

```bash
sha256sum ~/TV-CORPORATIVA/tv-caddy-root.crt
```

No Windows:

```powershell
Get-FileHash "$env:USERPROFILE\Downloads\tv-caddy-root.crt" -Algorithm SHA256
```
