# NGL Anonymous Messaging Frontend

A React.js-inspired frontend for the NGL (anonymous messaging) application that can be run as static HTML files.

## Features

- **Send Messages**: Send anonymous messages to any user by their user ID
- **Sign Up**: Create a new account to receive anonymous messages
- **Login & View Messages**: Login to view received messages with pagination
- **Server Status**: Real-time server status checking
- **Responsive Design**: Works on desktop and mobile devices

## Files Structure

```
react-frontend/
├── index.html          # Homepage with navigation
├── send.html           # Send anonymous messages
├── signup.html         # Create new account
├── login.html          # User login
├── inbox.html  # View received messages
└── README.md          # This file
```

## How to Use

### Method 1: Double-click to run
1. Simply double-click on any HTML file to open it in your default web browser
2. Start with `index.html` for the homepage

### Method 2: Run from file explorer
1. Navigate to the `react-frontend` folder
2. Right-click on `index.html` and select "Open with" → your preferred browser

### Method 3: Local web server (recommended)
For better compatibility with modern browsers, you can serve the files using a local web server:

```bash
# Using Python 3
python -m http.server 8000

# Using Node.js
npx serve .

# Using Live Server (VS Code extension)
# Right-click on index.html and select "Open with Live Server"
```

Then navigate to `http://localhost:8000` in your browser.

## Pages Overview

### 1. Homepage (`index.html`)
- Shows server status
- Navigation to all other pages
- Instructions on how the app works

### 2. Send Message (`send.html`)
- Enter recipient's user ID
- Real-time user validation
- Send anonymous messages
- Navigation to signup/login pages (as requested)

### 3. Sign Up (`signup.html`)
- Create new account
- Real-time user ID availability checking
- Password confirmation
- Secure account creation

### 4. Login (`login.html`)
- User authentication
- Automatic redirect to view messages
- Session management with localStorage

### 5. View Messages (`inbox.html`)
- View all received messages
- Pagination support
- Message timestamps
- Token refresh for expired sessions
- Logout functionality

## Technical Details

### Technologies Used
- **HTML5**: Structure and markup
- **CSS3**: Styling with gradients and animations
- **JavaScript (ES6+)**: Client-side functionality
- **Bootstrap 5**: Responsive UI framework
- **Font Awesome**: Icons
- **Fetch API**: HTTP requests to backend

### Backend Integration
The frontend communicates with the backend API at:
```
https://potro-backend-1.onrender.com
```

### API Endpoints Used
- `GET /` - Server status check
- `GET /sending/{user_id}` - Check if user exists
- `POST /sending/{user_id}?message={message}` - Send message
- `POST /authentication/signup` - Create account
- `POST /authentication/login` - User login
- `POST /authentication/refresh` - Refresh token
- `GET /viewmessages?page={page}&limit={limit}` - Get messages

### Local Storage
The app uses localStorage to persist:
- Access tokens
- Refresh tokens
- Token type
- Username

### Features Implemented
- ✅ Real-time server status checking
- ✅ User ID validation with live feedback
- ✅ Anonymous message sending
- ✅ Account creation with duplicate checking
- ✅ Secure login with token management
- ✅ Message viewing with pagination
- ✅ Token refresh for expired sessions
- ✅ Responsive design for all screen sizes
- ✅ Error handling and user feedback
- ✅ Navigation between pages
- ✅ Form validation and submission

### Browser Compatibility
- ✅ Chrome (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Edge
- ⚠️ Internet Explorer (limited support)

## Special Feature: Send Message Page Navigation

As specifically requested, the **Send Message page** includes navigation options to:
- **Sign Up page** - For users who don't have an account
- **Login page** - For existing users who want to view their messages

This makes it easy for users to access all functionality from the main send message interface.

## Security Features

- Input validation and sanitization
- XSS protection
- CORS handling
- Token-based authentication
- Automatic token refresh
- Secure password handling

## Troubleshooting

### Common Issues

1. **Server Offline**: Check your internet connection and server status
2. **CORS Errors**: Use a local web server instead of opening files directly
3. **Login Issues**: Clear localStorage and try again
4. **Messages Not Loading**: Check if you're logged in and token is valid

### Error Messages
The app provides clear error messages for:
- Network connectivity issues
- Invalid user credentials
- Server errors
- Token expiration
- Form validation errors

## Development Notes

- No build process required - pure HTML/CSS/JS
- Uses modern JavaScript features (ES6+)
- Responsive design with Bootstrap
- Clean, maintainable code structure
- Error handling and loading states
- Accessible UI components

## Future Enhancements

Potential improvements could include:
- Offline mode support
- Push notifications
- Message encryption
- File attachments
- User profiles
- Message reactions
- Dark mode theme
