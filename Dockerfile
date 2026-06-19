# TV Corporativa - imagem do servidor central
FROM python:3.12-slim

# Evita arquivos .pyc e força logs sem buffer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TV_HOST=0.0.0.0 \
    TV_PORT=8080

WORKDIR /app

# Dependências do servidor (leves). A integração de KPIs roda fora da imagem.
RUN pip install --no-cache-dir Flask==3.0.3 Werkzeug==3.0.3 waitress==3.0.0

# Código da aplicação
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Pastas de runtime (serão montadas como volumes no compose)
RUN mkdir -p data uploads

EXPOSE 8080

CMD ["python", "backend/server.py"]
