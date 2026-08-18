# [stage__base]-[BEGIN]================================================
FROM python:3.14.7-slim AS base

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
# Must match the host uid: compose runs the app with "user: ${USER_ID}" so that
# files written into the bind-mounted source tree stay owned by the host user.
ARG USER_ID=1000

WORKDIR ${WORKDIR}

# staticfiles/ and media/ are created here so the named volumes mounted over them
# inherit the app user's ownership — an empty volume would be root-owned and
# collectstatic (running as USER_ID) could not write to it.
# --create-home: gunicorn's control server writes under $HOME and logs an error
# on every boot if the directory does not exist.
RUN useradd --system --uid ${USER_ID} --create-home ${USER} &&\
    mkdir --parents ${WORKDIR}/staticfiles ${WORKDIR}/media &&\
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
# Build the environment outside WORKDIR. The dev compose bind-mounts the source
# tree over /wd, so a venv inside it has to be masked by an extra volume — and a
# masking volume created by an older image survives a Python upgrade and shadows
# the new one. Keeping the venv out of /wd removes that whole failure mode.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
# Never let uv fetch its own interpreter. .python-version must match the base
# image above; if it does not, uv would quietly build the venv against a
# downloaded Python that the final stage never copies, producing an image whose
# .venv/bin/python is a dangling symlink. Failing the build is the loud version.
ENV UV_PYTHON_DOWNLOADS=never
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
ARG VENV_DIR=/opt/venv

COPY --from=builder ${VENV_DIR} ${VENV_DIR}

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