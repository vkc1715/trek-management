from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models so they are registered with SQLAlchemy
from .user import User
from .trek import Trek
from .booking import Booking
from .staff_application import StaffApplication
