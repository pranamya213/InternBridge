from datetime import datetime
from app import db

class Application(db.Model):
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    internship_id = db.Column(db.Integer, db.ForeignKey('internships.id'), nullable=False)
    student_profile_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    
    cover_letter = db.Column(db.Text)
    
    status = db.Column(db.String(50), default='Applied')
    company_notes = db.Column(db.Text)
    
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)

    __table_args__ = (
        db.UniqueConstraint('internship_id', 'student_profile_id', name='uix_internship_student'),
    )

    # Relationships are set up on the related models

class ApplicationStatusHistory(db.Model):
    __tablename__ = 'application_status_history'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    
    status = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    application = db.relationship('Application', backref=db.backref('status_history', lazy=True, cascade='all, delete-orphan', order_by='ApplicationStatusHistory.created_at'))
