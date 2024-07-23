from neomodel import db  # type: ignore

from clinical_mdr_api import models
from clinical_mdr_api.domains.projects.project import ProjectAR
from clinical_mdr_api.models import ProjectCreateInput
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.oauth.user import user
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore
from clinical_mdr_api.services._utils import (
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)


class ProjectService:
    user_initials: str | None

    def __init__(self):
        self.user_initials = user().id()

    def get_all_projects(
        self,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 10,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[models.Project]:
        repos = MetaRepository()
        try:
            all_projects = repos.project_repository.find_all()
            repos.project_repository.close()
            items = [
                models.Project.from_project_ar(
                    project_ar, repos.clinical_programme_repository.find_by_uid
                )
                for project_ar in all_projects
            ]
            filtered_items = service_level_generic_filtering(
                items=items,
                filter_by=filter_by,
                filter_operator=filter_operator,
                sort_by=sort_by,
                total_count=total_count,
                page_number=page_number,
                page_size=page_size,
            )
            return GenericFilteringReturn.create(
                filtered_items.items, filtered_items.total
            )
        finally:
            repos.close()

    def get_project_headers(
        self,
        field_name: str,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        result_count: int = 10,
    ):
        repos = MetaRepository()
        all_projects = repos.project_repository.find_all()
        repos.project_repository.close()
        items = [
            models.Project.from_project_ar(
                project_ar, repos.clinical_programme_repository.find_by_uid
            )
            for project_ar in all_projects
        ]
        filtered_items = service_level_generic_header_filtering(
            items=items,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            result_count=result_count,
        )
        return filtered_items

    def get_by_study_uid(self, study_uid: str) -> models.Project:
        repos = MetaRepository()
        project_ar = repos.project_repository.find_by_study_uid(study_uid)
        return models.Project.from_project_ar(
            project_ar, repos.clinical_programme_repository.find_by_uid
        )

    @db.transaction
    def create(self, project_create_input: ProjectCreateInput) -> models.Project:
        repos = MetaRepository()
        try:
            project_ar = ProjectAR.from_input_values(
                project_number=project_create_input.project_number,
                name=project_create_input.name,
                clinical_programme_uid=project_create_input.clinical_programme_uid,
                description=project_create_input.description,
                generate_uid_callback=repos.project_repository.generate_uid,
                clinical_programme_exists_callback=repos.clinical_programme_repository.clinical_programme_exists,
            )

            repos.project_repository.save(project_ar)
            return models.Project.from_uid(
                uid=project_ar.uid,
                find_by_uid=repos.project_repository.find_by_uid,
                find_clinical_programme_by_uid=repos.clinical_programme_repository.find_by_uid,
            )
        finally:
            repos.close()
