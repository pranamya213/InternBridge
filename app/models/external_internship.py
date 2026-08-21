from datetime import datetime
import json
from app import db

class ExternalInternship(db.Model):
    __tablename__ = 'external_internships'
    __table_args__ = (
        db.UniqueConstraint('source_name', 'external_reference_id', name='uq_external_source_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    
    title = db.Column(db.String(150), nullable=False)
    company_name = db.Column(db.String(150), nullable=False)
    company_logo = db.Column(db.String(255))
    company_website = db.Column(db.String(255))
    company_description = db.Column(db.Text)
    
    short_description = db.Column(db.String(255))
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    internship_type = db.Column(db.String(100)) # Internship, Part-time Internship, Full-time Internship
    work_mode = db.Column(db.String(50)) # Remote, Hybrid, On-site
    location = db.Column(db.String(150))
    country = db.Column(db.String(100))
    state = db.Column(db.String(100))
    city = db.Column(db.String(100))
    duration = db.Column(db.String(100))
    
    stipend_type = db.Column(db.String(50)) # Paid, Unpaid, Performance-based, Negotiable
    stipend = db.Column(db.String(100))
    openings = db.Column(db.Integer)
    
    eligibility = db.Column(db.Text)
    required_skills_json = db.Column(db.Text) # JSON string array
    preferred_skills_json = db.Column(db.Text) # JSON string array
    responsibilities = db.Column(db.Text)
    qualifications = db.Column(db.Text)
    benefits = db.Column(db.Text)
    
    application_deadline = db.Column(db.Date, nullable=False)
    application_url = db.Column(db.String(500), nullable=False)
    source_name = db.Column(db.String(100), default='Admin Curated')
    source_url = db.Column(db.String(500))
    external_reference_id = db.Column(db.String(100))
    
    status = db.Column(db.String(20), default='Draft') # Draft, Published, Closed, Archived, Expired
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id')) # Admin who created it
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    fetched_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_required_skills(self, skills_list):
        self.required_skills_json = json.dumps(skills_list)
        
    def get_required_skills(self):
        return json.loads(self.required_skills_json) if self.required_skills_json else []
        
    def set_preferred_skills(self, skills_list):
        self.preferred_skills_json = json.dumps(skills_list)
        
    def get_preferred_skills(self):
        return json.loads(self.preferred_skills_json) if self.preferred_skills_json else []
