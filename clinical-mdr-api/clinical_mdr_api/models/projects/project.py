from typing import Callable, Self

from pydantic import Field

from clinical_mdr_api.domains.clinical_programmes.clinical_programme import (
    ClinicalProgrammeAR,
)
from clinical_mdr_api.domains.projects.project import ProjectAR
from clinical_mdr_api.models.clinical_programmes.clinical_programme import (
    ClinicalProgramme,
)
from clinical_mdr_api.models.utils import BaseModel


class Project(BaseModel):
    uid: str = Field(
        ...,
        title="uid",
        description="The unique id of the Project.",
    )

    project_number: str | None = Field(
        ...,
        title="project_number",
        description="",
    )

    clinical_programme: ClinicalProgramme = Field(
        ...,
        title="clinical_programme",
        description="",
    )

    name: str | None = Field(
        ...,
        title="name",
        description="",
    )

    description: str | None = Field(
        ...,
        title="description",
        description="",
    )

    @classmethod
    def from_uid(
        cls,
        uid: str,
        find_by_uid: Callable[[str], ProjectAR | None],
        find_clinical_programme_by_uid: Callable[[str], ClinicalProgrammeAR],
    ) -> Self | None:
        project = None
        if uid is not None:
            project_ar: ProjectAR = find_by_uid(uid)
            if project_ar is not None:
                project = Project.from_project_ar(
                    project_ar, find_clinical_programme_by_uid
                )
        return project

    @classmethod
    def from_project_ar(
        cls,
        project_ar: ProjectAR,
        find_clinical_programme_by_uid: Callable[[str], ClinicalProgrammeAR],
    ) -> Self:
        return Project(
            uid=project_ar.uid,
            project_number=project_ar.project_number,
            name=project_ar.name,
            clinical_programme=ClinicalProgramme(
                uid=project_ar.clinical_programme_uid,
                name=find_clinical_programme_by_uid(
                    project_ar.clinical_programme_uid
                ).name,
            ),
            description=project_ar.description,
        )


class ProjectCreateInput(BaseModel):
    project_number: str | None = Field(
        ...,
        title="project_number",
        description="",
    )

    name: str | None = Field(
        ...,
        title="name",
        description="",
    )

    description: str | None = Field(
        ...,
        title="description",
        description="",
    )

    clinical_programme_uid: str = Field(
        ...,
        title="clinical_programme_uid",
        description="",
    )
