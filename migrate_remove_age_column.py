"""
Migration script to remove the age column from kids table
Since age is now calculated from birthday
"""
import sqlite3
import shutil
from datetime import datetime

def migrate():
    db_path = 'instance/jtkidz.db'
    backup_path = f'instance/jtkidz_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    
    # Create backup
    print(f"Creating backup: {backup_path}")
    shutil.copy2(db_path, backup_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Starting migration to remove age column...")
    
    # Check if age column exists
    cursor.execute("PRAGMA table_info(kids)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'age' not in columns:
        print("Age column doesn't exist, nothing to do.")
        conn.close()
        return
    
    print("Age column found, recreating table without it...")
    
    # SQLite doesn't support DROP COLUMN directly, need to recreate table
    cursor.execute("""
        CREATE TABLE kids_new (
            id INTEGER PRIMARY KEY,
            full_name VARCHAR(100) NOT NULL,
            birthday DATE,
            gender VARCHAR(10),
            profile_pic VARCHAR(255),
            site VARCHAR(100) NOT NULL,
            barcode VARCHAR(50) UNIQUE NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            created_at DATETIME
        )
    """)
    
    # Copy data from old table to new table (excluding age)
    cursor.execute("""
        INSERT INTO kids_new (id, full_name, birthday, gender, profile_pic, site, barcode, status, created_at)
        SELECT id, full_name, birthday, gender, profile_pic, site, barcode, status, created_at
        FROM kids
    """)
    
    # Drop old table and rename new table
    cursor.execute("DROP TABLE kids")
    cursor.execute("ALTER TABLE kids_new RENAME TO kids")
    
    conn.commit()
    conn.close()
    
    print("Migration completed successfully!")
    print(f"Backup saved at: {backup_path}")

if __name__ == '__main__':
    migrate()
