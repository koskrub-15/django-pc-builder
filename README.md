# Django Project Builder

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- [just](https://github.com/casey/just) (optional, but recommended)

### 🏠 Homework Setup

Run everything from zero with a single command:

```shell
just homework-i-docker-i-run
```

Completely reset the environment:

```shell
just homework-i-docker-i-purge
```

---

## 📋 Overview

A Django-based web application combining synchronous WSGI endpoints and asynchronous ASGI (WebSocket) features. Nginx serves static/media files and proxies requests to `app-wsgi` (WSGI) and `app-asgi` (ASGI/Daphne). Docker Compose orchestrates all services.

### Key Features
- **Django Apps**: `blog`, `builder`, `chat`, `store`, `profile`, `about`
- **WebSocket Chat**: Real-time communication using Django Channels (ASGI/Daphne)
- **Static & Media Files**: Served efficiently by Nginx
- **Health Monitoring**: Endpoint at `/health/`
- **Docker-Ready**: Pre-configured setup for development and production

### Architecture
```
┌─────────┐    ┌──────────┐    ┌───────────┐
│ Nginx   │───▶│ app-wsgi │    │ app-asgi  │
│ (80)    │    │ (8000)   │    │ (8001)    │
└─────────┘    └──────────┘    └───────────┘
     │              │                 │
     └──────────────┴─────────────────┘
           /static/  /media/  /ws/
```

---

## 🗂️ Repository Structure

```
.
├── core/              # Django project (settings, urls, asgi, wsgi)
├── apps/              # Django applications
│   ├── blog/
│   ├── chat/
│   ├── builder/
│   └── ...
├── docker/            # Container configs
│   └── nginx/         # Nginx configuration files
├── staticfiles/       # Collected static files
├── media/             # User-uploaded media
├── compose.yaml       # Docker Compose base config
├── compose.override.dev.yaml  # Development overrides
└── requirements.txt   # Python dependencies
```

---

## 🐳 Docker Deployment

### Build & Run

```shell
# Using just (recommended)
just d-run

# Or manually
docker compose build
docker compose up -d
```

### View Logs

```shell
docker compose logs -f nginx      # Nginx logs
docker compose logs -f app-wsgi   # WSGI application logs
docker compose logs -f app-asgi   # ASGI/WebSocket logs
```

### Stop Services

```shell
docker compose down
```

### Complete Reset

```shell
# Using just
just d-purge

# Or manually
docker compose down -v
docker volume prune -f
```

### Development Mode

Use `compose.override.dev.yaml` for:
- Bind mounts for live code reload
- Debug settings
- Development tools

---

## 💻 Local Development (Without Docker)

### 1. Initialize Environment with uv

```shell
# Create project structure
uv init

# Sync dependencies
uv sync
```

### 2. Traditional Setup (Alternative)

```shell
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database & Static Files

```shell
# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --no-input
```

### 4. Run Services

```shell
# WSGI server (development)
python manage.py runserver

# ASGI server (Daphne) - in another terminal
daphne --bind 0.0.0.0 --port 8001 --access-log - --proxy-headers --verbosity 2 core.asgi:application
```

### Quick Dev Setup

```shell
just init-i-dev  # Creates venv, installs deps, configures pre-commit
```

---

## 🌐 Nginx Configuration

### Routing Rules

| Path | Target | Purpose |
|------|--------|---------|
| `/wd/app/static/` | `/var/www/static/` | Static files (CSS, JS) |
| `/media/` | `/var/www/media/` | User-uploaded media |
| `/ws/`, `/admin/ws/` | `django_asgi:8001` | WebSocket connections |
| `/health/` | Direct response | Health check endpoint |
| `/` | `django_wsgi:8000` | Main application |

### Key Files
- `docker/nginx/default.conf` - Site configuration
- `docker/nginx/nginx.conf` - Main Nginx config

---

## 📁 Static & Media Files

### Configuration

Ensure `core/settings.py` contains:

```python
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

### Docker Volumes

- **Nginx**: `/var/www/media/`
- **App containers**: `/wd/media/`

### Troubleshooting 404 Errors

```shell
# Check if files exist in container
docker compose exec nginx ls -la /var/www/media/

# Verify volume mounts
docker compose config

# Check permissions
docker compose exec app-wsgi ls -la /wd/media/
```

---

## 🔌 WebSocket Support (Django Channels)

### Configuration

- **ASGI App**: Configured in `core/asgi.py`
- **Daphne Server**: Runs on port 8001 with `--proxy-headers`
- **Consumers**: Located in `apps/chat/consumers.py`
- **Routing**: Defined in `apps/chat/routing.py`

### WebSocket Troubleshooting

```shell
# Check Daphne logs
docker compose logs -f app-asgi

# Verify Nginx passes correct headers (Upgrade, Connection)
docker compose exec nginx cat /etc/nginx/conf.d/default.conf | grep -A 10 "ws"
```

Ensure Nginx configuration includes:

```nginx
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

---

## 🧪 Testing

```shell
# Using Docker
docker compose exec app-wsgi python manage.py test

# Locally
python manage.py test
```

---

## 🛠️ Common Tasks

### Database Migrations

```shell
# Create migrations
python manage.py makemigrations

# Apply migrations (Docker)
docker compose exec app-wsgi python manage.py migrate

# Apply migrations (local)
python manage.py migrate
```

### Create Superuser

```shell
# Docker
docker compose exec app-wsgi python manage.py createsuperuser

# Local
python manage.py createsuperuser
```

### View All Commands

```shell
just --list
```

---

## 🔧 Troubleshooting

### Issue: Media files return 404

**Solutions:**
1. Verify `MEDIA_URL = "/media/"` in settings
2. Check file permissions in container
3. Confirm volume mounts are correct
4. Restart Nginx: `docker compose restart nginx`

### Issue: WebSocket connections fail

**Solutions:**
1. Check Daphne is running: `docker compose ps app-asgi`
2. Verify Nginx WebSocket proxy configuration
3. Check browser console for errors
4. Review Daphne logs for connection attempts

### Issue: Static files not loading

**Solutions:**
1. Run `python manage.py collectstatic --no-input`
2. Verify `STATIC_ROOT` and `STATIC_URL` in settings
3. Check Nginx static file alias configuration

---

## 📚 Additional Resources

- **just Commands**: See `just/` directory for task definitions
- **Nginx Config**: `docker/nginx/` directory
- **Django Apps**: Explore `apps/` directory structure

---

## 🤝 Contributing

1. Follow existing patterns in `apps/` directory
2. Create migrations after model changes: `python manage.py makemigrations`
3. Use `just` tasks for common workflows
4. Write tests for new features

---

## 📄 License

Check repository `LICENSE` file or contact maintainers.

---

**Made with ❤️ using Django, Docker, and just**