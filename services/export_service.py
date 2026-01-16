import pandas as pd
from models import Kid, Attendance, User
from database import db
from datetime import datetime
import os
import tempfile
from sqlalchemy import extract

def export_to_excel(report_type, site='', start_date='', end_date='', month='', year='', lesson=''):
    """
    Export attendance data to Excel file
    
    Args:
        report_type: 'site', 'monthly', or 'lesson'
        site: Site filter
        start_date: Start date for site report
        end_date: End date for site report
        month: Month for monthly report
        year: Year for monthly report
        lesson: Lesson number for lesson report
    
    Returns:
        Path to generated Excel file
    """
    if report_type == 'monthly':
        return export_monthly_report(site, month, year)
    elif report_type == 'lesson':
        return export_lesson_report(site, lesson)
    else:
        return export_site_report(site, start_date, end_date)

def get_age_group(age):
    """Return age group category"""
    if 3 <= age <= 8:
        return 'Kids (3-8)'
    elif 9 <= age <= 11:
        return 'Risers (9-11)'
    elif 12 <= age <= 14:
        return 'Teens (12-14)'
    else:
        return 'Other'

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
    ).join(Attendance, Kid.id == Attendance.kid_id).join(User, Attendance.scanned_by == User.id)
    
    if site:
        query = query.filter(Kid.site == site)
    if start_date:
        query = query.filter(Attendance.scan_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(Attendance.scan_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    results = query.order_by(Attendance.scan_date.desc(), Attendance.scan_time.desc()).all()
    
    # Convert to DataFrame with age groups
    data = []
    for r in results:
        data.append({
            'Name': r.full_name,
            'Age': r.age,
            'Age Group': get_age_group(r.age),
            'Site': r.site,
            'Barcode': r.barcode,
            'Date': r.scan_date.strftime('%Y-%m-%d'),
            'Time': r.scan_time.strftime('%I:%M %p'),
            'Scanned By': r.scanned_by
        })
    
    df = pd.DataFrame(data)
    
    if df.empty:
        # Create empty DataFrame with headers
        df = pd.DataFrame(columns=['Name', 'Age', 'Age Group', 'Site', 'Barcode', 'Date', 'Time', 'Scanned By'])
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    
    # Write to Excel with formatting
    with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Attendance Report', index=False)
        
        # Auto-adjust column widths
        worksheet = writer.sheets['Attendance Report']
        for idx, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2 if len(df) > 0 else len(col) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = max_length
    
    return temp_file.name

def export_monthly_report(site, month, year):
    """Export monthly attendance summary per child with age groups"""
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
    
    # Convert to DataFrame with age groups
    data = []
    month_name = datetime(int(year), int(month), 1).strftime('%B %Y')
    
    for r in results:
        data.append({
            'Name': r.full_name,
            'Age': r.age,
            'Age Group': get_age_group(r.age),
            'Site': r.site,
            'Barcode': r.barcode,
            f'Attendance Count ({month_name})': r.attendance_count
        })
    
    df = pd.DataFrame(data)
    
    if df.empty:
        # Create empty DataFrame with headers
        df = pd.DataFrame(columns=['Name', 'Age', 'Age Group', 'Site', 'Barcode', f'Attendance Count ({month_name})'])
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    
    # Write to Excel with separate sheets by age group
    with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
        # All data sheet
        df.to_excel(writer, sheet_name='All', index=False)
        
        # Separate sheets by age group
        if not df.empty:
            for age_group in ['Kids (3-8)', 'Risers (9-11)', 'Teens (12-14)', 'Other']:
                group_df = df[df['Age Group'] == age_group]
                if not group_df.empty:
                    group_df.to_excel(writer, sheet_name=age_group, index=False)
        
        # Auto-adjust column widths for all sheets
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for idx, col in enumerate(df.columns):
                max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2 if len(df) > 0 else len(col) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = max_length
    
    return temp_file.name

def export_lesson_report(site, lesson):
    """Export lesson-based attendance report"""
    query = db.session.query(
        Kid.full_name,
        Kid.age,
        Kid.site,
        Kid.barcode,
        Attendance.lesson,
        Attendance.scan_date,
        Attendance.scan_time,
        User.name.label('scanned_by')
    ).join(Attendance, Kid.id == Attendance.kid_id).join(User, Attendance.scanned_by == User.id)
    
    if site:
        query = query.filter(Kid.site == site)
    if lesson:
        query = query.filter(Attendance.lesson == int(lesson))
    
    results = query.order_by(Attendance.lesson, Kid.site, Kid.full_name).all()
    
    # Convert to DataFrame
    data = []
    for r in results:
        data.append({
            'Lesson': f'Lesson {r.lesson}',
            'Name': r.full_name,
            'Age': r.age,
            'Age Group': get_age_group(r.age),
            'Site': r.site,
            'Barcode': r.barcode,
            'Date': r.scan_date.strftime('%Y-%m-%d'),
            'Time': r.scan_time.strftime('%I:%M %p'),
            'Scanned By': r.scanned_by
        })
    
    df = pd.DataFrame(data)
    
    if df.empty:
        df = pd.DataFrame(columns=['Lesson', 'Name', 'Age', 'Age Group', 'Site', 'Barcode', 'Date', 'Time', 'Scanned By'])
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    
    # Write to Excel with separate sheets per lesson
    with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
        # All data sheet
        df.to_excel(writer, sheet_name='All Lessons', index=False)
        
        # Separate sheets by lesson if not filtering
        if not lesson and not df.empty:
            for lesson_num in range(1, 7):
                lesson_df = df[df['Lesson'] == f'Lesson {lesson_num}']
                if not lesson_df.empty:
                    lesson_df.to_excel(writer, sheet_name=f'Lesson {lesson_num}', index=False)
        
        # Auto-adjust column widths
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for idx, col in enumerate(df.columns):
                max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2 if len(df) > 0 else len(col) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = max_length
    
    return temp_file.name
