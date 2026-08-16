from datetime import datetime
import json
from app import db

class Internship(db.Model):
    __tablename__ = 'internships'

    id = db.Column(db.Integer, primary_key=True)
    company_profile_id = db.Column(db.Integer, db.ForeignKey('company_profiles.id'), nullable=False)
    
    title = db.Column(db.String(150), nullable=False)
    short_description = db.Column(db.String(255))
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    internship_type = db.Column(db.String(100)) # Internship, Part-time Internship, Full-time Internship
    work_mode = db.Column(db.String(50)) # Remote, Hybrid, On-site
    location = db.Column(db.String(150))
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
    
    application_deadline = db.Column(db.Date)
    
    status = db.Column(db.String(20), default='Draft') # Draft, Published, Closed, Archived
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime)
    
    applications = db.relationship('Application', backref='internship', lazy=True, cascade="all, delete-orphan")

    def set_required_skills(self, skills_list):
        self.required_skills_json = json.dumps(skills_list)
        
    def get_required_skills(self):
        return json.loads(self.required_skills_json) if self.required_skills_json else []
        
    def set_preferred_skills(self, skills_list):
        self.preferred_skills_json = json.dumps(skills_list)
        
    def get_preferred_skills(self):
        return json.loads(self.preferred_skills_json) if self.preferred_skills_json else []
