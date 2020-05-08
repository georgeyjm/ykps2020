from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash

from . import db, login_manager


class Student(db.Model):
    '''Model for the students table.'''

    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.String(16), nullable=False, unique=True)
    name_en = db.Column(db.String(128), nullable=True)
    name_zh = db.Column(db.String(128), nullable=True)

    def __repr__(self):
        return '<Student "{}">'.format(self.name_en)
    
    def get_id_name(self):
        '''Returns a tuple containing the ID and the bilingual name of the student.'''
        return self.id, f'{self.name_en} {self.name_zh}'


class User(db.Model, UserMixin):
    '''Model for the users table.'''

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    # school_id = db.Column(db.String(128), nullable=False, unique=True)
    # name = db.Column(db.String(128), nullable=False)
    password = db.Column(db.String(128), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)

    student = db.relationship(Student, backref='user')

    def __repr__(self):
        return '<User #{}>'.format(self.id)

    def authenticate(self, password):
        '''Checks if provided password matches stored password.'''
        return check_password_hash(self.password, password)
    
    @staticmethod
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)


class Message(db.Model):
    '''Model for the messages table.'''

    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_anonymous = db.Column(db.Boolean, nullable=False, default=0)

    author = db.relationship(Student, foreign_keys=[author_id], backref='messages')
    recipient = db.relationship(Student, foreign_keys=[recipient_id], backref='messages_received')

    def __repr__(self):
        return '<Message #{}>'.format(self.id)


class Change(db.Model):
    '''Model for the changes table.'''

    __tablename__ = 'changes'

    id = db.Column(db.Integer, primary_key=True)
    change_type = db.Column(db.String(16), nullable=False)
    message_id = db.Column(db.Integer, nullable=False)
    changed_at = db.Column(db.DateTime, nullable=False, default=datetime.now)


    def __repr__(self):
        return '<Change #{}>'.format(self.id)


db.create_all() # Initialize tables using the above configuration
