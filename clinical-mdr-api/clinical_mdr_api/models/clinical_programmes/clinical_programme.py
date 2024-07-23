from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class ClinicalProgramme(BaseModel):
    uid: str = Field(
        ...,
        title="uid",
        description="The unique id of the ClinicalProgramme value.",
    )

    name: str = Field(
        ...,
        title="name",
        description="",
    )


class ClinicalProgrammeInput(BaseModel):
    name: str = Field(
        ...,
        title="name",
        description="",
        min_length=1,
    )
