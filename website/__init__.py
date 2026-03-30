import os
from os import path
from flask import Flask
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime
from sqlalchemy import text
from sqlalchemy import inspect

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
    app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
    app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')
    app.config['GOOGLE_REDIRECT_URI'] = os.environ.get('GOOGLE_REDIRECT_URI')
    app.config['GITHUB_API_TOKEN'] = os.environ.get('GITHUB_API_TOKEN')
    db.init_app(app)
    
    from .views import views
    from .auth import auth, init_oauth
    
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    init_oauth(app)
    
    from .models import User, Skills
    
    create_database(app)
    migrate_schema(app)
    
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


def migrate_schema(app):
    with app.app_context():
        dialect = db.engine.dialect.name
        if dialect == 'postgresql':
            statements = [
                'ALTER TABLE "user" ALTER COLUMN username TYPE TEXT',
                'ALTER TABLE "user" ALTER COLUMN password TYPE TEXT',
                'ALTER TABLE "user" ALTER COLUMN first_name TYPE TEXT',
                'ALTER TABLE personal_info ALTER COLUMN full_name TYPE TEXT',
                'ALTER TABLE personal_info ALTER COLUMN email TYPE TEXT',
                'ALTER TABLE personal_info ALTER COLUMN phone TYPE TEXT',
                'ALTER TABLE personal_info ALTER COLUMN address TYPE TEXT',
                'ALTER TABLE personal_info ALTER COLUMN linkedin TYPE TEXT',
                'ALTER TABLE personal_info ALTER COLUMN github TYPE TEXT',
                'ALTER TABLE personal_info ALTER COLUMN website TYPE TEXT',
                'ALTER TABLE resume ALTER COLUMN name TYPE TEXT',
                'ALTER TABLE bios ALTER COLUMN bio TYPE TEXT',
                'ALTER TABLE educations ALTER COLUMN uni TYPE TEXT',
                'ALTER TABLE educations ALTER COLUMN location TYPE TEXT',
                'ALTER TABLE educations ALTER COLUMN degree TYPE TEXT',
                'ALTER TABLE educations ALTER COLUMN start_year TYPE TEXT',
                'ALTER TABLE educations ALTER COLUMN end_year TYPE TEXT',
                'ALTER TABLE experiences ALTER COLUMN role TYPE TEXT',
                'ALTER TABLE experiences ALTER COLUMN comp TYPE TEXT',
                'ALTER TABLE experiences ALTER COLUMN "desc" TYPE TEXT',
                'ALTER TABLE experiences ALTER COLUMN start_date TYPE TEXT',
                'ALTER TABLE experiences ALTER COLUMN end_date TYPE TEXT',
                'ALTER TABLE projects ALTER COLUMN proj TYPE TEXT',
                'ALTER TABLE projects ALTER COLUMN tool TYPE TEXT',
                'ALTER TABLE projects ALTER COLUMN "desc" TYPE TEXT',
                'ALTER TABLE projects ALTER COLUMN link TYPE TEXT',
                'ALTER TABLE skills ALTER COLUMN data TYPE TEXT',
                'ALTER TABLE skills ALTER COLUMN "group" TYPE TEXT'
            ]
        elif dialect in ('mysql', 'mariadb'):
            statements = [
                'ALTER TABLE user MODIFY COLUMN username TEXT',
                'ALTER TABLE user MODIFY COLUMN password TEXT',
                'ALTER TABLE user MODIFY COLUMN first_name TEXT',
                'ALTER TABLE personal_info MODIFY COLUMN full_name TEXT',
                'ALTER TABLE personal_info MODIFY COLUMN email TEXT',
                'ALTER TABLE personal_info MODIFY COLUMN phone TEXT',
                'ALTER TABLE personal_info MODIFY COLUMN address TEXT',
                'ALTER TABLE personal_info MODIFY COLUMN linkedin TEXT',
                'ALTER TABLE personal_info MODIFY COLUMN github TEXT',
                'ALTER TABLE personal_info MODIFY COLUMN website TEXT',
                'ALTER TABLE resume MODIFY COLUMN name TEXT',
                'ALTER TABLE bios MODIFY COLUMN bio LONGTEXT',
                'ALTER TABLE educations MODIFY COLUMN uni TEXT',
                'ALTER TABLE educations MODIFY COLUMN location TEXT',
                'ALTER TABLE educations MODIFY COLUMN degree TEXT',
                'ALTER TABLE educations MODIFY COLUMN start_year TEXT',
                'ALTER TABLE educations MODIFY COLUMN end_year TEXT',
                'ALTER TABLE experiences MODIFY COLUMN role TEXT',
                'ALTER TABLE experiences MODIFY COLUMN comp TEXT',
                'ALTER TABLE experiences MODIFY COLUMN `desc` LONGTEXT',
                'ALTER TABLE experiences MODIFY COLUMN start_date TEXT',
                'ALTER TABLE experiences MODIFY COLUMN end_date TEXT',
                'ALTER TABLE projects MODIFY COLUMN proj TEXT',
                'ALTER TABLE projects MODIFY COLUMN tool TEXT',
                'ALTER TABLE projects MODIFY COLUMN `desc` LONGTEXT',
                'ALTER TABLE projects MODIFY COLUMN link TEXT',
                'ALTER TABLE skills MODIFY COLUMN data TEXT',
                'ALTER TABLE skills MODIFY COLUMN `group` TEXT'
            ]
        else:
            statements = []

        for stmt in statements:
            try:
                db.session.execute(text(stmt))
                db.session.commit()
            except Exception:
                db.session.rollback()

        try:
            inspector = inspect(db.engine)
            columns = {column['name'] for column in inspector.get_columns('personal_info')}

            if 'image_data' not in columns:
                if dialect == 'postgresql':
                    db.session.execute(text('ALTER TABLE personal_info ADD COLUMN image_data BYTEA'))
                elif dialect in ('mysql', 'mariadb'):
                    db.session.execute(text('ALTER TABLE personal_info ADD COLUMN image_data LONGBLOB'))
                else:
                    db.session.execute(text('ALTER TABLE personal_info ADD COLUMN image_data BLOB'))
                db.session.commit()

            if 'image_mime_type' not in columns:
                if dialect == 'postgresql':
                    db.session.execute(text('ALTER TABLE personal_info ADD COLUMN image_mime_type TEXT'))
                elif dialect in ('mysql', 'mariadb'):
                    db.session.execute(text('ALTER TABLE personal_info ADD COLUMN image_mime_type TEXT'))
                else:
                    db.session.execute(text('ALTER TABLE personal_info ADD COLUMN image_mime_type TEXT'))
                db.session.commit()
        except Exception:
            db.session.rollback()
