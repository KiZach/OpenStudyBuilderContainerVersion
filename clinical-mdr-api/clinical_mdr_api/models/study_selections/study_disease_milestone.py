from datetime import datetime

from pydantic import Field, validator

from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_disease_milestone import (
    StudyDiseaseMilestoneVO,
)
from clinical_mdr_api.models.utils import BaseModel


class StudyDiseaseMilestoneEditInput(BaseModel):
    disease_milestone_type: str | None = Field(
        None,
        title="Disease Milestone Type uid",
        description="Study Disease Milestone Type uid",
    )

    repetition_indicator: bool | None = Field(
        None,
        title="repetition_indicator",
        description="DiseaseMilestone repetition_indicator",
    )


class StudyDiseaseMilestoneCreateInput(StudyDiseaseMilestoneEditInput):
    # Override disease_milestone from Create Input to make it Mandatory
    disease_milestone_type: str = Field(
        ...,
        title="Disease Milestone Type uid",
        description="Study Disease Milestone Type uids",
    )
    repetition_indicator: bool = Field(
        ...,
        title="repetition_indicator",
        description="DiseaseMilestone repetition_indicator",
    )
    order: int | None = Field(
        None,
        title="order",
        description="The ordering of the selection",
    )
    study_uid: str = Field(
        ...,
        title="study_uid",
        description="The uid of the study",
    )


class StudyDiseaseMilestoneOGM(BaseModel, StudyDiseaseMilestoneVO):
    class Config:
        orm_mode = True

    uid: str = Field(
        ..., title="Uid", description="Uid of the DiseaseMilestone", source="uid"
    )
    study_uid: str = Field(
        ...,
        title="Uid",
        description="Uid of the study",
        source="has_after.audit_trail.uid",
    )

    order: int | None = Field(
        None, title="order", description="The ordering of the selection", source="order"
    )
    status: StudyStatus = Field(
        ...,
        title="Status",
        description="Study disease milestone status",
        source="status",
    )

    @validator("status", pre=True)
    # pylint: disable=no-self-argument,unused-argument
    def instantiate_study_status(cls, value, values):
        return StudyStatus[value]

    start_date: datetime | None = Field(
        ...,
        title="start_date",
        description="The most recent point in time when the study disease_milestone was edited."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
        source="has_after.date",
    )
    author: str = Field(
        ...,
        title="User Initials",
        description="Initials of user that created last modification",
        source="has_after.user_initials",
    )

    disease_milestone_type: str = Field(
        ...,
        title="Disease Milestone Type name",
        description="Name of the disease_milestone type based on CT term",
        source="has_disease_milestone_type.uid",
    )

    disease_milestone_type_definition: str = Field(
        ...,
        title="Disease Milestone Type name",
        description="Name of the disease_milestone type based on CT term",
        source="has_disease_milestone_type.has_attributes_root.latest_final.definition",
    )

    disease_milestone_type_named: str = Field(
        ...,
        title="Disease Milestone Type name",
        description="Name of the disease_milestone type based on CT term",
        source="has_disease_milestone_type.has_name_root.latest_final.name",
    )

    repetition_indicator: bool = Field(
        ...,
        title="repetition_indicator",
        description="DiseaseMilestone repetition_indicator",
        source="repetition_indicator",
    )


class StudyDiseaseMilestoneOGMVer(StudyDiseaseMilestoneOGM):
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
        description="The last point in time when the study disease milestone was modified."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
        source="has_before.date",
    )


class StudyDiseaseMilestone(StudyDiseaseMilestoneCreateInput):
    uid: str = Field(
        ...,
        title="Uid",
        description="Uid of the DiseaseMilestone",
    )
    study_uid: str = Field(
        ...,
        title="study_uid",
        description="Uid of the DiseaseMilestone Study",
    )
    study_version: str | None = Field(
        None,
        title="study version or date information",
        description="Study version number, if specified, otherwise None.",
    )
    disease_milestone_type: str
    disease_milestone_type_named: str
    disease_milestone_type_definition: str
    start_date: datetime = Field(
        ...,
        title="Modification date",
        description="Study DiseaseMilestone last modification date",
    )
    end_date: datetime | None = Field(
        None,
        title="Modification date",
        description="Study DiseaseMilestone last modification date",
    )
    status: str = Field(
        ..., title="Status", description="Study DiseaseMilestone status"
    )
    user_initials: str = Field(
        ...,
        title="User Initials",
        description="Initials of user that created last modification",
    )
    change_type: str | None = Field(None, description="Type of Action")


class StudyDiseaseMilestoneVersion(StudyDiseaseMilestone):
    changes: dict


class StudySelectionDiseaseMilestoneNewOrder(BaseModel):
    new_order: int = Field(
        ...,
        title="new_order",
        description="new order of the selected disease milestones",
    )
