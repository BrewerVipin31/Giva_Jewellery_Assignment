-- Run: sqlite3 chat.db < chat.db.sql

PRAGMA foreign_keys = ON;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    avatar TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT CHECK (type IN ('direct', 'group')) DEFAULT 'direct',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS conversation_members (
    conversation_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (conversation_id, user_id),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    sender_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS message_reads (
    message_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    read_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (message_id, user_id),
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation
    ON messages(conversation_id);

CREATE INDEX IF NOT EXISTS idx_messages_sender
    ON messages(sender_id);

CREATE INDEX IF NOT EXISTS idx_reads_user
    ON message_reads(user_id);

CREATE INDEX IF NOT EXISTS idx_reads_message
    ON message_reads(message_id);


-- SEED DATA: 5 users + groups
INSERT OR IGNORE INTO users (id, name) VALUES 
    (1, 'Vipin'), (2, 'Dhruv'), (3, 'Vihaan'), (4, 'Prince'), (5, 'Mohit'), (6, 'Vaibhav');

INSERT OR IGNORE INTO conversations (id, name, type) VALUES 
    ('conv1', 'Dhruv', 'direct'),
    ('conv2', 'Vihaan', 'direct'),
    ('conv3', 'Mohit', 'direct'),
    ('conv4', 'Vipin', 'direct'),
    ('group1', 'Only Friends', 'group'),
    ('group2', 'Project X', 'group');

INSERT OR IGNORE INTO conversation_members (conversation_id, user_id) VALUES
    ('conv1', 1), ('conv1', 2),
    ('conv2', 2), ('conv2', 3),
    ('conv3', 4), ('conv3', 5),
    ('conv4', 6), ('conv4', 1),
    ('group1', 1), ('group1', 2), ('group1', 3), ('group1', 4),('group1', 5),('group1', 6),
    ('group2', 2), ('group2', 3), ('group2', 5);
