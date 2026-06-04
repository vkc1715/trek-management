from . import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='user') # Roles: admin, staff, user
    is_blacklisted = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=True) # False for pending staff
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assigned_treks = db.relationship('Trek', backref='staff', lazy=True)
    bookings = db.relationship('Booking', backref='user', lazy=True, cascade='all, delete-orphan')
    staff_applications = db.relationship('StaffApplication', foreign_keys='StaffApplication.user_id', backref='applicant', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
