# ReStockr Early Access API

Hyper-local restocking platform backend - Early Access signup system for Customers, Vendors, and Riders.

## 🎯 Features

- ✅ **Early Access Signups**: Capture customer, vendor, and rider signups
- ✅ **Strong Typing**: Full type safety with Pydantic and SQLAlchemy
- ✅ **Phone Validation**: Auto-prepend +234 for Nigerian numbers
- ✅ **Email Confirmation**: Automated welcome emails
- ✅ **Admin Dashboard**: List, filter, and export signups (CSV/JSON/Excel)
- ✅ **Health Checks**: System and database monitoring
- ✅ **PostGIS Support**: Geographic data ready for future features
- ✅ **Async Architecture**: Full async/await with PostgreSQL

## 🏗️ Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL + PostGIS
- **ORM**: SQLAlchemy 2.0 (Async)
- **Validation**: Pydantic v2
- **Email**: aiosmtplib (Async SMTP)

## 📦 Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ with PostGIS extension
- Virtual environment tool

### Setup

1. **Clone and navigate to project**
   ```bash
   cd /Users/Penivera/Projects/restokr
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Setup PostgreSQL database**
   ```sql
   CREATE DATABASE restokr;
   \c restokr
   CREATE EXTENSION postgis;
   ```

6. **Run database migrations**
   ```bash
   # The app will auto-create tables on first run
   # Or use Alembic for version control (recommended for production)
   alembic init migrations
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
   ```

## 🚀 Running the API

### Development Mode
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Access the API:
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

## 📡 API Endpoints

### Public Endpoints

#### `POST /api/v1/signup`
Create early access signup
```json
{
  "full_name": "Adebayo Johnson",
  "email": "adebayo@example.com",
  "phone_number": "08012345678",
  "role": "customer",
  "city": "Abuja"
}
```

#### `GET /api/v1/health`
System health check with database connectivity test

#### `GET /api/v1/health/ping`
Lightweight ping endpoint

### Admin Endpoints (HTTP Basic Auth Required)

#### `GET /api/v1/admin/signups`
List all signups with pagination
- Query params: `page`, `page_size`, `role`, `city`

#### `GET /api/v1/admin/export?format=csv`
Export signups in CSV, JSON, or Excel
- Query params: `format` (csv/json/excel), `role` (optional filter)

#### `GET /api/v1/admin/stats`
Get signup statistics

**Admin Credentials** (default, change in `.env`):
- Username: `admin`
- Password: `changeme123`

## 🏛️ Project Structure

```
restokr/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app + lifespan
│   ├── config.py            # Settings with Field() defaults
│   ├── database.py          # Async SQLAlchemy setup
│   ├── models/              # Database models
│   │   ├── __init__.py
│   │   └── signup.py        # EarlyAccessSignup model
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   └── signup.py        # Request/Response models
│   ├── api/                 # Route handlers
│   │   ├── __init__.py
│   │   ├── deps.py          # Dependencies (auth, db)
│   │   └── v1/
│   │       ├── signups.py   # Signup endpoints
│   │       ├── admin.py     # Admin endpoints
│   │       └── health.py    # Health checks
│   ├── core/                # Business logic
│   │   ├── __init__.py
│   │   └── email.py         # Email service
│   └── utils/               # Utilities
│       └── __init__.py
├── requirements.txt
├── .env.example
└── README.md
```

## 🔒 Security Features

- **HTTP Basic Auth** for admin routes (constant-time comparison)
- **Email/Phone uniqueness** validation
- **SQL injection protection** via SQLAlchemy parameterized queries
- **CORS** configured for specific origins
- **Environment-based secrets** (no hardcoded credentials)

## 📧 Email Configuration

The system sends confirmation emails to new signups. Configure SMTP in `.env`:

### Gmail Example
1. Enable 2FA in Google Account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Update `.env`:
   ```
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-16-char-app-password
   ```

### Other Providers
- **SendGrid**: Use SMTP relay
- **Mailgun**: Configure SMTP credentials
- **AWS SES**: Use SMTP interface

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## 📊 Database Schema

### `early_access_signups` Table

| Column           | Type        | Description                    |
|------------------|-------------|--------------------------------|
| id               | Integer     | Primary key                    |
| full_name        | String(255) | User's full name               |
| email            | String(255) | Unique email                   |
| phone_number     | String(20)  | Unique phone (E.164 format)    |
| role             | Enum        | customer/vendor/rider          |
| city             | String(100) | Location (default: Abuja)      |
| location         | Geography   | PostGIS point (future use)     |
| created_at       | DateTime    | Signup timestamp               |
| is_exported      | Boolean     | Export tracking                |
| email_confirmed  | Boolean     | Email confirmation status      |

## 🚧 Roadmap

- [ ] Alembic migration setup
- [ ] Unit tests with pytest
- [ ] Rate limiting (SlowAPI)
- [ ] Redis caching for stats
- [ ] Vendor KYC document upload (AWS S3)
- [ ] Rider verification endpoints
- [ ] Customer address management

## 📝 License

Proprietary - Akodu Resources Limited. All rights reserved.

## 🤝 Contributing

This is a private project under NDA. Contact project lead for contribution guidelines.

---

Built with ❤️ by the ReStockr Team
