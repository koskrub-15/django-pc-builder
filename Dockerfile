# [stage__base]-[BEGIN]================================================
FROM python:3.13.1-slim AS base

ENV PYTHONUNBUFFERED=1

ARG WORKDIR=/wd

# [update_and_pre_install]-[BEGIN]
# Also install "libmagic"
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    \
    apt update \
    && apt upgrade --yes

# [update_and_pre_install]-[END]

ARG USER=user

WORKDIR ${WORKDIR}

RUN useradd --system ${USER} &&\
    chown --recursive ${USER} ${WORKDIR}
# [stage__base]-[END]================================================

# [stage__builder]-[BEGIN]===============================================
FROM base AS builder

COPY --from=ghcr.io/astral-sh/uv:0.6.13 /uv /uvx /bin/
#
# Compile Python source files to bytecode after installation
# https://docs.astral.sh/uv/configuration/environment/#uv_compile_bytecode
ENV UV_COMPILE_BYTECODE=1
# Silences warnings about the use of the "copy" link mode
# https://docs.astral.sh/uv/reference/settings/#link-mode
ENV UV_LINK_MODE=copy
# Enable caching for faster builds
# https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_CACHE_DIR=/opt/uv-cache/
#
RUN --mount=type=cache,target=/opt/uv-cache/ \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=.python-version,target=.python-version \
    \
    uv sync --frozen
# [stage__builder]-[END]================================================

# [stage__final]-[BEGIN]================================================
FROM base AS final

ARG USER=user
ARG WORKDIR=/wd
ARG VENV_DIR=${WORKDIR}/.venv

COPY --from=builder /wd/.venv ${VENV_DIR}

COPY --chown=${USER} --chmod=555 docker/app/entrypoint.sh /entrypoint.sh
COPY --chown=${USER} --chmod=555 docker/app/start.sh /start.sh
COPY --chown=${USER} --chmod=555 docker/app/start-wsgi.sh /start-wsgi.sh
COPY --chown=${USER} --chmod=555 docker/app/start-asgi.sh /start-asgi.sh
COPY --chown=${USER} --chmod=555 docker/app/init.sh /init.sh

COPY --chown=${USER} manage.py manage.py
COPY --chown=${USER} core/ core/
COPY --chown=${USER} apps/ apps/

USER ${USER}

ENV PATH="${VENV_DIR}/bin:$PATH"

ENTRYPOINT ["/entrypoint.sh"]
# [stage__final]-[END]==================================================