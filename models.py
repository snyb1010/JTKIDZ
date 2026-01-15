from database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

class User(db.Model):
    """User model for admin and staff"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='staff')  # 'admin' or 'staff'
    assigned_sites = db.Column(db.Text, nullable=True)  # JSON array of assigned sites for staff
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password, password)
    
    def get_assigned_sites(self):
        """Get list of assigned sites"""
        if self.role == 'admin':
            return []  # Admin has access to all sites
        if not self.assigned_sites:
            return []
        try:
            return json.loads(self.assigned_sites)
        except:
            return []
    
    def set_assigned_sites(self, sites_list):
        """Set assigned sites as JSON"""
        if sites_list:
            self.assigned_sites = json.dumps(sites_list)
        else:
            self.assigned_sites = None
    
    def can_access_site(self, site):
        """Check if user can access a specific site"""
        if self.role == 'admin':
            return True
        sites = self.get_assigned_sites()
        return site in sites
    
    def __repr__(self):
        return f'<User {self.email}>'


class Kid(db.Model):
    """Kid model for children profiles"""
    __tablename__ = 'kids'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    birthday = db.Column(db.Date, nullable=True)  # New: Birthday field
    gender = db.Column(db.String(10), nullable=True)  # New: 'Male' or 'Female'
    profile_pic = db.Column(db.String(255), nullable=True)  # New: Profile picture filename
    site = db.Column(db.String(100), nullable=False)
    barcode = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active')  # 'active' or 'inactive'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to attendance
    attendance_records = db.relationship('Attendance', backref='kid', lazy=True)
    
    @property
    def age(self):
        """Calculate age from birthday (automatically updates on birthday)"""
        if not self.birthday:
            return 0
        from datetime import date
        today = date.today()
        age = today.year - self.birthday.year
        # Subtract 1 if birthday hasn't occurred yet this year
        if (today.month, today.day) < (self.birthday.month, self.birthday.day):
            age -= 1
        return age
    
    @property
    def age_group(self):
        """Return age group category"""
        current_age = self.age
        if 3 <= current_age <= 8:
            return 'Kids (3-8)'
        elif 9 <= current_age <= 11:
            return 'Risers (9-11)'
        elif 12 <= current_age <= 14:
            return 'Teens (12-14)'
        else:
            return 'Other'
    
    def __repr__(self):
        return f'<Kid {self.full_name} - {self.barcode}>'


class Attendance(db.Model):
    """Attendance model for tracking scans"""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    kid_id = db.Column(db.Integer, db.ForeignKey('kids.id'), nullable=False)
    site = db.Column(db.String(100), nullable=False)
    scan_date = db.Column(db.Date, nullable=False)
    scan_time = db.Column(db.Time, nullable=False)
    scanned_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to user who scanned
    scanner = db.relationship('User', backref='scans_made', lazy=True)
    
    def __repr__(self):
        return f'<Attendance kid_id={self.kid_id} date={self.scan_date}>'
