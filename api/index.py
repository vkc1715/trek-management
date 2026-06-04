import os
import sys

# Add the project root directory to the Python path so that imports work
# when running `python api/index.py` directly.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from flask import Flask, render_template
from flask_login import LoginManager
from models import db, User
from routes.main import main_bp
from config import Config
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp

def create_app(config_class=Config):
    app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static")
    app.config.from_object(config_class)

    # Ensure database and upload directories exist
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
        db.create_all()
        
        # Initialize database with default data
        from database.init_db import initialize_database
        initialize_database()

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
    app.run(debug=True,host='0.0.0.0',port=5000)
