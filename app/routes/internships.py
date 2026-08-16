from flask import Blueprint, render_template, request
from app.models.internship import Internship
from app.models.company_profile import CompanyProfile
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
    if sort_by == 'newest':
        query = query.order_by(Internship.published_at.desc())
    elif sort_by == 'deadline_soonest':
        # Need to handle null deadlines; putting them last usually involves more complex order_by, 
        # but for simplicity we order by deadline asc
        query = query.order_by(Internship.application_deadline.asc())
    elif sort_by == 'recently_updated':
        query = query.order_by(Internship.updated_at.desc())
        
    internships = query.all()
    
    # Fetch unique domains and durations for filters
    # In a real app we might cache this or query distinct values
    domains = [i[0] for i in Internship.query.with_entities(Internship.category).filter(Internship.status == 'Published', Internship.category != None).distinct().all()]
    durations = [i[0] for i in Internship.query.with_entities(Internship.duration).filter(Internship.status == 'Published', Internship.duration != None).distinct().all()]
    
    return render_template('internships/index.html', internships=internships, domains=domains, durations=durations)

@internships_bp.route('/<int:internship_id>')
def detail(internship_id):
    # Only allow viewing published internships
    internship = Internship.query.filter_by(id=internship_id, status='Published').first_or_404()
    return render_template('internships/detail.html', internship=internship)
