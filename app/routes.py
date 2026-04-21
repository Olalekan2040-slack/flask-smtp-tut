from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from . import db
from .models import User
from .forms import RegistrationForm, ResendVerificationForm
from .email_utils import send_verification_email, confirm_verification_token

bp = Blueprint('routes', __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('Email already registered.', 'danger')
            return redirect(url_for('routes.register'))
        
        new_user = User(email=form.email.data, password=form.password.data, verified=False)
        db.session.add(new_user)
        db.session.commit()
        
        send_verification_email(new_user)
        flash('A verification email has been sent. Please check your inbox.', 'info')
        return redirect(url_for('routes.login'))
    
    return render_template('register.html', form=form)

@bp.route('/verify/<token>')
def verify_email(token):
    email = confirm_verification_token(token)
    if not email:
        flash('The verification link is invalid or has expired.', 'danger')
        return redirect(url_for('routes.register'))
    
    user = User.query.filter_by(email=email).first_or_404()
    if user.verified:
        flash('Account already verified.', 'success')
    else:
        user.verified = True
        db.session.commit()
        flash('Your email has been verified! You can now log in.', 'success')
    
    return redirect(url_for('routes.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    # Simple login logic (expand with proper password check)
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user and user.verified:  # Add password check in production
            login_user(user)
            return redirect(url_for('routes.dashboard'))
        elif user and not user.verified:
            flash('Your email is not verified. Please verify your email to log in.', 'warning')
            return redirect(url_for('routes.resend_verification', email=email))
        else:
            flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.verified:
        logout_user()
        flash('Please verify your email to access the dashboard.', 'warning')
        return render_template('dashboard.html')
    return f'Welcome to dashboard, {current_user.email}!'

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.login'))

@bp.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    form = ResendVerificationForm()
    email = request.args.get('email')
    if email:
        form.email.data = email
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash('Email not found. Please register first.', 'danger')
            return redirect(url_for('routes.register'))
        
        if user.verified:
            flash('This email is already verified. You can log in.', 'info')
            return redirect(url_for('routes.login'))
        
        send_verification_email(user)
        flash('A new verification link has been sent to your email.', 'success')
        return redirect(url_for('routes.login'))
    
    return render_template('resend_verification.html', form=form)