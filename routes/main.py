from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from models import db, Trek, Booking

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    featured_treks = Trek.query.filter_by(status='Open').limit(3).all()
    return render_template('index.html', featured_treks=featured_treks)

@main_bp.route('/treks')
def explore():
    search_query = request.args.get('search', '').strip()
    difficulty_filter = request.args.get('difficulty', '')
    location_filter = request.args.get('location', '')
    status_filter = request.args.get('status', '')
    
    query = Trek.query
    
    if search_query:
        query = query.filter(Trek.trek_name.ilike(f'%{search_query}%'))
    if difficulty_filter:
        query = query.filter(Trek.difficulty.ilike(difficulty_filter))
    if location_filter:
        query = query.filter(Trek.location.ilike(f'%{location_filter}%'))
    if status_filter:
        query = query.filter(Trek.status.ilike(status_filter))
    
    # If no status filter is explicitly set, we default to showing all public statuses
    if not status_filter:
        query = query.filter(Trek.status.in_(['Open', 'Closed', 'Completed']))
        
    treks = query.order_by(Trek.start_date.asc()).all()
    return render_template('explore.html', treks=treks)

@main_bp.route('/trek/<int:id>')
def trek_details(id):
    trek = Trek.query.get_or_404(id)
    return render_template('trek_details.html', trek=trek)

@main_bp.route('/book/<int:trek_id>', methods=['POST'])
@login_required
def book_trek(trek_id):
    if current_user.role != 'user':
        flash('Only standard users can book treks.', 'danger')
        return redirect(url_for('main.trek_details', id=trek_id))
        
    if current_user.is_blacklisted:
        flash('Your account is currently restricted from booking.', 'danger')
        return redirect(url_for('main.trek_details', id=trek_id))
        
    trek = Trek.query.get_or_404(trek_id)
    
    if trek.status != 'Open':
        flash('This trek is not currently open for booking.', 'warning')
        return redirect(url_for('main.trek_details', id=trek_id))
        
    if trek.available_slots <= 0:
        flash('Sorry, this trek is fully booked.', 'danger')
        return redirect(url_for('main.trek_details', id=trek_id))
        
    existing_booking = Booking.query.filter_by(user_id=current_user.id, trek_id=trek_id, status='Booked').first()
    if existing_booking:
        flash('You have already booked this trek.', 'warning')
        return redirect(url_for('dashboard.user_dashboard'))
        
    try:
        new_booking = Booking(user_id=current_user.id, trek_id=trek_id, status='Booked')
        trek.available_slots -= 1
        db.session.add(new_booking)
        db.session.commit()
        flash('Booking successful! Get ready for your adventure.', 'success')
        return redirect(url_for('dashboard.user_dashboard'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while booking. Please try again.', 'danger')
        return redirect(url_for('main.trek_details', id=trek_id))

@main_bp.route('/cancel/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    if current_user.role != 'user':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('main.index'))
        
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.user_id != current_user.id:
        flash('You can only cancel your own bookings.', 'danger')
        return redirect(url_for('dashboard.user_dashboard'))
        
    if booking.status != 'Booked':
        flash('This booking is not active.', 'warning')
        return redirect(url_for('dashboard.user_dashboard'))
        
    try:
        booking.status = 'Cancelled'
        if booking.trek:
            booking.trek.available_slots += 1
        db.session.commit()
        flash('Your booking has been cancelled.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred during cancellation.', 'danger')
        
    return redirect(url_for('dashboard.user_dashboard'))
