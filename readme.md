# Chat Application with Message Read Status

A real-time chat application built with Flask and JavaScript that supports direct messaging, group conversations, and message read receipts.

## Project Overview

This project implements a fully functional chat application that allows multiple users to communicate in both direct and group conversations, with real-time tracking of message read status.

## Features

### Core Features (Assignment Requirements)
- **User Management**: 6 pre-seeded users with profile avatars
- **Conversations**: Support for direct (1-on-1) and group conversations
- **Message Sending**: Real-time text messaging with persistence
- **Read Status Tracking**: Messages marked as read/unread with visual indicators
- **Unread Message Count**: Badge displays on each conversation
- **Auto-mark as Read**: Messages automatically marked read when conversation is opened

### Bonus Features Implemented
- **Multi-user Support**: 6 users instead of minimum 2
- **Group Conversations**: Support for group chats with multiple participants
- **Real-time Updates**: WebSocket integration using Flask-SocketIO
- **Login System**: Secure login page with user selection and password
- **Beautiful UI**: Modern, responsive design with smooth animations
- **Session Management**: Persistent login with logout functionality

## Database Design

### Design Choice: Option C - Message Read Receipts Table

**Why Option C?**

Option C was chosen for the following reasons:

1. **Scalability for Group Chats**: Multiple users can read the same message independently
2. **Detailed Tracking**: Can track exactly when each user read each message
3. **Future-proof**: Easy to add features like "read by X people" or read receipts list
4. **Clean Separation**: Messages table stays simple and focused

### Database Schema
```sql
-- Users
users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    avatar TEXT
)

-- Conversations (Direct + Groups)
conversations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT CHECK(type IN ('direct', 'group')),
    created_at DATETIME
)

-- Conversation Members (Multi-user support)
conversation_members (
    conversation_id TEXT,
    user_id INTEGER,
    joined_at DATETIME,
    PRIMARY KEY (conversation_id, user_id),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)

-- Messages
messages (
    id INTEGER PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    sender_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
)

-- Message Read Receipts (Option C Implementation)
message_reads (
    message_id INTEGER,
    user_id INTEGER,
    read_at DATETIME,
    PRIMARY KEY (message_id, user_id),
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)
```

### Key Design Features

- **Foreign Key Constraints with CASCADE**: Automatic cleanup of orphaned records
- **Composite Primary Keys**: Prevents duplicate entries efficiently
- **CHECK Constraints**: Ensures data integrity at database level
- **Performance Indexes**: Optimized queries on frequently accessed columns

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- SQLite3
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

1. **Clone or download the repository**
```bash
   cd path/to/project
```

2. **Install required Python packages**
```bash
   pip install flask flask-cors flask-socketio python-socketio
```

3. **Initialize the database**
   
   The database will be created automatically when you run the app, or you can create it manually:
```bash
   sqlite3 chat.db < chat.db.sql
```

4. **Start the backend server**
```bash
   python3 app.py
```
   
   You should see:
```
   Database initialized with 6 users + groups!
   Starting Chat App on http://localhost:5000
```

5. **Open the application**
   
   Open `login.html` in your web browser, or use a local HTTP server:
```bash
   python3 -m http.server 8000
   # Then navigate to: http://localhost:8000/login.html
```

## Project Structure
```
chat-application/
├── app.py              # Flask backend with API endpoints and WebSocket
├── chat.db.sql         # Database schema and seed data
├─- UI
    ├── login.html          # Login page with user selection
    ├──index.html          # Main chat interface
├── chat.db             # SQLite database (auto-generated)
└── README.md           # This file
```

## API Endpoints

### 1. List Conversations
```http
GET /conversations?user_id={id}
```
Returns all conversations for a user with unread message counts.

**Response:**
```json
[
  {
    "id": "conv1",
    "name": "Dhruv",
    "type": "direct",
    "unread_count": 3,
    "member_count": 2
  }
]
```

### 2. Get Messages
```http
GET /conversations/{conv_id}/messages?user_id={id}
```
Fetches all messages in a conversation and auto-marks unread messages as read.

**Response:**
```json
[
  {
    "id": 1,
    "conversation_id": "conv1",
    "sender_id": 2,
    "sender_name": "Dhruv",
    "content": "Hello!",
    "created_at": "2026-01-15 10:30:00",
    "is_read": 1
  }
]
```

### 3. Send Message
```http
POST /messages
Content-Type: application/json

{
  "conversation_id": "conv1",
  "sender_id": 1,
  "content": "Hello there!"
}
```

**Response:**
```json
{
  "id": 42,
  "success": true,
  "message": "Message sent!"
}
```

### 4. Mark Messages as Read
```http
POST /conversations/{conv_id}/read
Content-Type: application/json

{
  "user_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "marked_count": 5
}
```

### 5. Get User Info
```http
GET /users/{user_id}
```

### 6. Get Conversation Members
```http
GET /conversations/{conv_id}/members
```

### 7. Health Check
```http
GET /
```

## WebSocket Events

### Client → Server

**`authenticate`**: Join all user's conversations
```javascript
socket.emit('authenticate', { user_id: 1 });
```

**`message`**: Send a new message
```javascript
socket.emit('message', {
  conversation_id: 'conv1',
  sender_id: 1,
  content: 'Hello!'
});
```

**`join_conversation`**: Join a specific conversation room
```javascript
socket.emit('join_conversation', {
  conversation_id: 'conv1',
  user_id: 1
});
```

### Server → Client

**`new_message`**: Receive new message in real-time
```javascript
socket.on('new_message', (message) => {
  // Handle new message
});
```

**`authenticated`**: Confirmation of successful authentication

**`joined`**: Confirmation of joining a conversation room

## 👥 Pre-seeded Users

| ID | Name    | Emoji | Login Password |
|----|---------|-------|----------------|
| 1  | Vipin   | 👦🏻   | Any password   |
| 2  | Dhruv   | 🌚    | Any password   |
| 3  | Vihaan  | 🤓    | Any password   |
| 4  | Prince  | 👶🏻   | Any password   |
| 5  | Mohit   | 🗣️    | Any password   |
| 6  | Vaibhav | 🦹🏻‍♂️ | Any password   |

**Note:** Password validation is for demonstration purposes only. Any password will work.

## How Read Status Works

### Option C Implementation Logic

1. **Message is Unread**: If no row exists in `message_reads` for (message_id, user_id)
2. **Marking as Read**: Insert row into `message_reads` with current timestamp
3. **Auto-mark on Open**: When user opens conversation, all unread messages are marked read
4. **Unread Count Query**: 
```sql
   SELECT COUNT(*) FROM messages m
   LEFT JOIN message_reads mr ON m.id = mr.message_id AND mr.user_id = ?
   WHERE mr.message_id IS NULL AND m.sender_id != ?
```

### Visual Indicators

- ✓ (Single check) = Message sent
- ✓✓ (Double check, green) = Message read by recipient
- 🔴 Red badge = Unread message count on conversation

## UI Features

- **Modern Gradient Design**: Purple gradient background with glass-morphism effects
- **Responsive Layout**: Adapts to different screen sizes
- **Smooth Animations**: Slide-in animations for messages
- **Active Conversation Highlighting**: Clear visual feedback
- **Loading States**: Visual feedback during async operations
- **Error Handling**: User-friendly error messages with retry options

## Edge Cases Handled

1. **Empty Message Validation**: Cannot send empty messages
2. **Authorization Checks**: Users can only access conversations they're members of
3. **Duplicate Read Receipts**: `INSERT OR IGNORE` prevents duplicates
4. **Missing User Data**: Fallback to "Unknown" for missing users
5. **Network Errors**: Graceful error messages with retry functionality
6. **Session Management**: Auto-redirect to login if not authenticated
7. **Concurrent Message Sending**: Disabled input during send operation

## Testing the Application

### Manual Testing Steps

1. **Test Login**:
   - Open login.html
   - Select a user
   - Enter any password
   - Verify redirect to chat

2. **Test Conversations**:
   - Verify conversation list loads
   - Check unread badges appear correctly
   - Click different conversations

3. **Test Messaging**:
   - Send messages in direct chat
   - Send messages in group chat
   - Verify messages appear immediately
   - Check read receipts (✓/✓✓)

4. **Test Read Status**:
   - Login as User A, send message to User B
   - Login as User B, open conversation
   - Verify message shows as read (✓✓) for User A
   - Verify unread badge disappears for User B

5. **Test Multi-User**:
   - Login as different users in separate windows
   - Send messages between them
   - Verify real-time updates work

## Known Limitations

- **No message editing or deletion**: Messages are immutable once sent
- **No file attachments**: Only text messages supported
- **No typing indicators**: Not implemented in current version
- **No message pagination**: Loads last 50 messages only
- **No proper authentication**: Password is for demo only, not validated

## Future Enhancements

- Real authentication with password hashing
- Message editing and deletion
- File and image attachments
- Online/offline status
- Message search functionality
- Push notifications
- Message pagination
- User profiles with avatars
- Emoji picker

### Bonus Features Implemented

- ✅ Multiple users (6 instead of 2)
- ✅ Group conversations
- ✅ Real-time updates (WebSocket)
- ✅ Professional UI with animations
- ✅ Login system
- ✅ Session management

## Technologies Used

**Backend:**
- Flask (Python web framework)
- Flask-CORS (Cross-origin resource sharing)
- Flask-SocketIO (WebSocket support)
- SQLite3 (Database)

**Frontend:**
- HTML5
- CSS3 (with animations and gradients)
- Vanilla JavaScript (ES6+)
- Socket.IO Client

## License

This project is created for educational purposes as part of an internship assignment.

## Author

Vipin Yadav

## 🙏 Acknowledgments

- Assignment provided by Giva Jewellery
- Built with Flask and Socket.IO
- Inspired by modern chat applications

---

**Note**: This is a demonstration project. For production use, implement proper authentication, input sanitization, rate limiting, and security measures.