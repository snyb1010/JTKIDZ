from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from models import Kid, User
from database import db
from blueprints.auth import login_required, admin_required
from services.barcode_service import generate_barcode
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import pandas as pd
import tempfile
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO

kids_bp = Blueprint('kids', __name__, url_prefix='/kids')

# Configuration for file uploads
UPLOAD_FOLDER = 'static/img/profiles'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_EXCEL_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_excel_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXCEL_EXTENSIONS

@kids_bp.route('/')
@login_required
def list_kids():
    """List all kids with age group filtering"""
    site_filter = request.args.get('site', '')
    status_filter = request.args.get('status', 'active')
    age_group_filter = request.args.get('age_group', '')
    sort_by = request.args.get('sort', 'name')  # New: sort parameter
    
    # Get current user and their site access
    current_user = User.query.get(session['user_id'])
    
    query = Kid.query
    
    # Filter by staff's assigned sites (staff can only see their sites)
    if current_user.role == 'staff':
        assigned_sites = current_user.get_assigned_sites()
        if assigned_sites:
            query = query.filter(Kid.site.in_(assigned_sites))
        else:
            # Staff with no assigned sites sees nothing
            query = query.filter(Kid.id == -1)
    
    if site_filter:
        query = query.filter_by(site=site_filter)
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    # Get all kids first (can't filter by age property in SQL)
    kids = query.all()
    
    # Filter by age group in Python
    if age_group_filter == 'kids':
        kids = [k for k in kids if 3 <= k.age <= 8]
    elif age_group_filter == 'risers':
        kids = [k for k in kids if 9 <= k.age <= 11]
    elif age_group_filter == 'teens':
        kids = [k for k in kids if 12 <= k.age <= 13]
    elif age_group_filter == 'youth':
        kids = [k for k in kids if k.age >= 14]
    elif age_group_filter == 'other':
        kids = [k for k in kids if k.age < 3]
    
    # Sort kids based on parameter
    if sort_by == 'barcode':
        kids = sorted(kids, key=lambda k: k.barcode)
    elif sort_by == 'gender':
        kids = sorted(kids, key=lambda k: (k.gender or 'ZZZ', k.full_name))  # Gender then name
    else:  # default: sort by name
        kids = sorted(kids, key=lambda k: k.full_name)
    
    # Get sites based on user role
    if current_user.role == 'admin':
        sites = db.session.query(Kid.site).distinct().order_by(Kid.site).all()
    else:
        # Staff only sees their assigned sites
        assigned_sites = current_user.get_assigned_sites()
        sites = [(s,) for s in assigned_sites]
    
    sites = [s[0] for s in sites]
    
    return render_template('kids_list.html', kids=kids, sites=sites, 
                          current_site=site_filter, current_status=status_filter,
                          current_age_group=age_group_filter, current_sort=sort_by)

@kids_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add_kid():
    """Add new kid"""
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        birthday_str = request.form.get('birthday')
        gender = request.form.get('gender')
        site = request.form.get('site')
        
        # Validate required fields
        if not full_name or not birthday_str or not gender or not site:
            flash('Please fill in all required fields', 'danger')
            return render_template('kid_form.html', kid=None)
        
        # Parse birthday
        birthday = None
        if birthday_str:
            try:
                birthday = datetime.strptime(birthday_str, '%Y-%m-%d').date()
            except:
                flash('Invalid birthday format', 'danger')
                return render_template('kid_form.html', kid=None)
        
        # Handle profile picture upload
        profile_pic = None
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Create unique filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                name_part = secure_filename(full_name.replace(' ', '_'))
                ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{name_part}_{timestamp}.{ext}"
                
                # Ensure upload folder exists
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                
                file.save(os.path.join(UPLOAD_FOLDER, unique_filename))
                profile_pic = unique_filename
        
        # Generate unique barcode
        last_kid = Kid.query.order_by(Kid.id.desc()).first()
        next_id = (last_kid.id + 1) if last_kid else 1
        barcode = f'JT{next_id:06d}'
        
        # Check if barcode already exists
        while Kid.query.filter_by(barcode=barcode).first():
            next_id += 1
            barcode = f'JT{next_id:06d}'
        
        kid = Kid(
            full_name=full_name,
            birthday=birthday,
            gender=gender,
            profile_pic=profile_pic,
            site=site,
            barcode=barcode,
            status='active'
        )
        
        db.session.add(kid)
        db.session.commit()
        
        # Generate barcode image
        generate_barcode(kid.barcode, kid.full_name)
        
        flash(f'Kid {full_name} added successfully! Barcode: {barcode}', 'success')
        return redirect(url_for('kids.list_kids'))
    
    return render_template('kid_form.html', kid=None)

@kids_bp.route('/edit/<int:kid_id>', methods=['GET', 'POST'])
@admin_required
def edit_kid(kid_id):
    """Edit existing kid"""
    kid = Kid.query.get_or_404(kid_id)
    
    if request.method == 'POST':
        kid.full_name = request.form.get('full_name')
        
        # Update birthday
        birthday_str = request.form.get('birthday')
        if birthday_str:
            try:
                kid.birthday = datetime.strptime(birthday_str, '%Y-%m-%d').date()
            except:
                flash('Invalid birthday format', 'danger')
                return render_template('kid_form.html', kid=kid)
        
        kid.gender = request.form.get('gender')
        kid.site = request.form.get('site')
        kid.status = request.form.get('status')
        
        # Handle profile picture upload
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename and allowed_file(file.filename):
                # Delete old picture if exists
                if kid.profile_pic:
                    old_pic_path = os.path.join(UPLOAD_FOLDER, kid.profile_pic)
                    if os.path.exists(old_pic_path):
                        os.remove(old_pic_path)
                
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                name_part = secure_filename(kid.full_name.replace(' ', '_'))
                ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{name_part}_{timestamp}.{ext}"
                
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                file.save(os.path.join(UPLOAD_FOLDER, unique_filename))
                kid.profile_pic = unique_filename
        
        db.session.commit()
        flash(f'Kid {kid.full_name} updated successfully!', 'success')
        return redirect(url_for('kids.list_kids'))
    
    return render_template('kid_form.html', kid=kid)

@kids_bp.route('/deactivate/<int:kid_id>')
@admin_required
def deactivate_kid(kid_id):
    """Deactivate a kid"""
    kid = Kid.query.get_or_404(kid_id)
    kid.status = 'inactive'
    db.session.commit()
    flash(f'{kid.full_name} has been deactivated.', 'info')
    return redirect(url_for('kids.list_kids'))

@kids_bp.route('/activate/<int:kid_id>')
@admin_required
def activate_kid(kid_id):
    """Activate a kid"""
    kid = Kid.query.get_or_404(kid_id)
    kid.status = 'active'
    db.session.commit()
    flash(f'{kid.full_name} has been activated.', 'success')
    return redirect(url_for('kids.list_kids'))

@kids_bp.route('/barcode/<int:kid_id>')
@login_required
def view_barcode(kid_id):
    """View barcode for printing"""
    kid = Kid.query.get_or_404(kid_id)
    return render_template('barcode_print.html', kid=kid)

@kids_bp.route('/barcodes/bulk')
@admin_required
def bulk_barcodes():
    """View all active barcodes for bulk printing with sorting options"""
    sort_by = request.args.get('sort', 'site')
    site_filter = request.args.get('site', '')
    
    query = Kid.query.filter_by(status='active')
    
    # Filter by site if specified
    if site_filter:
        query = query.filter_by(site=site_filter)
    
    kids = query.all()
    
    # Sort kids based on parameter
    if sort_by == 'barcode':
        kids = sorted(kids, key=lambda k: k.barcode)
    elif sort_by == 'gender':
        kids = sorted(kids, key=lambda k: (k.gender or 'ZZZ', k.full_name))
    elif sort_by == 'age':
        kids = sorted(kids, key=lambda k: (k.age, k.full_name))
    else:  # default: name
        kids = sorted(kids, key=lambda k: k.full_name)
    
    # Get all sites for filter dropdown
    sites = db.session.query(Kid.site).distinct().order_by(Kid.site).all()
    sites = [s[0] for s in sites]
    
    return render_template('barcode_print.html', kids=kids, bulk=True, 
                          current_sort=sort_by, sites=sites, current_site=site_filter)

@kids_bp.route('/barcodes/export-pdf')
@admin_required
def export_barcodes_pdf():
    """Export barcodes to PDF based on current sorting/filtering"""
    from flask import current_app
    
    sort_by = request.args.get('sort', 'site')
    site_filter = request.args.get('site', '')
    
    query = Kid.query.filter_by(status='active')
    
    # Filter by site if specified
    if site_filter:
        query = query.filter_by(site=site_filter)
    
    kids = query.all()
    
    # Sort kids based on parameter
    if sort_by == 'barcode':
        kids = sorted(kids, key=lambda k: k.barcode)
    elif sort_by == 'gender':
        kids = sorted(kids, key=lambda k: (k.gender or 'ZZZ', k.full_name))
    elif sort_by == 'age':
        kids = sorted(kids, key=lambda k: (k.age, k.full_name))
    else:  # default: name
        kids = sorted(kids, key=lambda k: k.full_name)
    
    # Create PDF in memory
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Set up layout (3 columns, multiple rows)
    card_width = 2.5 * inch
    card_height = 3 * inch
    margin = 0.5 * inch
    cols = 3
    
    x_positions = [margin, margin + card_width, margin + 2 * card_width]
    y_start = height - margin - card_height
    
    current_x_idx = 0
    current_y = y_start
    
    # Logo path - use absolute path from Flask app root
    logo_path = os.path.join(current_app.root_path, 'static', 'img', 'logo.png')
    
    for kid in kids:
        x = x_positions[current_x_idx]
        y = current_y
        
        # Draw background color based on gender
        if kid.gender == 'Male':
            pdf.setFillColorRGB(0.38, 0.65, 0.96)  # Royal blue
        elif kid.gender == 'Female':
            pdf.setFillColorRGB(0.96, 0.45, 0.71)  # Royal pink
        else:
            pdf.setFillColorRGB(1, 1, 1)  # White
        
        pdf.rect(x, y, card_width, card_height, fill=1, stroke=1)
        
        # Draw logo if exists
        if os.path.exists(logo_path):
            try:
                pdf.drawImage(logo_path, x + card_width/2 - 0.4*inch, y + card_height - 0.6*inch, 
                            width=0.8*inch, height=0.4*inch, preserveAspectRatio=True, mask='auto')
            except Exception as e:
                print(f"Logo error: {e}")
        
        # Draw kid name (black text)
        pdf.setFillColorRGB(0, 0, 0)
        pdf.setFont("Helvetica-Bold", 12)
        text_width = pdf.stringWidth(kid.full_name, "Helvetica-Bold", 12)
        pdf.drawString(x + (card_width - text_width)/2, y + card_height - 0.9*inch, kid.full_name)
        
        # Draw site, age, gender info
        pdf.setFont("Helvetica", 9)
        info_text = f"{kid.site} • Age {kid.age} • {kid.gender}"
        text_width = pdf.stringWidth(info_text, "Helvetica", 9)
        pdf.drawString(x + (card_width - text_width)/2, y + card_height - 1.15*inch, info_text)
        
        # Draw barcode image if exists - use absolute path
        barcode_filename = f"{kid.barcode}_{kid.full_name.replace(' ', '_')}.png"
        barcode_path = os.path.join(current_app.root_path, 'static', 'img', 'barcodes', barcode_filename)
        
        if os.path.exists(barcode_path):
            try:
                pdf.drawImage(barcode_path, x + 0.25*inch, y + 0.8*inch,
                            width=2*inch, height=1*inch, preserveAspectRatio=True, mask='auto')
            except Exception as e:
                print(f"Barcode error for {kid.barcode}: {e}")
                pdf.setFont("Helvetica", 8)
                pdf.drawString(x + 0.5*inch, y + 1.3*inch, "Barcode error")
        else:
            pdf.setFont("Helvetica", 8)
            pdf.drawString(x + 0.5*inch, y + 1.3*inch, "Barcode not generated")
                            width=2*inch, height=1*inch, preserveAspectRatio=True, mask='auto')
            except:
                pdf.setFont("Helvetica", 8)
                pdf.drawString(x + 0.5*inch, y + 1.3*inch, "Barcode not generated")
        
        # Draw barcode number
        pdf.setFont("Courier-Bold", 10)
        text_width = pdf.stringWidth(kid.barcode, "Courier-Bold", 10)
        pdf.drawString(x + (card_width - text_width)/2, y + 0.5*inch, kid.barcode)
        
        # Move to next position
        current_x_idx += 1
        if current_x_idx >= cols:
            current_x_idx = 0
            current_y -= card_height
            
            # Check if we need a new page
            if current_y < margin:
                pdf.showPage()
                current_y = y_start
    
    # Save PDF
    pdf.save()
    buffer.seek(0)
    
    # Generate filename
    filename = f"JT_KIDZ_Barcodes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    if site_filter:
        filename = f"JT_KIDZ_Barcodes_{site_filter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=filename)

@kids_bp.route('/bulk-import', methods=['GET', 'POST'])
@admin_required
def bulk_import():
    """Bulk import kids from Excel file"""
    if request.method == 'POST':
        if 'excel_file' not in request.files:
            flash('No file uploaded', 'danger')
            return redirect(request.url)
        
        file = request.files['excel_file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        if not allowed_excel_file(file.filename):
            flash('Invalid file type. Please upload .xlsx or .xls file', 'danger')
            return redirect(request.url)
        
        try:
            # Read Excel file
            df = pd.read_excel(file)
            
            # Validate required columns
            required_columns = ['full_name', 'birthday', 'gender', 'site']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                flash(f'Missing required columns: {", ".join(missing_columns)}', 'danger')
                return redirect(request.url)
            
            # Process each row
            success_count = 0
            error_rows = []
            
            for index, row in df.iterrows():
                try:
                    # Validate required fields
                    if pd.isna(row['full_name']) or pd.isna(row['birthday']) or pd.isna(row['gender']) or pd.isna(row['site']):
                        error_rows.append(f"Row {index + 2}: Missing required data")
                        continue
                    
                    # Parse birthday
                    if isinstance(row['birthday'], str):
                        birthday = datetime.strptime(row['birthday'], '%Y-%m-%d').date()
                    else:
                        birthday = row['birthday'].date() if hasattr(row['birthday'], 'date') else row['birthday']
                    
                    # Generate unique barcode
                    last_kid = Kid.query.order_by(Kid.id.desc()).first()
                    next_id = (last_kid.id + 1) if last_kid else 1
                    barcode = f'JT{next_id:06d}'
                    
                    while Kid.query.filter_by(barcode=barcode).first():
                        next_id += 1
                        barcode = f'JT{next_id:06d}'
                    
                    # Create kid
                    kid = Kid(
                        full_name=str(row['full_name']).strip(),
                        birthday=birthday,
                        gender=str(row['gender']).strip(),
                        site=str(row['site']).strip(),
                        barcode=barcode,
                        status='active'
                    )
                    
                    db.session.add(kid)
                    db.session.flush()  # Get the kid.id
                    
                    # Generate barcode image
                    generate_barcode(kid.barcode, kid.full_name)
                    
                    success_count += 1
                    
                except Exception as e:
                    error_rows.append(f"Row {index + 2}: {str(e)}")
                    continue
            
            db.session.commit()
            
            # Show results
            if success_count > 0:
                flash(f'Successfully imported {success_count} kids!', 'success')
            if error_rows:
                flash(f'Errors: {"; ".join(error_rows[:5])}', 'warning')
            
            return redirect(url_for('kids.list_kids'))
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'danger')
            return redirect(request.url)
    
    return render_template('kids_bulk_import.html')

@kids_bp.route('/bulk-import/template')
@admin_required
def download_template():
    """Download Excel template for bulk import"""
    # Create sample Excel file
    data = {
        'full_name': ['Juan Dela Cruz', 'Maria Santos'],
        'birthday': ['2015-01-15', '2016-06-20'],
        'gender': ['Male', 'Female'],
        'site': ['Barangay San Pedro', 'Barangay Tagburos']
    }
    
    df = pd.DataFrame(data)
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    df.to_excel(temp_file.name, index=False, engine='openpyxl')
    
    return send_file(temp_file.name, 
                    as_attachment=True, 
                    download_name='jtkidz_import_template.xlsx',
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

