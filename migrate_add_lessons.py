"""
Migration script to add lesson tracking feature
- Adds lesson column to attendance table
- Creates site_lesson_settings table
"""

import sqlite3
from datetime import date

def migrate():
    conn = sqlite3.connect('instance/jtkidz.db')
    cursor = conn.cursor()
    
    print("Starting migration: Add lesson tracking...")
    
    try:
        # Step 1: Add lesson column to attendance table
        print("1. Adding lesson column to attendance table...")
        cursor.execute('''
            ALTER TABLE attendance 
            ADD COLUMN lesson INTEGER NOT NULL DEFAULT 1
        ''')
        print("   ✓ Lesson column added")
        
        # Step 2: Create site_lesson_settings table
        print("2. Creating site_lesson_settings table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS site_lesson_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site VARCHAR(100) UNIQUE NOT NULL,
                current_lesson INTEGER NOT NULL DEFAULT 1,
                lesson_start_date DATE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("   ✓ site_lesson_settings table created")
        
        # Step 3: Initialize site lesson settings for all existing sites
        print("3. Initializing lesson settings for existing sites...")
        cursor.execute('SELECT DISTINCT site FROM kids ORDER BY site')
        sites = cursor.fetchall()
        
        # Set Jan 24, 2026 as default start date for Lesson 1
        default_start_date = '2026-01-24'
        
        for (site,) in sites:
            cursor.execute('''
                INSERT OR IGNORE INTO site_lesson_settings (site, current_lesson, lesson_start_date)
                VALUES (?, 1, ?)
            ''', (site, default_start_date))
            print(f"   ✓ Initialized {site} - Lesson 1 (Start: {default_start_date})")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print(f"   - Added lesson tracking to {cursor.rowcount} attendance records")
        print(f"   - Initialized {len(sites)} sites with Lesson 1")
        
    except sqlite3.Error as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
