# db.py
import sqlite3

DATABASE = 'cash_management.db'
USERS = 'users.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Enables dict-like access
    return conn

def init_db():
    conn = sqlite3.connect(USERS)
    conn.row_factory = sqlite3.Row  # Enables dict-like access
    return conn

