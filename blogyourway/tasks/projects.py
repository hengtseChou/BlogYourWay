from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from flask import Request
from flask_login import current_user

from blogyourway.models.projects import ProjectContent, ProjectInfo
from blogyourway.mongo import Database, mongodb
from blogyourway.tasks.utils import FormValidator, UIDGenerator, process_form_images, process_tags


class NewProjectSetup:
    def __init__(self, project_uid_generator: UIDGenerator, db_handler: Database) -> None:
        self._project_uid = project_uid_generator.generate_post_uid()
        self._db_handler = db_handler

    def _form_validatd(self, request: Request, validator: FormValidator) -> bool:
        return True

    def _create_project_info(self, request: Request, author_name: str) -> dict:
        new_project_info = ProjectInfo(
            project_uid=self._project_uid,
            custom_slug=request.form.get("custom-slug"),
            title=request.form.get("title"),
            short_description=request.form.get("desc"),
            author=author_name,
            tags=process_tags(request.form.get("tags")),
            images=process_form_images(request),
        )
        return asdict(new_project_info)

    def _create_project_content(self, request: Request, author_name: str) -> dict:
        new_project_content = ProjectContent(
            project_uid=self._project_uid,
            author=author_name,
            content=request.form.get("content"),
        )
        return asdict(new_project_content)

    def create_project(self, author_name: str, request: Request) -> str | None:
        validator = FormValidator()
        if not self._form_validatd(request=request, validator=validator):
            return None
        # validated
        new_project_info = self._create_project_info(author_name=author_name, request=request)
        new_project_content = self._create_project_content(author_name=author_name, request=request)

        self._db_handler.project_info.insert_one(new_project_info)
        self._db_handler.project_content.insert_one(new_project_content)
        # self._increment_tags_for_user(new_project_info)

        return self._project_uid


def create_project(request: Request) -> str:
    uid_generator = UIDGenerator(db_handler=mongodb)

    new_project_setup = NewProjectSetup(project_uid_generator=uid_generator, db_handler=mongodb)
    new_post_uid = new_project_setup.create_project(
        author_name=current_user.username, request=request
    )
    return new_post_uid


class ProjectsUtils:
    def __init__(self, db_handler: Database):
        self._db_handler = db_handler

    def find_projects_info_by_username(self, username: str) -> list[dict]:
        result = (
            self._db_handler.project_info.find({"author": username, "archived": False})
            .sort("created_at", -1)
            .as_list()
        )
        return result

    def find_projects_with_pagination(
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

    def find_all_archived_project_info(self, username) -> list[dict]:
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


projects_utils = ProjectsUtils(mongodb)


@dataclass
class UpdatedProjectInfo:
    title: str
    short_description: str
    tags: list[str]
    images: list[dict[str, str]]
    custom_slug: str
    last_updated: datetime = field(init=False)

    def __post_init__(self):
        self.last_updated = datetime.now(timezone.utc)


@dataclass
class UpdatedProjectContent:
    content: str


class ProjectUpdateSetup:
    def __init__(self, db_handler: Database) -> None:
        self._db_handler = db_handler

    def _form_validatd(self, request: Request, validator: FormValidator) -> bool:
        return True

    def _updated_project_info(self, request: Request) -> dict:
        updated_post_info = UpdatedProjectInfo(
            title=request.form.get("title"),
            short_description=request.form.get("desc"),
            tags=process_tags(request.form.get("tags")),
            images=process_form_images(request),
            custom_slug=request.form.get("custom_slug"),
        )
        return asdict(updated_post_info)

    def _updated_project_content(self, request: Request) -> dict:
        updated_post_content = UpdatedProjectContent(content=request.form.get("content"))
        return asdict(updated_post_content)

    def update_project(self, project_uid: str, request: Request) -> None:
        validator = FormValidator()
        if not self._form_validatd(request=request, validator=validator):
            return
        # validated
        updated_project_info = self._updated_project_info(request=request)
        updated_project_content = self._updated_project_content(request=request)

        self._db_handler.project_info.update_values(
            filter={"project_uid": project_uid}, update=updated_project_info
        )
        self._db_handler.project_content.update_values(
            filter={"project_uid": project_uid}, update=updated_project_content
        )


def update_project(project_uid: str, request: Request) -> None:
    project_update_setup = ProjectUpdateSetup(db_handler=mongodb)
    project_update_setup.update_project(project_uid=project_uid, request=request)
