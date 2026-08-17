from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from app.models.internship import Internship
from app.models.company_profile import CompanyProfile
from app.models.student_profile import StudentProfile
from app.utils.decorators import role_required
from app.services.matching_service import calculate_match
from sqlalchemy import or_

internships_bp = Blueprint('internships', __name__)

@internships_bp.route('/')
def index():
    query = Internship.query.filter_by(status='Published')
    
    # Search by keyword
    search = request.args.get('search')
    if search:
        search_term = f"%{search}%"
        query = query.join(CompanyProfile).filter(
            or_(
                Internship.title.ilike(search_term),
                Internship.category.ilike(search_term),
                Internship.required_skills_json.ilike(search_term),
                CompanyProfile.company_name.ilike(search_term)
            )
        )
        
    # Filters
    work_mode = request.args.get('work_mode')
    if work_mode:
        query = query.filter(Internship.work_mode == work_mode)
        
    domain = request.args.get('domain')
    if domain:
        query = query.filter(Internship.category == domain)
        
    duration = request.args.get('duration')
    if duration:
        query = query.filter(Internship.duration == duration)
        
    # Sorting
    sort_by = request.args.get('sort_by', 'newest')
    
    # We delay 'recommended' sort after fetching all since it's dynamic
    if sort_by == 'newest':
        query = query.order_by(Internship.published_at.desc())
    elif sort_by == 'deadline_soonest':
        query = query.order_by(Internship.application_deadline.asc())
    elif sort_by == 'recently_updated':
        query = query.order_by(Internship.updated_at.desc())
        
    internships = query.all()
    
    # Calculate match scores if student is logged in
    student_profile = None
    if current_user.is_authenticated and current_user.role == 'student':
        student_profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        if student_profile:
            for internship in internships:
                match_data = calculate_match(student_profile, internship)
                internship.match_data = match_data
                internship.match_score = match_data['score']
                
            if sort_by == 'recommended':
                internships.sort(key=lambda x: getattr(x, 'match_score', 0), reverse=True)
    
    # Fetch unique domains and durations for filters
    # In a real app we might cache this or query distinct values
    domains = [i[0] for i in Internship.query.with_entities(Internship.category).filter(Internship.status == 'Published', Internship.category != None).distinct().all()]
    durations = [i[0] for i in Internship.query.with_entities(Internship.duration).filter(Internship.status == 'Published', Internship.duration != None).distinct().all()]
    
    return render_template('internships/index.html', internships=internships, domains=domains, durations=durations)

@internships_bp.route('/<int:internship_id>')
def detail(internship_id):
    # Actually, we should let them view 'Closed' internships too if they have the link, 
    # but the prompt implies only Published. I'll allow Published and Closed to be viewed 
    # by public, as is typical, but only Published can be applied to.
    internship = Internship.query.filter(Internship.id == internship_id, Internship.status.in_(['Published', 'Closed'])).first_or_404()
    
    has_applied = False
    application_id = None
    match_data = None
    
    if current_user.is_authenticated and current_user.role == 'student':
        from app.models.student_profile import StudentProfile
        from app.models.application import Application
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        if profile:
            match_data = calculate_match(profile, internship)
            
            app_record = Application.query.filter_by(internship_id=internship.id, student_profile_id=profile.id).first()
            if app_record:
                has_applied = True
                application_id = app_record.id
                
    from datetime import datetime
    is_past_deadline = False
    if internship.application_deadline and internship.application_deadline < datetime.utcnow().date():
        is_past_deadline = True
                
    return render_template('internships/detail.html', internship=internship, has_applied=has_applied, application_id=application_id, is_past_deadline=is_past_deadline, match_data=match_data)

@internships_bp.route('/<int:internship_id>/match')
@login_required
@role_required('student')
def match_analysis(internship_id):
    internship = Internship.query.filter(Internship.id == internship_id, Internship.status.in_(['Published', 'Closed'])).first_or_404()
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    
    if not profile:
        flash("Please complete your profile to see match analysis.", "warning")
        return redirect(url_for('student.profile_edit'))
        
    match_data = calculate_match(profile, internship)
    return render_template('internships/match_analysis.html', internship=internship, match_data=match_data)
