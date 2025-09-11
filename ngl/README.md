# NGL Messaging API - PostgreSQL Upgrade

## Overview
This FastAPI application has been upgraded from SQLite to PostgreSQL hosted on Render cloud service.

## Database Configuration
The application now uses PostgreSQL hosted on Render with the following configuration:
- **Host**: dpg-d2u2top5pdvs73a2pc9g-a (Render PostgreSQL)
- **Port**: 5432
- **Database**: aaaa_x5td
- **Username**: aaaa_x5td_user
- **SSL**: Required (for remote Render database)

## Installation & Setup

### 1. Install Dependencies
```bash
"D:/Flask project/env/Scripts/python.exe" -m pip install -r requirements.txt
```

### 2. Environment Configuration
The database credentials are stored in the `.env` file. Make sure it contains:
```env
DATABASE_HOST=dpg-d2u2top5pdvs73a2pc9g-a
DATABASE_PORT=5432
DATABASE_NAME=aaaa_x5td
DATABASE_USER=aaaa_x5td_user
DATABASE_PASSWORD=sddyF001zkU890k9fKE7ERKDd0WqttHC
```

### 3. Database Migration
Run the migration script to create tables in PostgreSQL:
```bash
"D:/Flask project/env/Scripts/python.exe" migrate_to_postgres.py
```

### 4. Start the Application
```bash
"D:/Flask project/env/Scripts/python.exe" -m uvicorn main:app --reload
```

## Remote Database Considerations (Render)

Since the PostgreSQL database is hosted on Render (not locally), the configuration includes:

### SSL Requirements
- **SSL Mode**: `require` - Mandatory for Render PostgreSQL
- **Connection Security**: All connections are encrypted

### Connection Pooling
- **Pool Size**: 10 connections
- **Max Overflow**: 20 additional connections
- **Pool Pre-ping**: Validates connections before use
- **Pool Recycle**: Connections recycled every hour

### Network Considerations
- **Latency**: Expect slightly higher latency compared to local databases
- **Reliability**: Render provides high availability
- **IP Whitelisting**: May be required depending on Render configuration

## Key Changes Made

### Database Configuration (`database.py`)
- Switched from `sqlite+aiosqlite` to `postgresql+asyncpg`
- Added SSL requirement for Render PostgreSQL
- Configured connection pooling for remote database
- Added environment variable support with `python-dotenv`
- Fixed foreign key relationship (User.id is String, Message.user_id now also String)

### Dependencies (`requirements.txt`)
- Replaced `aiosqlite` with `asyncpg` for PostgreSQL support
- Added `python-dotenv` for environment variable management

### Security (`oAuthentication.py`)
- Updated to use environment variables for all configuration
- Made token expiration times configurable

### Data Models
- Fixed the foreign key relationship between User and Message tables
- User.id: String (primary key)
- Message.user_id: String (foreign key to users.id)

## API Endpoints

### Authentication
- `POST /authentication/signup` - Create new user
- `POST /authentication/login` - User login
- `POST /authentication/refresh` - Refresh JWT token

### Messaging
- `GET /sending/{user_id}` - Get user information
- `POST /sending/{user_id}` - Send message to user
- `GET /recieving/inbox` - Get user's messages (requires authentication)
- `GET /recieving/get_message/{id}` - Get specific message (requires authentication)

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    password VARCHAR NOT NULL
);
```

### Messages Table
```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL REFERENCES users(id),
    content VARCHAR NOT NULL,
    time VARCHAR NOT NULL
);
```

## Environment Variables
All sensitive configuration is now managed through environment variables:
- Database credentials
- JWT secret keys
- Token expiration times
- Algorithm settings

## Security Notes
- The `.env` file is excluded from version control for security
- JWT tokens use secure secret keys
- Password hashing uses bcrypt
- Database credentials are not hardcoded

## Troubleshooting

### Connection Issues
1. Verify the PostgreSQL server is accessible
2. Check network connectivity to the database host
3. Ensure credentials are correct in the `.env` file

### Migration Issues
1. Run the migration script: `python migrate_to_postgres.py`
2. Check the database logs for any errors
3. Verify the database user has proper permissions

### Import Issues
If you encounter relative import errors, ensure you're running the application from the correct directory and with the proper command structure.
