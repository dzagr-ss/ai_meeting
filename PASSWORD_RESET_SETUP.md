# Password Reset Setup Guide

This guide explains how to set up and use the password reset functionality in the Meeting Transcription App.

## Features

- **Forgot Password**: Users can request a password reset by entering their email address
- **Email Confirmation**: A secure token is sent to the user's email address
- **Password Update**: Users can set a new password using the token from the email
- **Security**: Tokens expire after 1 hour and can only be used once

## Backend Setup

### 1. Environment Variables

Add the following environment variables to your `.env` file:

```bash
# Email Configuration (for password reset)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
```

### 2. Gmail App Password Setup

If using Gmail, you'll need to create an App Password:

1. Go to your Google Account settings
2. Navigate to Security → 2-Step Verification
3. At the bottom, select "App passwords"
4. Generate a new app password for "Mail"
5. Use this app password as `SMTP_PASSWORD` (not your regular Gmail password)

### 3. Database Migration

The password reset functionality requires a new database table. Run the migration:

```bash
cd backend
alembic upgrade head
```

## API Endpoints

### Request Password Reset
```
POST /password-reset/request
Content-Type: application/json

{
  "email": "user@example.com"
}
```

### Confirm Password Reset
```
POST /password-reset/confirm
Content-Type: application/json

{
  "token": "reset-token-from-email",
  "new_password": "NewPassword123"
}
```

## Frontend Routes

- `/forgot-password` - Request password reset form
- `/reset-password?token=<token>` - Set new password form

## Password Requirements

New passwords must meet the following criteria:
- At least 8 characters long
- Contains at least one uppercase letter
- Contains at least one lowercase letter
- Contains at least one number

## Security Features

1. **Token Expiration**: Reset tokens expire after 1 hour
2. **Single Use**: Tokens can only be used once
3. **Token Invalidation**: Creating a new reset request invalidates previous tokens
4. **Email Privacy**: The system doesn't reveal whether an email exists in the database
5. **Rate Limiting**: Password reset requests are rate-limited to prevent abuse

## Usage Flow

1. User clicks "Forgot Password?" on the login page
2. User enters their email address
3. System sends a reset email with a secure token
4. User clicks the link in the email
5. User is redirected to the reset password page
6. User enters and confirms their new password
7. System validates the token and updates the password
8. User is redirected to the login page

## Troubleshooting

### Email Not Sending
- Check SMTP credentials in environment variables
- Verify Gmail App Password is correct
- Check firewall/network settings
- Review backend logs for email service errors

### Token Invalid/Expired
- Tokens expire after 1 hour
- Tokens can only be used once
- Request a new password reset if needed

### Password Validation Errors
- Ensure password meets all requirements
- Check that password confirmation matches

## Testing

You can test the password reset functionality by:

1. Creating a test user account
2. Using the forgot password feature
3. Checking your email for the reset link
4. Following the reset process

Note: In development, you may want to check the backend logs for the reset token if email sending is not configured. 