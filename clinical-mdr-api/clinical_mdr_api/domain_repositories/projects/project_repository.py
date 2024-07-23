from threading import Lock
from typing import Collection

from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from neomodel import exceptions

from clinical_mdr_api import config
from clinical_mdr_api.domain_repositories.generic_repository import (
    RepositoryClosureData,
)
from clinical_mdr_api.domain_repositories.models.clinical_programme import (
    ClinicalProgramme,
)
from clinical_mdr_api.domain_repositories.models.project import Project
from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.domains.projects.project import ProjectAR
from clinical_mdr_api.repositories._utils import sb_clear_cache


class ProjectRepository:
    cache_store_item_by_uid = TTLCache(
        maxsize=config.CACHE_MAX_SIZE, ttl=config.CACHE_TTL
    )
    lock_store_item_by_uid = Lock()
    cache_store_item_by_study_uid = TTLCache(
        maxsize=config.CACHE_MAX_SIZE, ttl=config.CACHE_TTL
    )
    lock_store_item_by_study_uid = Lock()
    cache_store_item_by_project_number = TTLCache(
        maxsize=config.CACHE_MAX_SIZE, ttl=config.CACHE_TTL
    )
    lock_store_item_by_project_number = Lock()

    def project_number_exists(self, project_number: str) -> bool:
        project = Project.nodes.first_or_none(project_number=project_number)
        return bool(project)

    def generate_uid(self) -> str:
        return Project.get_next_free_uid_and_increment_counter()

    def get_hashkey(
        self,
        uid: str,
    ):
        """
        Returns a hash key that will be used for mapping objects stored in cache,
        which ultimately determines whether a method invocation is a hit or miss.
        """
        return hashkey(
            str(type(self)),
            uid,
        )

    @cached(cache=cache_store_item_by_uid, key=get_hashkey, lock=lock_store_item_by_uid)
    def find_by_uid(self, uid: str) -> ProjectAR | None:
        project = Project.nodes.get_or_none(uid=uid)
        if project is not None:
            project = ProjectAR.from_input_values(
                project_number=project.project_number,
                name=project.name,
                clinical_programme_uid=project.holds_project.single().uid,
                description=project.description,
                generate_uid_callback=lambda: project.uid,
                clinical_programme_exists_callback=lambda _: True,
            )
            return project
        return None

    @cached(
        cache=cache_store_item_by_project_number,
        key=get_hashkey,
        lock=lock_store_item_by_project_number,
    )
    def find_by_project_number(self, project_number: str) -> ProjectAR | None:
        project = Project.nodes.first_or_none(project_number=project_number)
        if project is not None:
            project = ProjectAR.from_input_values(
                project_number=project.project_number,
                name=project.name,
                clinical_programme_uid=project.holds_project.single().uid,
                description=project.description,
                generate_uid_callback=lambda: project.uid,
                clinical_programme_exists_callback=lambda _: True,
            )
            return project
        return None

    @cached(
        cache=cache_store_item_by_study_uid,
        key=get_hashkey,
        lock=lock_store_item_by_study_uid,
    )
    def find_by_study_uid(self, uid: str) -> ProjectAR:
        """
        Returns data from the project to which the study with provided uid belongs.

        :param uid: uid of the study for which to get project data
        :return: The project Aggregate Root object
        """
        study_root = StudyRoot.nodes.get(uid=uid)
        if study_root is not None:
            study_value = study_root.latest_value.get_or_none()
            study_project_node = study_value.has_project.get_or_none()
            project_node = study_project_node.has_field.get_or_none()
            return ProjectAR.from_input_values(
                project_number=project_node.project_number,
                name=project_node.name,
                clinical_programme_uid=project_node.holds_project.single().uid,
                description=project_node.description,
                generate_uid_callback=lambda: project_node.uid,
                clinical_programme_exists_callback=lambda _: True,
            )
        raise exceptions.DoesNotExist(f"Study with provided uid does not exist ({uid})")

    @sb_clear_cache(
        caches=[
            "cache_store_item_by_uid",
            "cache_store_item_by_project_number",
            "cache_store_item_by_study_uid",
        ]
    )
    def save(self, project: ProjectAR) -> None:
        """
        Public repository method for persisting a (possibly modified) state of the Project instance into the underlying
        DB. Provided instance can be brand new instance (never persisted before) or an instance which has been
        retrieved with find_by_uid(..., for_update=True). Attempt to persist an instance which was retrieved with
        for_update==False ends in error.

        :param study: an instance of a project aggregate (ProjectAR class) to persist
        """
        repository_closure_data = project.repository_closure_data

        if repository_closure_data is None:
            # if save gets an object without a closure - it's a new object.
            # object should already have a UID.
            project_node = Project(
                uid=project.uid,
                project_number=project.project_number,
                name=project.name,
                description=project.description,
            )
            project_node.save()
            clinical_programme_node = ClinicalProgramme.nodes.get(
                uid=project.clinical_programme_uid
            )
            project_node.holds_project.connect(clinical_programme_node)
        else:
            # if save gets an object with a closure, it's a modified existing object.
            raise NotImplementedError

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass

    def find_all(self) -> Collection[ProjectAR]:
        projects: list[Project] = Project.nodes.all()
        # projecting results to ProjectAR instances
        projects: list[ProjectAR] = [
            ProjectAR.from_input_values(
                project_number=p.project_number,
                name=p.name,
                clinical_programme_uid=p.holds_project.single().uid,
                description=p.description,
                generate_uid_callback=lambda x=p: x.uid,
                clinical_programme_exists_callback=lambda _: True,
            )
            for p in projects
        ]

        # attaching a proper repository closure data
        repository_closure_data = RepositoryClosureData(
            not_for_update=True, repository=self, additional_closure=None
        )
        for project in projects:
            project.repository_closure_data = repository_closure_data

        return projects
