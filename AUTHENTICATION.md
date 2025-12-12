# ReStockr API - Authentication Guide

## Overview

The ReStockr API implements JWT (JSON Web Token) bearer authentication with refresh tokens, account activation, and comprehensive user management.

## Authentication Flow

### 1. Early Access Signup
```http
POST /api/v1/signup
Content-Type: application/json

{
  "full_name": "John Doe",
  "email": "john@example.com",
  "phone_number": "8012345678",
  "role": "customer",
  "city": "Lagos"
}
```

**Response:**
- User account created with `is_active=false`
- Activation token generated (valid for 7 days)
- Confirmation email sent (email functionality to be implemented)

### 2. Account Activation
```http
POST /api/v1/auth/activate
Content-Type: application/json

{
  "email": "john@example.com",
  "activation_token": "secure-token-from-email",
  "password": "SecurePass123"
}
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

**Response:**
```json
{
  "message": "Account activated successfully",
  "detail": "You can now log in with your email and password"
}
```

### 3. Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "SecurePass123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Token Details:**
- Access token expires in 30 minutes (configurable)
- Refresh token expires in 7 days (configurable)
- Refresh token stored in database for validation

### 4. Using Protected Endpoints

Add the access token to the `Authorization` header:

```http
GET /api/v1/users/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 5. Refresh Access Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Notes:**
- Both access and refresh tokens are rotated
- Old refresh token is invalidated

### 6. Logout
```http
POST /api/v1/auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "message": "Successfully logged out",
  "detail": "Your refresh token has been invalidated"
}
```

## User Profile Management

### Get Current User Profile
```http
GET /api/v1/users/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "id": 1,
  "email": "john@example.com",
  "full_name": "John Doe",
  "phone_number": "+2348012345678",
  "role": "customer",
  "city": "Lagos",
  "is_active": true,
  "email_confirmed": true,
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-15T14:20:00Z"
}
```

### Update Profile
```http
PATCH /api/v1/users/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "full_name": "John Updated Doe",
  "city": "Abuja",
  "phone_number": "+2348098765432"
}
```

### Deactivate Account
```http
DELETE /api/v1/users/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Activation Token Management

### Resend Activation Token
```http
POST /api/v1/auth/resend-activation?email=john@example.com
```

**Response:**
```json
{
  "message": "Activation email sent",
  "detail": "Please check your email for the new activation link"
}
```

## Security Features

### Password Hashing
- Uses bcrypt with automatic salt generation
- Passwords never stored in plain text
- Constant-time comparison for verification

### JWT Tokens
- HS256 algorithm (configurable)
- Tokens include type claim ("access" or "refresh")
- Issued at (iat) and expiration (exp) timestamps
- Subject (sub) contains user email
- Role included in access token payload

### Token Validation
- Signature verification
- Expiration checking
- Type verification (access vs refresh)
- Database lookup for user existence
- Active status verification
- Refresh token matching (stored vs provided)

### Activation Tokens
- Cryptographically secure random generation (32 bytes URL-safe)
- 7-day expiration
- Single-use (cleared after activation)
- Indexed for fast lookup

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

**Causes:**
- Invalid or expired access token
- Invalid refresh token
- User not found

### 403 Forbidden
```json
{
  "detail": "Account not activated. Please activate your account first."
}
```

**Causes:**
- User account not activated (`is_active=false`)
- Deactivated account

### 400 Bad Request
```json
{
  "detail": "Invalid activation token"
}
```

**Causes:**
- Activation token mismatch
- Expired activation token
- Account already activated

## Configuration

Environment variables (`.env` file):

```env
# JWT Configuration
SECRET_KEY=your-secret-key-change-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

**Important:**
- Generate a strong SECRET_KEY for production (minimum 32 characters)
- Use `openssl rand -hex 32` to generate a secure key
- Never commit the production SECRET_KEY to version control

## Swagger UI Usage

1. Navigate to `/docs`
2. Click the "Authorize" button (lock icon)
3. Select "HTTPBearer"
4. Enter your access token (without "Bearer " prefix)
5. Click "Authorize"
6. All subsequent requests will include the token automatically

**Token Persistence:**
- Swagger UI persists authorization between page refreshes
- Logout clears the token from the UI

## Database Schema

### Authentication Fields (added to `early_access_signups` table):

```sql
-- Authentication
password_hash VARCHAR(255) NULL  -- Bcrypt hashed password
is_active BOOLEAN DEFAULT FALSE  -- Account activation status
activation_token VARCHAR(255) NULL  -- One-time activation token
activation_token_expiry TIMESTAMP NULL  -- Token expiration
refresh_token TEXT NULL  -- Current valid refresh token
last_login TIMESTAMP NULL  -- Last successful login

-- Indexes
CREATE INDEX idx_activation_token ON early_access_signups(activation_token);
```

## API Endpoints Summary

### Authentication (`/api/v1/auth`)
- `POST /login` - User login
- `POST /logout` - Invalidate refresh token
- `POST /refresh` - Get new access token
- `POST /activate` - Activate account with token
- `POST /resend-activation` - Request new activation token

### Users (`/api/v1/users`)
- `GET /me` - Get current user profile
- `PATCH /me` - Update profile
- `DELETE /me` - Deactivate account

### Admin (`/api/v1/admin`)
- All endpoints support HTTP Basic Auth (legacy)
- Can be migrated to JWT bearer authentication

## Testing with cURL

### Signup
```bash
curl -X POST http://localhost:8000/api/v1/signup \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test User",
    "email": "test@example.com",
    "phone_number": "8012345678",
    "role": "customer",
    "city": "Lagos"
  }'
```

### Activate (with token from email/database)
```bash
curl -X POST http://localhost:8000/api/v1/auth/activate \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "activation_token": "your-activation-token",
    "password": "SecurePass123"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123"
  }'
```

### Get Profile
```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Next Steps

1. **Email Integration**: Implement activation email sending with actual SMTP
2. **Password Reset**: Add forgot password / reset password flow
3. **Admin JWT**: Migrate admin endpoints to JWT bearer authentication
4. **Rate Limiting**: Add rate limiting for login attempts
5. **Email Verification**: Separate email confirmation from account activation
6. **Two-Factor Authentication**: Add optional 2FA support
7. **Session Management**: Track active sessions per user
8. **OAuth Integration**: Add social login (Google, Facebook, etc.)
