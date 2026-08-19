from app import db
from app.models.notification import Notification
from flask import url_for

def create_notification(user_id, notification_type, title, message, link=None, related_application_id=None, related_internship_id=None):
    """
    Core function to create and save a notification.
    """
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link,
        related_application_id=related_application_id,
        related_internship_id=related_internship_id
    )
    db.session.add(notification)
    db.session.commit()
    return notification

def notify_application_submitted(application):
    """Notify company when a new application is received."""
    # Prevent duplicate notification for same application
    existing = Notification.query.filter_by(
        user_id=application.internship.company.user_id,
        notification_type='application_submitted',
        related_application_id=application.id
    ).first()
    
    if existing:
        return
        
    student_name = application.student.user.full_name
    internship_title = application.internship.title
    
    create_notification(
        user_id=application.internship.company.user_id,
        notification_type='application_submitted',
        title='New Application Received',
        message=f'{student_name} has applied for {internship_title}.',
        link=url_for('applications.company_applicant_detail', application_id=application.id),
        related_application_id=application.id,
        related_internship_id=application.internship_id
    )

def notify_application_status_change(application):
    """Notify student when their application status changes."""
    status = application.status
    internship_title = application.internship.title
    
    if status == 'Under Review':
        title = 'Application Under Review'
        message = f'Your application for {internship_title} is now under review.'
    elif status == 'Shortlisted':
        title = 'Application Shortlisted'
        message = f'Great news! You have been shortlisted for {internship_title}.'
    elif status == 'Accepted':
        title = 'Application Accepted'
        message = f'Congratulations! Your application for {internship_title} has been accepted.'
    elif status == 'Rejected':
        title = 'Application Update'
        message = f'Your application for {internship_title} was not selected this time.'
    else:
        return # Do not notify for Withdrawn or Applied statuses
        
    create_notification(
        user_id=application.student.user_id,
        notification_type='application_status_changed',
        title=title,
        message=message,
        link=url_for('applications.student_application_detail', application_id=application.id),
        related_application_id=application.id,
        related_internship_id=application.internship_id
    )

def notify_interview_invitation(interview):
    """Notify student about a new interview invitation."""
    student_id = interview.application.student.user_id
    internship_title = interview.application.internship.title
    date_str = interview.scheduled_date.strftime('%B %d, %Y')
    time_str = interview.start_time.strftime('%I:%M %p')
    
    create_notification(
        user_id=student_id,
        notification_type='interview_invitation',
        title='📅 Interview Invitation',
        message=f'You have been invited for an interview for {internship_title} on {date_str} at {time_str}.',
        link=url_for('interviews.student_interview_detail', interview_id=interview.id),
        related_application_id=interview.application_id,
        related_internship_id=interview.application.internship_id
    )

def notify_interview_update(interview):
    """Notify student when an interview is updated."""
    student_id = interview.application.student.user_id
    internship_title = interview.application.internship.title
    date_str = interview.scheduled_date.strftime('%B %d, %Y')
    time_str = interview.start_time.strftime('%I:%M %p')
    
    create_notification(
        user_id=student_id,
        notification_type='interview_updated',
        title='Interview Updated',
        message=f'Your interview for {internship_title} has been updated to {date_str} at {time_str}.',
        link=url_for('interviews.student_interview_detail', interview_id=interview.id),
        related_application_id=interview.application_id,
        related_internship_id=interview.application.internship_id
    )

def notify_interview_cancelled(interview):
    """Notify student when an interview is cancelled."""
    student_id = interview.application.student.user_id
    internship_title = interview.application.internship.title
    
    create_notification(
        user_id=student_id,
        notification_type='interview_cancelled',
        title='Interview Cancelled',
        message=f'Your scheduled interview for {internship_title} has been cancelled.',
        link=url_for('interviews.student_interview_detail', interview_id=interview.id),
        related_application_id=interview.application_id,
        related_internship_id=interview.application.internship_id
    )

def notify_interview_response(interview):
    """Notify company when a student accepts or declines an interview."""
    company_user_id = interview.application.internship.company.user_id
    student_name = interview.application.student.user.full_name
    response = interview.student_response
    
    if response == 'Accepted':
        title = 'Interview Accepted'
        message = f'{student_name} has accepted the interview invitation.'
    elif response == 'Declined':
        title = 'Interview Declined'
        message = f'{student_name} has declined the interview invitation.'
    else:
        return
        
    create_notification(
        user_id=company_user_id,
        notification_type='interview_response',
        title=title,
        message=message,
        link=url_for('interviews.company_interview_detail', interview_id=interview.id),
        related_application_id=interview.application_id,
        related_internship_id=interview.application.internship_id
    )

def notify_high_match_candidate(application, match_score):
    """Notify company about a high match candidate."""
    # Prevent duplicate high-match notification
    existing = Notification.query.filter_by(
        user_id=application.internship.company.user_id,
        notification_type='high_match_candidate',
        related_application_id=application.id
    ).first()
    
    if existing:
        return
        
    student_name = application.student.user.full_name
    internship_title = application.internship.title
    
    create_notification(
        user_id=application.internship.company.user_id,
        notification_type='high_match_candidate',
        title='⭐ High-Match Candidate Applied',
        message=f'{student_name} matches {match_score}% of the requirements for {internship_title}.',
        link=url_for('applications.company_applicant_detail', application_id=application.id),
        related_application_id=application.id,
        related_internship_id=application.internship_id
    )
