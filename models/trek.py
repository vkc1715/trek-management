from . import db
from datetime import datetime

class Trek(db.Model):
    __tablename__ = 'treks'
    
    id = db.Column(db.Integer, primary_key=True)
    trek_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False) # Easy, Moderate, Hard
    duration_days = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    trek_image = db.Column(db.String(500), default='https://images.unsplash.com/photo-1551632811-561732d1e306?q=80&w=2070&auto=format&fit=crop')
    status = db.Column(db.String(20), default='Pending') # Pending, Approved, Open, Closed, Completed
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='trek', lazy=True, cascade='all, delete-orphan')
