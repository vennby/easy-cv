import os
from os import path
from flask import Flask
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime

load_dotenv()

db = SQLAlchemy()
DB_NAME = "database.db"

def fmt_month_year(date_str):
    """Format date string (YYYY-MM-DD or YYYY-MM or YYYY) to 'Mon YYYY' format."""
    if not date_str:
        return ""
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(str(date_str), fmt).strftime("%b %Y")
        except (ValueError, TypeError):
            continue
    return str(date_str)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('PROD_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    db.init_app(app)
    
    from .views import views
    from .auth import auth
    
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    
    from .models import User, Skills
    
    create_database(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.sign_in'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    # Register custom Jinja filter
    app.jinja_env.filters['fmt_month_year'] = fmt_month_year
    
    return app

def create_database(app):
    if not path.exists('instance/' + DB_NAME):
        with app.app_context():
            db.create_all()
            print('Created Database!')
