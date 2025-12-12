# ReStockr API - Industry Standard Authentication

## Overview

ReStockr API now implements industry-standard authentication with:
- ✅ OAuth2 Password Flow (RFC 6749)
- ✅ Social Authentication (Google, Facebook, Apple)
- ✅ JWT Bearer Tokens
- ✅ Redis Token Blacklisting
- ✅ Secure Password Hashing (bcrypt)

## Authentication Methods

### 1. Email/Password Authentication

#### **Step 1: Sign Up**
```http
POST /api/v1/signup
Content-Type: application/json

{
  "full_name": "John Doe",
  "email": "john@example.com",
  "phone_number": "08012345678",
  "role": "customer",
  "city": "Lagos"
}
```

**Response:**
```json
{
  "id": 1,
  "full_name": "John Doe",
  "email": "john@example.com",
  "phone_number": "+2348012345678",
  "role": "customer",
  "city": "Lagos",
  "created_at": "2025-12-12T10:00:00Z",
  "email_confirmed": false
}
```

**Note:** No password required at signup. User receives activation email.

#### **Step 2: Activate Account (Set Password)**
```http
POST /api/v1/auth/activate
Content-Type: application/json

{
  "email": "john@example.com",
  "activation_token": "token-from-email",
  "password": "SecurePass123"
}
```

**Password Requirements:**
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit

#### **Step 3: Login (OAuth2 Compatible)**
```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=john@example.com&password=SecurePass123
```

**Or with cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john@example.com&password=SecurePass123"
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

### 2. Social Authentication (OAuth2)

**Supported Providers:**
- Google
- Facebook
- Apple

#### **Frontend Flow:**
1. User clicks "Sign in with Google/Facebook/Apple"
2. Frontend initiates OAuth flow with provider
3. Provider redirects back with access token
4. Frontend sends token to backend

#### **Backend Endpoint:**
```http
POST /api/v1/auth/social/signup
Content-Type: application/json

{
  "provider": "google",
  "access_token": "ya29.a0AfH6SMBx...",
  "email": "john@gmail.com",
  "full_name": "John Doe",
  "provider_user_id": "102345678901234567890",
  "role": "customer",
  "city": "Lagos",
  "phone_number": "08012345678"
}
```

**Provider Values:**
- `"google"` - Google OAuth
- `"facebook"` - Facebook Login
- `"apple"` - Sign in with Apple

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Benefits:**
- ✅ Auto-activated (no email verification needed)
- ✅ Email pre-verified by provider
- ✅ Existing users automatically logged in
- ✅ No password required

## Using Access Tokens

All protected endpoints require the `Authorization` header:

```http
GET /api/v1/users/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Token Management

### Refresh Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Logout (Blacklist Token)
```http
POST /api/v1/auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**What happens:**
1. Access token added to Redis blacklist
2. Refresh token cleared from database
3. Token cannot be used again (instant revocation)

## Frontend Integration Examples

### React/Next.js with Google OAuth

```typescript
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';
import { jwtDecode } from 'jwt-decode';

function LoginPage() {
  const handleGoogleSuccess = async (credentialResponse) => {
    const decoded = jwtDecode(credentialResponse.credential);
    
    // Send to backend
    const response = await fetch('/api/v1/auth/social/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider: 'google',
        access_token: credentialResponse.credential,
        email: decoded.email,
        full_name: decoded.name,
        provider_user_id: decoded.sub,
        role: 'customer',
        city: 'Lagos'
      })
    });
    
    const data = await response.json();
    // Store tokens
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
  };

  return (
    <GoogleLogin
      onSuccess={handleGoogleSuccess}
      onError={() => console.log('Login Failed')}
    />
  );
}
```

### Facebook Login

```typescript
import FacebookLogin from '@greatsumini/react-facebook-login';

function LoginPage() {
  const handleFacebookSuccess = async (response) => {
    const apiResponse = await fetch('/api/v1/auth/social/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider: 'facebook',
        access_token: response.accessToken,
        email: response.email,
        full_name: response.name,
        provider_user_id: response.userID,
        role: 'customer',
        city: 'Lagos'
      })
    });
    
    const data = await apiResponse.json();
    // Store tokens
    localStorage.setItem('access_token', data.access_token);
  };

  return (
    <FacebookLogin
      appId="YOUR_FB_APP_ID"
      onSuccess={handleFacebookSuccess}
      onFail={(error) => console.log('Login Failed!', error)}
    />
  );
}
```

### Apple Sign In

```typescript
import AppleLogin from 'react-apple-login';

function LoginPage() {
  const handleAppleSuccess = async (response) => {
    const apiResponse = await fetch('/api/v1/auth/social/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider: 'apple',
        access_token: response.authorization.id_token,
        email: response.user?.email || 'unknown@apple.com',
        full_name: response.user?.name?.firstName || 'Apple User',
        provider_user_id: response.authorization.code,
        role: 'customer',
        city: 'Lagos'
      })
    });
    
    const data = await apiResponse.json();
    localStorage.setItem('access_token', data.access_token);
  };

  return (
    <AppleLogin
      clientId="YOUR_APPLE_CLIENT_ID"
      redirectURI="https://your-app.com/callback"
      responseType="code"
      responseMode="form_post"
      callback={handleAppleSuccess}
    />
  );
}
```

## Database Schema

### New Columns Added:
```sql
-- Social authentication
auth_provider VARCHAR(50) NULL  -- 'google', 'facebook', 'apple'
provider_user_id VARCHAR(255) NULL  -- Unique ID from provider

-- Indexes
CREATE INDEX idx_provider_user_id ON early_access_signups(provider_user_id);
```

### User Model Fields:
- `email` - User email (unique)
- `password` - Hashed password (NULL for social users)
- `full_name` - Display name
- `phone_number` - Contact number
- `role` - customer/vendor/rider
- `is_active` - Account activated
- `auth_provider` - OAuth provider or NULL
- `provider_user_id` - Provider's user ID
- `refresh_token` - Current refresh token
- `last_login` - Last login timestamp

## Security Features

### Password Security
- ✅ bcrypt hashing with automatic salt
- ✅ Minimum 8 characters
- ✅ Complexity requirements enforced
- ✅ Never stored or transmitted in plaintext

### Token Security
- ✅ JWT with HS256 signing
- ✅ Short-lived access tokens (30 min)
- ✅ Long-lived refresh tokens (7 days)
- ✅ Redis blacklisting for instant revocation
- ✅ Automatic expiry cleanup

### OAuth Security
- ✅ Provider-verified emails
- ✅ Secure provider_user_id storage
- ✅ Auto-activation for social users
- ✅ Duplicate prevention by email/provider_id

## API Endpoints Summary

### Public Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/signup` | Create account (no password) |
| POST | `/api/v1/auth/activate` | Set password & activate |
| POST | `/api/v1/auth/login` | Email/password login (OAuth2) |
| POST | `/api/v1/auth/social/signup` | Social OAuth signup/login |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/resend-activation` | Resend activation email |

### Protected Endpoints (Require Bearer Token)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/users/me` | Get user profile |
| PATCH | `/api/v1/users/me` | Update profile |
| DELETE | `/api/v1/users/me` | Deactivate account |
| POST | `/api/v1/auth/logout` | Logout & blacklist token |

## Testing with Swagger UI

1. Go to `/docs`
2. For OAuth2 password flow:
   - Click "Authorize"
   - Select "OAuth2PasswordBearer"
   - Use "Token URL": `/api/v1/auth/login`
   - Enter username (email) and password
3. For Bearer token:
   - Click "Authorize"
   - Enter access token
   - All requests automatically authenticated

## Environment Variables

```env
# JWT Settings
SECRET_KEY=your-secret-key-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis (Token Blacklisting)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# OAuth Provider Keys (Frontend)
# Google: Configure at https://console.cloud.google.com
# Facebook: Configure at https://developers.facebook.com
# Apple: Configure at https://developer.apple.com
```

## Production Deployment

### Redis Setup
```bash
# Install Redis
brew install redis  # macOS
apt-get install redis-server  # Ubuntu

# Start Redis
redis-server

# Or with Docker
docker run -d -p 6379:6379 redis:latest
```

### Security Checklist
- [ ] Strong SECRET_KEY (32+ chars, random)
- [ ] Enable HTTPS only
- [ ] Set CORS_ORIGINS to production domains
- [ ] Configure Redis password
- [ ] Set up Redis persistence (AOF/RDB)
- [ ] Implement rate limiting
- [ ] Enable monitoring/alerting
- [ ] Regular security audits
- [ ] Rotate SECRET_KEY periodically

## Error Handling

### Common Errors

**401 Unauthorized:**
```json
{"detail": "Incorrect email or password"}
```

**403 Forbidden:**
```json
{"detail": "Account not activated. Please check your email for activation instructions."}
```

**400 Bad Request:**
```json
{"detail": "Password must contain at least one uppercase letter"}
```

## Migration from Old System

If upgrading from previous version:

1. Run migrations:
```bash
python migrate_social_auth.py
```

2. Update frontend to use:
   - `OAuth2PasswordRequestForm` for login
   - Social signup endpoint for OAuth
   - Bearer token for all protected routes

3. Users with existing passwords: No action needed
4. New social users: Auto-activated, no password required

## Benefits Over Previous System

✅ **Industry Standard**: OAuth2 password flow (RFC 6749 compliant)  
✅ **Social Login**: Seamless Google/Facebook/Apple integration  
✅ **Better UX**: No password required for social signup  
✅ **More Secure**: Redis blacklisting, instant token revocation  
✅ **Scalable**: Works with multiple server instances  
✅ **Auto-Activation**: Social users ready immediately  
✅ **Unified**: Single endpoint for all social providers
