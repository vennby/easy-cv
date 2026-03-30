import os
from urllib.parse import urlparse
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from .models import *
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user
from authlib.integrations.flask_client import OAuth

auth = Blueprint('auth', __name__)
oauth = OAuth()


def init_oauth(app):
    oauth.init_app(app)
    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )

@auth.route('/')
def landing():
    return render_template("main.html", user=current_user, show_navbar=False)

@auth.route('/sign-in', methods=['GET','POST'])
def sign_in():
    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user:
            if check_password_hash(user.password, password):
                flash("Signed in successfully!", category='success')
                login_user(user, remember=True)
                if not user.onboarding_completed:
                    return redirect(url_for('views.profile', tour='1'))
                return redirect(url_for('views.home'))
            else:
                flash("Incorrect password, try again.", category='error')
        else:
            flash("User does not exist.", category='error')
            
    return render_template("sign_in.html", user=current_user)


@auth.route('/google-sign-in')
def google_sign_in():
    if not current_app.config.get('GOOGLE_CLIENT_ID') or not current_app.config.get('GOOGLE_CLIENT_SECRET'):
        flash('Google sign-in is not configured yet. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.', category='error')
        return redirect(url_for('auth.sign_in'))

    dynamic_redirect_uri = url_for('auth.google_authorize', _external=True)
    configured_redirect_uri = (current_app.config.get('GOOGLE_REDIRECT_URI') or '').strip()

    # Use configured URI only when host matches current request host.
    # This avoids session cookie host mismatches that trigger OAuth state/CSRF errors.
    redirect_uri = dynamic_redirect_uri
    if configured_redirect_uri:
        configured_host = urlparse(configured_redirect_uri).netloc
        dynamic_host = urlparse(dynamic_redirect_uri).netloc
        if configured_host == dynamic_host:
            redirect_uri = configured_redirect_uri

    try:
        return oauth.google.authorize_redirect(redirect_uri)
    except Exception as exc:
        flash(f'Google sign-in could not start: {exc}', category='error')
        return redirect(url_for('auth.sign_in'))


@auth.route('/google-authorize')
def google_authorize():
    if not current_app.config.get('GOOGLE_CLIENT_ID') or not current_app.config.get('GOOGLE_CLIENT_SECRET'):
        flash('Google sign-in is not configured yet. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.', category='error')
        return redirect(url_for('auth.sign_in'))

    try:
        token = oauth.google.authorize_access_token()
    except Exception as exc:
        flash(f'Google authentication failed: {exc}', category='error')
        return redirect(url_for('auth.sign_in'))
    user_info = token.get('userinfo')
    if not user_info:
        user_info = oauth.google.parse_id_token(token)
    if not user_info:
        flash('Unable to fetch your Google profile. Please try again.', category='error')
        return redirect(url_for('auth.sign_in'))

    email = (user_info.get('email') or '').strip().lower()
    full_name = (user_info.get('name') or '').strip()
    first_name = full_name.split(' ')[0] if full_name else (user_info.get('given_name') or 'User')
    google_sub = (user_info.get('sub') or '').strip()

    if not google_sub:
        flash('Google account data is incomplete. Please try another account.', category='error')
        return redirect(url_for('auth.sign_in'))

    user = User.query.filter_by(username=f'google:{google_sub}').first()

    if not user and email:
        existing_by_username = User.query.filter_by(username=email).first()
        if existing_by_username:
            user = existing_by_username

    if not user and email:
        linked_profile = PersonalInfo.query.filter_by(email=email).first()
        if linked_profile:
            user = User.query.get(linked_profile.user_id)

    if not user:
        user = User(
            username=f'google:{google_sub}',
            first_name=first_name,
            password=generate_password_hash(os.urandom(24).hex(), method='pbkdf2:sha256')
        )
        db.session.add(user)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Could not create your account from Google sign-in. Please try again.', category='error')
            return redirect(url_for('auth.sign_in'))

    personal_info = PersonalInfo.query.filter_by(user_id=user.id).first()
    if not personal_info:
        personal_info = PersonalInfo(
            user_id=user.id,
            email=email or None,
            full_name=(full_name or first_name or None)
        )
        db.session.add(personal_info)
    else:
        if email and not personal_info.email:
            personal_info.email = email
        if (full_name or first_name) and not personal_info.full_name:
            personal_info.full_name = full_name or first_name

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Could not complete Google profile setup. Please try again.', category='error')
        return redirect(url_for('auth.sign_in'))

    login_user(user, remember=True)
    flash('Signed in with Google!', category='success')
    if not user.onboarding_completed:
        return redirect(url_for('views.profile', tour='1'))
    return redirect(url_for('views.home'))

@auth.route('/sign-out')
@login_required
def sign_out():
    logout_user()
    return redirect(url_for('auth.landing'))

@auth.route('/sign-up', methods=['GET','POST'])
def sign_up():
    if request.method=='POST':
        username = request.form.get('username')
        first_name = request.form.get('first_name')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        
        user = User.query.filter_by(username=username).first()
        
        if user:
            flash("user already exists!", category='error')
        elif len(username) < 4:
            flash("username must be greater than 4 characters.", category='error')
        elif len(first_name) < 2:
            flash("first name must be greater than 2 characters.", category='error')
        elif password1 != password2:
            flash("passwords don't match.", category='error')
        elif len(password1) < 4:
            flash("password must be greater than 4 characters.", category='error')
        else:
            new_user = User(username=username, first_name=first_name, password=generate_password_hash(password1, method='pbkdf2:sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash("Account created!", category='success')
            return redirect(url_for('views.profile', tour='1'))

    return render_template("sign_up.html", user=current_user)

@auth.route('/home')
@login_required
def home():
    return render_template('home.html', user=current_user)