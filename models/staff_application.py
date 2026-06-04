from . import db
from datetime import datetime

class StaffApplication(db.Model):
    __tablename__ = 'staff_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    motivation = db.Column(db.Text, nullable=False)
    trekking_experience = db.Column(db.Text, nullable=False)
    emergency_contact = db.Column(db.String(15), nullable=False)
    status = db.Column(db.String(20), default='Pending') # Pending, Approved, Rejected
    rejection_reason = db.Column(db.Text, nullable=True)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Optional relationships to reviewing admin, if needed
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref='reviewed_applications', lazy=True)
