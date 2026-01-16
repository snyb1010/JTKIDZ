from flask import Flask, render_template, redirect, url_for, session
from config import Config
from database import db, init_db
from models import User, Kid, Attendance
from blueprints.auth import auth_bp, login_required
from blueprints.kids import kids_bp
from blueprints.attendance import attendance_bp
from blueprints.reports import reports_bp
from blueprints.users import users_bp
from blueprints.lessons import lessons_bp
from datetime import datetime
import os

def get_current_date():
    """Get current date in Philippines timezone"""
    return datetime.now(Config.TIMEZONE).date()

app = Flask(__name__)
app.config.from_object(Config)

# Ensure instance folder exists
os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)

# Initialize database
init_db(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(kids_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(users_bp)
app.register_blueprint(lessons_bp)

@app.route('/')
def index():
    """Redirect to login or dashboard"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    # Get statistics (using Philippines time)
    total_kids = Kid.query.filter_by(status='active').count()
    today = get_current_date()
    attendance_today = Attendance.query.filter_by(scan_date=today).count()
    
    # Get unique sites
    sites = db.session.query(Kid.site).distinct().all()
    active_sites = len(sites)
    
    # Age group counts (calculate in Python since age is a property)
    active_kids = Kid.query.filter_by(status='active').all()
    kids_count = sum(1 for k in active_kids if 3 <= k.age <= 8)
    risers_count = sum(1 for k in active_kids if 9 <= k.age <= 11)
    teens_count = sum(1 for k in active_kids if 12 <= k.age <= 14)
    other_count = sum(1 for k in active_kids if k.age < 3 or k.age > 14)
    
    # Recent attendance
    recent_attendance = db.session.query(Attendance, Kid).join(Kid).filter(
        Attendance.scan_date == today
    ).order_by(Attendance.scan_time.desc()).limit(10).all()
    
    stats = {
        'total_kids': total_kids,
        'attendance_today': attendance_today,
        'active_sites': active_sites,
        'kids_count': kids_count,
        'risers_count': risers_count,
        'teens_count': teens_count,
        'other_count': other_count
    }
    
    return render_template('dashboard.html', stats=stats, recent_attendance=recent_attendance)

@app.context_processor
def inject_user():
    """Make user info available in all templates"""
    return dict(
        current_user_name=session.get('user_name'),
        current_user_role=session.get('user_role')
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
