from flask import Blueprint, render_template, request, send_file, session
from models import Kid, Attendance, User
from database import db
from blueprints.auth import login_required, admin_required
from services.export_service import export_to_excel
from datetime import datetime, date
from sqlalchemy import func, extract

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

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
    
    filepath = export_to_excel(report_type, site, start_date, end_date, month, year)
    
    return send_file(filepath, as_attachment=True, download_name=f'jtkidz_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
