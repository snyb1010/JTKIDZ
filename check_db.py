import sqlite3

# Check jtkidz.db
conn = sqlite3.connect('instance/jtkidz.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print("Tables in jtkidz.db:", tables)

if 'attendance' in tables:
    cursor.execute("PRAGMA table_info(attendance)")
    columns = cursor.fetchall()
    print("\nAttendance table columns:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")

conn.close()
