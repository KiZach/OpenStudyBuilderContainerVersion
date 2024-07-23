from datetime import datetime

from pydantic import Field

from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.models import _generic_descriptions
from clinical_mdr_api.models.utils import BaseModel


class SimpleDataModel(BaseModel):
    uid: str
    name: str


class DataModelIG(BaseModel):
    uid: str
    name: str = Field(
        ...,
        title="name",
        description="The name or the data model ig. E.g. 'SDTM', 'ADAM', ...",
    )
    description: str = Field(
        ...,
        title="name_sentence_case",
        description="",
    )
    implemented_data_model: SimpleDataModel | None = Field(
        None, title="implemented_data_model", description="", nullable=True
    )
    version_number: str = Field(
        ...,
        title="version_number",
        description="The version or the data model ig. E.g. '1.1.1'",
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
            implemented_data_model=SimpleDataModel(
                uid=input_dict.get("implemented_data_model").get("uid"),
                name=input_dict.get("implemented_data_model").get("name"),
            )
            if input_dict.get("implemented_data_model")
            else None,
            version_number=input_dict.get("version_number"),
            start_date=convert_to_datetime(input_dict.get("start_date")),
            status=input_dict.get("status"),
        )
