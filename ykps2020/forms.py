from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length
from wtforms.widgets import TextArea

from .helper import get_available_students


class LoginForm(FlaskForm):

    username = StringField('Username', validators=[DataRequired()], render_kw={'spellcheck': 'false'})
    password = PasswordField('Password', validators=[DataRequired()])


class MessageForm(FlaskForm):

    recipient_id = SelectField('<strong>Recipient</strong>', coerce=int, validators=[DataRequired()])
    content = StringField('<strong>Content</strong>', widget=TextArea(), validators=[DataRequired(), Length(max=1000)], render_kw={'maxlength': '1000'})
    is_anonymous = BooleanField('Make this message anonymous')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recipient_id.choices = get_available_students()

    # It seems like SQLAlchemy has built-in validation for
    # foreign key fields, and thus this validation is not needed
    # def validate_recipient_id(form, field):
    #     possible_ids = [i for i in zip(*form.recipient_id.choices)][0]
    #     if field.data not in possible_ids:
    #         raise ValidationError('Invalid recipient') # Remember to import
