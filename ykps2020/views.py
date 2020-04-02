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


@app.route('/dashboard')
@login_required
def dashboard_page():
    # messages = Message.query.filter_by(student_id=current_user.id).all()
    messages = User.query.get(current_user.id).student.messages
    return render_template('dashboard.html', messages=messages)


@app.route('/message/new')
@login_required
def new_message_page():
    # Get all students the user has not written a message to
    subquery = db.session.query(Message.recipient_id).filter(Message.author_id == current_user.student.id)
    query_filter = Student.id.notin_(subquery)
    students = Student.query.filter(query_filter).filter(Student.id != current_user.student.id).all()
    if not students:
        # No student left to leave a message
        # TODO: Notify the user about this
        return redirect(url_for('dashboard_page'))

    return render_template('new-message.html', students=students)


@app.route('/message/edit/<message_id>')
@login_required
def edit_message_page(message_id):
    
    message = Message.query.get(message_id)

    if not message or message.author_id != current_user.student.id:
        # Data validation and authentication
        return redirect(url_for('dashboard_page'))
    
    # Get all students the user has not written a message to
    subquery = db.session.query(Message.recipient_id).filter(Message.author_id == current_user.student.id)
    query_filter = Student.id.notin_(subquery)
    students = Student.query.filter(query_filter).filter(Student.id != current_user.student.id).all()

    return render_template('edit-message.html', current=message, students=students)



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


@app.route('/message/delete', methods=['POST'])
@login_required
def delete_message():
    '''API for deleting a message.'''

    # Get form data, defaults to empty string
    message_id = request.form.get('id', '')

    # TODO: Data validation

    # Validate data and perform deletion in the database
    message = Message.query.filter_by(id=message_id) # Cannot use get here
    if not message:
        return jsonify({'code': 1})
    message.delete()
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


@app.route('/message/edit/<message_id>', methods=['POST'])
@login_required
def edit_message(message_id):

    message = Message.query.get(message_id)
    message_recipient_id = request.form.get('message-recipient', '')
    message_content = request.form.get('message-content', '')
    message_anonymous = request.form.get('message-anonymous', 'off')

    # TODO: Data validation

    if not message or message.author_id != current_user.student.id:
        # Data validation and authentication
        return redirect(url_for('dashboard_page'))
    
    message_anonymous = True if message_anonymous == 'on' else False

    # Update message
    message.recipient_id = message_recipient_id
    message.content = message_content
    message.is_anonymous = message_anonymous
    db.session.commit()

    return redirect(url_for('dashboard_page'))



#################### Misc Views ####################

@login_manager.unauthorized_handler
def unauthorized_access():
    '''Redicts unauthorized users to login page.'''
    return redirect(url_for('login_page'))
