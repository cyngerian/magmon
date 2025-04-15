# Admin Password Reset Implementation Plan

## Overview
Create an admin-only interface for managing user passwords, specifically designed for a small user base (6 users) where the admin knows all users personally.

## Database Changes

### User Model Additions
```sql
ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;
ALTER TABLE user ADD COLUMN temp_password_hash VARCHAR;
ALTER TABLE user ADD COLUMN must_change_password BOOLEAN DEFAULT FALSE;
ALTER TABLE user ADD COLUMN temp_password_expires_at TIMESTAMP;
```

## Backend Components

### New API Endpoints

1. **Admin Check Endpoint**
```python
GET /api/admin/check
Response: { "is_admin": boolean }
```

2. **List Users Endpoint**
```python
GET /api/admin/users
Response: [
    {
        "id": number,
        "username": string,
        "email": string,
        "avatar_url": string | null,
        "must_change_password": boolean,
        "last_login": string | null
    }
]
```

3. **Reset Password Endpoint**
```python
POST /api/admin/users/{userId}/reset-password
Response: {
    "temp_password": string,
    "expires_at": string
}
```

### Security Considerations

1. Admin Authentication:
   - Add `@require_admin` decorator for admin endpoints
   - Check `is_admin` flag in JWT claims
   - Require recent authentication for admin actions

2. Temporary Password System:
   - Generate secure random temporary passwords
   - Set 24-hour expiration
   - Force password change on next login
   - Store temporary password hash separately

3. Rate Limiting:
   - Limit reset attempts per admin per hour
   - Log all password reset actions

## Frontend Components

### New Admin Route
```typescript
/admin/users
```

### New Components

1. **AdminLayout.tsx**
   - Admin navigation
   - Admin-specific header
   - Security checks

2. **UserManagementPage.tsx**
```typescript
interface User {
    id: number;
    username: string;
    email: string;
    avatar_url: string | null;
    must_change_password: boolean;
    last_login: string | null;
}

interface ResetResponse {
    temp_password: string;
    expires_at: string;
}
```

### UI Design

1. **Users List View**
```
+------------------------------------------+
|                 Users                     |
+------------------------------------------+
| [Search/Filter]                          |
|                                          |
| +----------------+----------+-----------+ |
| | User           | Status   | Actions   | |
| +----------------+----------+-----------+ |
| | 🎭 Username    | Active   | [Reset]   | |
| | 📧 Email       |          |           | |
| +----------------+----------+-----------+ |
| | 🎭 Username    | Pending  | [Reset]   | |
| | 📧 Email       | Reset    |           | |
| +----------------+----------+-----------+ |
```

2. **Reset Password Modal**
```
+------------------------------------------+
|          Reset Password for User          |
+------------------------------------------+
| Are you sure you want to reset the       |
| password for [Username]?                  |
|                                          |
| This will:                               |
| • Generate a temporary password          |
| • Force a password change on next login  |
| • Expire in 24 hours                     |
|                                          |
| [Cancel]              [Reset Password]   |
+------------------------------------------+
```

3. **Temporary Password Display**
```
+------------------------------------------+
|        Temporary Password Created         |
+------------------------------------------+
| Password: XXXX-XXXX-XXXX                 |
| Expires: [Date/Time]                     |
|                                          |
| [Copy to Clipboard]    [Close]           |
+------------------------------------------+
```

## Implementation Steps

1. **Backend Setup**
   - Add database migrations
   - Create admin decorators
   - Implement API endpoints
   - Add security middleware

2. **Frontend Setup**
   - Create admin routes
   - Build user management components
   - Implement admin checks
   - Add password reset flow

3. **Testing**
   - Admin authentication
   - Password reset flow
   - Temporary password login
   - Force password change
   - Expiration handling

4. **Security Review**
   - Audit admin routes
   - Review JWT handling
   - Check rate limiting
   - Verify password hashing

## Usage Flow

1. Admin logs in and navigates to /admin/users
2. Selects user needing password reset
3. Confirms reset action
4. Receives temporary password
5. Communicates password to user securely
6. User logs in with temporary password
7. User is forced to create new password
8. New password is saved, temporary password is cleared

## Error Handling

1. Invalid admin access attempts
2. Expired temporary passwords
3. Failed reset attempts
4. Network issues
5. Database errors

## Monitoring

1. Log all password resets
2. Track failed admin access attempts
3. Monitor temporary password usage
4. Alert on suspicious activity

This implementation provides a secure, straightforward way for you as the admin to help users who have forgotten their passwords, while maintaining security and usability appropriate for a small, known user base.