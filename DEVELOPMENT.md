# DEVELOPMENT GUIDE for DataMate

This document provides a comprehensive development guide for DataMate, a polyglot, microservices-based project consisting of Java, Python, and React components. It describes how to set up, build, test, run, and contribute in a local Docker Compose-based environment, without exposing secrets.

<!-- NOTE: This file is intended as a high-level guide. Do not duplicate content from component READMEs; reference them where appropriate. -->

## Overview

DataMate is composed of multiple services (Java backend, Python runtime, and React frontend) coordinated via Docker Compose for local development. The guide below covers prerequisites, quick-start steps, project structure, development workflow, environment configuration, testing, debugging, common issues, documentation, contribution workflow, and licensing.

Refer to the component READMEs for detailed implementation notes:
- Backend: backend/README.md
- Runtime: runtime/datamate-python/README.md
- Frontend: frontend/README.md

For code style guidelines, see AGENTS.md in the repository root.

## Prerequisites

- Java Development: JDK 21 and Maven
- Python: Python 3.12 and Poetry
- Node.js: Node.js 18
- Docker and Docker Compose
- Optional: Make (for convenience)

Notes:
- Ensure Java and Python environments are on the system PATH where applicable.
- Docker Compose will orchestrate the local development stack.

## Quick Start

1) Clone the repository and install dependencies:
- git clone https://github.com/your-org/datemate.git
- cd datemate
- (Optional) Create and activate a Python virtual environment if not using Poetry-managed envs.
- Build dependencies per component as described below.

2) Start the local stack with Docker Compose:
- docker compose up -d
- This brings up the Java backend, Python runtime, and React frontend services along with any required databases and caches as defined in the docker-compose.yml.

3) Start individual components (if you prefer not to use the Docker stack):
- Java backend
  - mvn -f backend/pom.xml -DskipTests package
  - Run the main application (path may vary): java -jar backend/main-application/target/*.jar
- Python runtime
  - cd runtime/datamate-python
  - poetry install
  - uvicorn app.main:app --reload --port 18000 --host 0.0.0.0
- React frontend
  - cd frontend
  - npm ci
  - npm run dev

4) Stop the stack:
- docker compose down

> Tip: In a team setting, prefer Docker Compose for consistency across development environments.

## Project Structure

- backend/
- frontend/
- runtime/
- deployment/
- docs/
- AGENTS.md (code style guidelines)
- docker/ (docker-related tooling)
- .env* files (per-component configurations, see Environment Configuration section)

This is a polyglot project with the following language footprints:
- Java for the backend services under backend/
- Python for the runtime under runtime/datamate-python/
- React/TypeScript for the frontend under frontend/

## Development Workflow

Language-specific workflows:

- Java (Backend)
  - Build: mvn -f backend/pom.xml -DskipTests package
  - Test: mvn -f backend/pom.xml test
  - Run: mvn -f backend/pom.xml -Dexec.mainClass=... spring-boot:run (or run the packaged jar)
- Python (Runtime)
  - Install: cd runtime/datamate-python && poetry install
  - Test: pytest
  - Run: uvicorn app.main:app --reload --port 18000 --host 0.0.0.0
- Frontend (React)
  - Install: cd frontend && npm ci
  - Test: No frontend tests configured
  - Build: npm run build
  - Run: npm run dev

General tips:
- Use Docker Compose for a repeatable local stack.
- Run linters and tests before creating PRs.
- Keep dependencies in sync across environments.

## Environment Configuration

Each component can have its own environment file(s). Do not commit secrets. Use sample/.env.example files as references when available.

- Backend
  - Path: backend/.env (example keys below)
  - Typical keys: DB_URL, DB_USER, DB_PASSWORD, JWT_SECRET, REDIS_URL, CLOUD_STORAGE_ENDPOINT
- Runtime (Python)
  - Path: runtime/datamate-python/.env
  - Typical keys: DATABASE_URL, RAY_ADDRESS, CELERY_BROKER_URL, APP_SETTINGS
- Frontend
  - Path: frontend/.env
  - Typical keys: VITE_API_BASE_URL, VITE_DEFAULT_LOCALE, NODE_ENV

Notes:
- Copy the corresponding .env.example to .env and fill in values as needed.
- Do not commit .env files containing secrets.

## Testing

- Java: JUnit 5 tests run via Maven (mvn test).
- Python: pytest in runtime/datamate-python/test or relevant tests.
- Frontend: No frontend tests configured in this repo.

## Code Style

Code style follows the repository-wide guidelines described in AGENTS.md. See:
- AGENTS.md (root): Code style guidelines for all languages.
- Java: Follow Java conventions in backend/ and accordance with project conventions.
- Python: Follow PEP 8 and project-specific conventions in runtime/datamate-python.
- React: Follow the frontend conventions in frontend/ (TypeScript/TSX).

Link to guidelines: AGENTS.md

## Debugging

- Java (Backend): Enable JPDA debugging by starting the JVM with a debug port and attach a debugger.
  - Example (local): export JAVA_TOOL_OPTIONS='-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:5005' && java -jar path/to/app.jar
  - Attach with IDE on port 5005 after launch.
- Python (Runtime): Run with debugpy listening on port 5678 to attach from IDEs.
  - Example: cd runtime/datamate-python && poetry install
    python -m debugpy --listen 5678 --wait-for-client -m uvicorn app.main:app --reload --port 18000 --host 0.0.0.0
- Frontend (React): Use Node inspector to debug front-end code in dev server.
  - Example: npm run dev -- --inspect-brk=9229

Tips: Use your preferred IDEs (IntelliJ/VSCode/WebStorm) to attach to the running processes on their respective ports.

## Common Issues

- Port conflicts: Check which process is using a port with lsof -i TCP:<PORT> or ss -ltnp. Stop or reconfigure conflicting services.
- Database connection errors: Ensure .env contains correct DATABASE_URL and credentials; ensure the database service is up in Docker Compose.
- Ray cluster issues (Python runtime): Ensure Ray is started and accessible at the configured RAY_ADDRESS; check logs for worker failures and bootstrap status.

## Documentation

Component READMEs provide detailed usage and design decisions. See:
- backend/README.md
- runtime/datamate-python/README.md
- frontend/README.md
- deployment/README.md

## Contributing

Contributions follow a PR workflow:
- Create a feature/bugfix branch from main (e.g., feature/new-action)
- Implement changes with tests where applicable
- Run unit tests for the changed components
- Open a PR with a clear description of the changes and the rationale
- Ensure CI checks pass (build, unit tests, lint)
- Obtain reviews and address feedback
- Merge to main after approval

## License

Apache 2.0

---

References:
- AGENTS.md for code style guidelines: AGENTS.md
- Java dependencies: backend/pom.xml
- Node dependencies: frontend/package.json
- Python dependencies: runtime/datamate-python/pyproject.toml
