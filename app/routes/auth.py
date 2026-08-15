from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_based_on_role(current_user.role)

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please provide both email and password.', 'error')
            return render_template('auth/login.html')

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return _redirect_based_on_role(user.role)
        else:
            flash('Invalid email or password.', 'error')

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))

@auth_bp.route('/register')
def register():
    if current_user.is_authenticated:
        return _redirect_based_on_role(current_user.role)
    return render_template('auth/register.html')

@auth_bp.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if current_user.is_authenticated:
        return _redirect_based_on_role(current_user.role)

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Basic Validation
        if not all([full_name, email, password, confirm_password]):
            flash('All fields are required.', 'error')
            return render_template('auth/register_student.html')
            
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('auth/register_student.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register_student.html')

        # Check existing user
        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'error')
            return render_template('auth/register_student.html')

        # Create user
        user = User(full_name=full_name, email=email, role='student')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Student account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_student.html')

@auth_bp.route('/register/company', methods=['GET', 'POST'])
def register_company():
    if current_user.is_authenticated:
        return _redirect_based_on_role(current_user.role)

    if request.method == 'POST':
        # Using full_name field for Contact Person/Company Name for simplicity in this phase
        company_name = request.form.get('company_name', '').strip()
        contact_name = request.form.get('contact_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Basic Validation
        if not all([company_name, contact_name, email, password, confirm_password]):
            flash('All fields are required.', 'error')
            return render_template('auth/register_company.html')
            
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('auth/register_company.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register_company.html')

        # Check existing user
        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'error')
            return render_template('auth/register_company.html')

        # Create user (store company name in full_name for now)
        user = User(full_name=f"{company_name} ({contact_name})", email=email, role='company')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Company account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_company.html')


def _redirect_based_on_role(role):
    """Helper to redirect users to their respective dashboards."""
    if role == 'student':
        return redirect(url_for('student.dashboard'))
    elif role == 'company':
        return redirect(url_for('company.dashboard'))
    elif role == 'admin':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('main.home'))
