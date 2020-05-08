import re
import sys
import traceback
from functools import wraps

from flask import Response, request, render_template, send_file, redirect, url_for, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash

from . import app, db, login_manager, cache
from .models import Student, User, Message
from .forms import LoginForm, MessageForm
from .helper import ykps_auth, record_change



#################### Web Pages ####################

@app.route('/')
@cache.cached(timeout=3600)
def index_page():
    return render_template('index.min.html')


@app.route('/login')
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_page'))
    form = LoginForm()
    return render_template('login.min.html', form=form)


@app.route('/logout')
@login_required
def logout_page():
    logout_user()
    return redirect(url_for('login_page'))


@app.route('/dashboard')
@login_required
def dashboard_page():
    messages = User.query.get(current_user.id).student.messages
    return render_template('dashboard.min.html', messages=messages)


@app.route('/message/new')
@login_required
def new_message_page():
    form = MessageForm()
    if not form.recipient_id.choices:
        # No student left to leave a message
        # TODO: Notify the user about this
        return redirect(url_for('dashboard_page'))
    return render_template('new-message.min.html', form=form)


@app.route('/message/edit/<message_id>')
@login_required
def edit_message_page(message_id):
    message = Message.query.get(message_id)
    # Data validation
    if not message or message.author_id != current_user.student.id:
        return redirect(url_for('dashboard_page'))
    
    # Pre-populate form data
    recipient_info = message.recipient.get_id_name()
    form = MessageForm()
    form.recipient_id.choices.insert(0, recipient_info) # TODO: insert at the right position
    form.recipient_id.default = recipient_info[0]
    form.content.data = message.content
    form.is_anonymous.data = message.is_anonymous

    return render_template('edit-message.min.html', form=form)



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
        return render_template('login.min.html', form=form, login_msg=return_msg)


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
    record_change(message_id, 'delete')
    db.session.commit()
    return jsonify({'code': 0})


@app.route('/message/new', methods=['POST'])
@login_required
def new_message():
    '''Create a new message in the database.'''
    form = MessageForm()
    if form.validate_on_submit():
        # Perform database insertion
        message = Message(
            author_id=current_user.student.id,
            recipient_id=form.recipient_id.data,
            content=form.content.data,
            is_anonymous=form.is_anonymous.data
        )
        db.session.add(message)
        db.session.commit()
        record_change(message.id, 'new', commit=True)

    return redirect(url_for('dashboard_page'))


@app.route('/message/edit/<message_id>', methods=['POST'])
@login_required
def edit_message(message_id):
    '''Updates the data of a message in the database.'''
    message = Message.query.get(message_id)
    # Data validation
    if not message or message.author_id != current_user.student.id:
        return redirect(url_for('dashboard_page'))
    
    # TODO: This is not elegant enough
    recipient_info = message.recipient.get_id_name()
    form = MessageForm()
    form.recipient_id.choices.insert(0, recipient_info)
    if form.validate_on_submit():
        # Update database entry
        message.recipient_id = form.recipient_id.data
        message.content = form.content.data
        message.is_anonymous = form.is_anonymous.data
        record_change(message_id, 'edit')
        db.session.commit()

    return redirect(url_for('dashboard_page'))



#################### Misc Views ####################

@login_manager.unauthorized_handler
def unauthorized_access():
    '''Redirect unauthorized users to login page.'''
    return redirect(url_for('login_page'))
