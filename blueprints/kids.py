from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from models import Kid, User
from database import db
from blueprints.auth import login_required, admin_required
from services.barcode_service import generate_barcode
from datetime import datetime
from werkzeug.utils import secure_filename
import os

kids_bp = Blueprint('kids', __name__, url_prefix='/kids')

# Configuration for file uploads
UPLOAD_FOLDER = 'static/img/profiles'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@kids_bp.route('/')
@login_required
def list_kids():
    """List all kids with age group filtering"""
    site_filter = request.args.get('site', '')
    status_filter = request.args.get('status', 'active')
    age_group_filter = request.args.get('age_group', '')
    
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
    kids = query.order_by(Kid.full_name).all()
    
    # Filter by age group in Python
    if age_group_filter == 'kids':
        kids = [k for k in kids if 3 <= k.age <= 8]
    elif age_group_filter == 'risers':
        kids = [k for k in kids if 9 <= k.age <= 11]
    elif age_group_filter == 'teens':
        kids = [k for k in kids if 12 <= k.age <= 14]
    elif age_group_filter == 'other':
        kids = [k for k in kids if k.age < 3 or k.age > 14]
    
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
                          current_age_group=age_group_filter)

@kids_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add_kid():
    """Add new kid"""
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        birthday_str = request.form.get('birthday')
        gender = request.form.get('gender')
        site = request.form.get('site')
        
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
    """View all active barcodes for bulk printing"""
    kids = Kid.query.filter_by(status='active').order_by(Kid.site, Kid.full_name).all()
    return render_template('barcode_print.html', kids=kids, bulk=True)
