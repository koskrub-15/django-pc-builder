# Django PC Builder & E-Commerce Platform

---

## 📋 Overview

This is a full-featured web application built with Django that serves as a portfolio project. It combines a PC building service, an e-commerce platform, a real-time chat system, and a content blog. The application is containerized using Docker and includes a comprehensive set of features for both users and administrators.

### Key Features
- **PC Builder & Quoting:** Allows administrators to manage a list of PC components. Users can view pre-configured PC builds with dynamically calculated total prices.
- **Order & Tracking System:** Customers can place orders for PC builds. A detailed, step-by-step progress tracker allows customers to monitor their order status in real-time (e.g., components ordered, build in progress, testing, delivered).
- **Real-Time Chat:** A WebSocket-based chat system using Django Channels enables customers to communicate directly with administrators. It's deeply integrated with the builder, allowing admins to send component lists and create orders directly from the chat interface.
- **Blog Platform:** A complete blogging system with posts, categories, and comments for sharing articles about PC hardware, builds, and gaming.
- **User Authentication:** Robust user management powered by `django-allauth`, supporting user registration, login/logout, and profile management.
- **Dockerized Environment:** The entire application stack (Nginx, Django WSGI, Django ASGI) is managed by Docker Compose for easy setup and deployment.

### Architecture
The architecture uses Nginx as a reverse proxy to serve static/media files and route requests to the appropriate backend service:
- **app-wsgi (Gunicorn):** Handles standard synchronous HTTP requests for most of the Django application.
- **app-asgi (Daphne):** Manages asynchronous WebSocket connections for the real-time chat feature.

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

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- [just](https://github.com/casey/just) (optional, but recommended for convenience)

### Full Docker Setup

This single command will build the Docker images, apply database migrations, and start all services.

```shell
just homework-i-docker-i-run
```

To completely stop and remove all containers, networks, and volumes:

```shell
just homework-i-docker-i-purge
```

---

## 🐳 Docker Deployment

### Build & Run

If you are not using `just`, you can run the services manually:

```shell
# Build and start containers in detached mode
docker compose build
docker compose up -d
```

### View Logs

You can monitor the logs for each service:

```shell
docker compose logs -f nginx      # Nginx logs
docker compose logs -f app-wsgi   # WSGI application logs
docker compose logs -f app-asgi   # ASGI/WebSocket logs
```

### Stop Services

```shell
docker compose down
```

---

## 💻 Local Development (Without Docker)

### 1. Initialize Environment

It's recommended to use `uv` for managing the virtual environment and dependencies.

```shell
# Create a virtual environment and install dependencies
uv sync

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Database & Static Files

```shell
# Run database migrations
python manage.py migrate

# Collect static files (for production simulation)
python manage.py collectstatic --no-input
```

### 3. Run Services

You need to run the WSGI and ASGI servers in separate terminals.

```shell
# Terminal 1: Run the WSGI development server
python manage.py runserver
```

```shell
# Terminal 2: Run the ASGI server (Daphne) for WebSockets
daphne --bind 0.0.0.0 --port 8001 core.asgi:application
```

### Quick Dev Setup with `just`

The `just init-i-dev` command automates the setup of the virtual environment, dependency installation, and pre-commit hooks.

```bash
just init-i-dev
```

---

## 🛠️ Common Tasks

### Database Migrations

When you change your models, you need to create and apply migrations.

```shell
# Create new migration files based on model changes
python manage.py makemigrations

# Apply migrations to the database (Docker)
docker compose exec app-wsgi python manage.py migrate
```

### Create Superuser

To access the Django admin interface (`/admin/`), you need a superuser account.

```shell
# Using Docker
docker compose exec app-wsgi python manage.py createsuperuser

# Locally
python manage.py createsuperuser
```

### List All `just` Commands

To see a list of all available helper commands:

```shell
just --list
```

---

## 🧪 Testing

Run the test suite to ensure application stability.

```shell
# Using Docker
docker compose exec app-wsgi python manage.py test

# Locally
python manage.py test
```
