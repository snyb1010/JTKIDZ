from flask import Blueprint, render_template, request, jsonify, session
from models import Kid, Attendance, User
from database import db
from blueprints.auth import login_required
from datetime import datetime, date

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

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
    
    # Check if already scanned today
    today = date.today()
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
    
    # Record attendance
    now = datetime.now()
    attendance = Attendance(
        kid_id=kid.id,
        site=kid.site,
        scan_date=today,
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
    """View today's attendance"""
    today = date.today()
    records = db.session.query(Attendance, Kid, User).join(Kid).join(User, Attendance.scanned_by == User.id).filter(
        Attendance.scan_date == today
    ).order_by(Attendance.scan_time.desc()).all()
    
    return render_template('attendance_today.html', records=records, date=today)
