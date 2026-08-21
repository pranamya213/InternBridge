from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from app.models.internship import Internship
from app.models.external_internship import ExternalInternship
from app.models.company_profile import CompanyProfile
from app.models.student_profile import StudentProfile
from app.utils.decorators import role_required
from app.services.matching_service import calculate_match
from sqlalchemy import or_
from datetime import datetime

internships_bp = Blueprint('internships', __name__)

@internships_bp.route('/')
def index():
    # 1. Fetch Internal Internships
    internal_query = Internship.query.filter_by(status='Published')
    
    # Filter out expired ones for internal if applicable (usually handled by status, but let's be safe)
    today = datetime.utcnow().date()
    internal_query = internal_query.filter(or_(Internship.application_deadline >= today, Internship.application_deadline == None))
    
    # 2. Fetch External Internships
    external_query = ExternalInternship.query.filter_by(status='Published')
    external_query = external_query.filter(or_(ExternalInternship.application_deadline >= today, ExternalInternship.application_deadline == None))
    
    search = request.args.get('search')
    if search:
        search_term = f"%{search}%"
        internal_query = internal_query.join(CompanyProfile).filter(
            or_(
                Internship.title.ilike(search_term),
                Internship.category.ilike(search_term),
                Internship.required_skills_json.ilike(search_term),
                CompanyProfile.company_name.ilike(search_term)
            )
        )
        external_query = external_query.filter(
            or_(
                ExternalInternship.title.ilike(search_term),
                ExternalInternship.category.ilike(search_term),
                ExternalInternship.required_skills_json.ilike(search_term),
                ExternalInternship.company_name.ilike(search_term)
            )
        )
        
    work_mode = request.args.get('work_mode')
    if work_mode:
        internal_query = internal_query.filter(Internship.work_mode == work_mode)
        external_query = external_query.filter(ExternalInternship.work_mode == work_mode)
        
    domain = request.args.get('domain')
    if domain:
        internal_query = internal_query.filter(Internship.category == domain)
        external_query = external_query.filter(ExternalInternship.category == domain)
        
    duration = request.args.get('duration')
    if duration:
        internal_query = internal_query.filter(Internship.duration == duration)
        external_query = external_query.filter(ExternalInternship.duration == duration)
        
    country = request.args.get('country')
    if country:
        # Note: Internal internships don't have 'country' field yet, we use a simple string match for now
        # or we just let them pass if they don't explicitly say 'International'
        if country == 'International':
            external_query = external_query.filter(ExternalInternship.country == 'International')
        elif country == 'India':
            external_query = external_query.filter(ExternalInternship.country == 'India')

    state = request.args.get('state')
    if state and country == 'India':
        external_query = external_query.filter(ExternalInternship.state == state)

    source_filter = request.args.get('source_filter')
    
    internal_internships = []
    if not source_filter or source_filter == 'InternBridge':
        internal_internships = internal_query.all()
        for i in internal_internships:
            i.is_external = False
            i.display_company_name = i.company.company_name
            i.display_source = 'InternBridge'
            
            # Simple heuristic for internal internships since they don't have country/state yet
            loc_lower = (i.location or '').lower()
            if any(k in loc_lower for k in ['bengaluru', 'bangalore', 'mysuru', 'karnataka', 'hubballi']):
                i.loc_priority = 0
            elif 'india' in loc_lower or (i.location and i.location.strip() != ''):
                i.loc_priority = 1
            else:
                i.loc_priority = 2 # Unknown
            
    external_internships = []
    if not source_filter or source_filter == 'External':
        external_internships = external_query.all()
        for i in external_internships:
            i.is_external = True
            i.display_company_name = i.company_name
            i.display_source = i.source_name
            
            if i.state == 'Karnataka':
                i.loc_priority = 0
            elif i.country == 'India':
                i.loc_priority = 1
            elif i.country == 'International':
                i.loc_priority = 3
            else:
                i.loc_priority = 2
            
    all_internships = internal_internships + external_internships
    
    # Hide international unless explicitly requested
    if not country:
        all_internships = [i for i in all_internships if getattr(i, 'loc_priority', 2) != 3]
    elif country != 'International':
        all_internships = [i for i in all_internships if getattr(i, 'loc_priority', 2) != 3]
    
    # Calculate match scores if student is logged in
    student_profile = None
    if current_user.is_authenticated and current_user.role == 'student':
        student_profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        if student_profile:
            for internship in all_internships:
                match_data = calculate_match(student_profile, internship)
                internship.match_data = match_data
                internship.match_score = match_data['score']
                
    sort_by = request.args.get('sort_by', 'recommended')
    
    if sort_by == 'newest':
        all_internships.sort(key=lambda x: (getattr(x, 'loc_priority', 2), -(getattr(x, 'published_at', None) or getattr(x, 'created_at', None) or datetime.min).timestamp()))
    elif sort_by == 'deadline_soonest':
        all_internships.sort(key=lambda x: (getattr(x, 'loc_priority', 2), getattr(x, 'application_deadline', None) or datetime.max.date()))
    elif sort_by == 'recently_updated':
        all_internships.sort(key=lambda x: (getattr(x, 'loc_priority', 2), -(getattr(x, 'updated_at', None) or datetime.min).timestamp()))
    else: # recommended or default
        if student_profile:
            all_internships.sort(key=lambda x: (getattr(x, 'loc_priority', 2), -getattr(x, 'match_score', 0), -(getattr(x, 'published_at', None) or getattr(x, 'created_at', None) or datetime.min).timestamp()))
        else:
            all_internships.sort(key=lambda x: (getattr(x, 'loc_priority', 2), -(getattr(x, 'published_at', None) or getattr(x, 'created_at', None) or datetime.min).timestamp()))
            
    # Fetch unique domains and durations
    domains_internal = [i[0] for i in Internship.query.with_entities(Internship.category).filter(Internship.status == 'Published', Internship.category != None).distinct().all()]
    domains_external = [i[0] for i in ExternalInternship.query.with_entities(ExternalInternship.category).filter(ExternalInternship.status == 'Published', ExternalInternship.category != None).distinct().all()]
    domains = sorted(list(set(domains_internal + domains_external)))
    
    durations_internal = [i[0] for i in Internship.query.with_entities(Internship.duration).filter(Internship.status == 'Published', Internship.duration != None).distinct().all()]
    durations_external = [i[0] for i in ExternalInternship.query.with_entities(ExternalInternship.duration).filter(ExternalInternship.status == 'Published', ExternalInternship.duration != None).distinct().all()]
    durations = sorted(list(set(durations_internal + durations_external)))
    
    from app.utils.location_helpers import INDIAN_STATES
    indian_states_list = sorted(list(INDIAN_STATES.values()))
    
    return render_template('internships/index.html', internships=all_internships, domains=domains, durations=durations, indian_states=indian_states_list)

@internships_bp.route('/<int:internship_id>')
def detail(internship_id):
    internship = Internship.query.filter(Internship.id == internship_id, Internship.status.in_(['Published', 'Closed'])).first_or_404()
    internship.is_external = False
    
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
                
    is_past_deadline = False
    if internship.application_deadline and internship.application_deadline < datetime.utcnow().date():
        is_past_deadline = True
                
    return render_template('internships/detail.html', internship=internship, has_applied=has_applied, application_id=application_id, is_past_deadline=is_past_deadline, match_data=match_data)

@internships_bp.route('/external/<int:internship_id>')
def external_detail(internship_id):
    internship = ExternalInternship.query.filter(ExternalInternship.id == internship_id, ExternalInternship.status.in_(['Published', 'Closed'])).first_or_404()
    internship.is_external = True
    
    match_data = None
    
    if current_user.is_authenticated and current_user.role == 'student':
        from app.models.student_profile import StudentProfile
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        if profile:
            match_data = calculate_match(profile, internship)
            
    is_past_deadline = False
    if internship.application_deadline and internship.application_deadline < datetime.utcnow().date():
        is_past_deadline = True
                
    return render_template('internships/detail.html', internship=internship, has_applied=False, application_id=None, is_past_deadline=is_past_deadline, match_data=match_data)


@internships_bp.route('/<int:internship_id>/match')
@login_required
@role_required('student')
def match_analysis(internship_id):
    internship = Internship.query.filter(Internship.id == internship_id, Internship.status.in_(['Published', 'Closed'])).first_or_404()
    internship.is_external = False
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    
    if not profile:
        flash("Please complete your profile to see match analysis.", "warning")
        return redirect(url_for('student.profile_edit'))
        
    match_data = calculate_match(profile, internship)
    return render_template('internships/match_analysis.html', internship=internship, match_data=match_data)

@internships_bp.route('/external/<int:internship_id>/match')
@login_required
@role_required('student')
def external_match_analysis(internship_id):
    internship = ExternalInternship.query.filter(ExternalInternship.id == internship_id, ExternalInternship.status.in_(['Published', 'Closed'])).first_or_404()
    internship.is_external = True
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    
    if not profile:
        flash("Please complete your profile to see match analysis.", "warning")
        return redirect(url_for('student.profile_edit'))
        
    match_data = calculate_match(profile, internship)
    return render_template('internships/match_analysis.html', internship=internship, match_data=match_data)
