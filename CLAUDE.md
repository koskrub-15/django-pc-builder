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
  about/       — about page + contact form
  base/        — homepage
  blog/        — posts, categories, comments
  builder/     — PC components, builds, orders, progress tracker
  chat/        — real-time WebSocket chat (admin ↔ customer)
  profile/     — user order history
  store/       — services, ordering steps and FAQ page
  templates/   — all HTML templates (shared across apps)
core/
  settings.py  — main settings
  urls.py      — root URL config
  asgi.py      — ASGI app with WebSocket routing
```

## Running the Project

```bash
# Full Docker setup (config + build + migrate + start) → http://localhost:8080
just d-up

# Tear down (containers, volumes, locally built images)
just d-purge

# See all commands
just --list
```

`just d-up` creates `.env` and `compose.override.yaml` from the committed
examples if they are missing, so it works straight after a clone.

## Development Setup

```bash
# Install uv, just, pre-commit, create venv
just init-i-dev

# Copy config files
just init-i-configs
```

## Running Tests

```bash
# Locally, no setup needed (recommended)
just test-i-run

# With a per-file coverage report
just test-i-coverage

# Inside the running container
just test-i-docker-run
```

`core/test_settings.py` — test settings with SQLite in-memory, an in-memory
channel layer, and a locmem email backend; no env vars needed.

CI enforces a 90% coverage floor (currently at 99%).

## Key Architectural Notes

- **WSGI / ASGI split**: `app-wsgi` (Gunicorn) handles HTTP, `app-asgi` (Daphne) handles WebSocket connections at `/ws/`.
- **Chat flow**: messages are sent via HTTP POST (`send_message` view) which saves to DB and broadcasts to the WebSocket channel layer group. All connected WS clients receive the message in real-time. The `get_messages` JSON endpoint exists for API access.
- **Admin-only views**: `builder/` and chat `thread_list` require `is_staff=True`, enforced via `@user_passes_test(is_admin)`.
- **Email**: all email functions use `fail_silently=True` — SMTP errors are logged but don't crash the request.
- **No personal data in the repo**: the About page renders owner name/bio/socials from the `SITE_OWNER` settings dict (`SITE__OWNER_*` env vars), and every field is optional — a fresh clone shows only the project blurb and the contact form.
- **Chat message escaping**: `ChatMessage.is_html` marks the few messages the app composes itself (order summaries, component tables, built with `format_html`). Those render unescaped; everything a user types must stay `is_html=False` or it becomes stored XSS.

## Code Conventions

- Type annotations on all function signatures
- `ruff` for linting and formatting (`just pre-commit-i-run-i-all`)
- `mypy` for type checking (via pre-commit)
- No comments explaining obvious code — only non-obvious constraints or workarounds
- Tests in `apps/<app>/tests/` packages using Django `TestCase`
