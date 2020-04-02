import re
import sys
import traceback
from functools import wraps

from flask import Response, request, render_template, send_file, redirect, url_for, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash

from . import app, db, login_manager
from .models import Student, User, Message
from .helper import ykps_auth



#################### Web Pages ####################

@app.route('/')
def index_page():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_page'))
    else:
        return redirect(url_for('login_page'))


@app.route('/login')
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_page'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout_page():
    logout_user()
    return redirect(url_for('login_page'))


# @app.route('/match-teacher')
# @login_required
# def match_teacher_page():
#     if not (current_user.is_teacher and current_user.teacher_id == None):
#         # Ensure only the correct users are accessing
#         return redirect(url_for('dashboard_page'))
        
#     # Get all teachers who are not yet matched to a user
#     subquery = db.session.query(User.teacher_id).filter(User.teacher_id.isnot(None))
#     query_filter = Teacher.id.notin_(subquery)
#     teachers = Teacher.query.filter(query_filter).all()
#     return render_template('match-teacher.html', teachers=teachers)


@app.route('/dashboard')
@login_required
def dashboard_page():
    # messages = Message.query.filter_by(student_id=current_user.id).all()
    messages = User.query.get(current_user.id).student.messages
    return render_template('dashboard.html', messages=messages)


@app.route('/message/new')
@login_required
def new_message_page():
    # Get all classes which the student has no feedback in
    subquery = db.session.query(Message.recipient_id).filter(Message.author_id == current_user.student.id)
    query_filter = Student.id.notin_(subquery)
    students = Student.query.filter(query_filter).filter(Student.id != current_user.student.id).all()
    if not students:
        # No student left to leave a message
        # TODO: Notify the user about this
        return redirect(url_for('dashboard_page'))

    return render_template('new-message.html', students=students)


@app.route('/feedback/edit/<feedback_id>')
@login_required
def edit_feedback_page(feedback_id):
    if current_user.is_teacher:
        # Ensure only the correct users are accessing
        return redirect(url_for('dashboard_page'))
    
    feedback = Feedback.query.get(feedback_id)

    if not feedback or feedback.student_id != current_user.id:
        # Data validation and authentication
        return redirect(url_for('dashboard_page'))
    
    # Get all classes which the student has no feedback in
    subquery = db.session.query(Feedback.class_id).filter(Feedback.student_id == current_user.id)
    query_filter = Class.id.notin_(subquery)
    classes = Class.query.filter(query_filter).all()

    return render_template('edit-feedback.html', current=feedback, classes=classes)


# @app.route('/feedback/export')
# @login_required
# def export_feedback_page():
#     if not current_user.is_teacher:
#         # Ensure only the correct users are accessing
#         return redirect(url_for('dashboard_page'))
    
#     classes = Class.query.filter_by(teacher_id=current_user.teacher.id).all()

#     if not classes:
#         # No class left to give feedback
#         # TODO: Notify the user about this
#         return redirect(url_for('dashboard_page'))

#     return render_template('export-feedback.html', classes=classes)



#################### APIs ####################

@app.route('/login', methods=['POST'])
def login():
    '''API for authenticating via the school's system.'''

    # Get form data, defaults to empty string
    username = request.form.get('username', '')
    password = request.form.get('password', '')

    success_flag = False

    if all((username, password)): # Data validation
        # Try fetching user from database
        student = Student.query.filter_by(school_id=username).first()

        if not student:
            success_flag = False

        # New user trying to log in
        elif not student.user:
            # Authenticate via PowerSchool
            code, name = ykps_auth(username, password)

            if code == 0:
                # User credentials validated, insert into database
                hashed_password = generate_password_hash(password)
                is_new_teacher = not re.match(r's\d{5}', username)
                user = User(student_id=student.id, password=hashed_password)
                db.session.add(user)
                db.session.commit()
                success_flag = True
        
        # If user is already in the database, validate credentials directly
        elif student.user[0].authenticate(password):
            success_flag = True

    if success_flag:
        # User credentials validated, logs in the user
        login_user(student.user[0])
        return redirect(url_for('dashboard_page'))
    else:
        return render_template('login.html', login_msg='Incorrect credentials!')


# @app.route('/match-teacher', methods=['POST'])
# @login_required
# def match_teacher():
#     '''API for matching a teacher user to a teacher.'''

#     if not (current_user.is_teacher and current_user.teacher_id == None):
#         # Ensure only the correct users are accessing
#         return redirect(url_for('dashboard_page'))

#     # Get form data, defaults to empty string
#     teacher_id = request.form.get('teacher-id', '')

#     # TODO: Data validation

#     # Update user's teacher_id field
#     current_user.teacher_id = teacher_id
#     db.session.commit()
#     return redirect(url_for('dashboard_page'))


@app.route('/feedback/delete', methods=['POST'])
@login_required
def delete_feedback():
    '''API for deleting a feedback.'''

    if current_user.is_teacher:
        # Ensure only the correct users are accessing
        return jsonify({'code': 2})

    # Get form data, defaults to empty string
    feedback_id = request.form.get('id', '')

    # TODO: Data validation

    # Validate data and perform deletion in the database
    feedback = Feedback.query.filter_by(id=feedback_id) # Cannot use get here
    if not feedback:
        return jsonify({'code': 1})
    feedback.delete()
    db.session.commit()
    return jsonify({'code': 0})


@app.route('/message/new', methods=['POST'])
@login_required
def new_message():
    '''API for creating a new message.'''

    message_recipient_id = request.form.get('message-recipient', '')
    message_content = request.form.get('message-content', '')
    message_anonymous = request.form.get('message-anonymous', 'off')

    # TODO: Data validation

    message_anonymous = True if message_anonymous == 'on' else False

    # Performs database insertion
    message = Message(author_id=current_user.student.id, recipient_id=message_recipient_id, content=message_content, is_anonymous=message_anonymous)
    db.session.add(message)
    db.session.commit()

    return redirect(url_for('dashboard_page'))


@app.route('/feedback/edit/<feedback_id>', methods=['POST'])
@login_required
def edit_feedback(feedback_id):
    if current_user.is_teacher:
        # Ensure only the correct users are accessing
        return redirect(url_for('dashboard_page'))
    
    feedback = Feedback.query.get(feedback_id)
    feedback_class_id = request.form.get('feedback-class', '')
    feedback_content = request.form.get('feedback-content', '')
    feedback_anonymous = request.form.get('feedback-anonymous', 'off')

    # TODO: Data validation

    if not feedback or feedback.student_id != current_user.id:
        # Data validation and authentication
        return redirect(url_for('dashboard_page'))
    
    feedback_anonymous = True if feedback_anonymous == 'on' else False

    # Update feedback
    feedback.class_id = feedback_class_id
    feedback.content = feedback_content
    feedback.is_anonymous = feedback_anonymous
    db.session.commit()

    return redirect(url_for('dashboard_page'))


# @app.route('/feedback/export', methods=['POST'])
# @login_required
# def export_feedback():
#     if not current_user.is_teacher:
#         # Ensure only the correct users are accessing
#         return redirect(url_for('dashboard_page'))

#     classes = request.form.getlist('classes')
#     export_format = request.form.get('export-format', '')

#     if not classes or not export_format in ('excel', 'csv'):
#         # No classes selected or incorrect format
#         # TODO: Notify user about this
#         return redirect(url_for('export_feedback_page'))
    
#     # Get all requested feedbacks
#     df = pd.read_sql(
#         db.session.query(
#             Feedback.class_id,
#             Feedback.student_id,
#             Feedback.content.label('Content'),
#             Feedback.is_anonymous
#         ).filter(Feedback.class_id.in_(classes)).order_by(Feedback.class_id).statement,
#         db.session.bind
#     )
#     # Get the file path and filename
#     filepath, filename = get_export_file(export_format)

#     # Process data frame
#     df['Class'] = df.apply(lambda row: Class.query.get(row['class_id']).name, axis=1)
#     df['Student'] = df.apply(lambda row: 'Anonymous' if row['is_anonymous'] else User.query.get(row['student_id']).name, axis=1)
#     df.drop(columns=['class_id', 'student_id', 'is_anonymous'], inplace=True) # Drop columns
#     df = df[['Class', 'Student', 'Content']] # Reorder columns
    
#     # Export data frame to file
#     if export_format == 'excel':
#         df.to_excel(filepath, sheet_name='Feedbacks', index=False)
#     elif export_format == 'csv':
#         with open(filepath, 'w', encoding='utf-8') as f:
#             df.to_csv(f, index=False)

#     return send_file(filepath, as_attachment=True, attachment_filename=filename)



#################### Misc Views ####################

@login_manager.unauthorized_handler
def unauthorized_access():
    '''Redicts unauthorized users to login page.'''
    return redirect(url_for('login_page'))
