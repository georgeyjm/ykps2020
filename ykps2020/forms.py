from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField
from wtforms.validators import DataRequired
from wtforms.widgets import TextArea

from .helper import get_available_students


class LoginForm(FlaskForm):

    username = StringField('Username', validators=[DataRequired()], render_kw={'spellcheck': 'false'})
    password = PasswordField('Password', validators=[DataRequired()])


class MessageForm(FlaskForm):

    recipient_id = SelectField('<strong>Recipient</strong>', coerce=int, validators=[DataRequired()])
    content = StringField('<strong>Content</strong>', widget=TextArea(), validators=[DataRequired()])
    is_anonymous = BooleanField('Make this message anonymous')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recipient_id.choices = get_available_students()

    def validate_match1(form, field):
        if not re.search(r"^[0-9]+:[0-9]+$", field.data):
            raise ValidationError("Invalid input syntax")

        s1, s2 = form.data.split(":")
        form.score1 = int(s1)
        form.score2 = int(s2)
