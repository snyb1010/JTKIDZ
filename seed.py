"""
Seed database with initial admin user and sample data
Run this once to initialize the system
"""
from app import app
from database import db
from models import User, Kid, Attendance
from services.barcode_service import generate_barcode
from datetime import date, time, timedelta
import random

def seed_database():
    with app.app_context():
        # Clear existing data (optional - comment out if you want to keep existing data)
        print("Clearing existing data...")
        Attendance.query.delete()
        Kid.query.delete()
        User.query.delete()
        db.session.commit()
        
        # Create admin user
        print("Creating admin user...")
        admin = User(
            name="Admin User",
            email="admin@jtkidz.com",
            role="admin"
        )
        admin.set_password("admin123")
        db.session.add(admin)
        
        # Create staff user
        print("Creating staff user...")
        staff = User(
            name="Staff Volunteer",
            email="staff@jtkidz.com",
            role="staff"
        )
        staff.set_password("staff123")
        db.session.add(staff)
        
        db.session.commit()
        
        # Sample sites in Puerto Princesa
        sites = [
            "Barangay San Pedro",
            "Barangay Tagburos",
            "Barangay Bancao-Bancao",
            "Barangay Manalo",
            "Barangay Mabuhay"
        ]
        
        # Sample Filipino names
        first_names = ["Juan", "Maria", "Jose", "Ana", "Pedro", "Rosa", "Miguel", "Sofia", "Carlos", "Elena",
                      "Diego", "Isabel", "Luis", "Carmen", "Rafael", "Lucia", "Gabriel", "Teresa", "Daniel", "Patricia"]
        last_names = ["Santos", "Reyes", "Cruz", "Bautista", "Garcia", "Mendoza", "Lopez", "Gonzales", "Rodriguez", "Flores"]
        
        # Create sample kids
        print("Creating sample kids...")
        kids_list = []
        for i in range(30):
            full_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            age = random.randint(5, 17)
            site = random.choice(sites)
            barcode = f"JT{(i+1):06d}"
            
            kid = Kid(
                full_name=full_name,
                age=age,
                site=site,
                barcode=barcode,
                status="active"
            )
            db.session.add(kid)
            kids_list.append(kid)
            
        db.session.commit()
        
        # Generate barcodes for all kids
        print("Generating barcodes...")
        for kid in kids_list:
            try:
                generate_barcode(kid.barcode, kid.full_name)
                print(f"Generated barcode for {kid.full_name} ({kid.barcode})")
            except Exception as e:
                print(f"Error generating barcode for {kid.full_name}: {e}")
        
        # Create sample attendance for the past 7 days
        print("Creating sample attendance records...")
        today = date.today()
        for days_ago in range(7):
            attendance_date = today - timedelta(days=days_ago)
            
            # Random 60-80% of kids attend each day
            attending_kids = random.sample(kids_list, random.randint(18, 24))
            
            for kid in attending_kids:
                # Random time between 2 PM and 5 PM
                hour = random.randint(14, 16)
                minute = random.randint(0, 59)
                scan_time = time(hour, minute)
                
                attendance = Attendance(
                    kid_id=kid.id,
                    site=kid.site,
                    scan_date=attendance_date,
                    scan_time=scan_time,
                    scanned_by=random.choice([admin.id, staff.id])
                )
                db.session.add(attendance)
        
        db.session.commit()
        
        print("\n✅ Database seeded successfully!")
        print("\n📋 Login Credentials:")
        print("Admin: admin@jtkidz.com / admin123")
        print("Staff: staff@jtkidz.com / staff123")
        print(f"\n👥 Created {len(kids_list)} sample kids across {len(sites)} sites")
        print("🎯 Sample attendance data added for the past 7 days")

if __name__ == "__main__":
    seed_database()
