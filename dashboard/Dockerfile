# syntax=docker/dockerfile:1
#
# Reproduzierbares Image fuer das VAR Live-Demo Dashboard.
# Build-Kontext ist der PROJEKT-ROOT (wegen ../data), daher:
#
#   docker build -f dashboard/Dockerfile -t var-dashboard .
#   docker run --rm -p 8501:8501 var-dashboard
#
# Danach im Browser: http://localhost:8501

FROM python:3.12-slim

# uv in fixer Version aus dem offiziellen Image kopieren (Reproduzierbarkeit).
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/dashboard/.venv/bin:$PATH" \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app/dashboard

# 1) Nur Metadaten kopieren -> Docker-Layer-Caching fuer die Dependencies.
COPY dashboard/pyproject.toml dashboard/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# 2) App-Code und Daten.
#    app.py erwartet die Daten unter <projekt-root>/data, hier also /app/data.
COPY dashboard/app.py ./
COPY data/ /app/data/

EXPOSE 8501

# Eingebauter Health-Endpoint von Streamlit.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8501/_stcore/health').status==200 else 1)"

CMD ["streamlit", "run", "app.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true"]

