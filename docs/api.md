# API Specification & Endpoints

## Base URL
/api/v1

## Endpoints

### Health
- GET /health - System health check, uptime, and status.

### Authentication
- POST /api/v1/auth/register - Register a new user account.
- POST /api/v1/auth/login - Authenticate user and issue tokens.
- POST /api/v1/auth/refresh-token - Refresh expired access token.
- POST /api/v1/auth/logout - Invalidate user session / token.

### Users
- GET /api/v1/users/me - Get current authenticated user profile.
- PATCH /api/v1/users/me - Update current user profile.
