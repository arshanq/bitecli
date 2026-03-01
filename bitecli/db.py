import sqlite3
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

def get_db_path():
    """Returns the path to the sqlite database in the user's config directory."""
    config_dir = os.environ.get("BITECLI_CONFIG_DIR", os.path.expanduser("~/.config/bitecli"))
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "bitecli.db")

def get_connection():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            content TEXT,
            published TEXT,
            feed_name TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def store_article(article: Dict[str, Any]) -> bool:
    """
    Stores a new article. Returns True if inserted, False if already exists (based on URL).
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Generate an ID based on url hash or just a uuid
    article_id = str(uuid.uuid5(uuid.NAMESPACE_URL, article['url']))
    
    try:
        cursor.execute('''
            INSERT INTO articles (id, title, url, content, published, feed_name, is_read)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        ''', (
            article_id,
            article.get('title', 'Unknown Title'),
            article['url'],
            article.get('content', ''),
            article.get('published', ''),
            article.get('feed_name', 'Unknown Feed')
        ))
        conn.commit()
        inserted = True
    except sqlite3.IntegrityError:
        # URL already exists
        inserted = False
    finally:
        conn.close()
        
    return inserted

def get_unread_article() -> Optional[Dict[str, Any]]:
    """Fetches a single unread article."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, title, url, content, published, feed_name
        FROM articles
        WHERE is_read = 0
        ORDER BY published DESC, created_at DESC
        LIMIT 1
    ''')
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def mark_as_read(article_id: str):
    """Marks an article as read."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE articles SET is_read = 1 WHERE id = ?', (article_id,))
    conn.commit()
    conn.close()

def get_stats() -> Dict[str, int]:
    """Returns counts of total, read, and unread articles."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM articles')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM articles WHERE is_read = 0')
    unread = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM articles WHERE is_read = 1')
    read = cursor.fetchone()[0]
    conn.close()
    
    return {'total': total, 'unread': unread, 'read': read}
