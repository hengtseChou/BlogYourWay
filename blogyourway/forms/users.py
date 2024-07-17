from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Regexp


class LoginForm(FlaskForm):
    email = StringField(render_kw={"placeholder": "Email"}, validators=[DataRequired(), Email()])
    password = PasswordField(render_kw={"placeholder": "Password"}, validators=[DataRequired()])
    submit_ = SubmitField(label="Login")


class SignUpForm(FlaskForm):
    email = StringField(render_kw={"placeholder": "Email"}, validators=[DataRequired(), Email()])
    password = PasswordField(
        render_kw={"placeholder": "Password"},
        validators=[
            DataRequired(),
            Regexp(
                "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?!.*\s).{8,}$",
                message="Password must be 8 characters long, with upper and lower cases letters.",
            ),
        ],
    )
    username = StringField(
        render_kw={"placeholder": "Username"},
        validators=[
            DataRequired(),
            Regexp(
                "^[a-zA-Z0-9-]+$",
                message="Use only letters (lowercase), numbers, and '-'.",
            ),
        ],
    )
    blogname = StringField(
        render_kw={"placeholder": "Blog's name"},
        validators=[DataRequired(), Length(max=20, message="20 characters maximum.")],
    )
    terms = BooleanField(
        "I understand this is a fully experimental project, there is no guarantee of complete data preservation.",
        validators=[DataRequired()],
    )
    submit_ = SubmitField(label="Create")


class EditAboutForm(FlaskForm):
    profile_img_url = StringField(render_kw={"placeholder": "Insert image url"})
    short_bio = StringField(render_kw={"placeholder": "Bio on your home page"})
    editor = TextAreaField(
        render_kw={
            "placeholder": "Note: If you want to include images in your post, you can upload them on [imgur.com](https://imgur.com/)."
        }
    )
    submit_ = SubmitField(label="Save Changes")
