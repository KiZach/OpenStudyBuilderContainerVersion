from datetime import datetime

from pydantic import Field

from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.models import _generic_descriptions
from clinical_mdr_api.models.utils import BaseModel


class SimpleImplementationGuide(BaseModel):
    uid: str
    name: str


class DataModel(BaseModel):
    uid: str
    name: str = Field(
        ...,
        title="name",
        description="The name or the data model. E.g. 'SDTM', 'ADAM', ...",
    )
    description: str = Field(
        ...,
        title="name_sentence_case",
        description="",
    )
    implementation_guides: list[SimpleImplementationGuide] = Field(
        [],
        title="implementation_guides",
        description="",
    )
    version_number: str = Field(
        ...,
        title="version_number",
        description="The version or the data model ig. E.g. '1.4'",
    )
    start_date: datetime = Field(
        ...,
        title="start_date",
        description=_generic_descriptions.START_DATE,
    )
    status: str = Field(..., title="status", description="")

    @classmethod
    def from_repository_output(cls, input_dict: dict):
        return cls(
            uid=input_dict.get("uid"),
            name=input_dict.get("standard_value").get("name"),
            description=input_dict.get("standard_value").get("description"),
            implementation_guides=[
                SimpleImplementationGuide(
                    uid=ig.get("uid"),
                    name=ig.get("name"),
                )
                for ig in input_dict.get("implementation_guides")
            ],
            version_number=input_dict.get("version_number"),
            start_date=convert_to_datetime(input_dict.get("start_date")),
            status=input_dict.get("status"),
        )
