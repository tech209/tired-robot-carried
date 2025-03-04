import sqlite3
import os

DB_FILE = "cia_foia_library.db"

def get_connection():
    """
    Returns a SQLite connection to our local database file.
    Using check_same_thread=False allows usage across multiple threads.
    """
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn

def initialize_db():
    """
    Creates all necessary tables in the SQLite database if they don't already exist.
    Includes:
      - documents: stores basic metadata about each PDF.
      - documents_fts: an FTS5 virtual table for efficient full-text searching.
      - tags: a simple many-to-one relation of tag strings to documents.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url TEXT UNIQUE,
            file_path TEXT,
            file_size INTEGER,
            download_date TEXT
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts 
        USING fts5(
            title, 
            content, 
            url, 
            file_path, 
            file_size, 
            download_date
        );

        CREATE TABLE IF NOT EXISTS tags (
            document_id INTEGER,
            tag TEXT,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        );
    """)
    conn.commit()
    conn.close()