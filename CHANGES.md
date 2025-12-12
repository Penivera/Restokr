# Authentication System Updates

## Changes Made

### 1. **Renamed `password_hash` to `password`**
   - Database column renamed via migration
   - Model updated in `app/models/signup.py`
   - All references updated in auth endpoints

### 2. **Redis Integration for Token Blacklisting**
   - Added Redis configuration to `app/config.py`:
     - `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD`
   - Created `app/core/redis.py` with:
     - `init_redis()` - Initialize connection
     - `close_redis()` - Clean shutdown
     - `blacklist_token(token, expires_in)` - Blacklist access tokens
     - `is_token_blacklisted(token)` - Check if token is blacklisted
   - Updated `app/main.py` to initialize/close Redis on startup/shutdown
   - Updated `app/api/deps.py` to check token blacklist before authentication
   - Updated logout endpoint to blacklist access tokens

### 3. **Updated Project Branding**
   - Changed from "ReStockr Early Access API" to "ReStockr API"
   - Updated description to remove "Early Access" references
   - This is now the main platform signup, not just early access

### 4. **Fixed Phone Number Column Size**
   - Increased from `VARCHAR(20)` to `VARCHAR(50)`
   - Accommodates formatted phone numbers

## Database Migrations Run

1. ✅ `migrate_auth_columns.py` - Added authentication columns
2. ✅ `migrate_phone_column.py` - Increased phone_number size
3. ✅ `migrate_rename_password.py` - Renamed password_hash to password

## New Dependencies

- `redis` - For token blacklisting and caching

## Configuration Updates

### `.env` file (add these):
```env
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

## How Token Blacklisting Works

1. **Login**: User receives access_token (30 min) + refresh_token (7 days)
2. **Access Protected Endpoints**: 
   - Token checked against Redis blacklist
   - If blacklisted → 401 Unauthorized
   - If valid → Proceed
3. **Logout**:
   - Access token added to Redis with TTL = remaining token lifetime
   - Refresh token cleared from database
   - Token cannot be used again
4. **Token Expiry**:
   - Blacklisted tokens automatically removed from Redis when they expire
   - No manual cleanup needed

## Redis Setup

### Install Redis (if not installed):

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

**Docker:**
```bash
docker run -d -p 6379:6379 redis:latest
```

### Verify Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

## API Changes

### Logout Endpoint Updated
**Before:**
```python
POST /api/v1/auth/logout
# Only cleared refresh_token in database
```

**After:**
```python
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
# Now:
# 1. Blacklists the access token in Redis
# 2. Clears refresh_token in database
```

### Token Validation Enhanced
**Before:**
```python
# Only checked token signature and expiry
```

**After:**
```python
# Now checks:
# 1. Token signature (JWT validation)
# 2. Token expiry
# 3. Token type (access vs refresh)
# 4. Token blacklist (Redis)
# 5. User exists and is active
```

## Benefits of Redis Blacklisting

1. **Immediate Revocation**: Tokens invalidated instantly on logout
2. **Automatic Cleanup**: Expired tokens auto-removed (TTL)
3. **Scalable**: Works across multiple server instances
4. **Fast**: Redis lookup is O(1)
5. **Memory Efficient**: Only stores active blacklisted tokens

## Graceful Degradation

If Redis is unavailable:
- Application still starts (warning logged)
- Token blacklisting disabled
- Authentication still works
- Logout only clears refresh_token (access tokens remain valid until expiry)

## Testing

1. **Start Redis:**
   ```bash
   redis-cli ping
   ```

2. **Start the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

3. **Test authentication flow:**
   ```bash
   # 1. Signup
   POST /api/v1/signup
   
   # 2. Activate account
   POST /api/v1/auth/activate
   
   # 3. Login (get tokens)
   POST /api/v1/auth/login
   
   # 4. Use protected endpoint
   GET /api/v1/users/me (with Bearer token)
   
   # 5. Logout (blacklist token)
   POST /api/v1/auth/logout (with Bearer token)
   
   # 6. Try using same token (should fail)
   GET /api/v1/users/me (with same Bearer token)
   # Returns: 401 Unauthorized - "Token has been revoked"
   ```

## Security Improvements

- ✅ Tokens can be revoked immediately (not just on expiry)
- ✅ Stolen tokens can be blacklisted
- ✅ Multiple device logout support
- ✅ Distributed session management
- ✅ Audit trail (Redis logs token blacklisting)

## Production Checklist

- [ ] Install and configure Redis
- [ ] Set `REDIS_PASSWORD` for production Redis instance
- [ ] Configure Redis persistence (AOF/RDB)
- [ ] Set up Redis monitoring
- [ ] Configure Redis maxmemory policy
- [ ] Enable Redis authentication
- [ ] Set up Redis replication (if multi-server)
