from flask import Blueprint, render_template, request, send_file, session
from models import Kid, Attendance, User, SiteLessonSettings
from database import db
from blueprints.auth import login_required, admin_required
from services.export_service import export_to_excel
from datetime import datetime, date, timedelta
from sqlalchemy import func, extract
from collections import defaultdict

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/attendance-summary')
@admin_required
def attendance_summary():
    """Admin attendance summary grouped by site with age breakdown"""
    # Get date from query params or use today
    selected_date = request.args.get('date', '')
    if selected_date:
        try:
            view_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except:
            from blueprints.attendance import get_current_date
            view_date = get_current_date()
    else:
        from blueprints.attendance import get_current_date
        view_date = get_current_date()
    
    # Get all attendance for selected date
    records = db.session.query(Attendance, Kid, User).join(Kid).join(User, Attendance.scanned_by == User.id).filter(
        Attendance.scan_date == view_date
    ).order_by(Kid.site, Attendance.scan_time).all()
    
    # Group by site
    sites_data = defaultdict(lambda: {
        'all': [],
        'kids': [],
        'risers': [],
        'teens': [],
        'other': [],
        'total': 0,
        'kids_count': 0,
        'risers_count': 0,
        'teens_count': 0,
        'other_count': 0
    })
    
    for attendance, kid, user in records:
        site = kid.site
        # Create a simple object-like dict that the template can access
        class RecordWrapper:
            def __init__(self, attendance, kid, user):
                self.kid = kid
                self.created_at = attendance.created_at
                self.user = user
        
        record_data = RecordWrapper(attendance, kid, user)
        
        sites_data[site]['all'].append(record_data)
        sites_data[site]['total'] += 1
        
        # Group by age
        if 3 <= kid.age <= 8:
            sites_data[site]['kids'].append(record_data)
            sites_data[site]['kids_count'] += 1
        elif 9 <= kid.age <= 11:
            sites_data[site]['risers'].append(record_data)
            sites_data[site]['risers_count'] += 1
        elif 12 <= kid.age <= 14:
            sites_data[site]['teens'].append(record_data)
            sites_data[site]['teens_count'] += 1
        else:
            sites_data[site]['other'].append(record_data)
            sites_data[site]['other_count'] += 1
    
    # Calculate overall totals
    overall = {
        'total': sum(data['total'] for data in sites_data.values()),
        'kids_count': sum(data['kids_count'] for data in sites_data.values()),
        'risers_count': sum(data['risers_count'] for data in sites_data.values()),
        'teens_count': sum(data['teens_count'] for data in sites_data.values()),
        'other_count': sum(data['other_count'] for data in sites_data.values())
    }
    
    # Sort sites alphabetically
    sorted_sites = dict(sorted(sites_data.items()))
    
    return render_template('reports_attendance_summary.html', 
                          sites_data=sorted_sites,
                          overall=overall,
                          date=view_date,
                          selected_date=selected_date)

@reports_bp.route('/site')
@admin_required
def site_report():
    """Report filtered by site and date range"""
    site = request.args.get('site', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # Get all sites
    sites = db.session.query(Kid.site).distinct().order_by(Kid.site).all()
    sites = [s[0] for s in sites]
    
    records = []
    stats = {}
    
    if site or (start_date and end_date):
        query = db.session.query(Attendance, Kid).join(Kid)
        
        if site:
            query = query.filter(Kid.site == site)
        if start_date:
            query = query.filter(Attendance.scan_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(Attendance.scan_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        records = query.order_by(Attendance.scan_date.desc(), Attendance.scan_time.desc()).all()
        
        # Calculate stats
        total_kids = Kid.query.filter_by(site=site, status='active').count() if site else Kid.query.filter_by(status='active').count()
        total_attendance = len(records)
        unique_kids = len(set([r[0].kid_id for r in records]))
        
        stats = {
            'total_kids': total_kids,
            'total_attendance': total_attendance,
            'unique_kids': unique_kids,
            'attendance_rate': round((unique_kids / total_kids * 100) if total_kids > 0 else 0, 1)
        }
    
    return render_template('reports_site.html', 
                          records=records, 
                          sites=sites, 
                          stats=stats,
                          current_site=site,
                          start_date=start_date,
                          end_date=end_date)

@reports_bp.route('/monthly')
@admin_required
def monthly_report():
    """Monthly attendance summary per child"""
    site = request.args.get('site', '')
    month = request.args.get('month', '')
    year = request.args.get('year', str(date.today().year))
    
    # Get all sites
    sites = db.session.query(Kid.site).distinct().order_by(Kid.site).all()
    sites = [s[0] for s in sites]
    
    summary = []
    
    if month and year:
        # Query kids and count their attendance for the month
        query = db.session.query(
            Kid,
            func.count(Attendance.id).label('attendance_count')
        ).outerjoin(Attendance, 
            (Kid.id == Attendance.kid_id) & 
            (extract('month', Attendance.scan_date) == int(month)) &
            (extract('year', Attendance.scan_date) == int(year))
        )
        
        if site:
            query = query.filter(Kid.site == site)
        
        query = query.filter(Kid.status == 'active')
        summary = query.group_by(Kid.id).order_by(Kid.site, Kid.full_name).all()
    
    return render_template('reports_monthly.html',
                          summary=summary,
                          sites=sites,
                          current_site=site,
                          current_month=month,
                          current_year=year)

@reports_bp.route('/lessons')
@admin_required
def lesson_report():
    """Lesson-based attendance report with charts"""
    lesson_filter = request.args.get('lesson', '', type=str)
    site_filter = request.args.get('site', '')
    
    # Get all sites
    sites = db.session.query(Kid.site).distinct().order_by(Kid.site).all()
    sites = [s[0] for s in sites]
    
    # Build lesson data for all sites and all lessons
    lesson_data = []
    
    for lesson_num in range(1, 7):
        lesson_stats = {
            'lesson': lesson_num,
            'sites': []
        }
        
        for site in sites:
            # Skip if filtering and doesn't match
            if site_filter and site != site_filter:
                continue
            if lesson_filter and str(lesson_num) != lesson_filter:
                continue
            
            # Get total active kids in site
            total_kids = Kid.query.filter_by(site=site, status='active').count()
            
            # Get attendance count for this lesson
            attendance_count = db.session.query(Attendance.kid_id).filter(
                Attendance.site == site,
                Attendance.lesson == lesson_num
            ).distinct().count()
            
            # Get lesson setting for this site
            setting = SiteLessonSettings.query.filter_by(site=site).first()
            is_current = setting and setting.current_lesson == lesson_num
            is_completed = setting and setting.current_lesson > lesson_num
            
            site_data = {
                'site': site,
                'total_kids': total_kids,
                'attendance_count': attendance_count,
                'completion_rate': round((attendance_count / total_kids * 100) if total_kids > 0 else 0, 1),
                'is_current': is_current,
                'is_completed': is_completed,
                'status': 'current' if is_current else ('completed' if is_completed else 'upcoming')
            }
            
            lesson_stats['sites'].append(site_data)
        
        if lesson_stats['sites']:  # Only add if has data
            lesson_data.append(lesson_stats)
    
    # Calculate overall statistics per lesson
    overall_by_lesson = []
    for lesson_num in range(1, 7):
        total_kids_all = sum(Kid.query.filter_by(site=s, status='active').count() for s in sites)
        total_attendance = db.session.query(Attendance.kid_id).filter(
            Attendance.lesson == lesson_num
        ).distinct().count()
        
        overall_by_lesson.append({
            'lesson': lesson_num,
            'total_kids': total_kids_all,
            'attendance': total_attendance,
            'rate': round((total_attendance / total_kids_all * 100) if total_kids_all > 0 else 0, 1)
        })
    
    return render_template('reports_lesson.html',
                          lesson_data=lesson_data,
                          overall_by_lesson=overall_by_lesson,
                          sites=sites,
                          current_site=site_filter,
                          current_lesson=lesson_filter)

@reports_bp.route('/lessons/detail')
@admin_required
def lesson_detail():
    """Detailed attendance for a specific site and lesson"""
    site = request.args.get('site', '')
    lesson = request.args.get('lesson', type=int)
    
    if not site or not lesson:
        flash('Site and lesson parameters are required', 'danger')
        return redirect(url_for('reports.lesson_report'))
    
    # Get all kids who attended this lesson at this site
    attendance_records = db.session.query(Attendance, Kid).join(Kid).filter(
        Attendance.site == site,
        Attendance.lesson == lesson
    ).order_by(Attendance.scan_date, Attendance.scan_time).all()
    
    # Get total active kids in site
    total_kids = Kid.query.filter_by(site=site, status='active').count()
    
    # Get unique kids count
    unique_kids = len(set([a.kid_id for a, k in attendance_records]))
    
    stats = {
        'site': site,
        'lesson': lesson,
        'total_kids': total_kids,
        'attended': unique_kids,
        'completion_rate': round((unique_kids / total_kids * 100) if total_kids > 0 else 0, 1),
        'total_scans': len(attendance_records)
    }
    
    return render_template('reports_lesson_detail.html',
                          attendance_records=attendance_records,
                          stats=stats)

@reports_bp.route('/worker-audit')
@admin_required
def worker_audit():
    """Admin audit report showing worker scanning patterns"""
    from blueprints.attendance import get_current_date
    
    # Get date range from query params
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    if not start_date or not end_date:
        # Default to last 7 days
        today = get_current_date()
        end_date = today.strftime('%Y-%m-%d')
        start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Get all staff users
    workers = User.query.filter_by(role='staff').all()
    
    # Build report data per worker
    worker_stats = []
    for worker in workers:
        # Get attendance scanned by this worker in date range
        scans = db.session.query(Attendance, Kid).join(Kid).filter(
            Attendance.scanned_by == worker.id,
            Attendance.scan_date >= start_date,
            Attendance.scan_date <= end_date
        ).order_by(Attendance.scan_date.desc(), Attendance.scan_time.desc()).all()
        
        # Detect suspicious patterns
        scan_times = []
        rapid_scans = 0
        for i, (att, kid) in enumerate(scans):
            scan_datetime = datetime.combine(att.scan_date, att.scan_time)
            scan_times.append(scan_datetime)
            
            # Check if scan was within 5 seconds of previous
            if i > 0:
                time_diff = (scan_times[i-1] - scan_times[i]).total_seconds()
                if abs(time_diff) < 5:
                    rapid_scans += 1
        
        # Group by date
        daily_counts = defaultdict(int)
        for att, kid in scans:
            daily_counts[att.scan_date] += 1
        
        worker_stats.append({
            'worker': worker,
            'total_scans': len(scans),
            'rapid_scans': rapid_scans,
            'days_active': len(daily_counts),
            'avg_per_day': round(len(scans) / max(len(daily_counts), 1), 1),
            'recent_scans': scans[:10]  # Last 10 scans
        })
    
    return render_template('reports_worker_audit.html',
                          worker_stats=worker_stats,
                          start_date=start_date,
                          end_date=end_date)

@reports_bp.route('/export')
@admin_required
def export_report():
    """Export attendance to Excel"""
    report_type = request.args.get('type', 'site')
    site = request.args.get('site', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    month = request.args.get('month', '')
    year = request.args.get('year', '')
    lesson = request.args.get('lesson', '')
    
    filepath = export_to_excel(report_type, site, start_date, end_date, month, year, lesson)
    
    return send_file(filepath, as_attachment=True, download_name=f'jtkidz_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
