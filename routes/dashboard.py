from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from utils.decorators import role_required
from models import db, Trek, Booking, User, StaffApplication
from datetime import datetime
from sqlalchemy import or_, func, extract, desc
import calendar

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    # Base Stats
    stats = {
        'total_treks': db.session.query(func.count(Trek.id)).scalar() or 0,
        'total_users': db.session.query(func.count(User.id)).filter_by(role='user').scalar() or 0,
        'total_staff': db.session.query(func.count(User.id)).filter_by(role='staff').scalar() or 0,
        'total_bookings': db.session.query(func.count(Booking.id)).scalar() or 0,
        'open_treks': db.session.query(func.count(Trek.id)).filter_by(status='Open').scalar() or 0,
        'completed_treks': db.session.query(func.count(Trek.id)).filter_by(status='Completed').scalar() or 0,
        'closed_treks': db.session.query(func.count(Trek.id)).filter_by(status='Closed').scalar() or 0,
    }
    
    # Active users (users with at least one booking)
    active_users_count = db.session.query(func.count(func.distinct(Booking.user_id))).scalar() or 0
    stats['active_users'] = active_users_count
    
    # Chart 1: Difficulty Distribution
    difficulty_data = db.session.query(Trek.difficulty, func.count(Trek.id)).group_by(Trek.difficulty).all()
    diff_labels = [d[0] for d in difficulty_data] if difficulty_data else []
    diff_counts = [d[1] for d in difficulty_data] if difficulty_data else []

    # Chart 2: Bookings per Trek (Top 5) & Popular Treks Leaderboard
    popular_treks = db.session.query(
        Trek.trek_name, 
        func.count(Booking.id).label('booking_count')
    ).join(Booking, Trek.id == Booking.trek_id).group_by(Trek.id).order_by(desc('booking_count')).limit(5).all()
    
    pop_labels = [t[0] for t in popular_treks] if popular_treks else []
    pop_counts = [t[1] for t in popular_treks] if popular_treks else []

    # Chart 3: Monthly Booking Trends (Current Year)
    current_year = datetime.now().year
    monthly_data = db.session.query(
        extract('month', Booking.booking_date).label('month'),
        func.count(Booking.id).label('count')
    ).filter(extract('year', Booking.booking_date) == current_year).group_by('month').all()
    
    # Fill missing months with 0
    month_dict = {int(m[0]): m[1] for m in monthly_data}
    monthly_labels = [calendar.month_abbr[i] for i in range(1, 13)]
    monthly_counts = [month_dict.get(i, 0) for i in range(1, 13)]

    # Staff Performance
    staff_performance = db.session.query(
        User.full_name,
        func.count(func.distinct(Trek.id)).label('assigned_count'),
        func.count(Booking.id).label('participant_count')
    ).filter(User.role == 'staff').outerjoin(Trek, Trek.assigned_staff_id == User.id)\
     .outerjoin(Booking, (Booking.trek_id == Trek.id) & (Booking.status == 'Booked'))\
     .group_by(User.id).order_by(desc('assigned_count')).all()

    # Insight snippets
    most_popular_location = db.session.query(Trek.location, func.count(Booking.id).label('c')).join(Booking).group_by(Trek.location).order_by(desc('c')).first()
    location_insight = most_popular_location[0] if most_popular_location else "N/A"

    charts_data = {
        'diff_labels': diff_labels, 'diff_counts': diff_counts,
        'pop_labels': pop_labels, 'pop_counts': pop_counts,
        'monthly_labels': monthly_labels, 'monthly_counts': monthly_counts
    }
    
    return render_template('dashboard/admin.html', 
                           stats=stats, 
                           charts_data=charts_data,
                           popular_treks=popular_treks,
                           staff_performance=staff_performance,
                           location_insight=location_insight)

@dashboard_bp.route('/admin/treks')
@login_required
@role_required('admin')
def admin_treks():
    search_query = request.args.get('search', '').strip()
    difficulty_filter = request.args.get('difficulty', '')
    status_filter = request.args.get('status', '')
    location_filter = request.args.get('location', '')
    
    query = Trek.query
    
    if search_query:
        query = query.filter(Trek.trek_name.ilike(f'%{search_query}%'))
    if difficulty_filter:
        query = query.filter(Trek.difficulty.ilike(difficulty_filter))
    if status_filter:
        query = query.filter(Trek.status.ilike(status_filter))
    if location_filter:
        query = query.filter(Trek.location.ilike(f'%{location_filter}%'))
        
    treks = query.order_by(Trek.created_at.desc()).all()
    
    return render_template('dashboard/admin_treks.html', treks=treks)

@dashboard_bp.route('/admin/treks/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_add_trek():
    staff_members = User.query.filter_by(role='staff', is_approved=True, is_blacklisted=False).all()
    
    if request.method == 'POST':
        try:
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
            
            if end_date <= start_date:
                flash('End date must be after start date.', 'danger')
                return redirect(url_for('dashboard.admin_add_trek'))
                
            available_slots = int(request.form.get('available_slots', 0))
            if available_slots < 0:
                flash('Available slots must be positive.', 'danger')
                return redirect(url_for('dashboard.admin_add_trek'))
                
            duration = int(request.form.get('duration_days', 0))
            if duration <= 0:
                flash('Duration must be positive.', 'danger')
                return redirect(url_for('dashboard.admin_add_trek'))
                
            staff_id = request.form.get('assigned_staff_id')
            assigned_staff_id = int(staff_id) if staff_id else None
            
            if assigned_staff_id:
                overlapping_trek = Trek.query.filter(
                    Trek.assigned_staff_id == assigned_staff_id,
                    Trek.start_date <= end_date,
                    Trek.end_date >= start_date
                ).first()
                if overlapping_trek:
                    flash('Selected staff is already assigned to an overlapping trek.', 'danger')
                    return redirect(url_for('dashboard.admin_add_trek'))
            
            new_trek = Trek(
                trek_name=request.form.get('trek_name').strip(),
                location=request.form.get('location').strip(),
                difficulty=request.form.get('difficulty'),
                duration_days=duration,
                available_slots=available_slots,
                description=request.form.get('description', '').strip(),
                status=request.form.get('status'),
                start_date=start_date,
                end_date=end_date,
                assigned_staff_id=assigned_staff_id,
                trek_image=request.form.get('trek_image', 'https://images.unsplash.com/photo-1551632811-561732d1e306?q=80&w=2070&auto=format&fit=crop').strip()
            )
            
            db.session.add(new_trek)
            db.session.commit()
            flash('Trek created successfully.', 'success')
            return redirect(url_for('dashboard.admin_treks'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please check your inputs.', 'danger')
            
    return render_template('dashboard/admin_trek_form.html', staff_members=staff_members, action='Create')

@dashboard_bp.route('/admin/treks/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_edit_trek(id):
    trek = Trek.query.get_or_404(id)
    staff_members = User.query.filter_by(role='staff', is_approved=True, is_blacklisted=False).all()
    
    if request.method == 'POST':
        try:
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
            
            if end_date <= start_date:
                flash('End date must be after start date.', 'danger')
                return redirect(url_for('dashboard.admin_edit_trek', id=id))
                
            available_slots = int(request.form.get('available_slots', 0))
            if available_slots < 0:
                flash('Available slots must be positive.', 'danger')
                return redirect(url_for('dashboard.admin_edit_trek', id=id))
                
            duration = int(request.form.get('duration_days', 0))
            if duration <= 0:
                flash('Duration must be positive.', 'danger')
                return redirect(url_for('dashboard.admin_edit_trek', id=id))
                
            staff_id = request.form.get('assigned_staff_id')
            assigned_staff_id = int(staff_id) if staff_id else None
            
            if assigned_staff_id:
                overlapping_trek = Trek.query.filter(
                    Trek.id != id,
                    Trek.assigned_staff_id == assigned_staff_id,
                    Trek.start_date <= end_date,
                    Trek.end_date >= start_date
                ).first()
                if overlapping_trek:
                    flash('Selected staff is already assigned to an overlapping trek.', 'danger')
                    return redirect(url_for('dashboard.admin_edit_trek', id=id))
            
            trek.trek_name = request.form.get('trek_name').strip()
            trek.location = request.form.get('location').strip()
            trek.difficulty = request.form.get('difficulty')
            trek.duration_days = duration
            trek.available_slots = available_slots
            trek.description = request.form.get('description', '').strip()
            trek.status = request.form.get('status')
            trek.start_date = start_date
            trek.end_date = end_date
            trek.assigned_staff_id = assigned_staff_id
            trek.trek_image = request.form.get('trek_image', trek.trek_image).strip()
            
            db.session.commit()
            flash('Trek updated successfully.', 'success')
            return redirect(url_for('dashboard.admin_treks'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please check your inputs.', 'danger')
            
    return render_template('dashboard/admin_trek_form.html', staff_members=staff_members, trek=trek, action='Edit')

@dashboard_bp.route('/admin/treks/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_trek(id):
    trek = Trek.query.get_or_404(id)
    try:
        db.session.delete(trek)
        db.session.commit()
        flash('Trek deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Cannot delete trek. It may have associated bookings.', 'danger')
    return redirect(url_for('dashboard.admin_treks'))

@dashboard_bp.route('/admin/users')
@login_required
@role_required('admin')
def admin_users():
    search_query = request.args.get('search', '').strip()
    
    query = User.query.filter_by(role='user')
    if search_query:
        query = query.filter(or_(
            User.full_name.ilike(f'%{search_query}%'),
            User.email.ilike(f'%{search_query}%'),
            User.phone.ilike(f'%{search_query}%')
        ))
        
    users = query.order_by(User.created_at.desc()).all()
    return render_template('dashboard/admin_users.html', users=users)

@dashboard_bp.route('/admin/users/<int:id>/toggle_blacklist', methods=['POST'])
@login_required
@role_required('admin')
def admin_toggle_user_blacklist(id):
    user = User.query.get_or_404(id)
    if user.role != 'user':
        flash('Invalid operation.', 'danger')
        return redirect(url_for('dashboard.admin_users'))
        
    user.is_blacklisted = not user.is_blacklisted
    db.session.commit()
    
    action = "blacklisted" if user.is_blacklisted else "reinstated"
    flash(f'User {user.full_name} has been {action}.', 'success')
    return redirect(url_for('dashboard.admin_users'))

@dashboard_bp.route('/admin/staff_applications')
@login_required
@role_required('admin')
def admin_staff_applications():
    search_query = request.args.get('search', '').strip()
    
    query = StaffApplication.query.join(User, StaffApplication.user_id == User.id)
    
    if search_query:
        query = query.filter(or_(
            User.full_name.ilike(f'%{search_query}%'),
            User.email.ilike(f'%{search_query}%')
        ))
        
    applications = query.order_by(StaffApplication.applied_at.desc()).all()
    
    pending = [app for app in applications if app.status == 'Pending']
    approved = [app for app in applications if app.status == 'Approved']
    rejected = [app for app in applications if app.status == 'Rejected']
    
    return render_template('dashboard/staff_applications.html', 
                           pending=pending, 
                           approved=approved, 
                           rejected=rejected,
                           search_query=search_query)

@dashboard_bp.route('/admin/staff_applications/<int:id>/approve', methods=['POST'])
@login_required
@role_required('admin')
def admin_approve_application(id):
    application = StaffApplication.query.get_or_404(id)
    
    application.status = 'Approved'
    application.reviewed_at = datetime.utcnow()
    application.reviewed_by = current_user.id
    
    # Update user role
    user = application.applicant
    user.role = 'staff'
    user.is_approved = True
    
    db.session.commit()
    flash(f'Application for {user.full_name} approved successfully.', 'success')
    return redirect(url_for('dashboard.admin_staff_applications'))

@dashboard_bp.route('/admin/staff_applications/<int:id>/reject', methods=['POST'])
@login_required
@role_required('admin')
def admin_reject_application(id):
    application = StaffApplication.query.get_or_404(id)
    rejection_reason = request.form.get('rejection_reason', '').strip()
    
    if len(rejection_reason) < 20:
        flash('Rejection reason must be at least 20 characters.', 'danger')
        return redirect(url_for('dashboard.admin_staff_applications'))
        
    application.status = 'Rejected'
    application.rejection_reason = rejection_reason
    application.reviewed_at = datetime.utcnow()
    application.reviewed_by = current_user.id
    
    db.session.commit()
    flash(f'Application rejected.', 'warning')
    return redirect(url_for('dashboard.admin_staff_applications'))

@dashboard_bp.route('/staff/dashboard')
@login_required
@role_required('staff')
def staff_dashboard():
    # Use aggregates to avoid fetching large lists just for counts
    stats = {
        'total_assigned': db.session.query(func.count(Trek.id)).filter_by(assigned_staff_id=current_user.id).scalar() or 0,
        'active_treks': db.session.query(func.count(Trek.id)).filter_by(assigned_staff_id=current_user.id, status='Open').scalar() or 0,
        'completed_treks': db.session.query(func.count(Trek.id)).filter_by(assigned_staff_id=current_user.id, status='Completed').scalar() or 0,
        'total_participants': db.session.query(func.count(Booking.id)).join(Trek).filter(
            Trek.assigned_staff_id == current_user.id,
            Booking.status == 'Booked'
        ).scalar() or 0
    }
    
    search_query = request.args.get('search', '').strip()
    difficulty_filter = request.args.get('difficulty', '')
    status_filter = request.args.get('status', '')
    
    query = Trek.query.filter_by(assigned_staff_id=current_user.id)
    
    if search_query:
        query = query.filter(Trek.trek_name.ilike(f'%{search_query}%'))
    if difficulty_filter:
        query = query.filter(Trek.difficulty.ilike(difficulty_filter))
    if status_filter:
        query = query.filter(Trek.status.ilike(status_filter))
        
    assigned_treks = query.order_by(Trek.start_date.asc()).all()
    
    return render_template('dashboard/staff.html', assigned_treks=assigned_treks, stats=stats)

@dashboard_bp.route('/staff/trek/<int:id>/update', methods=['POST'])
@login_required
@role_required('staff')
def staff_update_trek(id):
    trek = Trek.query.get_or_404(id)
    if trek.assigned_staff_id != current_user.id:
        flash('Unauthorized. You can only manage treks assigned to you.', 'danger')
        return redirect(url_for('dashboard.staff_dashboard'))
        
    try:
        new_status = request.form.get('status')
        new_slots = int(request.form.get('available_slots', trek.available_slots))
        
        if new_slots < 0:
            flash('Slots cannot be negative.', 'danger')
        elif new_status not in ['Pending', 'Open', 'Closed', 'Completed']:
            flash('Invalid status.', 'danger')
        else:
            trek.status = new_status
            trek.available_slots = new_slots
            db.session.commit()
            flash('Trek updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating trek.', 'danger')
        
    return redirect(url_for('dashboard.staff_dashboard'))

@dashboard_bp.route('/staff/trek/<int:id>/participants')
@login_required
@role_required('staff')
def staff_trek_participants(id):
    trek = Trek.query.get_or_404(id)
    if trek.assigned_staff_id != current_user.id:
        flash('Unauthorized to view this trek.', 'danger')
        return redirect(url_for('dashboard.staff_dashboard'))
        
    bookings = Booking.query.filter_by(trek_id=id, status='Booked').all()
    return render_template('dashboard/staff_participants.html', trek=trek, bookings=bookings)

@dashboard_bp.route('/user/dashboard')
@login_required
@role_required('user')
def user_dashboard():
    stats = {
        'total_bookings': db.session.query(func.count(Booking.id)).filter_by(user_id=current_user.id).scalar() or 0,
        'active_count': db.session.query(func.count(Booking.id)).filter_by(user_id=current_user.id, status='Booked').scalar() or 0,
        'cancelled_count': db.session.query(func.count(Booking.id)).filter_by(user_id=current_user.id, status='Cancelled').scalar() or 0,
        'completed_count': db.session.query(func.count(Booking.id)).join(Trek).filter(
            Booking.user_id == current_user.id,
            or_(Booking.status == 'Completed', Trek.status == 'Completed')
        ).scalar() or 0
    }
    
    # Fetch lists for rendering
    all_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    active_bookings = [b for b in all_bookings if b.status == 'Booked']
    past_bookings = [b for b in all_bookings if b.status in ['Completed', 'Cancelled'] or (b.trek and b.trek.status == 'Completed')]
    # Fetch latest staff application
    staff_application = StaffApplication.query.filter_by(user_id=current_user.id).order_by(StaffApplication.applied_at.desc()).first()
    
    return render_template('dashboard/user.html', 
                           active_bookings=active_bookings, 
                           past_bookings=past_bookings, 
                           stats=stats,
                           staff_application=staff_application)

@dashboard_bp.route('/user/apply_staff', methods=['POST'])
@login_required
@role_required('user')
def user_apply_staff():
    motivation = request.form.get('motivation', '').strip()
    experience = request.form.get('trekking_experience', '').strip()
    emergency_contact = request.form.get('emergency_contact', '').strip()
    
    # Validation
    if len(motivation) < 50 or len(motivation) > 500:
        flash('Motivation must be between 50 and 500 characters.', 'danger')
        return redirect(url_for('dashboard.user_dashboard'))
        
    if len(experience) < 20 or len(experience) > 1000:
        flash('Experience must be between 20 and 1000 characters.', 'danger')
        return redirect(url_for('dashboard.user_dashboard'))
        
    import re
    if not re.match(r'^\d{10}$', emergency_contact):
        flash('Emergency contact must be exactly 10 digits.', 'danger')
        return redirect(url_for('dashboard.user_dashboard'))
        
    # Check if a pending or approved application already exists
    existing = StaffApplication.query.filter_by(user_id=current_user.id).filter(StaffApplication.status.in_(['Pending', 'Approved'])).first()
    if existing:
        flash('You already have a pending or approved application.', 'warning')
        return redirect(url_for('dashboard.user_dashboard'))
        
    new_application = StaffApplication(
        user_id=current_user.id,
        motivation=motivation,
        trekking_experience=experience,
        emergency_contact=emergency_contact,
        status='Pending'
    )
    
    db.session.add(new_application)
    db.session.commit()
    flash('Your staff application has been submitted successfully.', 'success')
    return redirect(url_for('dashboard.user_dashboard'))

@dashboard_bp.route('/user/profile', methods=['GET', 'POST'])
@login_required
@role_required('user')
def user_profile():
    import re
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        
        if not re.match(r'^[A-Za-z\s]{3,40}$', full_name):
            flash('Invalid Name. Must be 3-40 characters, letters only.', 'danger')
            return redirect(url_for('dashboard.user_profile'))
            
        if not re.match(r'^\d{10}$', phone):
            flash('Invalid Phone. Must be exactly 10 digits.', 'danger')
            return redirect(url_for('dashboard.user_profile'))
            
        try:
            current_user.full_name = full_name
            current_user.phone = phone
            db.session.commit()
            flash('Profile updated successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error updating profile.', 'danger')
        return redirect(url_for('dashboard.user_profile'))
        
    return render_template('dashboard/profile.html')

@dashboard_bp.route('/admin/bookings')
@login_required
@role_required('admin')
def admin_bookings():
    bookings = Booking.query.order_by(Booking.booking_date.desc()).all()
    return render_template('dashboard/admin_bookings.html', bookings=bookings)
