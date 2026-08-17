from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.utils.decorators import role_required
from app import db
from app.models.company_profile import CompanyProfile
from app.models.internship import Internship
from datetime import datetime
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
    internships_stats = {'total': 0, 'published': 0, 'draft': 0, 'closed': 0}
    applicant_stats = {'total': 0, 'new': 0, 'reviewing': 0, 'shortlisted': 0}
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
        
        internships = Internship.query.filter_by(company_profile_id=profile.id).all()
        internships_stats['total'] = len(internships)
        internships_stats['published'] = sum(1 for i in internships if i.status == 'Published')
        internships_stats['draft'] = sum(1 for i in internships if i.status == 'Draft')
        internships_stats['closed'] = sum(1 for i in internships if i.status == 'Closed')
        
        # Calculate applicant stats
        from app.models.application import Application
        from app.services.matching_service import calculate_match
        
        all_apps = Application.query.join(Internship).filter(Internship.company_profile_id == profile.id).all()
        applicant_stats['total'] = len(all_apps)
        applicant_stats['new'] = sum(1 for a in all_apps if a.status == 'Applied')
        applicant_stats['reviewing'] = sum(1 for a in all_apps if a.status == 'Under Review')
        applicant_stats['shortlisted'] = sum(1 for a in all_apps if a.status == 'Shortlisted')
        
        top_candidates = []
        if all_apps:
            for app in all_apps:
                app.match_data = calculate_match(app.student, app.internship)
                app.match_score = app.match_data['score']
                
            all_apps.sort(key=lambda x: getattr(x, 'match_score', 0), reverse=True)
            top_candidates = all_apps[:3]
        
    return render_template('company/dashboard.html', profile=profile, completion_percentage=completion_percentage, stats=internships_stats, applicant_stats=applicant_stats, top_candidates=top_candidates)

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

# ==========================================
# INTERNSHIP MANAGEMENT ROUTES
# ==========================================

@company_bp.route('/internships')
@login_required
@role_required('company')
def internships_list():
    profile = get_or_create_profile(current_user.id)
    internships = Internship.query.filter_by(company_profile_id=profile.id).order_by(Internship.created_at.desc()).all()
    return render_template('company/internships.html', internships=internships)

@company_bp.route('/internships/create', methods=['GET', 'POST'])
@login_required
@role_required('company')
def internship_create():
    profile = get_or_create_profile(current_user.id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        if not title:
            flash('Title is required.', 'danger')
            return redirect(url_for('company.internship_create'))
            
        internship = Internship(
            company_profile_id=profile.id,
            title=title,
            short_description=request.form.get('short_description'),
            description=request.form.get('description'),
            category=request.form.get('category'),
            internship_type=request.form.get('internship_type'),
            work_mode=request.form.get('work_mode'),
            location=request.form.get('location'),
            duration=request.form.get('duration'),
            stipend_type=request.form.get('stipend_type'),
            stipend=request.form.get('stipend'),
            eligibility=request.form.get('eligibility'),
            responsibilities=request.form.get('responsibilities'),
            qualifications=request.form.get('qualifications'),
            benefits=request.form.get('benefits'),
            status='Draft'
        )
        
        openings = request.form.get('openings')
        if openings and openings.isdigit():
            internship.openings = int(openings)
            
        deadline_str = request.form.get('application_deadline')
        if deadline_str:
            try:
                internship.application_deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                pass
                
        # Handle required skills (comma separated or multiple inputs, let's assume comma separated string for simplicity in form)
        req_skills_str = request.form.get('required_skills')
        if req_skills_str:
            skills = [s.strip() for s in req_skills_str.split(',') if s.strip()]
            internship.set_required_skills(skills)
            
        pref_skills_str = request.form.get('preferred_skills')
        if pref_skills_str:
            skills = [s.strip() for s in pref_skills_str.split(',') if s.strip()]
            internship.set_preferred_skills(skills)

        db.session.add(internship)
        db.session.commit()
        
        action = request.form.get('action')
        if action == 'publish':
            internship.status = 'Published'
            internship.published_at = datetime.utcnow()
            db.session.commit()
            flash('Internship published successfully.', 'success')
        else:
            flash('Internship saved as draft.', 'success')
            
        return redirect(url_for('company.internships_list'))
        
    return render_template('company/internship_create.html', profile=profile)

@company_bp.route('/internships/<int:internship_id>')
@login_required
@role_required('company')
def internship_detail(internship_id):
    profile = get_or_create_profile(current_user.id)
    internship = Internship.query.filter_by(id=internship_id, company_profile_id=profile.id).first_or_404()
    return render_template('company/internship_detail.html', internship=internship)

@company_bp.route('/internships/<int:internship_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('company')
def internship_edit(internship_id):
    profile = get_or_create_profile(current_user.id)
    internship = Internship.query.filter_by(id=internship_id, company_profile_id=profile.id).first_or_404()
    
    if request.method == 'POST':
        title = request.form.get('title')
        if not title:
            flash('Title is required.', 'danger')
            return redirect(url_for('company.internship_edit', internship_id=internship.id))
            
        internship.title = title
        internship.short_description = request.form.get('short_description')
        internship.description = request.form.get('description')
        internship.category = request.form.get('category')
        internship.internship_type = request.form.get('internship_type')
        internship.work_mode = request.form.get('work_mode')
        internship.location = request.form.get('location')
        internship.duration = request.form.get('duration')
        internship.stipend_type = request.form.get('stipend_type')
        internship.stipend = request.form.get('stipend')
        internship.eligibility = request.form.get('eligibility')
        internship.responsibilities = request.form.get('responsibilities')
        internship.qualifications = request.form.get('qualifications')
        internship.benefits = request.form.get('benefits')
        
        openings = request.form.get('openings')
        if openings and openings.isdigit():
            internship.openings = int(openings)
            
        deadline_str = request.form.get('application_deadline')
        if deadline_str:
            try:
                internship.application_deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                pass
                
        req_skills_str = request.form.get('required_skills')
        if req_skills_str is not None:
            skills = [s.strip() for s in req_skills_str.split(',') if s.strip()]
            internship.set_required_skills(skills)
            
        pref_skills_str = request.form.get('preferred_skills')
        if pref_skills_str is not None:
            skills = [s.strip() for s in pref_skills_str.split(',') if s.strip()]
            internship.set_preferred_skills(skills)
            
        db.session.commit()
        
        action = request.form.get('action')
        if action == 'publish' and internship.status == 'Draft':
            internship.status = 'Published'
            internship.published_at = datetime.utcnow()
            db.session.commit()
            flash('Internship published successfully.', 'success')
        else:
            flash('Internship updated successfully.', 'success')
            
        return redirect(url_for('company.internship_detail', internship_id=internship.id))
        
    return render_template('company/internship_edit.html', internship=internship)

@company_bp.route('/internships/<int:internship_id>/publish', methods=['POST'])
@login_required
@role_required('company')
def internship_publish(internship_id):
    profile = get_or_create_profile(current_user.id)
    internship = Internship.query.filter_by(id=internship_id, company_profile_id=profile.id).first_or_404()
    
    if internship.status == 'Draft' or internship.status == 'Closed':
        internship.status = 'Published'
        internship.published_at = datetime.utcnow()
        db.session.commit()
        flash('Internship published successfully.', 'success')
        
    return redirect(url_for('company.internships_list'))

@company_bp.route('/internships/<int:internship_id>/close', methods=['POST'])
@login_required
@role_required('company')
def internship_close(internship_id):
    profile = get_or_create_profile(current_user.id)
    internship = Internship.query.filter_by(id=internship_id, company_profile_id=profile.id).first_or_404()
    
    if internship.status == 'Published':
        internship.status = 'Closed'
        db.session.commit()
        flash('Internship closed.', 'info')
        
    return redirect(url_for('company.internships_list'))

@company_bp.route('/internships/<int:internship_id>/delete', methods=['POST'])
@login_required
@role_required('company')
def internship_delete(internship_id):
    profile = get_or_create_profile(current_user.id)
    internship = Internship.query.filter_by(id=internship_id, company_profile_id=profile.id).first_or_404()
    
    if internship.status in ['Published', 'Closed']:
        internship.status = 'Archived'
        db.session.commit()
        flash('Internship archived.', 'info')
    else:
        db.session.delete(internship)
        db.session.commit()
        flash('Internship deleted.', 'success')
        
    return redirect(url_for('company.internships_list'))

