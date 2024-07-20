from dataclasses import asdict
from datetime import datetime, timezone

from flask_login import current_user

from blogyourway.forms.projects import EditProjectForm, NewProjectForm
from blogyourway.models.projects import ProjectContent, ProjectInfo
from blogyourway.mongo import Database, mongodb
from blogyourway.helpers.utils import UIDGenerator, process_tags


def process_form_images(
    form: NewProjectForm | EditProjectForm,
) -> list[tuple[str, str]]:

    images = []
    for i in range(5):
        url = form.data.get(f"url{i}", "")
        if url:
            caption = form.data.get(f"caption{i}", "")
            images.append((url, caption))
    while len(images) < 5:
        images.append(tuple())

    return images


class NewProjectSetup:
    def __init__(self, project_uid_generator: UIDGenerator, db_handler: Database) -> None:
        self._project_uid = project_uid_generator.generate_project_uid()
        self._db_handler = db_handler

    def _create_project_info(self, form: NewProjectForm, author_name: str) -> dict:
        new_project_info = ProjectInfo(
            project_uid=self._project_uid,
            author=author_name,
            title=form.title.data,
            short_description=form.desc.data,
            tags=process_tags(form.tags.data),
            custom_slug=form.custom_slug.data,
            images=process_form_images(form),
        )
        return asdict(new_project_info)

    def _create_project_content(self, form: NewProjectForm, author_name: str) -> dict:
        new_project_content = ProjectContent(
            project_uid=self._project_uid,
            author=author_name,
            content=form.editor.data,
        )
        return asdict(new_project_content)

    def create_project(self, author_name: str, form: NewProjectForm) -> str | None:
        new_project_info = self._create_project_info(form, author_name)
        new_project_content = self._create_project_content(form, author_name)

        self._db_handler.project_info.insert_one(new_project_info)
        self._db_handler.project_content.insert_one(new_project_content)
        return self._project_uid


def create_project(form: NewProjectForm) -> str:
    uid_generator = UIDGenerator(db_handler=mongodb)

    new_project_setup = NewProjectSetup(project_uid_generator=uid_generator, db_handler=mongodb)
    new_project_uid = new_project_setup.create_project(author_name=current_user.username, form=form)
    return new_project_uid


###################################################################

# updating a project

###################################################################


class ProjectUpdateSetup:
    def __init__(self, db_handler: Database) -> None:
        self._db_handler = db_handler

    def update_project(self, project_uid: str, form: EditProjectForm) -> None:
        updated_project_info = {
            "title": form.title.data,
            "short_description": form.desc.data,
            "tags": process_tags(form.tags.data),
            "images": process_form_images(form),
            "custom_slug": form.custom_slug.data,
            "last_updated": datetime.now(timezone.utc),
        }
        updated_project_content = {"content": form.editor.data}

        self._db_handler.project_info.update_values(
            filter={"project_uid": project_uid}, update=updated_project_info
        )
        self._db_handler.project_content.update_values(
            filter={"project_uid": project_uid}, update=updated_project_content
        )


def update_project(project_uid: str, form: EditProjectForm) -> None:
    project_update_setup = ProjectUpdateSetup(db_handler=mongodb)
    project_update_setup.update_project(project_uid=project_uid, form=form)


###################################################################

# project utilities

###################################################################


class ProjectsUtils:
    def __init__(self, db_handler: Database):
        self._db_handler = db_handler

    def get_all_projects_info(self, include_archive=False) -> list[dict]:
        if include_archive:
            result = self._db_handler.project_info.find({}).as_list()
        else:
            result = (self._db_handler.project_info.find({"archived": False})).as_list()
        return result

    def get_projects_info(self, username: str) -> list[dict]:
        result = (
            self._db_handler.project_info.find({"author": username, "archived": False})
            .sort("created_at", -1)
            .as_list()
        )
        return result

    def get_projects_info_with_pagination(
        self, username: str, page_number: int, projects_per_page: int
    ) -> list[dict]:
        if page_number == 1:
            result = (
                self._db_handler.project_info.find({"author": username, "archived": False})
                .sort("created_at", -1)
                .limit(projects_per_page)
                .as_list()
            )

        elif page_number > 1:
            result = (
                self._db_handler.project_info.find({"author": username, "archived": False})
                .sort("created_at", -1)
                .skip((page_number - 1) * projects_per_page)
                .limit(projects_per_page)
                .as_list()
            )

        return result

    def get_archived_projects_info(self, username) -> list[dict]:
        result = (
            self._db_handler.project_info.find({"author": username, "archived": True})
            .sort("created_at", -1)
            .as_list()
        )
        return result

    def get_full_project(self, project_uid: str) -> dict:
        project = self._db_handler.project_info.find_one({"project_uid": project_uid})
        project_content = self._db_handler.project_content.find_one(
            {"project_uid": project_uid}
        ).get("content")
        project["content"] = project_content

        return project

    def read_increment(self, project_uid: str) -> None:
        self._db_handler.project_info.make_increments(
            filter={"project_uid": project_uid}, increments={"reads": 1}
        )

    def view_increment(self, project_uid: str) -> None:
        self._db_handler.project_info.make_increments(
            filter={"project_uid": project_uid}, increments={"views": 1}
        )


projects_utils = ProjectsUtils(mongodb)
