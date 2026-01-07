from database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """User model for admin and staff"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='staff')  # 'admin' or 'staff'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password, password)
    
    def __repr__(self):
        return f'<User {self.email}>'


class Kid(db.Model):
    """Kid model for children profiles"""
    __tablename__ = 'kids'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    site = db.Column(db.String(100), nullable=False)
    barcode = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active')  # 'active' or 'inactive'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to attendance
    attendance_records = db.relationship('Attendance', backref='kid', lazy=True)
    
    @property
    def age_group(self):
        """Return age group category"""
        if 3 <= self.age <= 8:
            return 'Kids (3-8)'
        elif 9 <= self.age <= 11:
            return 'Risers (9-11)'
        elif 12 <= self.age <= 14:
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
