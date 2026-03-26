from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import *
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)

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
                return redirect(url_for('views.home'))
            else:
                flash("Incorrect password, try again.", category='error')
        else:
            flash("User does not exist.", category='error')
            
    return render_template("sign_in.html", user=current_user)

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
            return redirect(url_for('views.home'))

    return render_template("sign_up.html", user=current_user)

@auth.route('/home')
@login_required
def home():
    return render_template('home.html', user=current_user)