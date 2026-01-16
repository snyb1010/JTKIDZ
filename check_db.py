import sqlite3

# Check jtkidz.db
conn = sqlite3.connect('instance/jtkidz.db')
cursor = conn.cursor()

# Check users table
print("=== USERS ===")
cursor.execute("SELECT id, name, email, role, assigned_sites FROM users")
users = cursor.fetchall()
for user in users:
    print(f"ID: {user[0]}, Name: {user[1]}, Email: {user[2]}, Role: {user[3]}, Assigned Sites: '{user[4]}'")

# Check kids table
print("\n=== KIDS ===")
cursor.execute("SELECT id, full_name, site, status FROM kids")
kids = cursor.fetchall()
for kid in kids:
    print(f"ID: {kid[0]}, Name: {kid[1]}, Site: '{kid[2]}', Status: {kid[3]}")

# Check attendance
print("\n=== ATTENDANCE ===")
cursor.execute("SELECT id, kid_id, site, lesson, scan_date FROM attendance")
attendance = cursor.fetchall()
for att in attendance:
    print(f"ID: {att[0]}, Kid ID: {att[1]}, Site: '{att[2]}', Lesson: {att[3]}, Date: {att[4]}")

conn.close()
