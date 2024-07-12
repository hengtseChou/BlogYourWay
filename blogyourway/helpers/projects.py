from dataclasses import asdict, dataclass, field
from datetime import datetime

from flask import Request
from flask_login import current_user

from blogyourway.config import ENV
from blogyourway.helpers.common import FormValidator, UIDGenerator, get_today
from blogyourway.helpers.posts import process_tags
from blogyourway.services.mongo import Database, mongodb


@dataclass
class ProjectInfo:
    project_uid: str
    custom_slug: str
    title: str
    short_description: str
    author: str
    tags: list[str]
    images: list[str]
    created_at: datetime = field(init=False)
    last_updated: datetime = field(init=False)
    archived: bool = False
    views: int = 0
    reads: int = 0

    def __post_init__(self):
        self.created_at = get_today(env=ENV)
        self.last_updated = get_today(env=ENV)


@dataclass
class ProjectContent:
    project_uid: str
    author: str
    content: str


def process_form_images(request: Request) -> list[dict[str, str]]:

    images = []
    num_of_images = len([i for i in request.form.keys() if "url" in i])
    for i in range(1, num_of_images + 1):
        image = {
            "url": request.form.get(f"url-{i}"),
            "caption": request.form.get(f"caption-{i}"),
        }
        images.append(image)
    return images


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


projects_utils = ProjectsUtils(mongodb)
