from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import URL, Email, InputRequired, Length, Optional, Regexp

SOCIAL_LINK_PLATFORM_CHOICES = [
    ("facebook", "facebook"),
    ("instagram", "instagram"),
    ("twitter", "twitter"),
    ("medium", "medium"),
    ("linkedin", "linkedin"),
    ("github", "github"),
]


class LoginForm(FlaskForm):
    email = StringField(render_kw={"placeholder": "Email"}, validators=[InputRequired(), Email()])
    password = PasswordField(render_kw={"placeholder": "Password"}, validators=[InputRequired()])
    submit_ = SubmitField(label="Login")


class SignUpForm(FlaskForm):
    email = StringField(render_kw={"placeholder": "Email"}, validators=[InputRequired(), Email()])
    password = PasswordField(
        render_kw={"placeholder": "Password"},
        validators=[
            InputRequired(),
            Regexp(
                "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?!.*\s).{8,}$",
                message="Password must be 8 characters long, with upper and lower cases letters.",
            ),
        ],
    )
    username = StringField(
        render_kw={"placeholder": "Username"},
        validators=[
            InputRequired(),
            Regexp(
                "^[a-zA-Z0-9-]+$",
                message="Use only letters (lowercase), numbers, and '-'.",
            ),
        ],
    )
    blogname = StringField(
        render_kw={"placeholder": "Blog's name"},
        validators=[
            InputRequired(),
            Length(min=1, max=20, message="20 characters maximum."),
        ],
    )
    terms = BooleanField(
        "I understand this is a fully experimental project, there is no guarantee of complete data preservation.",
        validators=[InputRequired()],
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


class GeneralSettingsForm(FlaskForm):
    cover_url = StringField(render_kw={"placeholder": "Insert image url"})
    blogname = StringField(validators=[Length(min=1, max=20)])
    gallery_enabled = BooleanField()
    changelog_enabled = BooleanField()
    submit_settings = SubmitField(label="Save Changes")


class UpdateSocialLinksForm(FlaskForm):
    url0 = StringField(validators=[Optional(), URL()], render_kw={"placeholder": "Url"})
    url1 = StringField(validators=[Optional(), URL()], render_kw={"placeholder": "Url"})
    url2 = StringField(validators=[Optional(), URL()], render_kw={"placeholder": "Url"})
    url3 = StringField(validators=[Optional(), URL()], render_kw={"placeholder": "Url"})
    url4 = StringField(validators=[Optional(), URL()], render_kw={"placeholder": "Url"})
    platform0 = SelectField(choices=SOCIAL_LINK_PLATFORM_CHOICES, validate_choice=False)
    platform1 = SelectField(choices=SOCIAL_LINK_PLATFORM_CHOICES, validate_choice=False)
    platform2 = SelectField(choices=SOCIAL_LINK_PLATFORM_CHOICES, validate_choice=False)
    platform3 = SelectField(choices=SOCIAL_LINK_PLATFORM_CHOICES, validate_choice=False)
    platform4 = SelectField(choices=SOCIAL_LINK_PLATFORM_CHOICES, validate_choice=False)
    submit_links = SubmitField(label="Save Changes")


class UpdatePasswordForm(FlaskForm):
    current_pw = PasswordField()
    new_pw = PasswordField(
        validators=[
            Regexp(
                "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?!.*\s).{8,}$",
                message="Password must be 8 characters long, with upper and lower cases letters.",
            )
        ]
    )
    new_pw_repeat = PasswordField(
        validators=[
            Regexp(
                "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?!.*\s).{8,}$",
                message="Password must be 8 characters long, with upper and lower cases letters.",
            )
        ]
    )
    submit_pw = SubmitField(
        label="Save Changes", render_kw={"onclick": "return validateNewPassword()"}
    )


class UserDeletionForm(FlaskForm):
    password = PasswordField(validators=[InputRequired()])
    submit_delete = SubmitField(label="Delete")
