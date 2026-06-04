import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_by_role(current_user.role)
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if user.is_blacklisted:
                flash('Your account has been suspended. Please contact support.', 'danger')
                return redirect(url_for('auth.login'))
                
            if user.role == 'staff' and not user.is_approved:
                flash('Your staff account is pending admin approval.', 'warning')
                return redirect(url_for('auth.login'))
                
            login_user(user)
            flash('Login successful!', 'success')
            return redirect_by_role(user.role)
        else:
            flash('Invalid email or password.', 'danger')
            
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect_by_role(current_user.role)
        
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        role = 'user' # Always default to user for new registrations
        
        # Backend Validation
        if not re.match(r'^[A-Za-z\s]{3,40}$', full_name):
            flash('Invalid Name. Must be 3-40 characters, letters only.', 'danger')
            return redirect(url_for('auth.register'))
            
        if not re.match(r'^\d{10}$', phone):
            flash('Invalid Phone. Must be exactly 10 digits.', 'danger')
            return redirect(url_for('auth.register'))
            
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email) or len(email) > 120:
            flash('Invalid Email format.', 'danger')
            return redirect(url_for('auth.register'))
            
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d\w\W]{8,30}$', password):
            flash('Invalid Password. Requires 8-30 chars, uppercase, lowercase, and number.', 'danger')
            return redirect(url_for('auth.register'))

        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email already registered. Please login.', 'warning')
            return redirect(url_for('auth.login'))
            
        new_user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            role=role,
            is_approved=True
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

def redirect_by_role(role):
    if role == 'admin':
        return redirect(url_for('dashboard.admin_dashboard'))
    elif role == 'staff':
        return redirect(url_for('dashboard.staff_dashboard'))
    return redirect(url_for('dashboard.user_dashboard'))
