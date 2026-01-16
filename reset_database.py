"""
Reset database - Clear all data for fresh testing
"""

import sqlite3
import os
from datetime import datetime

def reset_database():
    db_path = 'instance/jtkidz.db'
    
    # Create backup first
    backup_path = f'instance/jtkidz_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    
    if os.path.exists(db_path):
        print(f"Creating backup: {backup_path}")
        import shutil
        shutil.copy2(db_path, backup_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\nClearing database...")
    
    try:
        # Clear all tables (in order due to foreign keys)
        print("- Clearing attendance records...")
        cursor.execute('DELETE FROM attendance')
        
        print("- Clearing site lesson settings...")
        cursor.execute('DELETE FROM site_lesson_settings')
        
        print("- Clearing kids...")
        cursor.execute('DELETE FROM kids')
        
        print("- Clearing users (keeping admin)...")
        # Keep admin user, delete others
        cursor.execute("DELETE FROM users WHERE email != 'admin@jtkidz.com'")
        
        # Reset admin password to default
        from werkzeug.security import generate_password_hash
        admin_password = generate_password_hash('admin123')
        cursor.execute("UPDATE users SET password = ? WHERE email = 'admin@jtkidz.com'", (admin_password,))
        
        conn.commit()
        
        # Show remaining data
        cursor.execute('SELECT COUNT(*) FROM kids')
        kids_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM attendance')
        attendance_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users')
        users_count = cursor.fetchone()[0]
        
        print("\n✅ Database reset complete!")
        print(f"\nRemaining records:")
        print(f"  - Kids: {kids_count}")
        print(f"  - Attendance: {attendance_count}")
        print(f"  - Users: {users_count} (admin only)")
        print(f"\nBackup saved to: {backup_path}")
        print("\nAdmin login:")
        print("  Email: admin@jtkidz.com")
        print("  Password: admin123")
        
    except sqlite3.Error as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    confirm = input("⚠️  This will DELETE all kids, attendance, and staff data!\nType 'RESET' to confirm: ")
    if confirm == 'RESET':
        reset_database()
    else:
        print("❌ Reset cancelled")
