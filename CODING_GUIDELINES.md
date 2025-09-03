# Professional Django Development Guidelines

This document outlines the architectural principles and coding standards to be followed in this project. The goal is to create a codebase that is clean, maintainable, scalable, and easy to understand.

---

## 1. Configuration Management

**The Golden Rule: Decouple Configuration from Code.**

- **Environment-Specific Settings**: The project MUST use a `base.py`, `dev.py`, and `prod.py` structure.
- **No Hardcoded Defaults**: The `DJANGO_SETTINGS_MODULE` environment variable **MUST NOT** be hardcoded in any application file.
- **Secrets and Environment Variables**: All secrets and environment-specific values MUST be loaded from environment variables.

---

## 2. Core Software Design Principles (SOLID)

We adhere to the SOLID principles to guide our software design.

---

## 3. Project Architecture and Structure

- **Strict Decoupling**: The frontend and backend are two separate applications. There **MUST NOT** be any direct dependency or file import between them.
- **API-First Design**: The backend API is the contract. It should be designed, built, and validated before the frontend UI that consumes it.
- **Each App is a Feature**: Each Django app should represent a distinct feature or bounded context (e.g., `users`, `music`, `listening_sessions`).

---

## 4. The API as a Contract

- **Language-Agnostic Data**: The API communicates using JSON, a language-agnostic format. The frontend **MUST NOT** have any knowledge of the backend's internal data structures.
- **Frontend-Specific Types**: The frontend is responsible for defining its own TypeScript types and interfaces that model the expected JSON structure of the API responses.

---

## 5. Backend (Django)

### Database
- **Rich Data Models**: Models should accurately represent the application's domain.
- **Explicit Relationships**: Use `ForeignKey` and `ManyToManyField` with `through` models where appropriate.

### API (Django REST Framework)
- **Use ViewSets**: For standard CRUD operations, `ModelViewSet` provides a clean and conventional way to build endpoints.
- **Permissions**: Always apply appropriate permissions (`IsAuthenticated`) to secure endpoints.

---

## 6. Frontend (React)

- **Component-Based Architecture**: Break down the UI into small, reusable components.
- **Absolute Import Paths**: **MUST** use absolute paths (e.g., `from 'src/features/auth'`) instead of deep relative paths (`from '../../auth'`). This is configured in `tsconfig.json` and makes the codebase more maintainable.
- **Centralized State Management**: Use `zustand` for global state.
- **Custom Hooks**: Encapsulate complex logic and side effects into custom hooks.
- **API Client**: All API communication should go through a centralized `apiClient` that uses an interceptor to automatically attach the authentication token.

---

## 7. Testing Guidelines

- **Self-Contained Tests**: Tests **MUST** be independent and reliable. Each test should create all of its own required data.
