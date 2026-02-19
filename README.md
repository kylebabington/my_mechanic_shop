# My Mechanic Shop API

A RESTful Flask API for managing a mechanic shop: **customers**, **mechanics**, **service tickets**, and **inventory**. It supports customer registration, JWT-based authentication, pagination, rate limiting, and in-memory caching. API documentation is served via Swagger UI.

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

---

## Tech Stack

| Layer        | Technology |
|-------------|------------|
| Framework   | Flask      |
| ORM         | SQLAlchemy (Flask-SQLAlchemy, declarative base) |
| DB          | MySQL (mysql-connector-python) |
| Migrations  | Flask-Migrate |
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
├── app.py                    # Entry point; creates app and runs server
├── config.py                 # Loads .env; BaseConfig, DevelopmentConfig
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
│   ├── schemas/              # Marshmallow schemas
│   │   ├── customer_schema.py
│   │   ├── mechanic_schema.py
│   │   └── (tickets, etc.)
│   ├── blueprints/
│   │   ├── customers/        # /customers
│   │   ├── mechanics/        # /mechanics
│   │   ├── tickets/          # /service-tickets
│   │   └── inventory/        # /inventory
│   ├── utils/
│   │   └── util.py           # JWT encode, token_required decorator
│   └── static/
│       └── swagger.yaml      # OpenAPI 2.0 spec
└── README.md                 # This file
```

---

## Prerequisites

- **Python 3.10+** (project uses type hints and modern syntax)
- **MySQL** server (e.g. local or Docker)
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

   For Swagger UI and migrations (if not in `requirements.txt`):

   ```bash
   pip install flask-swagger-ui flask-migrate pyyaml
   ```

4. **Create the MySQL database**:

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
| `DATABASE_URL` | MySQL connection URL, e.g. `mysql+mysqlconnector://USER:PASSWORD@localhost/my_mechanic_shop_db` |
| `SECRET_KEY`   | Secret used for JWT signing; **must** be set for login and protected routes (e.g. a long random string) |
| `FLASK_DEBUG`  | Optional; `true` or `1` for debug mode |

Example `.env`:

```env
DATABASE_URL=mysql+mysqlconnector://root:YOUR_PASSWORD@localhost/my_mechanic_shop_db
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=true
```

**Important:** Never commit `.env`; it is listed in `.gitignore`.

---

## Running the Application

From the project root (with virtual environment activated):

```bash
python app.py
```

By default the app runs with `debug=True` and is available at **http://localhost:5000**.

To use a specific config (e.g. development):

```bash
set FLASK_ENV=development
python app.py
```

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

Ensure `DATABASE_URL` (and optionally `FLASK_APP=app.py`) is set when running these commands.

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
  All protected enpoints require:
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

A Postman collection is included: **`My Mechanic Shop API.postman_collection.json`**. Import it into Postman to run predefined requests. For auth-required endpoints, set the collection or request variable for the token (e.g. after login) and use it in the `Authorization: Bearer ...` header.

---

## License

This project is for educational use (e.g. Coding Temple). Specify your preferred license if you publish or reuse it.
