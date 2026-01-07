from flask import Blueprint, render_template, request, jsonify, session, current_app
from models import Kid, Attendance, User
from database import db
from blueprints.auth import login_required
from datetime import datetime, date

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

def get_current_datetime():
    """Get current datetime in Philippines timezone"""
    from config import Config
    return datetime.now(Config.TIMEZONE)

def get_current_date():
    """Get current date in Philippines timezone"""
    return get_current_datetime().date()

@attendance_bp.route('/scan')
@login_required
def scan_page():
    """Mobile barcode scanning page"""
    return render_template('scan.html')

@attendance_bp.route('/record', methods=['POST'])
@login_required
def record_attendance():
    """API endpoint to record attendance from barcode scan"""
    data = request.get_json()
    barcode = data.get('barcode', '').strip().upper()
    
    if not barcode:
        return jsonify({'success': False, 'message': 'No barcode provided'}), 400
    
    # Find kid by barcode
    kid = Kid.query.filter_by(barcode=barcode).first()
    
    if not kid:
        return jsonify({'success': False, 'message': 'Invalid barcode. Kid not found.'}), 404
    
    if kid.status != 'active':
        return jsonify({'success': False, 'message': f'{kid.full_name} is inactive.'}), 400
    
    # Check if staff user can access this site
    current_user = User.query.get(session['user_id'])
    if not current_user.can_access_site(kid.site):
        return jsonify({
            'success': False,
            'message': f'❌ {kid.full_name} is from {kid.site}. You are not assigned to this site.',
            'wrong_site': True
        }), 403
    
    # Check if already scanned today (using Philippines time)
    today = get_current_date()
    existing = Attendance.query.filter_by(
        kid_id=kid.id,
        scan_date=today
    ).first()
    
    if existing:
        return jsonify({
            'success': False,
            'message': f'{kid.full_name} already scanned today at {existing.scan_time.strftime("%I:%M %p")}',
            'already_scanned': True
        }), 400
    
    # Record attendance (using Philippines time)
    now = get_current_datetime()
    attendance = Attendance(
        kid_id=kid.id,
        site=kid.site,
        scan_date=now.date(),
        scan_time=now.time(),
        scanned_by=session['user_id']
    )
    
    db.session.add(attendance)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'✅ {kid.full_name} attendance recorded!',
        'kid_name': kid.full_name,
        'kid_age': kid.age,
        'site': kid.site,
        'time': now.strftime('%I:%M %p')
    }), 200

@attendance_bp.route('/today')
@login_required
def today_attendance():
    """View attendance with date filter and site filtering for workers"""
    # Get date from query params or use today (Philippines time)
    selected_date = request.args.get('date', '')
    if selected_date:
        try:
            view_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except:
            view_date = get_current_date()
    else:
        view_date = get_current_date()
    
    # Get current user and filter by assigned sites for workers
    current_user = User.query.get(session['user_id'])
    
    query = db.session.query(Attendance, Kid, User).join(Kid).join(User, Attendance.scanned_by == User.id).filter(
        Attendance.scan_date == view_date
    )
    
    # Filter by staff's assigned sites
    if current_user.role == 'staff':
        assigned_sites = current_user.get_assigned_sites()
        if assigned_sites:
            query = query.filter(Kid.site.in_(assigned_sites))
        else:
            # Staff with no sites sees nothing
            query = query.filter(Kid.id == -1)
    
    records = query.order_by(Attendance.scan_time.desc()).all()
    
    return render_template('attendance_today.html', records=records, date=view_date, selected_date=selected_date)
