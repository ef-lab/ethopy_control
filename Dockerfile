# =============================================================================
# ethopy_control - production image
#
# Single-stage on purpose. A multi-stage build would buy nothing here: every
# dependency is either pure Python (pymysql, ldap3) or ships prebuilt manylinux
# wheels (cryptography, paramiko). No compiler, no build-essential, no gcc,
# and no mysql-client are needed.
#
# Build:  docker compose build
# Run:    docker compose up -d
# =============================================================================

# Repo declares requires-python >=3.9; docs say 3.11; the dev .venv is 3.13.
# 3.12 is the safe middle ground (3.9 is end-of-life).
FROM python:3.12-slim

# PYTHONUNBUFFERED: send logs straight to stdout so `docker logs` shows them
#   immediately instead of holding them in a buffer.
# PYTHONDONTWRITEBYTECODE: no .pyc clutter in the container filesystem.
# PIP_NO_CACHE_DIR: don't keep pip's download cache in the image layer.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# --- Dependency layer -------------------------------------------------------
# Copy ONLY the dependency manifest first. Docker caches each instruction, so
# as long as pyproject.toml is unchanged, the slow pip install below is reused
# from cache and a code change rebuilds in seconds instead of minutes.
#
# README.md is required because pyproject.toml declares `readme = "README.md"`;
# without it the build fails on metadata generation.
#
# At this point no Python packages exist in the context, so `pip install .`
# resolves and installs the DEPENDENCIES ONLY - which is exactly what we want
# in this cached layer. The application code arrives in the next step.
#
# .[test] also pulls in pytest so the image carries its own self-check
# (`python -m pytest -q`). It costs a few MB and gives whoever inherits this a
# way to verify a new machine without needing a database.
COPY pyproject.toml README.md ./
# The rm cleans up the empty build/ and *.egg-info/ directories setuptools
# leaves behind in the working directory while building the wheel.
RUN pip install --no-cache-dir ".[test]" \
    && rm -rf /app/build /app/*.egg-info

# --- Application layer ------------------------------------------------------
# Copy the source. .dockerignore keeps .env, .venv, build/, dist/ and the logs
# out of this.
#
# IMPORTANT: the app runs from /app, not from site-packages. `pip install .`
# installs the utils/ and real_time_plot/ PACKAGES, but app.py, main.py and
# models.py are top-level MODULES and are not installed. Running with
# WORKDIR=/app is what makes `import app` resolve.
COPY . .

# --- Security ---------------------------------------------------------------
# Run as a non-root user. If the app is ever compromised, the attacker lands as
# an unprivileged user rather than as root inside the container.
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# Matches PORT's default in utils/config.py. Documentation only - the actual
# published port is set by docker-compose.yml.
EXPOSE 8000

# --- Health check -----------------------------------------------------------
# Uses Python's urllib, NOT curl: python:3.12-slim does not ship curl, which is
# the bug in the example Dockerfile that used to live in docs/setup.md.
#
# Targets /login, not /. `/` is behind @login_required and only 302-redirects
# here, so /login returning 200 is the honest "the app is really serving" test.
#
# NOTE: this marks the container unhealthy in `docker ps`, but Docker's restart
# policy does NOT act on healthcheck failures. See DEPLOY.md for what actually
# recovers what.
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/login', timeout=5).status == 200 else 1)"

# --- Start ------------------------------------------------------------------
# gunicorn, not `python main.py`: main.py starts Flask's development server,
# which is single-threaded and explicitly not for production use.
#
# `main:app` works because main.py does `from app import app` at module scope.
# Importing main does NOT execute main(), which deliberately skips its database
# pre-flight check - in a container we would rather start and serve errors than
# refuse to boot and crash-loop during a brief database blip.
#
# -w 4          : 4 sync worker processes. Correct here - the app has no
#                 WebSockets or SSE, only AJAX polling, so no async worker
#                 class is needed.
# --timeout 60  : a worker stuck longer than this is killed and respawned by
#                 the gunicorn master. This is what recovers a hung request,
#                 and it needs to exceed the 5s paramiko SSH reboot call.
# --access-logfile - : access logs to stdout, so `docker logs` has everything.
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "main:app"]
