# 🔐 ReStockr API - Quick Authentication Reference

## 🚀 Quick Start

### 1. Sign Up
```bash
POST /api/v1/signup
{
  "full_name": "John Doe",
  "email": "john@example.com",
  "phone_number": "8012345678",
  "role": "customer",
  "city": "Lagos"
}
```
✅ Account created (inactive)  
📧 Activation token generated

### 2. Activate Account
```bash
POST /api/v1/auth/activate
{
  "email": "john@example.com",
  "activation_token": "token-from-email-or-db",
  "password": "SecurePass123"
}
```
✅ Account activated  
🔓 Ready to login

### 3. Login
```bash
POST /api/v1/auth/login
{
  "email": "john@example.com",
  "password": "SecurePass123"
}
```
✅ Returns access_token + refresh_token  
⏱️ Access token valid for 30 minutes

### 4. Use Protected Endpoints
```bash
GET /api/v1/users/me
Header: Authorization: Bearer {access_token}
```
✅ Access your profile and protected resources

### 5. Refresh Token
```bash
POST /api/v1/auth/refresh
{
  "refresh_token": "your-refresh-token"
}
```
✅ Get new access_token + refresh_token  
🔄 Old refresh token invalidated

### 6. Logout
```bash
POST /api/v1/auth/logout
Header: Authorization: Bearer {access_token}
```
✅ Refresh token invalidated  
🔒 Must login again

---

## 📍 All Endpoints

### 🔓 Public (No Auth Required)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/signup` | Create account |
| POST | `/api/v1/auth/login` | Get tokens |
| POST | `/api/v1/auth/activate` | Activate account |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/resend-activation` | Resend activation token |
| GET | `/api/v1/health` | Health check |

### 🔐 Protected (Requires Bearer Token)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/users/me` | Get current user profile |
| PATCH | `/api/v1/users/me` | Update profile |
| DELETE | `/api/v1/users/me` | Deactivate account |
| POST | `/api/v1/auth/logout` | Logout |

### 🛡️ Admin (HTTP Basic Auth)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/admin/signups` | List all signups |
| GET | `/api/v1/admin/export` | Export data |
| GET | `/api/v1/admin/stats` | Get statistics |
| GET | `/api/v1/admin/analytics` | Get analytics |
| GET | `/api/v1/admin/recent` | Recent signups |

---

## 🎯 Token Information

### Access Token
- **Lifetime**: 30 minutes (default)
- **Purpose**: Access protected endpoints
- **Claims**: email, role, type, exp, iat
- **Usage**: `Authorization: Bearer {token}`

### Refresh Token
- **Lifetime**: 7 days (default)
- **Purpose**: Get new access token
- **Storage**: Database (validated on refresh)
- **Rotation**: New token issued on every refresh

### Activation Token
- **Lifetime**: 7 days (default)
- **Purpose**: Account activation
- **Usage**: One-time only (cleared after use)
- **Generation**: Cryptographically secure random

---

## 🔑 Password Requirements

✅ Minimum 8 characters  
✅ At least 1 uppercase letter (A-Z)  
✅ At least 1 lowercase letter (a-z)  
✅ At least 1 digit (0-9)

**Example**: `SecurePass123`, `MyP@ssw0rd`, `Test1234ABC`

---

## 🎨 Swagger UI Usage

1. Go to http://localhost:8000/docs
2. Click **"Authorize"** button (🔒)
3. Select **HTTPBearer** section
4. Paste your access token
5. Click **"Authorize"**
6. ✅ All requests now authenticated!

---

## ⚠️ Error Responses

### 401 Unauthorized
```json
{"detail": "Could not validate credentials"}
```
**Causes**: Invalid/expired token, user not found

### 403 Forbidden
```json
{"detail": "Account not activated. Please activate your account first."}
```
**Causes**: Account not activated, account deactivated

### 400 Bad Request
```json
{"detail": "Invalid activation token"}
```
**Causes**: Wrong token, expired token, already activated

---

## 🔧 Environment Variables

```env
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

**Generate SECRET_KEY**:
```bash
openssl rand -hex 32
```

---

## 📦 User Roles

- **customer** - End users who order items
- **vendor** - Sellers/stores who list products
- **rider** - Delivery personnel

---

## 🧪 Testing Flow

```python
# 1. Signup
POST /api/v1/signup → user_id, email

# 2. Get activation token (from DB or email)
SELECT activation_token FROM early_access_signups WHERE email = ?

# 3. Activate
POST /api/v1/auth/activate → success

# 4. Login
POST /api/v1/auth/login → access_token, refresh_token

# 5. Use API
GET /api/v1/users/me [Bearer token] → user_data

# 6. Refresh
POST /api/v1/auth/refresh → new_tokens

# 7. Logout
POST /api/v1/auth/logout [Bearer token] → success
```

---

## 🚨 Important Notes

⚠️ **Production**:
- Use strong SECRET_KEY (32+ chars)
- Enable HTTPS only
- Never commit SECRET_KEY to git
- Implement rate limiting
- Add email sending for activation

✅ **Development**:
- Use `.env` file for config
- Check activation token in database
- Monitor logs for auth events
- Test with Swagger UI or cURL

---

## 📞 Support

- **Docs**: `/docs` (Swagger UI)
- **Health**: `/api/v1/health`
- **Logs**: Check terminal/uvicorn output

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Documentation**: See AUTHENTICATION.md for details
