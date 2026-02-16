# Elderly Care & Mindful Support Hub

A Django-based platform that supports elderly care workflows, including caregiver/family coordination, community forum discussions, job postings, messaging, and admin tools.

## Tech Stack

- **Backend:** Django, Django Channels (ASGI/WebSockets)
- **Frontend:** Django templates + static assets
- **Database (default):** SQLite (`db.sqlite3`)
- **Real-time features:** Channels with `InMemoryChannelLayer` by default

---

## 1) Prerequisites

Install the following before setup:

- Python **3.10+** (recommended: 3.11 or newer)
- `pip`
- (Optional) `virtualenv`

Check your versions:

```bash
python --version
pip --version
```

---

## 2) Clone and enter the project

```bash
git clone <your-repo-url>
cd Elder_Care
```

---

## 3) Create and activate a virtual environment

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Upgrade packaging tools:

```bash
python -m pip install --upgrade pip setuptools wheel
```

---

## 4) Install dependencies

### Full dependency set

```bash
pip install -r requirements.txt
```

### Minimal dependency set (quick local run)

If you only need to boot core features quickly, use:

```bash
pip install -r temp_requirements.txt
```

> Note: `temp_requirements.txt` is a reduced set and may not cover every feature/module.

---

## 5) Environment variables (`.env`)

Create a `.env` file in the project root (`/workspace/Elder_Care/.env`):

```env
SECRET_KEY=replace-with-a-strong-secret-key
OPENAI_API_KEY=
```

### Variable reference

- `SECRET_KEY`: Django secret key (required for non-dev deployments; dev fallback exists but should not be relied on in production).
- `OPENAI_API_KEY`: Optional unless chatbot integrations are used.

---

## 6) Database setup

Run migrations:

```bash
python manage.py migrate
```

Create an admin user:

```bash
python manage.py createsuperuser
```

---

## 7) Run the application

### Standard Django development server

```bash
python manage.py runserver
```

Application URL: `http://127.0.0.1:8000/`

### ASGI server (Uvicorn)

```bash
python -m uvicorn elderly_care_hub.asgi:application --reload
```

---

## 8) Useful routes

- Home: `/`
- Forum: `/forum/`
- Accounts: `/accounts/`
- Jobs: `/jobs/`
- Custom admin login: `/custom_admin/login/`
- Django admin site (customized): `/djadmin/`

---

## 9) Development checks

Basic project checks:

```bash
python manage.py check
python manage.py test
```

If static assets were changed:

```bash
python manage.py collectstatic --noinput
```

---

## 10) Troubleshooting

### `ModuleNotFoundError: No module named 'django'`

Your virtual environment is not activated, or dependencies were not installed.

```bash
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### `OPENAI_API_KEY` errors

If chatbot features are enabled, set `OPENAI_API_KEY` in `.env`.

### WebSocket issues in development

The default channel layer is in-memory and intended for local development. For multi-process/production setups, configure Redis and `channels_redis`.

---

## 11) Deployment notes

- Set `DEBUG=False` in production.
- Configure `ALLOWED_HOSTS`.
- Use a persistent channel layer (Redis) instead of in-memory.
- Use a production-ready database (e.g., PostgreSQL) if needed.
- Serve static/media files with proper infrastructure.

---

## Project structure (high level)

- `elderly_care_hub/` — main Django project settings, URLs, ASGI/WSGI
- `accounts/`, `jobs/`, `chat/`, `forum/`, `content/`, `events/`, `feedback/`, `chatbot/` — core apps
- `custom_admin/` — custom administrative features/views
- `templates/`, `static/`, `media/` — frontend templates/assets/uploads
