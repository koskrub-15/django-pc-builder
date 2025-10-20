# Django Project

---

## 🏠 Homework

Homework-related actions.

### ▶️ Run

Make all actions needed to run homework from zero. Including configuration.

```shell
just homework-i-docker-i-run
```

### 🚮 Purge

Make all actions needed to run homework from zero.

```shell
just homework-i-docker-i-purge
```

### ⚙️ Initialize the project with uv

Creates pyproject.toml and a .venv using the specified Python version

```shell
uv init
```

### 🔄 Sync dependencies

Installs all dependencies listed in pyproject.toml (and uv.lock if present)

```shell
uv sync
```

---

## 🛠️ Development

### Install just

You must have [just] installed on your system to run different commands.

If you don't have [just] installed, you can find commands for installation here:

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

## 🐳 Docker

Use services in dockers.

### ▶️ Run

Just run

```shell
just d-run
```

### 🚮 Purge

Purge all data related to services

```shell
just d-purge
```
