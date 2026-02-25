# My Mechanic Shop API

A RESTful Flask API for managing a mechanic shop: **customers**, **mechanics**, **service tickets**, and **inventory**. It supports customer registration, JWT-based authentication, pagination, rate limiting, and in-memory caching. API documentation is served via Swagger UI.

**Quick start (tests only):** `pip install -r requirements.txt && pip install pytest && python -m pytest tests/ -v` — no database or `.env` required.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Database Migrations](#database-migrations)
- [API Overview](#api-overview)
- [Authentication](#authentication)
- [API Documentation (Swagger)](#api-documentation-swagger)
- [Testing](#testing)
- [Testing with Postman](#testing-with-postman)
- [License](#license)

---

## Features

- **Customers**: Register, login (JWT), update/delete profile, list (paginated), view own tickets
- **Mechanics**: CRUD with salary; many-to-many association with service tickets
- **Service tickets**: CRUD with VIN, service date, description; link to customer, mechanics, and parts (inventory)
- **Inventory**: CRUD for parts (name, price); many-to-many with service tickets
- **Security**: Password hashing (Werkzeug), JWT (python-jose) for protected routes
- **API behavior**: Rate limiting (Flask-Limiter), optional response caching (Flask-Caching), JSON request/response with Marshmallow validation
- **Docs**: OpenAPI 2.0 spec (`swagger.yaml`) and Swagger UI at `/api/docs`
- **Testing**: pytest/unittest test suite for customers, mechanics, service tickets, and inventory; uses SQLite via `TestingConfig`

---

## Tech Stack

| Layer        | Technology |
|-------------|------------|
| Framework   | Flask      |
| ORM         | SQLAlchemy (Flask-SQLAlchemy, declarative base) |
| DB          | PostgreSQL (psycopg2-binary) or MySQL (mysql-connector-python) |
| Migrations  | Flask-Migrate (Alembic) |
| Serialization / validation | Marshmallow (Flask-Marshmallow, marshmallow-sqlalchemy) |
| Auth        | JWT via python-jose; passwords via Werkzeug |
| Rate limiting | Flask-Limiter |
| Caching     | Flask-Caching (SimpleCache) |
| Config      | python-dotenv (.env) |
| API docs    | Swagger UI (flask-swagger-ui), static `swagger.yaml` |

---

## Project Structure

```
my_mechanic_shop/
├── flask_app.py              # App factory entry (Gunicorn/Flask: FLASK_APP=flask_app)
├── config.py                 # Loads .env; BaseConfig, DevelopmentConfig, TestingConfig, ProductionConfig
├── requirements.txt          # Python dependencies
├── .env.example              # Template for .env (copy to .env)
├── .gitignore
├── migrations/               # Flask-Migrate (Alembic) scripts
│   ├── env.py
│   ├── README
│   └── versions/
├── application/
│   ├── __init__.py           # create_app() factory; registers blueprints + Swagger UI
│   ├── extensions.py         # db, ma, limiter, cache, migrate (unbound)
│   ├── models/               # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── customer.py
│   │   ├── mechanic.py
│   │   ├── service_ticket.py
│   │   └── inventory.py
│   ├── schemas/              # Marshmallow schemas (shared)
│   │   ├── customer_schema.py
│   │   ├── mechanic_schema.py
│   │   ├── service_ticket_schema.py
│   │   └── inventory_schema.py
│   ├── blueprints/
│   │   ├── customers/        # /customers
│   │   ├── mechanics/        # /mechanics (routes + schemas)
│   │   ├── tickets/          # /service-tickets (routes + schemas)
│   │   └── inventory/        # /inventory
│   ├── utils/
│   │   └── util.py           # JWT encode, token_required decorator
│   └── static/
│       └── swagger.yaml      # OpenAPI 2.0 spec
├── tests/
│   ├── __init__.py
│   ├── test_customer.py
│   ├── test_mechanics.py
│   ├── test_tickets.py
│   └── test_inventory.py
└── README.md                 # This file
```

---

## Prerequisites

- **Python 3.10+** (project uses type hints and modern syntax)
- **PostgreSQL** or **MySQL** for running the API (e.g. local or cloud); not required for running tests (tests use SQLite)
- **pip** (or another Python package manager)

---

## Setup

1. **Clone the repository** (if applicable):

   ```bash
   git clone <repository-url>
   cd my_mechanic_shop
   ```

2. **Create and activate a virtual environment**:

   ```bash
   python -m venv venv
   # Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # Windows (CMD):
   .\venv\Scripts\activate.bat
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

   For full local development (Swagger UI, database migrations):

   ```bash
   pip install flask-swagger-ui flask-migrate pyyaml pytest
   ```

4. **Create the database** (PostgreSQL or MySQL):

   **PostgreSQL:**
   ```bash
   createdb my_mechanic_shop_db
   ```
   Or in `psql`: `CREATE DATABASE my_mechanic_shop_db;`

   **MySQL:**
   ```sql
   CREATE DATABASE my_mechanic_shop_db;
   ```

5. **Configure environment** (see [Configuration](#configuration)).

6. **Run migrations** (see [Database Migrations](#database-migrations)).

---

## Configuration

Configuration is driven by environment variables. Copy the example file and set your values:

```bash
cp .env.example .env
```

Edit `.env` with your settings. Required (and commonly used) variables:

| Variable       | Description |
|----------------|-------------|
| `DATABASE_URL` or `SQLALCHEMY_DATABASE_URI` | DB connection URL. **PostgreSQL:** `postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DATABASE` — **MySQL:** `mysql+mysqlconnector://USER:PASSWORD@localhost/my_mechanic_shop_db` |
| `SECRET_KEY`   | Secret used for JWT signing; **must** be set for login and protected routes (e.g. a long random string) |
| `FLASK_DEBUG`  | Optional; `true` or `1` for debug mode |
| `FLASK_APP`    | Optional; set to `flask_app` for `flask` CLI (e.g. `flask run`, `flask db upgrade`) |

Example `.env` (PostgreSQL):

```env
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/my_mechanic_shop_db
SECRET_KEY=your-secret-key-here
FLASK_APP=flask_app
FLASK_DEBUG=true
```

For MySQL use: `DATABASE_URL=mysql+mysqlconnector://root:YOUR_PASSWORD@localhost/my_mechanic_shop_db`

**Important:** Never commit `.env`; it is listed in `.gitignore`.

---

## Running the Application

From the project root (with virtual environment activated). Set `FLASK_APP` so the Flask CLI finds the app (or add `FLASK_APP=flask_app` to `.env`):

```bash
# Windows (PowerShell):
$env:FLASK_APP = "flask_app"; flask run

# Windows (CMD):
set FLASK_APP=flask_app && flask run

# macOS/Linux:
export FLASK_APP=flask_app
flask run
```

The app is available at **http://localhost:5000**. For production (e.g. Render), Gunicorn uses `flask_app:app`.

---

## Database Migrations

The project uses **Flask-Migrate** (Alembic) for schema changes.

- **Create a new migration** (after changing models):

  ```bash
  flask db migrate -m "Short description"
  ```

- **Apply migrations**:

  ```bash
  flask db upgrade
  ```

- **Roll back one revision**:

  ```bash
  flask db downgrade
  ```

Ensure `DATABASE_URL` (or `SQLALCHEMY_DATABASE_URI`) and `FLASK_APP=flask_app` are set when running these commands.

---

## Testing

The project includes a test suite (pytest or unittest) that uses **TestingConfig** with a SQLite in-memory/file database. No MySQL or `.env` is required to run tests.

**Run all tests (recommended):**

```bash
python -m pytest tests/ -v
```

Or with the standard library runner:

```bash
python -m unittest discover -s tests -v
```

Tests cover customers, mechanics, service tickets, and inventory (CRUD, auth, pagination, and relationships). Each test module uses a fresh app context and isolates database state.

---

## API Overview

| Resource        | Base path         | Main actions |
|----------------|-------------------|--------------|
| Customers      | `/customers`      | POST (register), GET (list paginated), POST `/login`, GET `/my-tickets` (auth), PUT/DELETE `/me` (auth) |
| Mechanics      | `/mechanics`      | CRUD; list supports pagination |
| Service tickets| `/service-tickets`| CRUD; link customer, mechanics, parts |
| Inventory      | `/inventory`      | CRUD for parts |

- **Consumes:** `application/json`
- **Produces:** `application/json`
- **Pagination:** List endpoints support `limit` and `offset` query parameters where documented.
- **Rate limits:** Defaults (e.g. 100/day, 10/hour) are set in `application/extensions.py` (Limiter).

---

## Authentication

- **Registration:** `POST /customers/` with body `{ "name", "email", "password", "phone" (optional) }`.
- **Login:** `POST /customers/login` with `{ "email", "password" }`. Response includes `auth_token` (JWT).
- **Protected routes:** Send the token in the header:
  ```http
  All protected endpoints require:
  Authorization: Bearer <auth_token>
  ```
- **Token lifetime:** JWTs are configured with a 1-hour expiration (see `application/utils/util.py`).

---

## API Documentation (Swagger)

Once the app is running, open:

**http://localhost:5000/api/docs**

This serves **Swagger UI** and loads the OpenAPI 2.0 spec from `application/static/swagger.yaml`. Use it to browse and try endpoints. For protected routes, use the “Authorize” option and set the Bearer token.

---

## Testing with Postman

A Postman collection is included in the project root: **`My Mechanic Shop API.postman_collection.json`**. Import it into Postman to run predefined requests.

- **Collection variable `base_url`**: Set to your API root (e.g. `http://localhost:5000` for local, or your Render/deployed URL). The default may point to a deployed instance.
- **Auth**: Run **Login** under Customers first; the collection script saves the returned `auth_token` into the `auth_token` variable. Protected requests use `Authorization: Bearer {{auth_token}}`.
- **IDs**: Set `customer_id`, `mechanic_id`, `ticket_id`, `part_id` as needed when calling Get-by-ID or update/delete requests.

---

## License

This project is for educational use (e.g. Coding Temple). Specify your preferred license if you publish or reuse it.
