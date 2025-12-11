# 🚀 Quick Start Guide

## Prerequisites Check
- [ ] Python 3.11+ installed
- [ ] PostgreSQL 14+ installed and running
- [ ] Virtual environment activated

## 5-Minute Setup

### 1. Install Dependencies
```bash
./venv/bin/pip install -r requirements.txt
```

### 2. Create Database
```bash
# Login to PostgreSQL
psql -U postgres

# Run these SQL commands
CREATE DATABASE restokr;
\c restokr
CREATE EXTENSION postgis;
\q
```

### 3. Configure Environment
```bash
# Copy template
cp .env.example .env

# Edit .env if needed (defaults work for local dev)
# DATABASE_URL is already set to: postgresql+asyncpg://postgres:admin@localhost/restokr
```

### 4. Initialize Database
```bash
# Auto-create tables on first run, OR use Alembic:
./venv/bin/alembic revision --autogenerate -m "Initial migration"
./venv/bin/alembic upgrade head
```

### 5. Start Server
```bash
./venv/bin/uvicorn app.main:app --reload
```

## ✅ Verify It's Working

### Test Health Endpoint
```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-11T...",
  "version": "1.0.0",
  "service": "ReStockr Early Access API",
  "database": {
    "status": "healthy",
    "message": "Connected (PostGIS: ...)"
  }
}
```

### Test Signup Endpoint
```bash
curl -X POST http://localhost:8000/api/v1/signup \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test User",
    "email": "test@example.com",
    "phone_number": "08012345678",
    "role": "customer"
  }'
```

### Access Interactive Docs
Open: http://localhost:8000/docs

## 🎯 Next Steps

1. **Test Admin Endpoints**: Login with `admin` / `changeme123` at `/docs`
2. **Change Admin Password**: Update `ADMIN_PASSWORD` in `.env`
3. **Configure Email**: Add SMTP settings to enable confirmation emails
4. **Review API**: Read `IMPLEMENTATION_SUMMARY.md` for full API reference

## 🐛 Troubleshooting

### Database Connection Error
```bash
# Check PostgreSQL is running
brew services list | grep postgresql  # macOS
sudo systemctl status postgresql      # Linux

# Verify database exists
psql -U postgres -l | grep restokr
```

### Import Errors
```bash
# Reinstall dependencies
./venv/bin/pip install --force-reinstall -r requirements.txt
```

### Port Already in Use
```bash
# Use different port
./venv/bin/uvicorn app.main:app --reload --port 8001
```

---

**Ready to build ReStockr! 🎉**
