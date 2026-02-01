from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import User, Kid
from database import db
from blueprints.auth import admin_required

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/')
@admin_required
def list_users():
    """List all users (admin and staff)"""
    users = User.query.order_by(User.role.desc(), User.name).all()  # Admin first, then staff
    
    # Parse assigned sites for display
    for user in users:
        user.sites_list = user.get_assigned_sites()
    
    return render_template('users_list.html', users=users)

@users_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    """Add new staff user"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        assigned_sites = request.form.getlist('sites')  # Multiple sites
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'error')
            return redirect(url_for('users.add_user'))
        
        # Create new user
        user = User(name=name, email=email, role='staff')
        user.set_password(password)
        user.set_assigned_sites(assigned_sites)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Worker {name} added successfully!', 'success')
        return redirect(url_for('users.list_users'))
    
    # Get all available sites
    sites = db.session.query(Kid.site).distinct().order_by(Kid.site).all()
    sites = [s[0] for s in sites]
    
    return render_template('user_form.html', sites=sites, user=None)

@users_bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Edit staff user"""
    user = User.query.get_or_404(user_id)
    
    if user.role == 'admin':
        flash('Cannot edit admin user!', 'error')
        return redirect(url_for('users.list_users'))
    
    if request.method == 'POST':
        user.name = request.form.get('name')
        user.email = request.form.get('email')
        password = request.form.get('password')
        assigned_sites = request.form.getlist('sites')
        
        # Update password if provided
        if password:
            user.set_password(password)
        
        user.set_assigned_sites(assigned_sites)
        
        db.session.commit()
        flash(f'Worker {user.name} updated successfully!', 'success')
        return redirect(url_for('users.list_users'))
    
    # Get all available sites
    sites = db.session.query(Kid.site).distinct().order_by(Kid.site).all()
    sites = [s[0] for s in sites]
    
    return render_template('user_form.html', sites=sites, user=user)

@users_bp.route('/delete/<int:user_id>')
@admin_required
def delete_user(user_id):
    """Delete staff user"""
    user = User.query.get_or_404(user_id)
    
    if user.role == 'admin':
        flash('Cannot delete admin user!', 'error')
        return redirect(url_for('users.list_users'))
    
    name = user.name
    db.session.delete(user)
    db.session.commit()
    
    flash(f'Worker {name} deleted successfully!', 'success')
    return redirect(url_for('users.list_users'))
