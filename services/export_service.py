import pandas as pd
from models import Kid, Attendance, User
from database import db
from datetime import datetime
import os
import tempfile
from sqlalchemy import extract

def export_to_excel(report_type, site='', start_date='', end_date='', month='', year=''):
    """
    Export attendance data to Excel file
    
    Args:
        report_type: 'site' or 'monthly'
        site: Site filter
        start_date: Start date for site report
        end_date: End date for site report
        month: Month for monthly report
        year: Year for monthly report
    
    Returns:
        Path to generated Excel file
    """
    if report_type == 'monthly':
        return export_monthly_report(site, month, year)
    else:
        return export_site_report(site, start_date, end_date)

def export_site_report(site, start_date, end_date):
    """Export site/date filtered attendance report"""
    query = db.session.query(
        Kid.full_name,
        Kid.age,
        Kid.site,
        Kid.barcode,
        Attendance.scan_date,
        Attendance.scan_time,
        User.name.label('scanned_by')
    ).join(Attendance).join(User, Attendance.scanned_by == User.id)
    
    if site:
        query = query.filter(Kid.site == site)
    if start_date:
        query = query.filter(Attendance.scan_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(Attendance.scan_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    results = query.order_by(Attendance.scan_date.desc(), Attendance.scan_time.desc()).all()
    
    # Convert to DataFrame
    data = []
    for r in results:
        data.append({
            'Name': r.full_name,
            'Age': r.age,
            'Site': r.site,
            'Barcode': r.barcode,
            'Date': r.scan_date.strftime('%Y-%m-%d'),
            'Time': r.scan_time.strftime('%I:%M %p'),
            'Scanned By': r.scanned_by
        })
    
    df = pd.DataFrame(data)
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    
    # Write to Excel
    with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Attendance Report', index=False)
        
        # Auto-adjust column widths
        worksheet = writer.sheets['Attendance Report']
        for idx, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = max_length
    
    return temp_file.name

def export_monthly_report(site, month, year):
    """Export monthly attendance summary per child"""
    query = db.session.query(
        Kid.full_name,
        Kid.age,
        Kid.site,
        Kid.barcode,
        db.func.count(Attendance.id).label('attendance_count')
    ).outerjoin(Attendance,
        (Kid.id == Attendance.kid_id) &
        (extract('month', Attendance.scan_date) == int(month)) &
        (extract('year', Attendance.scan_date) == int(year))
    )
    
    if site:
        query = query.filter(Kid.site == site)
    
    query = query.filter(Kid.status == 'active')
    results = query.group_by(Kid.id).order_by(Kid.site, Kid.full_name).all()
    
    # Convert to DataFrame
    data = []
    month_name = datetime(int(year), int(month), 1).strftime('%B %Y')
    
    for r in results:
        data.append({
            'Name': r.full_name,
            'Age': r.age,
            'Site': r.site,
            'Barcode': r.barcode,
            f'Attendance Count ({month_name})': r.attendance_count
        })
    
    df = pd.DataFrame(data)
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    
    # Write to Excel
    with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Monthly Summary', index=False)
        
        # Auto-adjust column widths
        worksheet = writer.sheets['Monthly Summary']
        for idx, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = max_length
    
    return temp_file.name
