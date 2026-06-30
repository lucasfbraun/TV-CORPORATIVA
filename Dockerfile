# TV Corporativa - imagem do servidor central
# (bookworm/Debian 12 — o Playwright ainda não suporta o trixie/Debian 13 no --with-deps)
FROM python:3.12-slim-bookworm

# Evita arquivos .pyc e força logs sem buffer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TV_HOST=0.0.0.0 \
    TV_PORT=8080

WORKDIR /app

# Cliente PostgreSQL (pg_dump/pg_restore para o backup) — v15 casa com o postgres:15 do compose
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Dependências do servidor
RUN pip install --no-cache-dir Flask==3.0.3 Werkzeug==3.0.3 waitress==3.0.0 playwright==1.47.0 psycopg2-binary==2.9.9

# Navegador headless (Chromium) para as Integrações com login (ex.: Grafana)
RUN playwright install --with-deps chromium

# Código da aplicação
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Pastas de runtime (serão montadas como volumes no compose)
RUN mkdir -p data uploads

EXPOSE 8080

CMD ["python", "backend/server.py"]
