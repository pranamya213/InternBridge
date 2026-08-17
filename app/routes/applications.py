from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.utils.decorators import role_required
from app import db
from app.models.internship import Internship
from app.models.student_profile import StudentProfile
from app.models.company_profile import CompanyProfile
from app.models.application import Application, ApplicationStatusHistory
from app.services.matching_service import calculate_match, rank_candidates_for_internship
from datetime import datetime

applications_bp = Blueprint('applications', __name__)

# ==========================================
# STUDENT ROUTES
# ==========================================

@applications_bp.route('/student/applications/apply/<int:internship_id>', methods=['GET', 'POST'])
@login_required
@role_required('student')
def student_apply(internship_id):
    internship = Internship.query.get_or_404(internship_id)
    student_profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    
    if not student_profile:
        flash('Please complete your student profile before applying.', 'warning')
        return redirect(url_for('student.profile_edit'))
        
    if internship.status != 'Published':
        flash('This internship is not open for applications.', 'danger')
        return redirect(url_for('internships.detail', internship_id=internship.id))
        
    if internship.application_deadline and internship.application_deadline < datetime.utcnow().date():
        flash('The application deadline for this internship has passed.', 'danger')
        return redirect(url_for('internships.detail', internship_id=internship.id))
        
    existing_app = Application.query.filter_by(internship_id=internship.id, student_profile_id=student_profile.id).first()
    if existing_app:
        flash('You have already applied for this internship.', 'info')
        return redirect(url_for('applications.student_application_detail', application_id=existing_app.id))
        
    if request.method == 'POST':
        cover_letter = request.form.get('cover_letter', '').strip()
        
        application = Application(
            internship_id=internship.id,
            student_profile_id=student_profile.id,
            cover_letter=cover_letter,
            status='Applied'
        )
        db.session.add(application)
        db.session.flush() # To get application ID for history
        
        history = ApplicationStatusHistory(
            application_id=application.id,
            status='Applied'
        )
        db.session.add(history)
        db.session.commit()
        
        flash('Your application has been submitted successfully!', 'success')
        return redirect(url_for('applications.student_application_detail', application_id=application.id))
        
    return render_template('applications/student_apply.html', internship=internship, student_profile=student_profile)

@applications_bp.route('/student/applications')
@login_required
@role_required('student')
def student_applications():
    student_profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if not student_profile:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('student.profile_edit'))
        
    status_filter = request.args.get('status')
    
    query = Application.query.filter_by(student_profile_id=student_profile.id)
    if status_filter and status_filter != 'All':
        query = query.filter_by(status=status_filter)
        
    applications = query.order_by(Application.applied_at.desc()).all()
    
    # Get stats for filters
    stats = {
        'All': Application.query.filter_by(student_profile_id=student_profile.id).count(),
        'Applied': Application.query.filter_by(student_profile_id=student_profile.id, status='Applied').count(),
        'Under Review': Application.query.filter_by(student_profile_id=student_profile.id, status='Under Review').count(),
        'Shortlisted': Application.query.filter_by(student_profile_id=student_profile.id, status='Shortlisted').count(),
        'Accepted': Application.query.filter_by(student_profile_id=student_profile.id, status='Accepted').count(),
        'Rejected': Application.query.filter_by(student_profile_id=student_profile.id, status='Rejected').count(),
        'Withdrawn': Application.query.filter_by(student_profile_id=student_profile.id, status='Withdrawn').count()
    }
    
    return render_template('applications/student_applications.html', applications=applications, current_filter=status_filter or 'All', stats=stats)

@applications_bp.route('/student/applications/<int:application_id>')
@login_required
@role_required('student')
def student_application_detail(application_id):
    student_profile = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    application = Application.query.filter_by(id=application_id, student_profile_id=student_profile.id).first_or_404()
    return render_template('applications/student_application_detail.html', application=application)

@applications_bp.route('/student/applications/<int:application_id>/withdraw', methods=['POST'])
@login_required
@role_required('student')
def student_withdraw_application(application_id):
    student_profile = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    application = Application.query.filter_by(id=application_id, student_profile_id=student_profile.id).first_or_404()
    
    if application.status in ['Accepted', 'Rejected']:
        flash(f'You cannot withdraw an application that is {application.status}.', 'danger')
    elif application.status != 'Withdrawn':
        application.status = 'Withdrawn'
        application.updated_at = datetime.utcnow()
        history = ApplicationStatusHistory(
            application_id=application.id,
            status='Withdrawn'
        )
        db.session.add(history)
        db.session.commit()
        flash('Your application has been withdrawn.', 'info')
        
    return redirect(url_for('applications.student_application_detail', application_id=application.id))

# ==========================================
# COMPANY ROUTES
# ==========================================

@applications_bp.route('/company/internships/<int:internship_id>/applications')
@login_required
@role_required('company')
def company_applicants(internship_id):
    company_profile = CompanyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    internship = Internship.query.filter_by(id=internship_id, company_profile_id=company_profile.id).first_or_404()
    
    status_filter = request.args.get('status')
    sort_by = request.args.get('sort_by', 'best_match')
    
    query = Application.query.filter_by(internship_id=internship.id)
    if status_filter and status_filter != 'All':
        query = query.filter_by(status=status_filter)
        
    applications_raw = query.all()
    
    # Rank candidates
    applications = rank_candidates_for_internship(internship, applications_raw, sort_by)
    
    stats = {
        'All': Application.query.filter_by(internship_id=internship.id).count(),
        'Applied': Application.query.filter_by(internship_id=internship.id, status='Applied').count(),
        'Under Review': Application.query.filter_by(internship_id=internship.id, status='Under Review').count(),
        'Shortlisted': Application.query.filter_by(internship_id=internship.id, status='Shortlisted').count(),
        'Accepted': Application.query.filter_by(internship_id=internship.id, status='Accepted').count(),
        'Rejected': Application.query.filter_by(internship_id=internship.id, status='Rejected').count(),
        'Withdrawn': Application.query.filter_by(internship_id=internship.id, status='Withdrawn').count()
    }
    
    return render_template('applications/company_applicants.html', internship=internship, applications=applications, current_filter=status_filter or 'All', stats=stats, sort_by=sort_by)

@applications_bp.route('/company/applications/<int:application_id>')
@login_required
@role_required('company')
def company_applicant_detail(application_id):
    company_profile = CompanyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    application = Application.query.join(Internship).filter(Application.id == application_id, Internship.company_profile_id == company_profile.id).first_or_404()
    
    # Calculate match data
    match_data = calculate_match(application.student, application.internship)
    
    return render_template('applications/company_applicant_detail.html', application=application, match_data=match_data)

@applications_bp.route('/company/applications/<int:application_id>/status', methods=['POST'])
@login_required
@role_required('company')
def company_update_status(application_id):
    company_profile = CompanyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    application = Application.query.join(Internship).filter(Application.id == application_id, Internship.company_profile_id == company_profile.id).first_or_404()
    
    new_status = request.form.get('status')
    valid_statuses = ['Applied', 'Under Review', 'Shortlisted', 'Accepted', 'Rejected']
    
    # Prevent invalid backward transitions/changes
    if application.status in ['Withdrawn', 'Accepted'] and new_status not in ['Withdrawn', 'Accepted']:
        flash(f'Cannot change status from {application.status} to {new_status}.', 'danger')
        return redirect(url_for('applications.company_applicant_detail', application_id=application.id))
        
    if new_status in valid_statuses and new_status != application.status:
        application.status = new_status
        application.updated_at = datetime.utcnow()
        if new_status in ['Under Review', 'Shortlisted', 'Accepted', 'Rejected']:
            application.reviewed_at = datetime.utcnow()
            
        history = ApplicationStatusHistory(
            application_id=application.id,
            status=new_status
        )
        db.session.add(history)
        db.session.commit()
        flash(f'Application status updated to {new_status}.', 'success')
        
    return redirect(url_for('applications.company_applicant_detail', application_id=application.id))

@applications_bp.route('/company/applications/<int:application_id>/notes', methods=['POST'])
@login_required
@role_required('company')
def company_update_notes(application_id):
    company_profile = CompanyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    application = Application.query.join(Internship).filter(Application.id == application_id, Internship.company_profile_id == company_profile.id).first_or_404()
    
    notes = request.form.get('company_notes')
    application.company_notes = notes
    db.session.commit()
    flash('Internal notes updated successfully.', 'success')
    
    return redirect(url_for('applications.company_applicant_detail', application_id=application.id))

@applications_bp.route('/company/internships/<int:internship_id>/applications/compare')
@login_required
@role_required('company')
def company_compare_candidates(internship_id):
    company_profile = CompanyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    internship = Internship.query.filter_by(id=internship_id, company_profile_id=company_profile.id).first_or_404()
    
    # Get applicant IDs securely from query parameters
    app_ids_str = request.args.get('ids', '')
    if not app_ids_str:
        flash("No candidates selected for comparison.", "warning")
        return redirect(url_for('applications.company_applicants', internship_id=internship.id))
        
    try:
        app_ids = [int(i.strip()) for i in app_ids_str.split(',') if i.strip()]
    except ValueError:
        abort(400, "Invalid application IDs.")
        
    # Securely fetch valid applications belonging to this internship and this company
    applications = Application.query.filter(Application.id.in_(app_ids), Application.internship_id == internship.id).all()
    
    if len(applications) < 2:
        flash("Please select at least 2 candidates to compare.", "warning")
        return redirect(url_for('applications.company_applicants', internship_id=internship.id))
        
    # Run ranking logic on them to get match data populated
    applications = rank_candidates_for_internship(internship, applications, sort_by='best_match')
    
    return render_template('applications/company_candidate_compare.html', internship=internship, applications=applications)
