from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.utils.decorators import role_required
from app import db
from app.models.interview import Interview
from app.models.application import Application
from app.models.internship import Internship
from app.models.company_profile import CompanyProfile
from app.models.student_profile import StudentProfile
from app.services.notification_service import (
    notify_interview_invitation, notify_interview_update, 
    notify_interview_cancelled, notify_interview_response
)
from datetime import datetime

interviews_bp = Blueprint('interviews', __name__)

# ==========================================
# COMPANY ROUTES
# ==========================================

@interviews_bp.route('/company/applications/<int:application_id>/interview/create', methods=['GET', 'POST'])
@login_required
@role_required('company')
def company_create_interview(application_id):
    company_profile = CompanyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    application = Application.query.join(Internship).filter(Application.id == application_id, Internship.company_profile_id == company_profile.id).first_or_404()
    
    if application.status in ['Rejected', 'Withdrawn']:
        flash('Cannot schedule interview for Rejected or Withdrawn applications.', 'danger')
        return redirect(url_for('applications.company_applicant_detail', application_id=application.id))

    if request.method == 'POST':
        interview_type = request.form.get('interview_type')
        scheduled_date_str = request.form.get('scheduled_date')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        meeting_link = request.form.get('meeting_link')
        location = request.form.get('location')
        instructions = request.form.get('instructions')
        company_notes = request.form.get('company_notes')

        try:
            scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            
            if end_time <= start_time:
                flash('End time must be after start time.', 'danger')
                return render_template('interviews/create_edit.html', application=application)
            
            if interview_type == 'Online' and not meeting_link:
                flash('Meeting link is required for online interviews.', 'danger')
                return render_template('interviews/create_edit.html', application=application)
                
            if interview_type == 'Offline' and not location:
                flash('Location is required for offline interviews.', 'danger')
                return render_template('interviews/create_edit.html', application=application)

            interview = Interview(
                application_id=application.id,
                scheduled_by=current_user.id,
                interview_type=interview_type,
                scheduled_date=scheduled_date,
                start_time=start_time,
                end_time=end_time,
                meeting_link=meeting_link,
                location=location,
                instructions=instructions,
                company_notes=company_notes
            )
            db.session.add(interview)
            db.session.commit()
            
            notify_interview_invitation(interview)
            flash('Interview scheduled successfully.', 'success')
            return redirect(url_for('applications.company_applicant_detail', application_id=application.id))
            
        except ValueError:
            flash('Invalid date or time format.', 'danger')

    return render_template('interviews/create_edit.html', application=application)

@interviews_bp.route('/company/interviews')
@login_required
@role_required('company')
def company_interviews():
    company_profile = CompanyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    status_filter = request.args.get('status', 'All')
    
    query = Interview.query.join(Application).join(Internship).filter(Internship.company_profile_id == company_profile.id)
    
    if status_filter == 'Upcoming':
        query = query.filter(Interview.status == 'Scheduled')
    elif status_filter == 'Pending Response':
        query = query.filter(Interview.student_response == 'Pending', Interview.status == 'Scheduled')
    elif status_filter == 'Completed':
        query = query.filter(Interview.status == 'Completed')
    elif status_filter == 'Cancelled':
        query = query.filter(Interview.status == 'Cancelled')

    interviews = query.order_by(Interview.scheduled_date.asc(), Interview.start_time.asc()).all()
    
    return render_template('interviews/company_interviews.html', interviews=interviews, current_filter=status_filter)

@interviews_bp.route('/company/interviews/<int:interview_id>')
@login_required
@role_required('company')
def company_interview_detail(interview_id):
    company_profile = CompanyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    interview = Interview.query.join(Application).join(Internship).filter(Interview.id == interview_id, Internship.company_profile_id == company_profile.id).first_or_404()
    return render_template('interviews/interview_detail.html', interview=interview, role='company')

@interviews_bp.route('/company/interviews/<int:interview_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('company')
def company_edit_interview(interview_id):
    company_profile = CompanyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    interview = Interview.query.join(Application).join(Internship).filter(Interview.id == interview_id, Internship.company_profile_id == company_profile.id).first_or_404()
    
    if interview.status != 'Scheduled':
        flash('Cannot edit a completed or cancelled interview.', 'danger')
        return redirect(url_for('interviews.company_interview_detail', interview_id=interview.id))

    if request.method == 'POST':
        interview.interview_type = request.form.get('interview_type')
        
        try:
            scheduled_date = datetime.strptime(request.form.get('scheduled_date'), '%Y-%m-%d').date()
            start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
            end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
            
            if end_time <= start_time:
                flash('End time must be after start time.', 'danger')
                return render_template('interviews/create_edit.html', application=interview.application, interview=interview)
            
            interview.scheduled_date = scheduled_date
            interview.start_time = start_time
            interview.end_time = end_time
            
        except ValueError:
            flash('Invalid date or time format.', 'danger')
            return render_template('interviews/create_edit.html', application=interview.application, interview=interview)

        interview.meeting_link = request.form.get('meeting_link')
        interview.location = request.form.get('location')
        interview.instructions = request.form.get('instructions')
        interview.company_notes = request.form.get('company_notes')
        
        if interview.interview_type == 'Online' and not interview.meeting_link:
            flash('Meeting link is required for online interviews.', 'danger')
            return render_template('interviews/create_edit.html', application=interview.application, interview=interview)
            
        if interview.interview_type == 'Offline' and not interview.location:
            flash('Location is required for offline interviews.', 'danger')
            return render_template('interviews/create_edit.html', application=interview.application, interview=interview)

        db.session.commit()
        notify_interview_update(interview)
        flash('Interview updated successfully.', 'success')
        return redirect(url_for('interviews.company_interview_detail', interview_id=interview.id))

    return render_template('interviews/create_edit.html', application=interview.application, interview=interview)

@interviews_bp.route('/company/interviews/<int:interview_id>/cancel', methods=['POST'])
@login_required
@role_required('company')
def company_cancel_interview(interview_id):
    company_profile = CompanyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    interview = Interview.query.join(Application).join(Internship).filter(Interview.id == interview_id, Internship.company_profile_id == company_profile.id).first_or_404()
    
    if interview.status != 'Cancelled':
        interview.status = 'Cancelled'
        interview.cancelled_at = datetime.utcnow()
        db.session.commit()
        notify_interview_cancelled(interview)
        flash('Interview cancelled successfully.', 'success')
        
    return redirect(url_for('interviews.company_interviews'))

# ==========================================
# STUDENT ROUTES
# ==========================================

@interviews_bp.route('/student/interviews')
@login_required
@role_required('student')
def student_interviews():
    student_profile = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    interviews = Interview.query.join(Application).filter(Application.student_profile_id == student_profile.id).order_by(Interview.scheduled_date.asc(), Interview.start_time.asc()).all()
    
    upcoming_interviews = [i for i in interviews if i.status == 'Scheduled']
    past_interviews = [i for i in interviews if i.status == 'Completed']
    cancelled_interviews = [i for i in interviews if i.status == 'Cancelled']
    
    return render_template('interviews/student_interviews.html', 
                           upcoming_interviews=upcoming_interviews,
                           past_interviews=past_interviews,
                           cancelled_interviews=cancelled_interviews)

@interviews_bp.route('/student/interviews/<int:interview_id>')
@login_required
@role_required('student')
def student_interview_detail(interview_id):
    student_profile = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    interview = Interview.query.join(Application).filter(Interview.id == interview_id, Application.student_profile_id == student_profile.id).first_or_404()
    return render_template('interviews/interview_detail.html', interview=interview, role='student')

@interviews_bp.route('/student/interviews/<int:interview_id>/accept', methods=['POST'])
@login_required
@role_required('student')
def student_accept_interview(interview_id):
    student_profile = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    interview = Interview.query.join(Application).filter(Interview.id == interview_id, Application.student_profile_id == student_profile.id).first_or_404()
    
    if interview.status == 'Cancelled':
        flash('You cannot accept a cancelled interview.', 'danger')
    elif interview.student_response != 'Accepted':
        interview.student_response = 'Accepted'
        db.session.commit()
        notify_interview_response(interview)
        flash('You have accepted the interview invitation.', 'success')
        
    return redirect(url_for('interviews.student_interview_detail', interview_id=interview.id))

@interviews_bp.route('/student/interviews/<int:interview_id>/decline', methods=['POST'])
@login_required
@role_required('student')
def student_decline_interview(interview_id):
    student_profile = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    interview = Interview.query.join(Application).filter(Interview.id == interview_id, Application.student_profile_id == student_profile.id).first_or_404()
    
    if interview.status == 'Cancelled':
        flash('You cannot decline a cancelled interview.', 'danger')
    elif interview.student_response != 'Declined':
        interview.student_response = 'Declined'
        db.session.commit()
        notify_interview_response(interview)
        flash('You have declined the interview invitation.', 'info')
        
    return redirect(url_for('interviews.student_interview_detail', interview_id=interview.id))
