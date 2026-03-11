"""Add role column to users table"""
import sqlite3
import os

db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if column already exists
cursor.execute("PRAGMA table_info(users)")
columns = [col[1] for col in cursor.fetchall()]

if 'role' not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'student'")
    conn.commit()
    print("✅ Added 'role' column to users table (default: 'student').")
else:
    print("ℹ️  'role' column already exists.")

conn.close()
