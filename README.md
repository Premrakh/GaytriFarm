# GaytriFarm Backend

Django-based backend for the GaytriFarm mobile app.  
Provides user management (registration, email verification, JWT auth with blacklist), order management (customer/distributor/delivery staff flows), monthly billing generation (Celery task), file uploads (MEDIA), and admin UI.

## Key components
- Django 5.x
- Django REST Framework
- djangorestframework-simplejwt (with token blacklist)
- Celery (with beat scheduling)
- PostgreSQL (recommended; pgbouncer supported)
- Media/static configured via `MEDIA_ROOT` / `STATIC_ROOT`

## Quick prerequisites
- Python 3.10+ (project uses 3.12 in the dev environment)
- PostgreSQL
- Redis (as Celery broker)
- Poetry (dependency manager)

## Install Poetry (if not installed)
Linux / macOS:
```bash
curl -sSL https://install.python-poetry.org | python3 -