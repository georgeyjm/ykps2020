import re
import sys
import traceback
from functools import wraps

from flask import Response, request, render_template, send_file, redirect, url_for, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash

from . import app, db, login_manager
from .models import Student, User, Message
from .forms import LoginForm
from .helper import ykps_auth, get_available_students



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
    form = LoginForm()
    return render_template('login.html', form=form)


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
    students = get_available_students()
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
    students = get_available_students()

    return render_template('edit-message.html', current=message, students=students)



#################### APIs ####################

@app.route('/login', methods=['POST'])
def login():
    '''Process POST request for authenticating a user.'''
    success_flag = False
    return_msg = 'Invalid credentials!'

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Try fetching user from database
        student = Student.query.filter_by(school_id=username).first()
        if not student:
            return_msg = 'You are not a Y12 student!'

        # New user trying to log in
        elif not student.user:
            # Authenticate via PowerSchool
            code, _ = ykps_auth(username, password)
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
        # User credentials validated, log in the user
        login_user(student.user[0])
        return redirect(url_for('dashboard_page'))
    else:
        return render_template('login.html', form=form, login_msg=return_msg)


@app.route('/message/delete', methods=['POST'])
@login_required
def delete_message():
    '''Delete a message from the database.'''
    message_id = request.form.get('id', '')

    # Data validation
    if not message_id.isdigit():
        return jsonify({'code': -1})

    # Further validation and perform data deletion
    message = Message.query.get(message_id)
    if not message or message.author_id != current_user.student.id:
        return jsonify({'code': -1})
    db.session.delete(message)
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
