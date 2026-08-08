"""WTForms definitions used across the app."""
from flask_wtf import FlaskForm
from wtforms import (
    IntegerField,
    PasswordField,
    StringField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    Optional,
    ValidationError,
)


class RegistrationForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField(
        "Email",
        validators=[DataRequired(), Email(check_deliverability=False), Length(max=180)],
    )
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", "Passwords must match")],
    )


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(check_deliverability=False)])
    password = PasswordField("Password", validators=[DataRequired()])


class BookForm(FlaskForm):
    isbn = StringField("ISBN", validators=[DataRequired(), Length(max=20)])
    title = StringField("Title", validators=[DataRequired(), Length(max=255)])
    author = StringField("Author", validators=[DataRequired(), Length(max=255)])
    publisher = StringField("Publisher", validators=[Optional(), Length(max=255)])
    category = StringField("Category", validators=[Optional(), Length(max=100)])
    publication_year = IntegerField(
        "Publication Year", validators=[Optional(), NumberRange(min=0, max=2100)]
    )
    total_copies = IntegerField(
        "Total Copies", validators=[DataRequired(), NumberRange(min=0)]
    )
    available_copies = IntegerField(
        "Available Copies", validators=[Optional(), NumberRange(min=0)]
    )
    description = TextAreaField("Description", validators=[Optional()])

    def validate_available_copies(self, field):
        if field.data is not None and self.total_copies.data is not None:
            if field.data > self.total_copies.data:
                raise ValidationError("Available copies cannot exceed total copies")


class RejectForm(FlaskForm):
    reason = StringField("Reason", validators=[DataRequired(), Length(max=255)])
