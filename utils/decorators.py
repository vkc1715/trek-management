from functools import wraps
from flask import abort, redirect, url_for
from flask_login import current_user

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            # Immediately reject if the user is blacklisted
            if getattr(current_user, 'is_blacklisted', False):
                abort(403)
                
            if current_user.role != role:
                abort(403)
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator
