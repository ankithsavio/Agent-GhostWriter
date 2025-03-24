FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PLAYWRIGHT_BROWSERS_PATH=/playwright-browsers

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock

RUN uv sync --frozen

RUN uv run spacy download en_core_web_sm

RUN uv run playwright install --with-deps chromium \
    && chmod -Rf 777 $PLAYWRIGHT_BROWSERS_PATH

COPY ./backend /app/backend
COPY ./config /app/config
COPY ./ghost_writer /app/ghost_writer
COPY ./llms /app/llms

CMD ["uv", "run", "-m", "backend.app.main"]