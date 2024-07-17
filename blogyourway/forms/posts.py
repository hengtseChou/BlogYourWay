from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired


class EditPostForm(FlaskForm):
    title = StringField(validators=[DataRequired()])
    subtitle = StringField(validators=[DataRequired()])
    tags = StringField(
        render_kw={"placeholder": "Separate tags with ','"}, validators=[DataRequired()]
    )
    cover_url = StringField(render_kw={"placeholder": "Insert image url here"})
    custom_slug = StringField(render_kw={"placeholder": "Must be an url-friendly string"})
    editor = TextAreaField()
    submit_ = SubmitField(label="Save Changes", render_kw={"onclick": "return validateUpdate()"})
