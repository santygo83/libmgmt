# Library Management System

A modular Flask web application for managing a library: book catalog, user registration,
a request → approval → issue → return workflow, dashboards, a small REST API, and role-based
access for **Admin** and **User**. Built to be simple enough to read, modify, and extend with an
AI coding agent such as OpenCode.

---

## 1. Overview

Users register, browse/search books, and request available titles. An admin reviews requests,
approves (which issues the book and creates a loan) or rejects them, and marks books returned.
Availability counts, overdue detection, and dashboard statistics are all derived from the data.

## 2. Architecture

A three-layer separation keeps business rules out of the web layer:

- **Models** (`app/models/`) — SQLAlchemy entities: `User`, `Book`, `BookRequest`, `Loan`.
- **Services** (`app/services/`) — all business logic and rule enforcement. Routes never touch
  invariants directly; they call services, which raise typed exceptions on rule violations.
- **Routes** (`app/routes/`) — thin Flask blueprints (`auth`, `admin`, `user`, `books`, `api`)
  that handle HTTP, forms, and templates.

The app is assembled by a factory (`create_app`) so tests can spin up an isolated instance.

## 3. Technology Stack

Python 3.11+, Flask, SQLAlchemy ORM, MySQL 8 (SQLite for tests), Flask-Login, Flask-Migrate
(Alembic), Flask-WTF (CSRF + forms), Jinja2, Bootstrap 5, pytest + pytest-cov, Ruff, python-dotenv.

## 4. Project Structure

```
library-management/
├── app/
│   ├── __init__.py            # app factory, health check, error handlers
│   ├── extensions.py          # db, login_manager, migrate, csrf
│   ├── forms.py               # WTForms
│   ├── models/                # user, book, request, loan
│   ├── routes/                # auth, admin, user, books, api, decorators
│   ├── services/              # book/request/loan/stats + exceptions
│   ├── utils/                 # timeutil (tz-aware utcnow)
│   ├── templates/             # base, auth/, admin/, user/, errors/
│   └── static/css, static/js
├── tests/                     # pytest suite (auth, books, requests, loans, admin/api)
├── config.py                  # env-driven config (dev/testing/prod)
├── run.py                     # entry point
├── seed.py                    # demo data
├── requirements.txt / requirements-dev.txt
├── Dockerfile / docker-compose.yml
├── .github/workflows/ci.yml
├── .env.example / .gitignore / pyproject.toml
└── README.md
```

## 5. Prerequisites

Python 3.11+, pip, and either a local MySQL 8 server or Docker (for the bundled MySQL).

## 6. Local Installation

```bash
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                 # then edit values
```

## 7. MySQL Setup

Create the database and user (adjust to your environment):

```sql
CREATE DATABASE library_db CHARACTER SET utf8mb4;
CREATE USER 'library_user'@'localhost' IDENTIFIED BY 'library_pass';
GRANT ALL PRIVILEGES ON library_db.* TO 'library_user'@'localhost';
FLUSH PRIVILEGES;
```

Or use Docker for MySQL only:

```bash
docker compose up -d db
```

## 8. Environment Variables

Set in `.env` (never commit it):

| Variable          | Purpose                                   |
|-------------------|-------------------------------------------|
| `SECRET_KEY`      | Flask session signing key                 |
| `DATABASE_URL`    | `mysql+pymysql://user:pass@host/library_db` |
| `FLASK_CONFIG`    | `development` / `testing` / `production`  |
| `LOAN_PERIOD_DAYS`| Default loan length (14)                  |
| `LOG_LEVEL`       | `INFO`, `DEBUG`, etc.                      |
| `PORT`            | App port (5000)                           |

## 9. Database Migration

```bash
export FLASK_APP=run.py
flask db init      # first time only
flask db migrate -m "initial"
flask db upgrade
```

For a quick start you can instead let the app create tables (the seed script does this).

## 10. Seed Data

```bash
python seed.py
```

Creates 1 admin, 3 users, 10 books, and a few requests/issued books.
**Demo credentials (change before any real use):**

- Admin: `admin@library.example.com` / `Admin@123`
- Users: `alice@` `bob@` `carol@library.example.com` / `User@123`

## 11. Running the Application

```bash
python run.py                       # http://localhost:5000
# or production server:
gunicorn --bind 0.0.0.0:5000 run:app
```

## 12. Running Tests

```bash
pytest -v
pytest --cov=app --cov-report=term-missing
```

Tests use an in-memory SQLite database, so no MySQL server is required. Core business logic
coverage is ~88%.

## 13. Docker Setup

Full stack (app + MySQL):

```bash
docker compose up --build
```

The app waits for MySQL to be healthy, creates tables, and serves on port 5000.

## 13a. AWS EC2 Deployment (without Docker)

Run the app as a Gunicorn service managed by **systemd**, behind **Nginx** as a reverse proxy.
MySQL can live on the same instance or on **Amazon RDS**. All the files are in `deploy/`.

### Automated (Amazon Linux 2023)

```bash
# On the EC2 instance, as ec2-user:
git clone <your-repo> ~/library-management     # or scp the project up
cd ~/library-management
cp .env.production.example .env                # then edit SECRET_KEY + DATABASE_URL
bash deploy/setup_ec2.sh
```

The script installs Python 3.11, Nginx, and (optionally) MariaDB, creates the virtualenv,
seeds the database, installs the systemd service, and configures Nginx. Open **port 80** in
the instance's security group, then visit `http://<EC2-PUBLIC-IP>/`.

### Manual steps (what the script does)

1. **Install packages:** `sudo dnf install -y python3.11 python3.11-pip nginx gcc`
   (add `mariadb105-server` for a local DB).
2. **Virtualenv:** `python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt`
3. **Configure:** `cp .env.production.example .env` and set a strong `SECRET_KEY`
   (`python -c "import secrets; print(secrets.token_hex(32))"`) and `DATABASE_URL`.
4. **DB + seed:** create `library_db`/`library_user` (see section 7), then `python seed.py`.
5. **Gunicorn service:** `sudo cp deploy/library.service /etc/systemd/system/` →
   `sudo systemctl daemon-reload && sudo systemctl enable --now library`.
6. **Nginx:** `sudo cp deploy/nginx-library.conf /etc/nginx/conf.d/library.conf` →
   `sudo nginx -t && sudo systemctl enable --now nginx`.
7. **SELinux (Amazon Linux only):** `sudo setsebool -P httpd_can_network_connect 1`
   so Nginx may reach the Gunicorn socket.

Gunicorn listens on a Unix socket (`/run/library/library.sock`); Nginx proxies port 80 to it
and serves `/static/` directly. The app uses `ProxyFix` to read the `X-Forwarded-*` headers
Nginx sets, so redirects and `request.scheme` stay correct.

### Using Amazon RDS instead of a local DB

Set `INSTALL_LOCAL_MYSQL=no bash deploy/setup_ec2.sh`, and in `.env` point `DATABASE_URL` at the
RDS endpoint. Ensure the RDS security group allows inbound MySQL (3306) from the EC2 instance's
security group, and create `library_db` on RDS first.

### Operating the service

```bash
sudo systemctl status library         # is it running?
sudo systemctl restart library        # after a code update
sudo journalctl -u library -f         # live application logs
```

### HTTPS

Once port 80 works, add TLS with Let's Encrypt:

```bash
sudo dnf install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 14. GitHub Actions CI/CD

`.github/workflows/ci.yml` runs on push/PR: checkout → setup Python → install deps →
Ruff lint → pytest with coverage → upload coverage artifact. The pipeline fails if lint or
tests fail. No secrets are stored in the workflow.

## 15. Demo Credentials

See section 10. For demonstration only — change immediately in any shared environment.

## 16. API Documentation

All endpoints return JSON.

| Method | Endpoint               | Description                    |
|--------|------------------------|--------------------------------|
| GET    | `/health`              | App + DB health                |
| GET    | `/api/health`          | Same, under API prefix         |
| GET    | `/api/books`           | List all books                 |
| GET    | `/api/books/<id>`      | Single book (404 if missing)   |
| GET    | `/api/books/search?q=` | Search title/author/ISBN/category |

Example:

```bash
curl http://localhost:5000/api/books/search?q=python
```

## 17. Troubleshooting

- **`Can't connect to MySQL`** — verify `DATABASE_URL`, that MySQL is running, and the user/db exist.
- **`Invalid email address` on register** — the validator rejects reserved TLDs like `.local`;
  use a normal domain.
- **CSRF errors** — ensure `SECRET_KEY` is set; CSRF is disabled automatically under `testing`.
- **Tables missing** — run migrations (`flask db upgrade`) or `python seed.py`.

---

## Security Notes

Passwords are hashed (Werkzeug), sessions are signed, admin routes are guarded by role checks,
forms use CSRF protection, all DB access goes through the ORM (no raw SQL from user input), and
all secrets come from environment variables. Stack traces are never shown to end users in
production; a generic 500 page is returned and the detail is logged.
