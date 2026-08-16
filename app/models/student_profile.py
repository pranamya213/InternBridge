from datetime import datetime
import json
from app import db

class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    
    # Basic Info
    headline = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    location = db.Column(db.String(100))
    dob = db.Column(db.Date)
    profile_picture = db.Column(db.String(255)) # URL or filename
    
    # About
    about_me = db.Column(db.Text)
    
    # Preferences (JSON storage as requested)
    work_mode_preferences = db.Column(db.Text) # Stored as JSON string
    location_preferences = db.Column(db.Text) # Stored as JSON string
    internship_duration = db.Column(db.String(50))
    availability = db.Column(db.String(100))

    # Relationships
    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))
    education = db.relationship('Education', backref='profile', cascade='all, delete-orphan')
    skills = db.relationship('StudentSkill', backref='profile', cascade='all, delete-orphan')
    career_interests = db.relationship('CareerInterest', backref='profile', cascade='all, delete-orphan')
    projects = db.relationship('Project', backref='profile', cascade='all, delete-orphan')
    certifications = db.relationship('Certification', backref='profile', cascade='all, delete-orphan')
    experience = db.relationship('Experience', backref='profile', cascade='all, delete-orphan')
    professional_links = db.relationship('ProfessionalLink', backref='profile', cascade='all, delete-orphan')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_work_modes(self, modes_list):
        self.work_mode_preferences = json.dumps(modes_list)
        
    def get_work_modes(self):
        return json.loads(self.work_mode_preferences) if self.work_mode_preferences else []
        
    def set_locations(self, locations_list):
        self.location_preferences = json.dumps(locations_list)
        
    def get_locations(self):
        return json.loads(self.location_preferences) if self.location_preferences else []


class Education(db.Model):
    __tablename__ = 'education'

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    
    degree = db.Column(db.String(100), nullable=False)
    institution = db.Column(db.String(150), nullable=False)
    field_of_study = db.Column(db.String(100), nullable=False)
    start_year = db.Column(db.Integer, nullable=False)
    end_year = db.Column(db.Integer)
    currently_studying = db.Column(db.Boolean, default=False)
    cgpa = db.Column(db.String(20))


class StudentSkill(db.Model):
    __tablename__ = 'student_skills'

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    
    skill_name = db.Column(db.String(100), nullable=False)
    proficiency = db.Column(db.String(20)) # Beginner, Intermediate, Advanced


class CareerInterest(db.Model):
    __tablename__ = 'career_interests'

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    
    role_name = db.Column(db.String(100), nullable=False)


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    technologies = db.Column(db.String(200)) # Comma separated or simple string is fine here as per example
    github_url = db.Column(db.String(255))
    live_demo_url = db.Column(db.String(255))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)


class Certification(db.Model):
    __tablename__ = 'certifications'

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    
    name = db.Column(db.String(150), nullable=False)
    organization = db.Column(db.String(150), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date)
    certificate_id = db.Column(db.String(100))
    certificate_url = db.Column(db.String(255))


class Experience(db.Model):
    __tablename__ = 'experience'

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    
    job_title = db.Column(db.String(100), nullable=False)
    organization = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    currently_working = db.Column(db.Boolean, default=False)


class ProfessionalLink(db.Model):
    __tablename__ = 'professional_links'

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    
    platform = db.Column(db.String(50), nullable=False) # GitHub, LinkedIn, Portfolio, Other
    url = db.Column(db.String(255), nullable=False)
