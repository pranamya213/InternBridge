from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils.decorators import role_required
from app.models.external_internship import ExternalInternship
from app import db
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    from app.models.user import User
    from app.models.student_profile import StudentProfile
    from app.models.company_profile import CompanyProfile
    from app.models.internship import Internship
    from app.models.application import Application
    from app.models.interview import Interview

    total_users = User.query.count()
    total_students = StudentProfile.query.count()
    total_companies = CompanyProfile.query.count()
    
    total_internal = Internship.query.count()
    published_internal = Internship.query.filter_by(status='Published').count()
    
    total_external = ExternalInternship.query.count()
    published_external = ExternalInternship.query.filter_by(status='Published').count()
    
    total_applications = Application.query.count()
    shortlisted_applications = Application.query.filter_by(status='Shortlisted').count()
    
    total_interviews = Interview.query.count()
    scheduled_interviews = Interview.query.filter_by(status='Scheduled').count()
    
    draft_external = ExternalInternship.query.filter_by(status='Draft').count()
    closed_external = ExternalInternship.query.filter_by(status='Closed').count()
    archived_external = ExternalInternship.query.filter_by(status='Archived').count()
    
    last_sync = db.session.query(db.func.max(ExternalInternship.fetched_at)).scalar()
    
    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_students=total_students,
                           total_companies=total_companies,
                           total_internal=total_internal,
                           published_internal=published_internal,
                           total_external=total_external,
                           published_external=published_external,
                           total_applications=total_applications,
                           shortlisted_applications=shortlisted_applications,
                           total_interviews=total_interviews,
                           scheduled_interviews=scheduled_interviews,
                           draft_external=draft_external,
                           closed_external=closed_external,
                           archived_external=archived_external,
                           last_sync=last_sync)

@admin_bp.route('/external-internships')
@login_required
@role_required('admin')
def external_internships():
    status = request.args.get('status')
    query = ExternalInternship.query
    if status:
        query = query.filter_by(status=status)
    
    internships = query.order_by(ExternalInternship.created_at.desc()).all()
    return render_template('admin/external_internships.html', internships=internships)

@admin_bp.route('/external-internships/sync', methods=['POST'])
@login_required
@role_required('admin')
def sync_external_internships_route():
    from app.services.external_internship_service import sync_external_internships
    stats = sync_external_internships()
    if stats['errors'] > 0:
        flash(f"Sync completed with some errors. Added: {stats['new_added']}, Updated: {stats['updated']}.", "warning")
    else:
        flash(f"Sync successful! Added: {stats['new_added']}, Updated: {stats['updated']}.", "success")
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/external-internships/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def external_internship_create():
    if request.method == 'POST':
        title = request.form.get('title')
        company_name = request.form.get('company_name')
        application_url = request.form.get('application_url')
        application_deadline_str = request.form.get('application_deadline')
        description = request.form.get('description')
        
        # Check duplicate
        if application_url:
            existing = ExternalInternship.query.filter_by(application_url=application_url).first()
            if existing:
                flash("This external internship (URL) has already been added.", "danger")
                return redirect(url_for('admin.external_internship_create'))
                
        application_deadline = None
        if application_deadline_str:
            application_deadline = datetime.strptime(application_deadline_str, '%Y-%m-%d').date()
            
        internship = ExternalInternship(
            title=title,
            company_name=company_name,
            company_logo=request.form.get('company_logo'),
            company_website=request.form.get('company_website'),
            company_description=request.form.get('company_description'),
            short_description=request.form.get('short_description'),
            description=description,
            category=request.form.get('category'),
            internship_type=request.form.get('internship_type'),
            work_mode=request.form.get('work_mode'),
            location=request.form.get('location'),
            duration=request.form.get('duration'),
            stipend_type=request.form.get('stipend_type'),
            stipend=request.form.get('stipend'),
            openings=request.form.get('openings'),
            eligibility=request.form.get('eligibility'),
            responsibilities=request.form.get('responsibilities'),
            qualifications=request.form.get('qualifications'),
            benefits=request.form.get('benefits'),
            application_deadline=application_deadline,
            application_url=application_url,
            source_name=request.form.get('source_name') or 'Admin Curated',
            source_url=request.form.get('source_url'),
            external_reference_id=request.form.get('external_reference_id'),
            status=request.form.get('status', 'Draft'),
            created_by=current_user.id
        )
        
        # Skills handling
        req_skills_raw = request.form.get('required_skills', '')
        if req_skills_raw:
            internship.set_required_skills([s.strip() for s in req_skills_raw.split(',') if s.strip()])
            
        pref_skills_raw = request.form.get('preferred_skills', '')
        if pref_skills_raw:
            internship.set_preferred_skills([s.strip() for s in pref_skills_raw.split(',') if s.strip()])
            
        if internship.status == 'Published':
            internship.published_at = datetime.utcnow()
            
        db.session.add(internship)
        db.session.commit()
        
        flash("External internship created successfully.", "success")
        return redirect(url_for('admin.external_internships'))
        
    return render_template('admin/external_internship_create.html')

@admin_bp.route('/external-internships/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def external_internship_edit(id):
    internship = ExternalInternship.query.get_or_404(id)
    
    if request.method == 'POST':
        internship.title = request.form.get('title')
        internship.company_name = request.form.get('company_name')
        
        new_app_url = request.form.get('application_url')
        if new_app_url and new_app_url != internship.application_url:
            existing = ExternalInternship.query.filter_by(application_url=new_app_url).first()
            if existing:
                flash("This external internship (URL) has already been added.", "danger")
                return redirect(url_for('admin.external_internship_edit', id=id))
        internship.application_url = new_app_url
        
        deadline_str = request.form.get('application_deadline')
        if deadline_str:
            internship.application_deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            
        internship.description = request.form.get('description')
        internship.company_logo = request.form.get('company_logo')
        internship.company_website = request.form.get('company_website')
        internship.company_description = request.form.get('company_description')
        internship.short_description = request.form.get('short_description')
        internship.category = request.form.get('category')
        internship.internship_type = request.form.get('internship_type')
        internship.work_mode = request.form.get('work_mode')
        internship.location = request.form.get('location')
        internship.duration = request.form.get('duration')
        internship.stipend_type = request.form.get('stipend_type')
        internship.stipend = request.form.get('stipend')
        internship.openings = request.form.get('openings')
        internship.eligibility = request.form.get('eligibility')
        internship.responsibilities = request.form.get('responsibilities')
        internship.qualifications = request.form.get('qualifications')
        internship.benefits = request.form.get('benefits')
        internship.source_name = request.form.get('source_name') or 'Admin Curated'
        internship.source_url = request.form.get('source_url')
        internship.external_reference_id = request.form.get('external_reference_id')
        
        new_status = request.form.get('status', 'Draft')
        if new_status == 'Published' and internship.status != 'Published':
            internship.published_at = datetime.utcnow()
        internship.status = new_status
        
        req_skills_raw = request.form.get('required_skills', '')
        if req_skills_raw:
            internship.set_required_skills([s.strip() for s in req_skills_raw.split(',') if s.strip()])
        else:
            internship.set_required_skills([])
            
        pref_skills_raw = request.form.get('preferred_skills', '')
        if pref_skills_raw:
            internship.set_preferred_skills([s.strip() for s in pref_skills_raw.split(',') if s.strip()])
        else:
            internship.set_preferred_skills([])
            
        db.session.commit()
        flash("External internship updated successfully.", "success")
        return redirect(url_for('admin.external_internships'))
        
    return render_template('admin/external_internship_edit.html', internship=internship)

@admin_bp.route('/external-internships/<int:id>/publish', methods=['POST'])
@login_required
@role_required('admin')
def external_internship_publish(id):
    internship = ExternalInternship.query.get_or_404(id)
    internship.status = 'Published'
    internship.published_at = datetime.utcnow()
    db.session.commit()
    flash("Internship published.", "success")
    return redirect(url_for('admin.external_internships'))

@admin_bp.route('/external-internships/<int:id>/close', methods=['POST'])
@login_required
@role_required('admin')
def external_internship_close(id):
    internship = ExternalInternship.query.get_or_404(id)
    internship.status = 'Closed'
    db.session.commit()
    flash("Internship closed.", "success")
    return redirect(url_for('admin.external_internships'))

@admin_bp.route('/external-internships/<int:id>/archive', methods=['POST'])
@login_required
@role_required('admin')
def external_internship_archive(id):
    internship = ExternalInternship.query.get_or_404(id)
    internship.status = 'Archived'
    db.session.commit()
    flash("Internship archived.", "success")
    return redirect(url_for('admin.external_internships'))

@admin_bp.route('/external-internships/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def external_internship_delete(id):
    internship = ExternalInternship.query.get_or_404(id)
    db.session.delete(internship)
    db.session.commit()
    flash("Internship deleted.", "success")
    return redirect(url_for('admin.external_internships'))
