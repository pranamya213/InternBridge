from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils.decorators import role_required
from app import db
from app.models.company_profile import CompanyProfile

company_bp = Blueprint('company', __name__)

def get_or_create_profile(user_id):
    profile = CompanyProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = CompanyProfile(user_id=user_id, company_name=current_user.full_name)
        db.session.add(profile)
        db.session.commit()
    return profile

@company_bp.route('/dashboard')
@login_required
@role_required('company')
def dashboard():
    profile = CompanyProfile.query.filter_by(user_id=current_user.id).first()
    completion_percentage = 0
    if profile:
        fields = [
            profile.company_name, profile.organization_type, profile.industry,
            profile.founded_year, profile.company_size, profile.location,
            profile.tagline, profile.about_company, profile.website,
            profile.contact_person_name, profile.contact_email,
            profile.get_domains(), profile.get_work_modes()
        ]
        completed_fields = sum(1 for field in fields if field)
        completion_percentage = int((completed_fields / len(fields)) * 100) if fields else 0
        
    return render_template('company/dashboard.html', profile=profile, completion_percentage=completion_percentage)

@company_bp.route('/profile')
@login_required
@role_required('company')
def profile_view():
    profile = get_or_create_profile(current_user.id)
    
    fields = [
        profile.company_name, profile.organization_type, profile.industry,
        profile.founded_year, profile.company_size, profile.location,
        profile.tagline, profile.about_company, profile.website,
        profile.contact_person_name, profile.contact_email,
        profile.get_domains(), profile.get_work_modes()
    ]
    completed_fields = sum(1 for field in fields if field)
    completion_percentage = int((completed_fields / len(fields)) * 100) if fields else 0
    
    return render_template('company/profile_view.html', profile=profile, completion_percentage=completion_percentage)

@company_bp.route('/profile/edit', methods=['GET'])
@login_required
@role_required('company')
def profile_edit():
    profile = get_or_create_profile(current_user.id)
    return render_template('company/profile_edit.html', profile=profile)

@company_bp.route('/profile/edit/basic', methods=['POST'])
@login_required
@role_required('company')
def edit_basic_info():
    profile = get_or_create_profile(current_user.id)
    
    company_name = request.form.get('company_name')
    if not company_name:
        flash('Company name is required.', 'danger')
        return redirect(url_for('company.profile_edit'))
        
    profile.company_name = company_name
    profile.organization_type = request.form.get('organization_type')
    profile.industry = request.form.get('industry')
    profile.company_size = request.form.get('company_size')
    profile.location = request.form.get('location')
    
    founded_year = request.form.get('founded_year')
    if founded_year:
        try:
            profile.founded_year = int(founded_year)
        except ValueError:
            pass
            
    db.session.commit()
    flash('Basic organization information updated successfully.', 'success')
    return redirect(url_for('company.profile_edit'))

@company_bp.route('/profile/edit/about', methods=['POST'])
@login_required
@role_required('company')
def edit_about():
    profile = get_or_create_profile(current_user.id)
    
    tagline = request.form.get('tagline')
    if tagline and len(tagline) > 150:
        flash('Tagline must be under 150 characters.', 'danger')
        return redirect(url_for('company.profile_edit'))
        
    profile.tagline = tagline
    profile.about_company = request.form.get('about_company')
    db.session.commit()
    flash('About section updated successfully.', 'success')
    return redirect(url_for('company.profile_edit'))

@company_bp.route('/profile/edit/contact', methods=['POST'])
@login_required
@role_required('company')
def edit_contact():
    profile = get_or_create_profile(current_user.id)
    
    profile.contact_person_name = request.form.get('contact_person_name')
    profile.contact_person_role = request.form.get('contact_person_role')
    profile.contact_email = request.form.get('contact_email')
    profile.contact_phone = request.form.get('contact_phone')
    
    profile.website = request.form.get('website')
    profile.linkedin = request.form.get('linkedin')
    profile.github = request.form.get('github')
    profile.other_link = request.form.get('other_link')
    
    db.session.commit()
    flash('Contact and links updated successfully.', 'success')
    return redirect(url_for('company.profile_edit'))

@company_bp.route('/profile/edit/preferences', methods=['POST'])
@login_required
@role_required('company')
def edit_preferences():
    profile = get_or_create_profile(current_user.id)
    
    work_modes = request.form.getlist('work_modes')
    profile.set_work_modes(work_modes)
    
    domains = request.form.getlist('domains')
    custom_domain = request.form.get('custom_domain')
    if custom_domain and custom_domain.strip():
        domains.append(custom_domain.strip())
    profile.set_domains(domains)
    
    profile.internship_duration = request.form.get('internship_duration')
    profile.internship_availability = request.form.get('internship_availability')
    
    db.session.commit()
    flash('Hiring preferences updated successfully.', 'success')
    return redirect(url_for('company.profile_edit'))
