import sqlite3
from datetime import datetime

DB_PATH = "engagement.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_url TEXT UNIQUE,
            shortcode TEXT,
            username TEXT,
            caption TEXT,
            likes_count INTEGER,
            comments_count INTEGER,
            timestamp TEXT,
            fetched_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_post(post_data: dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO posts (post_url, shortcode, username, caption, likes_count, comments_count, timestamp, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(post_url) DO UPDATE SET
            likes_count=excluded.likes_count,
            comments_count=excluded.comments_count,
            fetched_at=excluded.fetched_at
    """, (
        post_data.get("post_url"),
        post_data.get("shortcode"),
        post_data.get("username"),
        post_data.get("caption"),
        post_data.get("likes_count", 0),
        post_data.get("comments_count", 0),
        post_data.get("timestamp"),
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()

def get_all_posts():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
