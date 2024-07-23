from datetime import datetime
from typing import Callable, Self

from pydantic import Field, validator

from clinical_mdr_api import models
from clinical_mdr_api.domains.controlled_terminologies.ct_package import CTPackageAR
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_selection_standard_version import (
    StudyStandardVersionVO,
)
from clinical_mdr_api.models.utils import BaseModel, get_latest_on_datetime_str


class StudyStandardVersionInput(BaseModel):
    ct_package_uid: str = Field(
        ...,
        title="CTPackage uid",
        description="CTPackage uid to select for the study",
    )


class StudyStandardVersionOGM(BaseModel, StudyStandardVersionVO):
    class Config:
        orm_mode = True

    uid: str = Field(
        ..., title="Uid", description="Uid of the StandardVersion", source="uid"
    )
    study_uid: str = Field(
        ...,
        title="Uid",
        description="Uid of the study",
        source="has_after.audit_trail.uid",
    )

    study_status: StudyStatus = Field(
        ...,
        title="study status",
        description="Study status",
        source="status",
    )

    @validator("study_status", pre=True)
    # pylint: disable=no-self-argument,unused-argument
    def instantiate_study_status(cls, value, values):
        return StudyStatus[value]

    start_date: datetime | None = Field(
        ...,
        title="start_date",
        description="The most recent point in time when the study standard_version was edited."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
        source="has_after.date",
    )
    author: str = Field(
        ...,
        title="User Initials",
        description="Initials of user that created last modification",
        source="has_after.user_initials",
    )

    ct_package_uid: str = Field(
        ...,
        title="CTPackage uid",
        description="CTPackage Uid selected for the study",
        source="has_ct_package.uid",
    )


class StudyStandardVersionOGMVer(StudyStandardVersionOGM):
    study_uid: str = Field(
        ...,
        title="Uid",
        description="Uid of the study",
        source="has_after.audit_trail.uid",
    )
    change_type: str = Field(
        ...,
        title="start_date",
        description="type of action",
        source="has_after.__label__",
    )
    end_date: datetime | None = Field(
        None,
        title="end_date",
        description="The last point in time when the study standard version was modified."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
        source="has_before.date",
    )


class StudyStandardVersion(BaseModel):
    uid: str = Field(
        ...,
        title="Uid",
        description="Uid of the StandardVersion",
    )
    study_uid: str = Field(
        ...,
        title="study_uid",
        description="Uid of the StandardVersion Study",
    )
    study_version: str | None = Field(
        None,
        title="study version or date information",
        description="Study version number, if specified, otherwise None.",
    )
    ct_package: models.CTPackage | None = Field(
        None,
        title="CtPackage",
        description="CtPackage",
    )
    start_date: datetime = Field(
        ...,
        title="Modification date",
        description="Study StandardVersion last modification date",
    )
    end_date: datetime | None = Field(
        None,
        title="Modification date",
        description="Study StandardVersion last modification date",
    )
    study_status: str = Field(
        ..., title="Status", description="Study StandardVersion status"
    )
    user_initials: str = Field(
        ...,
        title="User Initials",
        description="Initials of user that created last modification",
    )
    change_type: str | None = Field(None, description="Type of Action")

    @classmethod
    def from_study_standard_version_vo(
        cls,
        study_standard_version_vo: StudyStandardVersionVO,
        find_ct_package_by_uid: Callable[[str], CTPackageAR | None],
        study_value_version: str | None = None,
    ) -> Self:
        ct_package = None
        ct_package = find_ct_package_by_uid(study_standard_version_vo.ct_package_uid)
        return cls(
            uid=study_standard_version_vo.uid,
            study_uid=study_standard_version_vo.study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            ct_package=ct_package,
            user_initials=study_standard_version_vo.author,
            start_date=study_standard_version_vo.start_date,
            end_date=study_standard_version_vo.end_date,
            study_status=study_standard_version_vo.study_status.name,
        )


class StudyStandardVersionVersion(StudyStandardVersion):
    changes: dict


class StudySelectionStandardVersionNewOrder(BaseModel):
    new_order: int = Field(
        ...,
        title="new_order",
        description="new order of the selected standard versions",
    )
