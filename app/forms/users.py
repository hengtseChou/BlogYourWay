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
    ("facebook", "Facebook"),
    ("instagram", "Instagram"),
    ("twitter", "Twitter"),
    ("medium", "Medium"),
    ("linkedin", "LinkedIn"),
    ("github", "GitHub"),
]


class LoginForm(FlaskForm):
    """
    Form for user login.

    Fields:
        email (StringField): User's email address.
        password (PasswordField): User's password.
        submit_ (SubmitField): Login button.
    """

    email = StringField(render_kw={"placeholder": "Email"}, validators=[InputRequired(), Email()])
    password = PasswordField(render_kw={"placeholder": "Password"}, validators=[InputRequired()])
    submit_ = SubmitField(label="Login")


class SignUpForm(FlaskForm):
    """
    Form for user sign-up.

    Fields:
        email (StringField): User's email address.
        password (PasswordField): User's password.
        username (StringField): Desired username.
        blogname (StringField): Name of the user's blog.
        terms (BooleanField): Acknowledgement of project status.
        submit_ (SubmitField): Sign-up button.
    """

    email = StringField(render_kw={"placeholder": "Email"}, validators=[InputRequired(), Email()])
    password = PasswordField(
        render_kw={"placeholder": "Password"},
        validators=[
            InputRequired(),
            Regexp(
                "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?!.*\s).{8,}$",
                message="Password must be at least 8 characters long and include both upper and lower case letters and digits.",
            ),
        ],
    )
    username = StringField(
        render_kw={"placeholder": "Username"},
        validators=[
            InputRequired(),
            Regexp(
                "^(?![-.])[a-z0-9.-]*(?<![-.])$",
                message="Username can contains only lowercase letters, numbers, dashes, and dots, and does not start or end with a dash or dot.",
            ),
        ],
    )
    blogname = StringField(
        render_kw={"placeholder": "Blog's name"},
        validators=[
            InputRequired(),
            Length(min=1, max=20, message="Blog name must be between 1 and 20 characters."),
        ],
    )
    terms = BooleanField(
        "I understand this is a fully experimental project, and there is no guarantee of complete data preservation.",
        validators=[InputRequired()],
    )
    submit_ = SubmitField(label="Create")


class EditAboutForm(FlaskForm):
    """
    Form for editing user profile information.

    Fields:
        profile_img_url (StringField): URL for the profile image.
        short_bio (StringField): Short biography for the home page.
        editor (TextAreaField): Additional notes or content.
        submit_ (SubmitField): Save changes button.
    """

    profile_img_url = StringField(render_kw={"placeholder": "Insert image URL"})
    short_bio = StringField(render_kw={"placeholder": "Bio on your home page"})
    editor = TextAreaField(
        render_kw={
            "placeholder": "Note: If you want to include images in your post, you can upload them on [imgur.com](https://imgur.com)."
        }
    )
    submit_ = SubmitField(label="Save Changes")


class GeneralSettingsForm(FlaskForm):
    """
    Form for updating general settings.

    Fields:
        cover_url (StringField): URL for the cover image.
        blogname (StringField): Blog name.
        gallery_enabled (BooleanField): Option to enable gallery.
        changelog_enabled (BooleanField): Option to enable changelog.
        submit_settings (SubmitField): Save settings button.
    """

    cover_url = StringField(render_kw={"placeholder": "Insert image URL"})
    blogname = StringField(validators=[Length(min=1, max=20)])
    gallery_enabled = BooleanField()
    changelog_enabled = BooleanField()
    submit_settings = SubmitField(label="Save Changes")


class UpdateSocialLinksForm(FlaskForm):
    """
    Form for updating social media links.

    Fields:
        url0, url1, url2, url3, url4 (StringField): URLs for social media profiles.
        platform0, platform1, platform2, platform3, platform4 (SelectField): Social media platforms.
        submit_links (SubmitField): Save links button.
    """

    url0 = StringField(validators=[Optional(), URL()], render_kw={"placeholder": "URL"})
    url1 = StringField(validators=[Optional(), URL()], render_kw={"placeholder": "URL"})
    url2 = StringField(validators=[Optional(), URL()], render_kw={"placeholder": "URL"})
    url3 = StringField(validators=[Optional(), URL()], render_kw={"placeholder": "URL"})
    url4 = StringField(validators=[Optional(), URL()], render_kw={"placeholder": "URL"})
    platform0 = SelectField(choices=SOCIAL_LINK_PLATFORM_CHOICES, validate_choice=False)
    platform1 = SelectField(choices=SOCIAL_LINK_PLATFORM_CHOICES, validate_choice=False)
    platform2 = SelectField(choices=SOCIAL_LINK_PLATFORM_CHOICES, validate_choice=False)
    platform3 = SelectField(choices=SOCIAL_LINK_PLATFORM_CHOICES, validate_choice=False)
    platform4 = SelectField(choices=SOCIAL_LINK_PLATFORM_CHOICES, validate_choice=False)
    submit_links = SubmitField(label="Save Changes")


class UpdatePasswordForm(FlaskForm):
    """
    Form for updating user password.

    Fields:
        current_pw (PasswordField): Current password.
        new_pw (PasswordField): New password.
        new_pw_repeat (PasswordField): Confirmation of the new password.
        submit_pw (SubmitField): Save changes button.
    """

    current_pw = PasswordField()
    new_pw = PasswordField(
        validators=[
            Regexp(
                "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?!.*\s).{8,}$",
                message="New password must be at least 8 characters long and include both upper and lower case letters and digits.",
            )
        ]
    )
    new_pw_repeat = PasswordField(
        validators=[
            Regexp(
                "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?!.*\s).{8,}$",
                message="New password must be at least 8 characters long and include both upper and lower case letters and digits.",
            )
        ]
    )
    submit_pw = SubmitField(
        label="Save Changes", render_kw={"onclick": "return validateNewPassword()"}
    )


class UserDeletionForm(FlaskForm):
    """
    Form for deleting a user account.

    Fields:
        password (PasswordField): Current password for verification.
        submit_delete (SubmitField): Delete account button.
    """

    password = PasswordField(validators=[InputRequired()])
    submit_delete = SubmitField(label="Delete")
