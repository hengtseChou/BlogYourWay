from app.helpers.utils import UIDGenerator, process_tags
from app.mongo import Database, mongodb
from app.models.changelog import Changelog
from app.forms.changelog import NewChangelogForm, EditChangelogForm
from datetime import datetime, timezone

from dataclasses import asdict
from flask_login import current_user


class NewChangelogSetup:
    def __init__(self, changelog_uid_generator: UIDGenerator, db_handler: Database) -> None:
        self._changelog_uid = changelog_uid_generator.generate_changelog_uid()
        self._db_handler = db_handler

    def _create_changelog(self, form: NewChangelogForm, author_name: str) -> dict:
        new_changelog = Changelog(
            changelog_uid=self._changelog_uid,
            title=form.title.data,
            author=author_name,
            date=datetime.strptime(form.date.data, "%m/%d/%Y").replace(tzinfo=timezone.utc),
            category=form.category.data, 
            content=form.editor.data,
            tags=process_tags(form.tags.data),
            link=form.link.data,
            link_description=form.link_description.data
        )
        return asdict(new_changelog)
    
    def create_changelog(self, form: NewChangelogForm, author_name: str) -> str:
        new_changelof_entry = self._create_changelog(form, author_name)
        self._db_handler.changelog.insert_one(new_changelof_entry)
        return self._changelog_uid

def create_changelog(form: NewChangelogForm) -> str:
    uid_generator = UIDGenerator(db_handler=mongodb)
    new_changelog_setup = NewChangelogSetup(uid_generator, mongodb)
    new_changelog_uid = new_changelog_setup.create_changelog(form=form, author_name=current_user.username)
    return new_changelog_uid

class ChangelogUpdateSetup:
    def __init__(self, db_handler: Database) -> None:
        self._db_handler = db_handler    

    def update_changelog(self, changelog_uid:str, form: EditChangelogForm) -> None:
        updated_changelog = {
            "title": form.title.data,
            "date": datetime.strptime(form.date.data, "%m/%d/%Y").replace(tzinfo=timezone.utc),
            "category": form.category.data,
            "content": form.editor.data,
            "tags": process_tags(form.tags.data),
            "link": form.link.data,
            "link_description": form.link_description.data,
            "last_updated": datetime.now(timezone.utc),
        }
        self._db_handler.changelog.update_values(
            filter={"changelog_uid": changelog_uid}, update=updated_changelog
        )

def update_changelog(changelog_uid: str, form: EditChangelogForm) -> None:
    changelog_update_setup = ChangelogUpdateSetup(mongodb)
    changelog_update_setup.update_changelog(changelog_uid=changelog_uid, form=form)

class ChangelogUtils:
    def __init__(self, db_handler: Database) -> None:
        self._db_handler = db_handler

    def get_changelogs(self, username: str, by_date=False) -> list[dict]:
        if by_date:
            result = (
                self._db_handler.changelog.find({"author": username, "archived": False})
                .sort("date", -1)
                .as_list()
            )
        else:
            result = (
                self._db_handler.changelog.find({"author": username, "archived": False})
                .sort("created_at", -1)
                .as_list()
            )
        return result

    def get_archived_changelogs(self, username: str) -> list[dict]:
        result = (
            self._db_handler.changelog.find({"author": username, "archived": True})
            .sort("created_at", -1)
            .as_list()
        )
        return result

    def get_changelogs_with_pagination(
        self, username: str, page_number: int, changelogs_per_page: int
    ) -> list[dict]:
        if page_number == 1:
            result = (
                self._db_handler.changelog.find({"author": username, "archived": False})
                .sort("created_at", -1)
                .limit(changelogs_per_page)
                .as_list()
            )
        elif page_number > 1:
            result = (
                self._db_handler.changelog.find({"author": username, "archived": False})
                .sort("created_at", -1)
                .skip((page_number - 1) * changelogs_per_page)
                .limit(changelogs_per_page)
                .as_list()
            )
        return result
    
changelog_utils = ChangelogUtils(mongodb)
    
        