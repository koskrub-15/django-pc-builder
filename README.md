# Django PC Builder & E-Commerce Platform

A full-featured web application combining a PC building service, e-commerce platform, real-time chat, and content blog.

---

## Overview

**Django PC Builder** is a portfolio project that integrates multiple systems into a single Django application: a PC configurator, an order tracking system, a WebSocket-based chat, and a blog.

### Key Features

- **PC Builder & Quoting**: Administrators manage component lists; users view pre-configured builds with dynamically calculated total prices.
- **Order Tracking System**: Step-by-step progress tracker lets customers monitor order status in real-time (components ordered → build in progress → testing → delivered).
- **Real-Time Chat**: WebSocket-based chat (Django Channels) integrated with the builder — admins can send component lists and create orders directly from the chat.
- **Blog Platform**: Posts, categories, and comments for sharing articles about PC hardware and builds.
- **User Authentication**: Registration, login/logout, and profile management via `django-allauth`.
- **Dockerized**: Full stack (Nginx, WSGI, ASGI) managed by Docker Compose.

### Tech Stack

- **Framework**: [Django](https://www.djangoproject.com/)
- **WebSockets**: [Django Channels](https://channels.readthedocs.io/) + Daphne
- **Database**: PostgreSQL
- **Auth**: [django-allauth](https://allauth.org/)
- **Environment**: [uv](https://github.com/astral-sh/uv) & [Docker](https://www.docker.com/)

### Architecture

Nginx routes HTTP requests to Gunicorn (WSGI) and WebSocket connections to Daphne (ASGI):

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

## Quick Start

### Run the App

Build images, apply migrations, and start all services from zero:

```shell
just homework-i-docker-i-run
```

### Purge Data

Stop and remove all containers, networks, and volumes:

```shell
just homework-i-docker-i-purge
```

---

## Development

### Install just

You must have [just] installed on your system to run different commands.

- [just.just](just/dev/just.just)

After installing [just], you can see all available commands with:

```bash
just --list
```

[just]: https://github.com/casey/just

### Initialize development environment

Create venv, register pre-commit hooks, and install dependencies:

```bash
just init-i-dev
```

---

## Docker

Use services via Docker Compose.

### Run

```shell
just d-up
```

### Purge

Purge all data related to services:

```shell
just d-purge
```

---

## Testing

```shell
# Using Docker
docker compose exec app-wsgi python manage.py test

# Locally
python manage.py test
```
