from dataclasses import asdict
from datetime import datetime, timezone

from flask_login import current_user

from app.forms.projects import EditProjectForm, NewProjectForm
from app.helpers.utils import UIDGenerator, process_tags
from app.models.projects import ProjectContent, ProjectInfo
from app.mongo import Database, mongodb


def process_form_images(form: NewProjectForm | EditProjectForm) -> list[tuple[str, str]]:
    """
    Process images from the project form.

    Args:
        form (NewProjectForm | EditProjectForm): The form containing project data.

    Returns:
        list[tuple[str, str]]: A list of tuples containing image URLs and captions.
    """
    images = []
    for i in range(5):
        url = form.data.get(f"url{i}", "")
        if url:
            caption = form.data.get(f"caption{i}", "")
            images.append((url, caption))
    while len(images) < 5:
        images.append(tuple())
    return images


##################################################################################################

# creating a new project

##################################################################################################


class NewProjectSetup:
    def __init__(self, project_uid_generator: UIDGenerator, db_handler: Database) -> None:
        """
        Initialize the NewProjectSetup class.

        Args:
            project_uid_generator (UIDGenerator): The UID generator for projects.
            db_handler (Database): The database handler.
        """
        self._project_uid = project_uid_generator.generate_project_uid()
        self._db_handler = db_handler

    def _create_project_info(self, form: NewProjectForm, author_name: str) -> dict:
        """
        Create a dictionary of project information.

        Args:
            form (NewProjectForm): The form containing project data.
            author_name (str): The author's username.

        Returns:
            dict: A dictionary containing the project's information.
        """
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
        """
        Create a dictionary of project content.

        Args:
            form (NewProjectForm): The form containing project data.
            author_name (str): The author's username.

        Returns:
            dict: A dictionary containing the project's content.
        """
        new_project_content = ProjectContent(
            project_uid=self._project_uid,
            author=author_name,
            content=form.editor.data,
        )
        return asdict(new_project_content)

    def create_project(self, form: NewProjectForm, author_name: str) -> str | None:
        """
        Create a new project in the database.

        Args:
            author_name (str): The author's username.
            form (NewProjectForm): The form containing project data.

        Returns:
            str | None: The UID of the newly created project, or None if creation failed.
        """
        new_project_info = self._create_project_info(form, author_name)
        new_project_content = self._create_project_content(form, author_name)

        self._db_handler.project_info.insert_one(new_project_info)
        self._db_handler.project_content.insert_one(new_project_content)
        return self._project_uid


def create_project(form: NewProjectForm) -> str:
    """
    Create a new project.

    Args:
        form (NewProjectForm): The form containing project data.

    Returns:
        str: The UID of the newly created project.
    """
    uid_generator = UIDGenerator(db_handler=mongodb)
    new_project_setup = NewProjectSetup(project_uid_generator=uid_generator, db_handler=mongodb)
    new_project_uid = new_project_setup.create_project(author_name=current_user.username, form=form)
    return new_project_uid


##################################################################################################

# updating a project

##################################################################################################


class ProjectUpdateSetup:
    def __init__(self, db_handler: Database) -> None:
        """
        Initialize the ProjectUpdateSetup class.

        Args:
            db_handler (Database): The database handler.
        """
        self._db_handler = db_handler

    def update_project(self, project_uid: str, form: EditProjectForm) -> None:
        """
        Update an existing project.

        Args:
            project_uid (str): The UID of the project to update.
            form (EditProjectForm): The form containing updated project data.
        """
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
    """
    Update an existing project.

    Args:
        project_uid (str): The UID of the project to update.
        form (EditProjectForm): The form containing updated project data.
    """
    project_update_setup = ProjectUpdateSetup(db_handler=mongodb)
    project_update_setup.update_project(project_uid=project_uid, form=form)


##################################################################################################

# project utilities

##################################################################################################


class ProjectsUtils:
    def __init__(self, db_handler: Database) -> None:
        """
        Initialize the ProjectsUtils class.

        Args:
            db_handler (Database): The database handler.
        """
        self._db_handler = db_handler

    def get_all_projects_info(self, include_archive=False) -> list[dict]:
        """
        Get information about all projects.

        Args:
            include_archive (bool, optional): Whether to include archived projects. Defaults to False.

        Returns:
            list[dict]: A list of dictionaries containing project information.
        """
        if include_archive:
            result = self._db_handler.project_info.find({}).as_list()
        else:
            result = self._db_handler.project_info.find({"archived": False}).as_list()
        return result

    def get_project_infos(self, username: str, archive="include") -> list[dict]:
        """
        Get information about projects for a specific user.

        Args:
            username (str): The username of the project author.

        Returns:
            list[dict]: A list of dictionaries containing project information.
        """
        if archive == "include":
            result = (
                self._db_handler.project_info.find({"author": username})
                .sort("created_at", -1)
                .as_list()
            )
        elif archive == "exclude":
            result = (
                self._db_handler.project_info.find({"author": username, "archived": False})
                .sort("created_at", -1)
                .as_list()
            )
        elif archive == "only":
            result = (
                self._db_handler.project_info.find({"author": username, "archived": True})
                .sort("created_at", -1)
                .as_list()
            )
        return result

    def get_archived_project_infos(self, username: str) -> list[dict]:
        """
        Get information about archived projects for a specific user.

        Args:
            username (str): The username of the project author.

        Returns:
            list[dict]: A list of dictionaries containing project information.
        """
        result = (
            self._db_handler.project_info.find({"author": username, "archived": True})
            .sort("created_at", -1)
            .as_list()
        )
        return result

    def get_project_infos_with_pagination(
        self, username: str, page_number: int, projects_per_page: int
    ) -> list[dict]:
        """
        Get paginated information about projects for a specific user.

        Args:
            username (str): The username of the project author.
            page_number (int): The page number.
            projects_per_page (int): The number of projects per page.

        Returns:
            list[dict]: A list of dictionaries containing project information.
        """
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

    def get_full_project(self, project_uid: str) -> dict:
        """
        Get full information about a project, including its content.

        Args:
            project_uid (str): The UID of the project.

        Returns:
            dict: A dictionary containing the project's full information.
        """
        project = self._db_handler.project_info.find_one({"project_uid": project_uid})
        project_content = self._db_handler.project_content.find_one(
            {"project_uid": project_uid}
        ).get("content")
        project["content"] = project_content
        return project

    def read_increment(self, project_uid: str) -> None:
        """
        Increment the read count for a project.

        Args:
            project_uid (str): The UID of the project.
        """
        self._db_handler.project_info.make_increments(
            filter={"project_uid": project_uid}, increments={"reads": 1}
        )

    def view_increment(self, project_uid: str) -> None:
        """
        Increment the view count for a project.

        Args:
            project_uid (str): The UID of the project.
        """
        self._db_handler.project_info.make_increments(
            filter={"project_uid": project_uid}, increments={"views": 1}
        )


projects_utils = ProjectsUtils(mongodb)
