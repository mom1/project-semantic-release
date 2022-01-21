# This Dockerfile is only for GitHub Actions
FROM python:3.10.2-slim-buster

ENV PATH="$PATH:/root/.local/bin" \
  # python:
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PYTHONDONTWRITEBYTECODE=1 \
  # pip:
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  # poetry:
  POETRY_VERSION=1.1.11 \
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry'

RUN curl -sSL 'https://install.python-poetry.org' | python - \
  && poetry --version

WORKDIR /semantic-release

COPY ./poetry.lock ./pyproject.toml /semantic-release/

RUN poetry install --no-dev -E emoji --no-interaction --no-ansi \
  # Upgrading pip, it is insecure, remove after `pip@21.1`
  && poetry run pip install -U pip \
  # Cleaning poetry installation's cache for production:
  && rm -rf "$POETRY_CACHE_DIR"

COPY . /semantic-release
RUN poetry run semantic_release.cli --help

ENTRYPOINT ["/semantic-release/action.sh"]
