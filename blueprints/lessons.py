from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from models import SiteLessonSettings, Kid, Attendance
from database import db
from blueprints.auth import login_required, admin_required
from datetime import datetime, date
from sqlalchemy import func

lessons_bp = Blueprint('lessons', __name__, url_prefix='/lessons')

@lessons_bp.route('/')
@admin_required
def manage_lessons():
    """Manage lesson progress for all sites"""
    # Get all sites
    sites = db.session.query(Kid.site).distinct().order_by(Kid.site).all()
    sites = [s[0] for s in sites]
    
    # Get lesson settings for each site
    lesson_data = []
    for site in sites:
        setting = SiteLessonSettings.query.filter_by(site=site).first()
        if not setting:
            # Create default if not exists
            setting = SiteLessonSettings(site=site, current_lesson=1, lesson_start_date=date(2026, 1, 24))
            db.session.add(setting)
            db.session.commit()
        
        # Get attendance count for current lesson
        attendance_count = Attendance.query.filter_by(
            site=site,
            lesson=setting.current_lesson
        ).distinct(Attendance.kid_id).count()
        
        # Get total active kids in site
        total_kids = Kid.query.filter_by(site=site, status='active').count()
        
        lesson_data.append({
            'site': site,
            'current_lesson': setting.current_lesson,
            'start_date': setting.lesson_start_date,
            'attendance_count': attendance_count,
            'total_kids': total_kids,
            'completion_rate': round((attendance_count / total_kids * 100) if total_kids > 0 else 0, 1)
        })
    
    return render_template('lessons_manage.html', lesson_data=lesson_data)

@lessons_bp.route('/advance/<site>', methods=['POST'])
@admin_required
def advance_lesson(site):
    """Advance to next lesson for a site"""
    setting = SiteLessonSettings.query.filter_by(site=site).first()
    
    if not setting:
        flash(f'Lesson settings not found for {site}', 'danger')
        return redirect(url_for('lessons.manage_lessons'))
    
    if setting.current_lesson >= 6:
        flash(f'{site} has already completed all 6 lessons!', 'warning')
        return redirect(url_for('lessons.manage_lessons'))
    
    # Advance to next lesson
    setting.current_lesson += 1
    setting.lesson_start_date = date.today()
    setting.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    flash(f'✅ {site} advanced to Lesson {setting.current_lesson}!', 'success')
    return redirect(url_for('lessons.manage_lessons'))

@lessons_bp.route('/set/<site>', methods=['POST'])
@admin_required
def set_lesson(site):
    """Manually set lesson number for a site"""
    lesson_number = request.form.get('lesson', type=int)
    start_date_str = request.form.get('start_date', '')
    
    if not lesson_number or lesson_number < 1 or lesson_number > 6:
        flash('Invalid lesson number. Must be between 1 and 6.', 'danger')
        return redirect(url_for('lessons.manage_lessons'))
    
    setting = SiteLessonSettings.query.filter_by(site=site).first()
    
    if not setting:
        setting = SiteLessonSettings(site=site)
        db.session.add(setting)
    
    setting.current_lesson = lesson_number
    
    if start_date_str:
        try:
            setting.lesson_start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except:
            flash('Invalid date format', 'warning')
    else:
        setting.lesson_start_date = date.today()
    
    setting.updated_at = datetime.utcnow()
    db.session.commit()
    
    flash(f'✅ {site} set to Lesson {lesson_number}!', 'success')
    return redirect(url_for('lessons.manage_lessons'))
