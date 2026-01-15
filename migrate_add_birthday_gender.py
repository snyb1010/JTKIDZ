"""
Migration script to add birthday, gender, and profile_pic columns to kids table
and convert existing age data to birthday estimates
"""
import sqlite3
from datetime import date, timedelta

def migrate():
    conn = sqlite3.connect('instance/jtkidz.db')
    cursor = conn.cursor()
    
    print("Starting migration...")
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(kids)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add birthday column if it doesn't exist
    if 'birthday' not in columns:
        print("Adding birthday column...")
        cursor.execute("ALTER TABLE kids ADD COLUMN birthday DATE")
        
        # Convert existing age to estimated birthday (current date - age years)
        cursor.execute("SELECT id, age FROM kids")
        kids = cursor.fetchall()
        today = date.today()
        
        for kid_id, age in kids:
            if age:
                # Estimate birthday as January 1st of the birth year
                birth_year = today.year - age
                estimated_birthday = date(birth_year, 1, 1)
                cursor.execute("UPDATE kids SET birthday = ? WHERE id = ?", 
                             (estimated_birthday.strftime('%Y-%m-%d'), kid_id))
                print(f"  Set birthday for kid ID {kid_id}: {estimated_birthday}")
    else:
        print("birthday column already exists, skipping...")
    
    # Add gender column if it doesn't exist
    if 'gender' not in columns:
        print("Adding gender column...")
        cursor.execute("ALTER TABLE kids ADD COLUMN gender VARCHAR(10)")
    else:
        print("gender column already exists, skipping...")
    
    # Add profile_pic column if it doesn't exist
    if 'profile_pic' not in columns:
        print("Adding profile_pic column...")
        cursor.execute("ALTER TABLE kids ADD COLUMN profile_pic VARCHAR(255)")
    else:
        print("profile_pic column already exists, skipping...")
    
    conn.commit()
    conn.close()
    
    print("Migration completed successfully!")
    print("\nNOTE: Existing kids have estimated birthdays set to January 1st.")
    print("You can edit each kid's profile to set their actual birthday.")

if __name__ == '__main__':
    migrate()
