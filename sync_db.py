from app import create_app, db
from sqlalchemy import text
import os

app = create_app()

def sync_db():
    with app.app_context():
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        print(f"Synchronizing database: {db_uri.split('@')[-1] if '@' in db_uri else db_uri}")
        
        try:
            # Create tables if they don't exist
            db.create_all()
            
            # Check if we need to rename column from 'content' to 'notes_text'
            # This handles older deployments
            if 'postgresql' in db_uri:
                # PostgreSQL check
                check_query = text("SELECT column_name FROM information_schema.columns WHERE table_name='topics' AND column_name='content';")
                result = db.session.execute(check_query).fetchone()
                if result:
                    print("Found 'content' column in 'topics' table. Renaming to 'notes_text'...")
                    db.session.execute(text("ALTER TABLE topics RENAME COLUMN content TO notes_text;"))
                    db.session.commit()
                    print("Column renamed successfully.")
            else:
                # SQLite check
                check_query = text("PRAGMA table_info(topics)")
                result = db.session.execute(check_query).fetchall()
                cols = [row[1] for row in result]
                if 'content' in cols and 'notes_text' not in cols:
                    print("Found 'content' column in 'topics' table (SQLite). Attempting rename...")
                    try:
                        db.session.execute(text("ALTER TABLE topics RENAME COLUMN content TO notes_text;"))
                        db.session.commit()
                        print("Column renamed successfully.")
                    except Exception as sqle:
                        print(f"SQLite rename failed (old version?): {sqle}")
            
            print("Database synchronization complete.")
        except Exception as e:
            print(f"Database sync error (non-critical): {e}")
            db.session.rollback()

if __name__ == '__main__':
    sync_db()
