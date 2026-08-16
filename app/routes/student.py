from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils.decorators import role_required
from app import db
from app.models.student_profile import (
    StudentProfile, Education, StudentSkill, CareerInterest, Project,
    Certification, Experience, ProfessionalLink
)
from datetime import datetime

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
@role_required('student')
def dashboard():
    return render_template('student/dashboard.html')

# Helper to get or create profile
def get_or_create_profile(user_id):
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = StudentProfile(user_id=user_id)
        db.session.add(profile)
        db.session.commit()
    return profile

# Profile View
@student_bp.route('/profile')
@login_required
@role_required('student')
def profile_view():
    profile = get_or_create_profile(current_user.id)
    
    # Calculate profile completion dynamically
    fields = [
        profile.headline, profile.phone, profile.location, profile.about_me,
        profile.education, profile.skills, profile.career_interests, 
        profile.projects, profile.certifications, profile.experience, profile.professional_links
    ]
    completed_fields = sum(1 for field in fields if field)
    completion_percentage = int((completed_fields / len(fields)) * 100) if fields else 0
    
    return render_template('student/profile_view.html', profile=profile, completion_percentage=completion_percentage)

# Profile Edit - Main Page
@student_bp.route('/profile/edit', methods=['GET'])
@login_required
@role_required('student')
def profile_edit():
    profile = get_or_create_profile(current_user.id)
    return render_template('student/profile_edit.html', profile=profile)

# Update Basic Info
@student_bp.route('/profile/edit/basic', methods=['POST'])
@login_required
@role_required('student')
def edit_basic_info():
    profile = get_or_create_profile(current_user.id)
    headline = request.form.get('headline')
    if headline and len(headline) > 100:
        flash('Headline must be under 100 characters.', 'danger')
        return redirect(url_for('student.profile_edit'))
        
    profile.headline = headline
    profile.phone = request.form.get('phone')
    profile.location = request.form.get('location')
    
    dob_str = request.form.get('dob')
    if dob_str:
        try:
            profile.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        except ValueError:
            pass
            
    db.session.commit()
    flash('Basic information updated successfully.', 'success')
    return redirect(url_for('student.profile_edit'))

# Update About
@student_bp.route('/profile/edit/about', methods=['POST'])
@login_required
@role_required('student')
def edit_about():
    profile = get_or_create_profile(current_user.id)
    profile.about_me = request.form.get('about_me')
    db.session.commit()
    flash('About me section updated.', 'success')
    return redirect(url_for('student.profile_edit'))

# Update Preferences
@student_bp.route('/profile/edit/preferences', methods=['POST'])
@login_required
@role_required('student')
def edit_preferences():
    profile = get_or_create_profile(current_user.id)
    work_modes = request.form.getlist('work_modes')
    profile.set_work_modes(work_modes)
    
    # Career Interests
    # First, clear existing
    CareerInterest.query.filter_by(profile_id=profile.id).delete()
    
    roles = request.form.getlist('roles')
    custom_role = request.form.get('custom_role')
    
    for role in roles:
        if role:
            db.session.add(CareerInterest(profile_id=profile.id, role_name=role))
            
    if custom_role and custom_role.strip():
        db.session.add(CareerInterest(profile_id=profile.id, role_name=custom_role.strip()))
        
    db.session.commit()
    flash('Preferences updated.', 'success')
    return redirect(url_for('student.profile_edit'))

# Add Education
@student_bp.route('/profile/education/add', methods=['POST'])
@login_required
@role_required('student')
def add_education():
    profile = get_or_create_profile(current_user.id)
    
    edu = Education(
        profile_id=profile.id,
        degree=request.form.get('degree'),
        institution=request.form.get('institution'),
        field_of_study=request.form.get('field_of_study'),
        start_year=request.form.get('start_year'),
        end_year=request.form.get('end_year') if not request.form.get('currently_studying') else None,
        currently_studying=bool(request.form.get('currently_studying')),
        cgpa=request.form.get('cgpa')
    )
    db.session.add(edu)
    db.session.commit()
    flash('Education added.', 'success')
    return redirect(url_for('student.profile_edit'))

# Delete Education
@student_bp.route('/profile/education/delete/<int:id>', methods=['POST'])
@login_required
@role_required('student')
def delete_education(id):
    profile = get_or_create_profile(current_user.id)
    edu = Education.query.filter_by(id=id, profile_id=profile.id).first_or_404()
    db.session.delete(edu)
    db.session.commit()
    flash('Education removed.', 'success')
    return redirect(url_for('student.profile_edit'))

# Add Skill
@student_bp.route('/profile/skills/add', methods=['POST'])
@login_required
@role_required('student')
def add_skill():
    profile = get_or_create_profile(current_user.id)
    skill_name = request.form.get('skill_name')
    
    if skill_name:
        # Check if skill already exists for this profile
        existing = StudentSkill.query.filter_by(profile_id=profile.id, skill_name=skill_name).first()
        if not existing:
            skill = StudentSkill(
                profile_id=profile.id,
                skill_name=skill_name,
                proficiency=request.form.get('proficiency')
            )
            db.session.add(skill)
            db.session.commit()
            flash('Skill added.', 'success')
        else:
            flash('Skill already exists.', 'warning')
            
    return redirect(url_for('student.profile_edit'))

# Delete Skill
@student_bp.route('/profile/skills/delete/<int:id>', methods=['POST'])
@login_required
@role_required('student')
def delete_skill(id):
    profile = get_or_create_profile(current_user.id)
    skill = StudentSkill.query.filter_by(id=id, profile_id=profile.id).first_or_404()
    db.session.delete(skill)
    db.session.commit()
    flash('Skill removed.', 'success')
    return redirect(url_for('student.profile_edit'))

# Add Project
@student_bp.route('/profile/projects/add', methods=['POST'])
@login_required
@role_required('student')
def add_project():
    profile = get_or_create_profile(current_user.id)
    
    project = Project(
        profile_id=profile.id,
        name=request.form.get('name'),
        description=request.form.get('description'),
        technologies=request.form.get('technologies'),
        github_url=request.form.get('github_url'),
        live_demo_url=request.form.get('live_demo_url')
    )
    
    start_date = request.form.get('start_date')
    if start_date:
        try: project.start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except: pass
        
    end_date = request.form.get('end_date')
    if end_date:
        try: project.end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except: pass
        
    db.session.add(project)
    db.session.commit()
    flash('Project added.', 'success')
    return redirect(url_for('student.profile_edit'))

# Delete Project
@student_bp.route('/profile/projects/delete/<int:id>', methods=['POST'])
@login_required
@role_required('student')
def delete_project(id):
    profile = get_or_create_profile(current_user.id)
    project = Project.query.filter_by(id=id, profile_id=profile.id).first_or_404()
    db.session.delete(project)
    db.session.commit()
    flash('Project removed.', 'success')
    return redirect(url_for('student.profile_edit'))

# Add Certification
@student_bp.route('/profile/certifications/add', methods=['POST'])
@login_required
@role_required('student')
def add_certification():
    profile = get_or_create_profile(current_user.id)
    
    issue_date_str = request.form.get('issue_date')
    try:
        issue_date = datetime.strptime(issue_date_str, '%Y-%m-%d').date() if issue_date_str else datetime.utcnow().date()
    except:
        issue_date = datetime.utcnow().date()
        
    cert = Certification(
        profile_id=profile.id,
        name=request.form.get('name'),
        organization=request.form.get('organization'),
        issue_date=issue_date,
        certificate_id=request.form.get('certificate_id'),
        certificate_url=request.form.get('certificate_url')
    )
    
    expiry_date = request.form.get('expiry_date')
    if expiry_date:
        try: cert.expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
        except: pass
        
    db.session.add(cert)
    db.session.commit()
    flash('Certification added.', 'success')
    return redirect(url_for('student.profile_edit'))

# Delete Certification
@student_bp.route('/profile/certifications/delete/<int:id>', methods=['POST'])
@login_required
@role_required('student')
def delete_certification(id):
    profile = get_or_create_profile(current_user.id)
    cert = Certification.query.filter_by(id=id, profile_id=profile.id).first_or_404()
    db.session.delete(cert)
    db.session.commit()
    flash('Certification removed.', 'success')
    return redirect(url_for('student.profile_edit'))

# Add Experience
@student_bp.route('/profile/experience/add', methods=['POST'])
@login_required
@role_required('student')
def add_experience():
    profile = get_or_create_profile(current_user.id)
    
    start_date_str = request.form.get('start_date')
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else datetime.utcnow().date()
    except:
        start_date = datetime.utcnow().date()
        
    exp = Experience(
        profile_id=profile.id,
        job_title=request.form.get('job_title'),
        organization=request.form.get('organization'),
        description=request.form.get('description'),
        start_date=start_date,
        currently_working=bool(request.form.get('currently_working'))
    )
    
    if not exp.currently_working:
        end_date = request.form.get('end_date')
        if end_date:
            try: exp.end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except: pass
            
    db.session.add(exp)
    db.session.commit()
    flash('Experience added.', 'success')
    return redirect(url_for('student.profile_edit'))

# Delete Experience
@student_bp.route('/profile/experience/delete/<int:id>', methods=['POST'])
@login_required
@role_required('student')
def delete_experience(id):
    profile = get_or_create_profile(current_user.id)
    exp = Experience.query.filter_by(id=id, profile_id=profile.id).first_or_404()
    db.session.delete(exp)
    db.session.commit()
    flash('Experience removed.', 'success')
    return redirect(url_for('student.profile_edit'))
