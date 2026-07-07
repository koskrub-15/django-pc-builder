# CLAUDE.md

## Project

Django PC Builder & E-Commerce Platform — portfolio project. Full-stack Django app with real-time chat, PC configurator, order tracking, and blog.

## Tech Stack

- **Django 5.2** — main framework (WSGI + ASGI split)
- **Django Channels** — WebSocket for real-time chat
- **PostgreSQL** — primary database
- **Redis** — channel layer backend for WebSockets
- **Nginx** — reverse proxy, serves static/media
- **uv** — dependency management
- **Docker Compose** — local and production environment

## Project Structure

```
apps/
  about/       — static about page
  base/        — homepage
  blog/        — posts, categories, comments
  builder/     — PC components, builds, orders, progress tracker
  chat/        — real-time WebSocket chat (admin ↔ customer)
  profile/     — user order history
  store/       — placeholder landing page
  templates/   — all HTML templates (shared across apps)
core/
  settings.py  — main settings
  urls.py      — root URL config
  asgi.py      — ASGI app with WebSocket routing
```

## Running the Project

```bash
# Full Docker setup (build + migrate + start)
just homework-i-docker-i-run

# Tear down
just homework-i-docker-i-purge

# See all commands
just --list
```

## Development Setup

```bash
# Install uv, just, pre-commit, create venv
just init-i-dev

# Copy config files
just init-i-configs
```

## Running Tests

```bash
# In Docker (recommended)
just test-i-docker-run

# Locally (without Docker)
.venv/bin/python manage.py test apps --settings=core.test_settings
```

`core/test_settings.py` — test settings with SQLite in-memory and locmem email backend, no env vars needed.

## Key Architectural Notes

- **WSGI / ASGI split**: `app-wsgi` (Gunicorn) handles HTTP, `app-asgi` (Daphne) handles WebSocket connections at `/ws/`.
- **Chat flow**: messages are sent via HTTP POST (`send_message` view) which saves to DB and broadcasts to the WebSocket channel layer group. All connected WS clients receive the message in real-time. The `get_messages` JSON endpoint exists for API access.
- **Admin-only views**: `builder/` and chat `thread_list` require `is_staff=True`, enforced via `@user_passes_test(is_admin)`.
- **Email**: all email functions use `fail_silently=True` — SMTP errors are logged but don't crash the request.

## Code Conventions

- Type annotations on all function signatures
- `ruff` for linting and formatting (`just pre-commit-i-run-i-all`)
- `mypy` for type checking (via pre-commit)
- No comments explaining obvious code — only non-obvious constraints or workarounds
- Tests in `apps/<app>/tests/` packages using Django `TestCase`
