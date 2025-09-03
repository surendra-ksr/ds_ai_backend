# Professional Django Development Guidelines

This document outlines the architectural principles and coding standards to be followed in this project. The goal is to create a codebase that is clean, maintainable, scalable, and easy to understand.

---

## 1. Configuration Management

**The Golden Rule: Decouple Configuration from Code.**

- **Environment-Specific Settings**: The project MUST use a `config/settings/` package containing `base.py`, `dev.py`, and `prod.py`.
- **Secrets and Environment Variables**: All secrets (API keys, `SECRET_KEY`) and environment-specific values MUST be loaded from environment variables (e.g., via a `.env` file).
- **Entry-Point Configuration**: The `DJANGO_SETTINGS_MODULE` environment variable is set in the project's entry points (`manage.py`, `wsgi.py`, `asgi.py`) and defaults to the `dev` environment.

---

## 2. Project Architecture and Structure

- **Application Source Root**: The `apps/` directory is the primary source root for all local Django applications. It is added to the `PYTHONPATH` by the project's entry points.
- **Direct Application Imports**: All internal application imports MUST be direct. For example, to import a model from the `securities` app, use `from securities.models import Security`, NOT `from apps.securities.models import Security`.
- **`INSTALLED_APPS` Naming**: Consistent with the direct import style, apps MUST be registered in `settings/base.py` using their direct name (e.g., `'securities'`, not `'apps.securities'`).
- **Each App is a Feature**: Each Django app should represent a distinct feature or bounded context (e.g., `users`, `securities`, `analysis`).
- **Required App Structure**: Every app MUST contain a `migrations` package with an `__init__.py` file inside it, even if the app has no models. This is required for Django's discovery mechanism.

---

## 3. The API as a Contract

- **API-First Design**: The backend API is the contract. It should be designed, built, and validated before the frontend UI that consumes it.
- **Language-Agnostic Data**: The API communicates using JSON.

---

## 4. Backend (Django)

### Database
- **Rich Data Models**: Models should accurately represent the application's domain.
- **Explicit Relationships**: Use `ForeignKey` and `ManyToManyField` where appropriate.

### API (Django REST Framework)
- **Use ViewSets**: For standard CRUD operations, `ModelViewSet` provides a clean and conventional way to build endpoints.
- **Permissions**: Always apply appropriate permissions to secure endpoints.

---

## 5. Testing Guidelines

- **Self-Contained Tests**: Tests **MUST** be independent and reliable. Each test should create all of its own required data.
