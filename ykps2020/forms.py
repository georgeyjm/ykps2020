from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField
from wtforms.validators import DataRequired
from wtforms.widgets import TextArea

from .helper import get_available_students


class LoginForm(FlaskForm):

    username = StringField('Username', validators=[DataRequired()], render_kw={'spellcheck': 'false'})
    password = PasswordField('Password', validators=[DataRequired()])


class MessageForm(FlaskForm):

    recipient_id = SelectField('<strong>Recipient</strong>', validators=[DataRequired()], coerce=int)
    content = StringField('<strong>Content</strong>', widget=TextArea(), validators=[DataRequired()])
    is_anonymous = BooleanField('Make this message anonymous')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recipient_id.choices = get_available_students()
