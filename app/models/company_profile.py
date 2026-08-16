from datetime import datetime
import json
from app import db

class CompanyProfile(db.Model):
    __tablename__ = 'company_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    
    # Basic Organization Information
    company_name = db.Column(db.String(150), nullable=False)
    organization_type = db.Column(db.String(100)) # Startup, Enterprise, etc.
    logo = db.Column(db.String(255))
    industry = db.Column(db.String(150))
    founded_year = db.Column(db.Integer)
    company_size = db.Column(db.String(50))
    location = db.Column(db.String(150))
    tagline = db.Column(db.String(150))
    about_company = db.Column(db.Text)
    
    # Professional Information
    website = db.Column(db.String(255))
    linkedin = db.Column(db.String(255))
    github = db.Column(db.String(255))
    other_link = db.Column(db.String(255))
    
    # Contact Information
    contact_person_name = db.Column(db.String(100))
    contact_person_role = db.Column(db.String(100))
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    
    # Hiring Information
    domains_json = db.Column(db.Text) # JSON string for areas of work
    work_modes_json = db.Column(db.Text) # JSON string for Remote, Hybrid, On-site
    internship_duration = db.Column(db.String(100))
    internship_availability = db.Column(db.String(100))

    # Relationships
    user = db.relationship('User', backref=db.backref('company_profile', uselist=False))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_domains(self, domains_list):
        self.domains_json = json.dumps(domains_list)
        
    def get_domains(self):
        return json.loads(self.domains_json) if self.domains_json else []
        
    def set_work_modes(self, modes_list):
        self.work_modes_json = json.dumps(modes_list)
        
    def get_work_modes(self):
        return json.loads(self.work_modes_json) if self.work_modes_json else []
