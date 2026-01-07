"""
Migration script to add assigned_sites column to users table
Run this once to update existing database
"""
from app import app
from database import db

def migrate():
    with app.app_context():
        # Check if column exists
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        
        if 'assigned_sites' not in columns:
            print("Adding assigned_sites column to users table...")
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE users ADD COLUMN assigned_sites TEXT'))
                conn.commit()
            print("✅ Migration completed successfully!")
        else:
            print("✅ Column already exists. No migration needed.")

if __name__ == '__main__':
    migrate()
