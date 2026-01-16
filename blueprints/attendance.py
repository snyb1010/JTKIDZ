from flask import Blueprint, render_template, request, jsonify, session, current_app
from models import Kid, Attendance, User, SiteLessonSettings
from database import db
from blueprints.auth import login_required
from datetime import datetime, date
import time

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
    # Get current user's sites
    current_user = User.query.get(session['user_id'])
    
    if current_user.role == 'admin':
        # Admin can see all sites
        sites = db.session.query(Kid.site).distinct().order_by(Kid.site).all()
        user_sites = [s[0] for s in sites]
    else:
        # Staff only sees their assigned sites
        user_sites = current_user.get_assigned_sites()
    
    # Get lesson settings for user's sites
    lesson_settings = {}
    for site in user_sites:
        setting = SiteLessonSettings.query.filter_by(site=site).first()
        if not setting:
            # Create default setting if doesn't exist
            setting = SiteLessonSettings(site=site, current_lesson=1, lesson_start_date=date(2026, 1, 24))
            db.session.add(setting)
            db.session.commit()
        lesson_settings[site] = {
            'current_lesson': setting.current_lesson,
            'start_date': setting.lesson_start_date.strftime('%b %d, %Y') if setting.lesson_start_date else 'Not set'
        }
    
    # For staff, determine which lessons they can access based on what they've scanned
    available_lessons = [1]  # Lesson 1 always available
    default_lesson = 1
    
    if current_user.role == 'staff':
        # Check what lessons this staff member has scanned for
        scanned_lessons = db.session.query(Attendance.lesson).filter(
            Attendance.scanned_by == current_user.id
        ).distinct().order_by(Attendance.lesson).all()
        
        if scanned_lessons:
            max_scanned = max([l[0] for l in scanned_lessons])
            # Can access all lessons up to max_scanned + 1 (up to lesson 6)
            available_lessons = list(range(1, min(max_scanned + 2, 7)))
            default_lesson = max_scanned if max_scanned < 6 else 6
    else:
        # Admin can access all lessons
        available_lessons = list(range(1, 7))
        if lesson_settings and user_sites:
            first_site = user_sites[0]
            default_lesson = lesson_settings.get(first_site, {}).get('current_lesson', 1)
    
    return render_template('scan.html', lesson_settings=lesson_settings, 
                          default_lesson=default_lesson, available_lessons=available_lessons)

@attendance_bp.route('/record', methods=['POST'])
@login_required
def record_attendance():
    """API endpoint to record attendance from barcode scan"""
    data = request.get_json()
    barcode = data.get('barcode', '').strip().upper()
    selected_lesson = data.get('lesson', 1)  # Get lesson from request
    
    if not barcode:
        return jsonify({'success': False, 'message': 'No barcode provided'}), 400
    
    # Anti-fraud: Prevent rapid scanning (2 seconds minimum between scans)
    current_time = time.time()
    last_scan_time = session.get('last_scan_time', 0)
    time_diff = current_time - last_scan_time
    
    if time_diff < 2:  # Less than 2 seconds since last scan
        return jsonify({
            'success': False,
            'message': f'⚠️ Please wait {int(2 - time_diff)} more seconds before next scan.',
            'too_fast': True
        }), 429
    
    # Validate lesson number
    if not selected_lesson or selected_lesson < 1 or selected_lesson > 6:
        return jsonify({'success': False, 'message': 'Invalid lesson number'}), 400
    
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
    
    # Check if already scanned today for this lesson (using Philippines time)
    today = get_current_date()
    existing = Attendance.query.filter_by(
        kid_id=kid.id,
        lesson=selected_lesson,
        scan_date=today
    ).first()
    
    if existing:
        return jsonify({
            'success': False,
            'message': f'{kid.full_name} already scanned for Lesson {selected_lesson} today at {existing.scan_time.strftime("%I:%M %p")}',
            'already_scanned': True
        }), 400
    
    # Record attendance (using Philippines time)
    now = get_current_datetime()
    attendance = Attendance(
        kid_id=kid.id,
        site=kid.site,
        lesson=selected_lesson,
        scan_date=now.date(),
        scan_time=now.time(),
        scanned_by=session['user_id']
    )
    
    db.session.add(attendance)
    db.session.commit()
    
    # Update last scan time to prevent rapid scanning
    session['last_scan_time'] = time.time()
    
    return jsonify({
        'success': True,
        'message': f'✅ {kid.full_name} - Lesson {selected_lesson} recorded!',
        'kid_name': kid.full_name,
        'kid_age': kid.age,
        'site': kid.site,
        'lesson': selected_lesson,
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
    
    # Get lesson filter
    selected_lesson = request.args.get('lesson', '')
    
    # Get current user and filter by assigned sites for workers
    current_user = User.query.get(session['user_id'])
    
    query = db.session.query(Attendance, Kid, User).join(Kid).join(User, Attendance.scanned_by == User.id).filter(
        Attendance.scan_date == view_date
    )
    
    # Filter by lesson if selected
    if selected_lesson:
        query = query.filter(Attendance.lesson == int(selected_lesson))
    
    # Filter by staff's assigned sites
    if current_user.role == 'staff':
        assigned_sites = current_user.get_assigned_sites()
        if assigned_sites:
            query = query.filter(Kid.site.in_(assigned_sites))
        else:
            # Staff with no sites sees nothing
            query = query.filter(Kid.id == -1)
    
    records = query.order_by(Attendance.scan_time.desc()).all()
    
    return render_template('attendance_today.html', records=records, date=view_date, selected_date=selected_date, selected_lesson=selected_lesson)
