# Admin Panel Setup Instructions

## Overview
The admin panel allows authorized users to view statistics, monitor data, and manage the Virtual Patient Simulator system.

## Environment Setup

### 1. Add Admin Credentials to Environment Variables

Add the following environment variables to your backend environment file:

**For Development (Backend/api/.env or Backend/src/.env):**
```bash
# Admin Credentials
ADMIN_NAME=Your Admin Name
ADMIN_ID=admin123
```

**For Production (Railway or your hosting platform):**
Set these as environment variables in your hosting platform's settings.

### 2. Example Configuration

```bash
# Example admin credentials
ADMIN_NAME=John Doe
ADMIN_ID=admin2024

# Note: Name matching is case-insensitive, but ID matching is case-sensitive
```

## How It Works

### Admin Login Flow

1. User clicks the "Login" button in the top-right corner of the homepage
2. User enters their name and ID in the login modal
3. System checks credentials against environment variables:
   - If credentials match `ADMIN_NAME` and `ADMIN_ID`: User is granted admin access
   - If credentials don't match: User is logged in as a regular user (no admin access)
4. Login is recorded in the database `audit_log` table
5. If admin: User can access the "Admin Page" from the dropdown menu

### Database Tables Used

The admin panel queries the following tables:
- `users` - User information and statistics
- `sessions` - Session data and status
- `chat_messages` - Messages and token usage
- `session_reports` - Generated reports
- `audit_log` - Activity logs
- `cases` - Available cases

### API Endpoints

All admin endpoints are prefixed with `/api/admin`:

- **POST /api/admin/login** - Admin authentication
- **GET /api/admin/stats** - Dashboard statistics
- **GET /api/admin/audit-logs?limit=50** - Audit log entries
- **GET /api/admin/sessions?limit=50** - Session data
- **GET /api/admin/users?limit=50** - User data
- **GET /api/admin/messages?limit=50** - Chat messages

## Admin Panel Features

### 1. Dashboard Overview
Displays 12 key statistics:
- Total Users
- Active Sessions
- Completed Sessions
- Downloads
- Exam Mode Sessions
- Practice Mode Sessions
- Average Duration
- Max Duration
- Min Duration
- Total Messages
- Total Input Tokens
- Total Output Tokens

Plus recent activity and session statistics.

### 2. Query Editor
Simple SQL query interface (for future implementation of direct database queries).

### 3. Data Monitoring
Four tabs for viewing detailed data:
- **Audit Logs**: View all system activities
- **Sessions**: View all session details with download options
- **Users**: View user profiles and activity
- **Messages**: View chat message history

### 4. API Documentation
Link to access complete API documentation.

## Security Notes

⚠️ **Important Security Considerations:**

1. **Never commit credentials to version control**
   - Add `.env` files to `.gitignore`
   - Use different credentials for development and production

2. **Use strong admin credentials**
   - Choose a unique admin ID (not easily guessable)
   - Consider using UUID format for admin ID

3. **Environment variables should be secured**
   - Restrict access to environment configuration
   - Rotate credentials periodically

4. **Admin access is powerful**
   - Only grant admin credentials to trusted users
   - Monitor admin activity through audit logs

## Testing Admin Access

### Test as Regular User:
```
Name: Test User
ID: student001
Result: Normal user access (no admin dropdown)
```

### Test as Admin:
```
Name: [Your ADMIN_NAME from .env]
ID: [Your ADMIN_ID from .env]
Result: Admin access granted (Admin Page option appears in dropdown)
```

## Troubleshooting

### Issue: Login button doesn't work
- Check that the backend server is running
- Verify database connection is established
- Check browser console for errors

### Issue: Admin Page option doesn't appear
- Verify credentials exactly match environment variables
- Check that name matching is case-insensitive but ID is case-sensitive
- Verify environment variables are loaded (restart backend after adding them)

### Issue: Statistics not showing
- Verify database tables exist and contain data
- Check backend logs for SQL errors
- Ensure database connection pool is configured correctly

## Development

The admin system consists of:

### Frontend Files:
- `Frontend/src/components/modals/AdminLoginModal.js`
- `Frontend/src/pages/AdminDashboard.js`
- `Frontend/src/pages/AdminDashboard.css`
- `Frontend/src/pages/HomePage.js` (updated with login button)
- `Frontend/src/services/apiService.js` (admin API methods)

### Backend Files:
- `Backend/api/routers/admin.py` (admin endpoints)
- `Backend/api/app.py` (router registration)

## Next Steps

After setting up admin credentials:

1. Add the environment variables to your `.env` file
2. Restart your backend server
3. Test the login functionality
4. Verify admin access works correctly
5. Monitor the audit logs to track admin activities

For questions or issues, please refer to the main project documentation.
