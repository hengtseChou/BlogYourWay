from dataclasses import asdict
from datetime import datetime, timezone

from flask_login import current_user

from app.forms.changelog import EditChangelogForm, NewChangelogForm
from app.helpers.utils import UIDGenerator, process_tags
from app.models.changelog import Changelog
from app.mongo import Database, mongodb


class NewChangelogSetup:
    """Handles the setup and creation of new changelog entries.

    Args:
        changelog_uid_generator (UIDGenerator): Generator for creating unique changelog IDs.
        db_handler (Database): Database handler for database operations.

    Attributes:
        _changelog_uid (str): The unique ID for the new changelog.
        _db_handler (Database): The database handler used for inserting new changelog entries.
    """

    def __init__(self, changelog_uid_generator: UIDGenerator, db_handler: Database) -> None:
        self._changelog_uid = changelog_uid_generator.generate_changelog_uid()
        self._db_handler = db_handler

    def _create_changelog(self, form: NewChangelogForm, author_name: str) -> dict:
        """Creates a new changelog entry from the provided form data.

        Args:
            form (NewChangelogForm): The form containing the data for the new changelog.
            author_name (str): The name of the author of the changelog.

        Returns:
            dict: A dictionary representation of the new changelog.
        """
        new_changelog = Changelog(
            changelog_uid=self._changelog_uid,
            title=form.title.data,
            author=author_name,
            date=datetime.strptime(form.date.data, "%m/%d/%Y").replace(tzinfo=timezone.utc),
            category=form.category.data,
            content=form.editor.data,
            tags=process_tags(form.tags.data),
            link=form.link.data,
            link_description=form.link_description.data,
        )
        return asdict(new_changelog)

    def create_changelog(self, form: NewChangelogForm, author_name: str) -> str:
        """Creates and inserts a new changelog entry into the database.

        Args:
            form (NewChangelogForm): The form containing the data for the new changelog.
            author_name (str): The name of the author of the changelog.

        Returns:
            str: The unique ID of the newly created changelog.
        """
        new_changelog_entry = self._create_changelog(form, author_name)
        self._db_handler.changelog.insert_one(new_changelog_entry)
        return self._changelog_uid


def create_changelog(form: NewChangelogForm) -> str:
    """Creates a new changelog entry and inserts it into the database.

    Args:
        form (NewChangelogForm): The form containing the data for the new changelog.

    Returns:
        str: The unique ID of the newly created changelog.
    """
    uid_generator = UIDGenerator(db_handler=mongodb)
    new_changelog_setup = NewChangelogSetup(uid_generator, mongodb)
    new_changelog_uid = new_changelog_setup.create_changelog(
        form=form, author_name=current_user.username
    )
    return new_changelog_uid


class ChangelogUpdateSetup:
    """Handles the update of existing changelog entries in the database.

    Args:
        db_handler (Database): Database handler for database operations.

    Attributes:
        _db_handler (Database): The database handler used for updating changelog entries.
    """

    def __init__(self, db_handler: Database) -> None:
        self._db_handler = db_handler

    def update_changelog(self, changelog_uid: str, form: EditChangelogForm) -> None:
        """Updates an existing changelog entry with new data.

        Args:
            changelog_uid (str): The unique ID of the changelog to update.
            form (EditChangelogForm): The form containing the updated data for the changelog.
        """
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
    """Updates an existing changelog entry using the provided form data.

    Args:
        changelog_uid (str): The unique ID of the changelog to update.
        form (EditChangelogForm): The form containing the updated data for the changelog.
    """
    changelog_update_setup = ChangelogUpdateSetup(mongodb)
    changelog_update_setup.update_changelog(changelog_uid=changelog_uid, form=form)


class ChangelogUtils:
    """Provides utility methods for retrieving changelog entries from the database.

    Args:
        db_handler (Database): Database handler for database operations.

    Attributes:
        _db_handler (Database): The database handler used for retrieving changelog entries.
    """

    def __init__(self, db_handler: Database) -> None:
        self._db_handler = db_handler

    def get_changelogs(self, username: str, by_date: bool = False) -> list[dict]:
        """Retrieves changelog entries for a specific user.

        Args:
            username (str): The username of the user whose changelogs are to be retrieved.
            by_date (bool, optional): Whether to sort changelogs by date. Defaults to False.

        Returns:
            list[dict]: A list of dictionaries representing the user's changelog entries.
        """
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
        """Retrieves archived changelog entries for a specific user.

        Args:
            username (str): The username of the user whose archived changelogs are to be retrieved.

        Returns:
            list[dict]: A list of dictionaries representing the user's archived changelog entries.
        """
        result = (
            self._db_handler.changelog.find({"author": username, "archived": True})
            .sort("created_at", -1)
            .as_list()
        )
        return result

    def get_changelogs_with_pagination(
        self, username: str, page_number: int, changelogs_per_page: int
    ) -> list[dict]:
        """Retrieves a paginated list of changelog entries for a specific user.

        Args:
            username (str): The username of the user whose changelogs are to be retrieved.
            page_number (int): The page number to retrieve.
            changelogs_per_page (int): The number of changelogs per page.

        Returns:
            list[dict]: A list of dictionaries representing the user's paginated changelog entries.
        """
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
