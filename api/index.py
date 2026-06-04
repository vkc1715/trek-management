import os
from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from models import db, User
from routes.main import main_bp
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    is_vercel = os.environ.get('VERCEL') == '1'

    # Local vs Deployed Behavior: 
    # Vercel provides a serverless environment with a read-only filesystem (in /var/task/).
    # We must not attempt to create folders or write SQLite files at runtime on Vercel.
    # For local development, we use SQLite normally and create the required folders.
    if not is_vercel:
        os.makedirs(os.path.join(app.root_path, 'database'), exist_ok=True)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)

    with app.app_context():
        # Do not attempt to initialize SQLite files or default data on Vercel.
        if not is_vercel:
            try:
                db.create_all()
                
                # Initialize database with default data
                from database.init_db import initialize_database
                initialize_database()
            except Exception as e:
                # Ensure application fails gracefully with a clear error message if SQLite is unavailable.
                print(f"CRITICAL ERROR: Failed to initialize SQLite database. Local database access is unavailable. Details: {e}")
        else:
            # If on Vercel and using SQLite, it will likely fail on read/write operations later, 
            # so we log a clear message here as a warning.
            if app.config.get('SQLALCHEMY_DATABASE_URI', '').startswith('sqlite'):
                print("WARNING: Application is running on Vercel with SQLite. Writes will fail because Vercel filesystem is read-only. Configure a cloud database instead.")

    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
