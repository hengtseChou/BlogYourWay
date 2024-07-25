from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, DateField, SelectField
from wtforms.validators import URL, InputRequired, Optional

CATEGORY_CHOICES = ["Career", "Personal", "About this site", "Others"]


class NewChangelogForm(FlaskForm):
    title = StringField(validators=[InputRequired()])
    date = StringField(validators=[InputRequired()])
    category = SelectField(choices=CATEGORY_CHOICES, validators=[InputRequired()])
    tags = StringField(
        render_kw={"placeholder": "Separate tags with ','"},
        validators=[InputRequired()],
    )
    editor = TextAreaField()
    link = StringField(
        render_kw={"placeholder": "Link"}, validators=[Optional(), URL()]
    )
    link_description = StringField(
        render_kw={"placeholder": "Link description"}, validators=[Optional()]
    )
    submit_ = SubmitField(label="Submit")


class EditChangelogForm(FlaskForm):
    title = StringField(validators=[InputRequired()])
    date = StringField(validators=[InputRequired()])
    category = SelectField(choices=CATEGORY_CHOICES, validators=[InputRequired()])
    tags = StringField(
        render_kw={"placeholder": "Separate tags with ','"},
        validators=[InputRequired()],
    )
    editor = TextAreaField()
    link = StringField(render_kw={"placeholder": "Link"}, validators=[Optional(), URL()])
    link_description = StringField(render_kw={"placeholder": "Link description"}, validators=[Optional()])
    submit_ = SubmitField(label="Submit")
