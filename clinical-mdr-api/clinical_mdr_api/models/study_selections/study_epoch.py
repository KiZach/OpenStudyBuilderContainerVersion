from datetime import datetime

from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class StudyEpochCreateInput(BaseModel):
    study_uid: str = Field(
        ...,
        title="study_uid",
        description="The uid of the study",
    )

    start_rule: str | None = Field(
        None, title="Start Description", description="Study Epoch Start description"
    )

    end_rule: str | None = Field(
        None, title="End Description", description="Study Epoch end description"
    )

    epoch: str | None = Field(None, title="Epoch", description="Study Epoch epoch")

    epoch_subtype: str = Field(
        ..., title="Epoch Sub Type", description="Study Epoch sub type"
    )

    duration_unit: str | None = Field(
        None, title="Duration Unit", description="Study Epoch duration preferred unit"
    )

    order: int | None = Field(
        None,
        title="order",
        description="The ordering of the selection",
    )
    description: str | None = Field(
        None, title="Description", description="Epoch description"
    )

    duration: int | None = Field(
        None, title="Epoch Duration", description="Calculated epoch duration"
    )
    color_hash: str | None = Field(
        "#FFFFFF", title="Epoch Color Hash", description="Epoch Color for display"
    )


class StudyEpochEditInput(StudyEpochCreateInput):
    # Override epoch from Create Input to make it Optional
    epoch_subtype: str | None = Field(
        None, title="Epoch Sub Type", description="Study Epoch sub type"
    )
    change_description: str = Field(
        ..., title="Change Description", description="Description of change reasons"
    )


class StudyEpochOGM(BaseModel):
    class Config:
        orm_mode = True

    uid: str = Field(..., title="Uid", description="Uid of the Epoch", source="uid")
    study_uid: str = Field(
        ...,
        title="Uid",
        description="Uid of the study",
        source="has_after.audit_trail.uid",
    )
    study_version: str | None = Field(
        None,
        title="study version or date information",
        description="Study version number, if specified, otherwise None.",
    )
    epoch: str = Field(
        ...,
        title="Epoch name",
        description="Name of the epoch based on CT term",
        source="has_epoch.uid",
    )
    epoch_subtype: str = Field(
        ...,
        title="Epoch sub type name",
        description="Name of the epoch sub type based on CT term",
        source="has_epoch_subtype.uid",
    )
    epoch_type: str = Field(
        ..., title="Type", description="Study Epoch type", source="has_epoch_type.uid"
    )
    duration_unit: str | None = Field(
        None,
        title="Duration Unit",
        description="Study Epoch duration preferred unit",
        source="has_duration_unit.uid",
    )

    order: int | None = Field(
        None,
        title="order",
        description="The ordering of the selection",
        source="order",
        nullable=True,
    )
    description: str | None = Field(
        None,
        title="Description",
        description="Epoch description",
        source="description",
        nullable=True,
    )

    color_hash: str | None = Field(
        None,
        title="Epoch Color Hash",
        description="Epoch Color for display",
        source="color_hash",
        nullable=True,
    )
    start_rule: str | None = Field(
        None,
        title="Start Description",
        description="Study Epoch Start description",
        source="start_rule",
        nullable=True,
    )

    end_rule: str | None = Field(
        None,
        title="End Description",
        description="Study Epoch end description",
        source="end_rule",
        nullable=True,
    )
    status: str = Field(
        ..., title="Status", description="Study Epoch status", source="status"
    )
    start_date: datetime = Field(
        ...,
        title="start_date",
        description="The most recent point in time when the study epoch was edited."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
        source="has_after.date",
    )
    user_initials: str = Field(
        ...,
        title="User Initials",
        description="Initials of user that created last modification",
        source="has_after.user_initials",
    )


class StudyEpochOGMVer(StudyEpochOGM):
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
        description="The last point in time when the study epoch was edited."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
        source="has_before.date",
    )


class StudyEpoch(StudyEpochCreateInput):
    uid: str = Field(
        ...,
        title="Uid",
        description="Uid of the Epoch",
    )
    study_version: str | None = Field(
        None,
        title="study version or date information",
        description="Study version number, if specified, otherwise None.",
    )
    epoch_name: str = Field(
        ..., title="Study epoch name", description="Name of the epoch based on CT term"
    )
    epoch_subtype_name: str = Field(
        ...,
        title="Study Epoch subtype name",
        description="Name of the epoch sub type based on CT term",
    )
    epoch_type: str = Field(..., title="Type", description="Study Epoch type uid")
    epoch_type_name: str = Field(..., title="Type", description="Study Epoch type name")
    start_day: int | None = Field(
        None, title="Start Day", description="Study Epoch start day"
    )
    end_day: int | None = Field(
        None, title="End Day", description="Study Epoch end day"
    )
    start_week: int | None = Field(
        None, title="Start Week", description="Study Epoch start week"
    )
    end_week: int | None = Field(
        None, title="End Week", description="Study Epoch end week"
    )
    start_date: str = Field(
        ...,
        title="Modification date",
        description="Study Epoch initial modification date",
    )
    end_date: str | None = Field(
        None,
        title="Modification date",
        description="Study Epoch last modification date",
    )
    status: str = Field(..., title="Status", description="Study Epoch status")
    user_initials: str = Field(
        ...,
        title="User Initials",
        description="Initials of user that created last modification",
    )
    possible_actions: list[str] = Field(
        ..., title="Possible actions", description="List of actions to perform on item"
    )
    change_description: str | None = Field(
        "", title="Change Description", description="Description of change reasons"
    )
    study_visit_count: int = Field(
        ..., description="Count of Study Visits assigned to Study Epoch"
    )
    change_type: str | None = Field(None, description="Type of Action")


class StudyEpochVersion(StudyEpoch):
    changes: dict


class StudyEpochTypes(BaseModel):
    type: str = Field(..., title="Type", description="Study Epoch type")
    type_name: str
    subtype: str = Field(..., title="Subtype", description="Study Epoch subtype")
    subtype_name: str
