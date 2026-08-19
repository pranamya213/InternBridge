from datetime import datetime
from app import db

class Interview(db.Model):
    __tablename__ = 'interviews'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    scheduled_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    interview_type = db.Column(db.String(30), nullable=False) # Online, Offline, Phone
    scheduled_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    
    meeting_link = db.Column(db.String(500), nullable=True)
    location = db.Column(db.String(300), nullable=True)
    instructions = db.Column(db.Text, nullable=True)
    
    status = db.Column(db.String(30), nullable=False, default='Scheduled') # Scheduled, Completed, Cancelled
    student_response = db.Column(db.String(30), nullable=True, default='Pending') # Pending, Accepted, Declined
    company_notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    application = db.relationship('Application', backref=db.backref('interviews', lazy=True, cascade='all, delete-orphan', order_by='Interview.scheduled_date.asc(), Interview.start_time.asc()'))
    scheduler = db.relationship('User', backref=db.backref('scheduled_interviews', lazy=True))
