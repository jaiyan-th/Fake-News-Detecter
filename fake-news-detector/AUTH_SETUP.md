# Authentication System Setup Guide

## Quick Start

1. **Install dependencies:**
```bash
cd fake-news-detector
pip install -r requirements.txt
```

2. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Generate secret key:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
# Copy output to SECRET_KEY in .env
```

4. **Start the server:**
```bash
python serve_frontend.py
```

## Email Configuration (Gmail)

To send welcome and login notification emails:

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Copy the 16-character password
3. **Update .env:**
```bash
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
```

## Google OAuth Configuration

To enable real Google Sign-in:

1. **Create Google Cloud Project:**
   - Go to: https://console.cloud.google.com/
   - Create new project or select existing

2. **Enable Google+ API:**
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google+ API" and enable it

3. **Create OAuth Credentials:**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: "Web application"
   - Authorized redirect URIs: `http://localhost:5000/api/auth/google/callback`
   - Copy Client ID and Client Secret

4. **Update .env:**
```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/api/auth/google/callback
```

## Testing Without Email/OAuth

The system works without email and OAuth configuration:
- Email notifications will be skipped (logged only)
- Google Sign-in button will show error if clicked
- Regular email/password registration and login work fully

## Features

- Real user registration with password validation
- Secure password hashing with bcrypt
- Email/password login
- Google OAuth sign-in
- Welcome emails on registration
- Login notification emails
- Session management with cookies
- Account locking after 5 failed login attempts
- Rate limiting on auth endpoints

## API Endpoints

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login with email/password
- `POST /api/auth/logout` - Logout current user
- `GET /api/auth/me` - Get current user info
- `GET /api/auth/google` - Initiate Google OAuth
- `GET /api/auth/google/callback` - OAuth callback

## Security Features

- Passwords hashed with bcrypt (work factor 12)
- HttpOnly session cookies
- CSRF protection on OAuth
- Rate limiting (5 login attempts per 15 minutes)
- Account locking after failed attempts
- Generic error messages (don't reveal if email exists)
- All authentication events logged
