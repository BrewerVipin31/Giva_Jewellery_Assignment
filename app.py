import os
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime
import uuid
from flask_socketio import SocketIO, emit, join_room, leave_room



app = Flask(__name__)
CORS(app)
DB = 'chat.db'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def init_db():
    """Initialize database from SQL file if it doesn't exist"""
    if not os.path.exists(DB):
        print("Database not found! Creating new database...")
        
        # Check if SQL file exists
        if not os.path.exists('chat.db.sql'):
            print("Error: chat.db.sql file not found!")
            print("Please ensure chat.db.sql is in the same directory as app.py")
            exit(1)
        
        try:
            # Read and execute SQL file
            with open('chat.db.sql', 'r') as f:
                sql_script = f.read()
            
            conn = sqlite3.connect(DB)
            conn.executescript(sql_script)
            conn.close()
            
            print("Database created successfully!")
        except Exception as e:
            print(f"Error creating database: {e}")
            print("Please check that chat.db.sql is valid SQL")
            exit(1)
    else:
        print("Database already exists!")


# API 1: List conversations with unread counts
@app.route('/conversations', methods=['GET'])
def list_conversations():
    try:
        user_id = request.args.get('user_id')
        if not user_id or not user_id.isdigit():
            return jsonify({'error': 'Invalid or missing user_id'}), 400
        user_id = int(user_id)
        conn = get_db()
        
        # Get all conversations for this user
        cursor = conn.execute('''
            SELECT DISTINCT c.id, c.name, c.type,
                   COALESCE(unread.unread_count, 0) as unread_count,
                   (SELECT COUNT(*) FROM conversation_members cm2 
                    WHERE cm2.conversation_id = c.id) as member_count
            FROM conversations c
            JOIN conversation_members cm ON c.id = cm.conversation_id
            LEFT JOIN (
                SELECT m.conversation_id, COUNT(*) as unread_count
                FROM messages m
                LEFT JOIN message_reads mr ON m.id = mr.message_id AND mr.user_id = ?
                WHERE mr.message_id IS NULL AND m.sender_id != ?
                GROUP BY m.conversation_id
            ) unread ON c.id = unread.conversation_id
            WHERE cm.user_id = ?
            ORDER BY unread.unread_count DESC, c.created_at DESC
        ''', (user_id, user_id, user_id))
        
        convs = []
        for row in cursor.fetchall():
            conv = dict(row)
            
            # For direct chats, get the other user's name
            if conv['type'] == 'direct':
                other_user = conn.execute('''
                    SELECT u.name FROM users u
                    JOIN conversation_members cm ON u.id = cm.user_id
                    WHERE cm.conversation_id = ? 
                    AND cm.user_id != ?
                    LIMIT 1
                ''', (conv['id'], user_id)).fetchone()
                
                if other_user:
                    conv['name'] = other_user['name']
            
            convs.append(conv)
        
        conn.close()
        return jsonify(convs)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    
# API 2: Get messages (auto-mark read)
@app.route('/conversations/<conv_id>/messages', methods=['GET'])
def get_messages(conv_id):
    user_id = request.args.get('user_id')
    if not user_id or not user_id.isdigit():
        return jsonify({'error': 'Invalid or missing user_id'}), 400
    user_id = int(user_id)
    
    try:
        conn = get_db()
        
        # Verify membership
        member_check = conn.execute('''
            SELECT 1 FROM conversation_members 
            WHERE conversation_id = ? AND user_id = ?
        ''', (conv_id, user_id)).fetchone()
        
        if not member_check:
            conn.close()
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Auto-mark unread messages as read
        conn.execute('''
            INSERT OR IGNORE INTO message_reads (message_id, user_id)
            SELECT m.id, ? FROM messages m
            LEFT JOIN message_reads mr ON m.id = mr.message_id AND mr.user_id = ?
            WHERE m.conversation_id = ? AND mr.message_id IS NULL AND m.sender_id != ?
        ''', (user_id, user_id, conv_id, user_id))
        
        # Fetch messages with sender names
        cursor = conn.execute('''
            SELECT m.*, u.name as sender_name,
                   CASE WHEN mr.user_id IS NOT NULL THEN 1 ELSE 0 END as is_read
            FROM messages m 
            JOIN users u ON m.sender_id = u.id
            LEFT JOIN message_reads mr ON m.id = mr.message_id AND mr.user_id = ?
            WHERE m.conversation_id = ? 
            ORDER BY m.created_at ASC
            LIMIT 50
        ''', (user_id, conv_id))
        
        msgs = [dict(row) for row in cursor.fetchall()]
        conn.commit()
        conn.close()
        return jsonify(msgs)
        
    except sqlite3.Error as e:
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# API 3: Send message
@app.route('/messages', methods=['POST'])
def send_message():
    try:
        data = request.json
        if not data.get('content', '').strip():
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        conn = get_db()
        cursor = conn.execute(
            '''INSERT INTO messages (conversation_id, sender_id, content) 
               VALUES (?, ?, ?)''',
            (data['conversation_id'], data['sender_id'], data['content'])
        )
        
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'id': new_id, 
            'success': True,
            'message': 'Message sent!'
        }), 201
        
    except sqlite3.Error as e:
        return jsonify({'error': 'Database error occurred'}), 500
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# API 4: Mark messages as read
@app.route('/conversations/<conv_id>/read', methods=['POST'])
def mark_as_read(conv_id):
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400
        
        conn = get_db()
        
        # Verify membership
        member_check = conn.execute('''
            SELECT 1 FROM conversation_members 
            WHERE conversation_id = ? AND user_id = ?
        ''', (conv_id, user_id)).fetchone()
        
        if not member_check:
            conn.close()
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Mark all unread messages as read
        cursor = conn.execute('''
            INSERT OR IGNORE INTO message_reads (message_id, user_id)
            SELECT m.id, ? FROM messages m
            LEFT JOIN message_reads mr ON m.id = mr.message_id AND mr.user_id = ?
            WHERE m.conversation_id = ? AND mr.message_id IS NULL AND m.sender_id != ?
        ''', (user_id, user_id, conv_id, user_id))
        
        marked_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'marked_count': marked_count
        }), 200
        
    except sqlite3.Error as e:
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# API 5: Get user info
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        conn = get_db()
        cursor = conn.execute('SELECT id, name, avatar FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return jsonify(dict(user)) if user else (jsonify({'error': 'User not found'}), 404)
    except sqlite3.Error as e:
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# API 6: Get conversation members
@app.route('/conversations/<conv_id>/members', methods=['GET'])
def get_members(conv_id):
    try:
        conn = get_db()
        cursor = conn.execute('''
            SELECT u.id, u.name, u.avatar 
            FROM users u
            JOIN conversation_members cm ON u.id = cm.user_id
            WHERE cm.conversation_id = ?
        ''', (conv_id,))
        members = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(members)
    except sqlite3.Error as e:
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# Health check
@app.route('/', methods=['GET'])
def health():
    return jsonify({
        'status': 'Chat API running!',
        'features': ['Multi-user', 'Groups', 'Read receipts'],
        'database': 'Connected'
    })

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('authenticate')
def authenticate(data):
    """Join all user's conversations on authentication"""
    user_id = data.get('user_id')
    if not user_id:
        return
    
    try:
        conn = get_db()
        cursor = conn.execute('''
            SELECT conversation_id FROM conversation_members 
            WHERE user_id = ?
        ''', (user_id,))
        conversations = cursor.fetchall()
        conn.close()
        
        for conv in conversations:
            join_room(conv['conversation_id'])
        
        emit('authenticated', {'success': True})
    except Exception as e:
        print(f"Authentication error: {e}")
        emit('error', {'message': 'Authentication failed'})

@socketio.on('message')
def handle_message(data):
    try:
        if not data.get('content', '').strip():
            return {'success': False, 'error': 'Empty message'}
        
        conversation_id = data.get('conversation_id')
        sender_id = data.get('sender_id')
        
        if not conversation_id or not sender_id:
            return {'success': False, 'error': 'Missing fields'}
        
        conn = get_db()
        
        member_check = conn.execute('''
            SELECT 1 FROM conversation_members 
            WHERE conversation_id = ? AND user_id = ?
        ''', (conversation_id, sender_id)).fetchone()
        
        if not member_check:
            conn.close()
            return {'success': False, 'error': 'Unauthorized'}
        
        cursor = conn.execute(
            '''INSERT INTO messages (conversation_id, sender_id, content) 
               VALUES (?, ?, ?)''',
            (conversation_id, sender_id, data['content'])
        )
        new_id = cursor.lastrowid
        
        cursor = conn.execute('''
            SELECT m.*, u.name as sender_name
            FROM messages m 
            JOIN users u ON m.sender_id = u.id
            WHERE m.id = ?
        ''', (new_id,))
        message = dict(cursor.fetchone())
        conn.commit()
        conn.close()
        
        emit('new_message', message, room=conversation_id)
        
        return {'success': True, 'message_id': new_id}
        
    except Exception as e:
        print(f"SocketIO error: {e}")
        return {'success': False, 'error': 'Server error'}

@socketio.on('join_conversation')
def join_conversation(data):
    conversation_id = data.get('conversation_id')
    user_id = data.get('user_id')
    
    try:
        conn = get_db()
        member = conn.execute('''
            SELECT 1 FROM conversation_members 
            WHERE conversation_id = ? AND user_id = ?
        ''', (conversation_id, user_id)).fetchone()
        conn.close()
        
        if member:
            join_room(conversation_id)
            emit('joined', {'conversation_id': conversation_id})
        else:
            emit('error', {'message': 'Not authorized'})
    except Exception as e:
        print(f"Join error: {e}")
        emit('error', {'message': 'Failed to join conversation'})

@socketio.on('leave_conversation')
def leave_conversation(data):
    try:
        leave_room(data.get('conversation_id'))
    except Exception as e:
        print(f"Leave error: {e}")

if __name__ == '__main__':
    init_db()
    print("Starting Chat App on http://localhost:5000")
    print("Open UI to chat!")
    socketio.run(app, debug=True, port=5000)