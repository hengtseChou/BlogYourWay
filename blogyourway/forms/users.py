from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Regexp


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class SignUpForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Regexp(
                "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?!.*\s).{8,}$",
                message="Password must be 8 characters long, with upper and lower cases letters.",
            ),
        ],
    )
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Regexp("^[a-zA-Z0-9-]+$", message="Use only letters (lowercase), numbers, and '-'."),
        ],
    )
    blogname = StringField(
        "Blog Name", validators=[DataRequired(), Length(max=20, message="20 characters maximum.")]
    )
    terms = BooleanField(
        "I understand this is a fully experimental project, there is no guarantee of complete data preservation.",
        validators=[DataRequired()],
    )
    submit = SubmitField("Create")
