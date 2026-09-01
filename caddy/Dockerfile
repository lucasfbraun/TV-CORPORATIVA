# Build customizado do Caddy com o plugin de DNS da Cloudflare, necessário
# para emitir certificado público (Let's Encrypt) por validação DNS-01 sem
# expor a aplicação à internet. A imagem oficial caddy:alpine não inclui
# plugins de terceiros.
FROM caddy:2.11.4-builder-alpine AS builder

RUN xcaddy build \
    --with github.com/caddy-dns/cloudflare

FROM caddy:2.11.4-alpine

COPY --from=builder /usr/bin/caddy /usr/bin/caddy
