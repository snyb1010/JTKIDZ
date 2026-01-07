from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import Kid
from database import db
from blueprints.auth import login_required, admin_required
from services.barcode_service import generate_barcode

kids_bp = Blueprint('kids', __name__, url_prefix='/kids')

@kids_bp.route('/')
@login_required
def list_kids():
    """List all kids"""
    site_filter = request.args.get('site', '')
    status_filter = request.args.get('status', 'active')
    
    query = Kid.query
    
    if site_filter:
        query = query.filter_by(site=site_filter)
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    kids = query.order_by(Kid.full_name).all()
    sites = db.session.query(Kid.site).distinct().all()
    sites = [s[0] for s in sites]
    
    return render_template('kids_list.html', kids=kids, sites=sites, 
                          current_site=site_filter, current_status=status_filter)

@kids_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add_kid():
    """Add new kid"""
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        age = request.form.get('age')
        site = request.form.get('site')
        
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
            age=int(age),
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
        kid.age = int(request.form.get('age'))
        kid.site = request.form.get('site')
        kid.status = request.form.get('status')
        
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
