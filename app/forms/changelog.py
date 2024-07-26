from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import URL, InputRequired, Optional

CATEGORY_CHOICES = ["Career", "Personal", "About this site", "Others"]


class NewChangelogForm(FlaskForm):
    """Form for creating a new changelog entry.

    Attributes:
        title (StringField): The title of the changelog.
        date (StringField): The date of the changelog in MM/DD/YYYY format.
        category (SelectField): The category of the changelog.
        tags (StringField): Tags for the changelog, separated by commas.
        editor (TextAreaField): The content of the changelog.
        link (StringField): An optional URL link related to the changelog.
        link_description (StringField): An optional description for the link.
        submit_ (SubmitField): The submit button for the form with a validation function.
    """

    title = StringField(validators=[InputRequired()])
    date = StringField(validators=[InputRequired()])
    category = SelectField(choices=CATEGORY_CHOICES, validators=[InputRequired()])
    tags = StringField(
        render_kw={"placeholder": "Separate tags with ','"},
        validators=[InputRequired()],
    )
    editor = TextAreaField()
    link = StringField(render_kw={"placeholder": "Link"}, validators=[Optional(), URL()])
    link_description = StringField(
        render_kw={"placeholder": "Link description"}, validators=[Optional()]
    )
    submit_ = SubmitField(label="Submit", render_kw={"onclick": "return validateNewChangelog()"})


class EditChangelogForm(FlaskForm):
    """Form for editing an existing changelog entry.

    Attributes:
        title (StringField): The title of the changelog.
        date (StringField): The date of the changelog in MM/DD/YYYY format.
        category (SelectField): The category of the changelog.
        tags (StringField): Tags for the changelog, separated by commas.
        editor (TextAreaField): The content of the changelog.
        link (StringField): An optional URL link related to the changelog.
        link_description (StringField): An optional description for the link.
        submit_ (SubmitField): The submit button for the form with a validation function.
    """

    title = StringField(validators=[InputRequired()])
    date = StringField(validators=[InputRequired()])
    category = SelectField(choices=CATEGORY_CHOICES, validators=[InputRequired()])
    tags = StringField(
        render_kw={"placeholder": "Separate tags with ','"},
        validators=[InputRequired()],
    )
    editor = TextAreaField()
    link = StringField(render_kw={"placeholder": "Link"}, validators=[Optional(), URL()])
    link_description = StringField(
        render_kw={"placeholder": "Link description"}, validators=[Optional()]
    )
    submit_ = SubmitField(label="Submit", render_kw={"onclick": "return validateUpdate()"})
