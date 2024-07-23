from datetime import datetime
from typing import Callable

from pydantic import Field, conlist, validator

from clinical_mdr_api.config import (
    DAY_UNIT_CONVERSION_FACTOR_TO_MASTER,
    DAY_UNIT_NAME,
    WEEK_UNIT_CONVERSION_FACTOR_TO_MASTER,
    WEEK_UNIT_NAME,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_epoch import (
    EpochNamedTuple,
    StudyEpochEpoch,
)
from clinical_mdr_api.domains.study_selections.study_visit import (
    StudyVisitContactMode,
    StudyVisitEpochAllocation,
    StudyVisitRepeatingFrequency,
    StudyVisitTimeReference,
    StudyVisitType,
    StudyVisitVO,
    VisitClass,
    VisitContactModeNamedTuple,
    VisitEpochAllocationNamedTuple,
    VisitRepeatingFrequencyNamedTuple,
    VisitSubclass,
    VisitTimeReferenceNamedTuple,
    VisitTypeNamedTuple,
)
from clinical_mdr_api.models.utils import BaseModel


class StudyVisitCreateInput(BaseModel):
    study_epoch_uid: str = Field(alias="study_epoch_uid")

    visit_type_uid: str = Field(source="has_visit_type.uid")
    time_reference_uid: str | None
    time_value: int | None
    time_unit_uid: str | None

    visit_sublabel_codelist_uid: str | None
    visit_sublabel_reference: str | None

    consecutive_visit_group: str | None

    show_visit: bool = Field(alias="show_visit")

    min_visit_window_value: int | None = -9999
    max_visit_window_value: int | None = 9999
    visit_window_unit_uid: str | None

    description: str | None

    start_rule: str | None
    end_rule: str | None
    visit_contact_mode_uid: str
    epoch_allocation_uid: str | None
    visit_class: str
    visit_subclass: str | None
    is_global_anchor_visit: bool
    is_soa_milestone: bool = False
    visit_name: str | None = None
    visit_short_name: str | None = None
    visit_number: float | None = None
    unique_visit_number: int | None = None
    repeating_frequency_uid: str | None = Field(
        None, source="has_repeating_frequency.uid"
    )


class StudyVisitEditInput(StudyVisitCreateInput):
    uid: str = Field(
        ...,
        title="Uid",
        description="Uid of the Visit",
    )


class TimeUnit(BaseModel):
    class Config:
        orm_mode = True

    name: str | None = Field(
        None,
        description="Uid of visit unit",
        source="has_timepoint.has_latest_value.has_unit_definition.has_latest_value.name",
    )
    conversion_factor_to_master: float | None = Field(
        None,
        description="Uid of visit unit",
        source="has_timepoint.has_latest_value.has_unit_definition.has_latest_value.conversion_factor_to_master",
    )
    from_timedelta: Callable | None = Field(None, exclude_from_orm=True)

    @validator("from_timedelta", always=True)
    # pylint: disable=no-self-argument,unused-argument
    def validate_time_unit_obj(cls, value, values):
        if values.get("conversion_factor_to_master") is not None:
            return lambda u, x: u.conversion_factor_to_master * x
        return None


class WindowTimeUnit(BaseModel):
    class Config:
        orm_mode = True

    name: str | None = Field(
        None,
        description="Uid of visit unit",
        source="has_window_unit.has_latest_value.name",
    )
    conversion_factor_to_master: float | None = Field(
        None,
        description="Uid of visit unit",
        source="has_window_unit.has_latest_value.conversion_factor_to_master",
    )
    from_timedelta: Callable | None = Field(None, exclude_from_orm=True)

    @validator("from_timedelta", always=True)
    # pylint: disable=no-self-argument,unused-argument
    def validate_time_unit_obj(cls, value, values):
        if values.get("conversion_factor_to_master"):
            return lambda u, x: u.conversion_factor_to_master * x
        return None


class TimePoint(BaseModel):
    class Config:
        orm_mode = True

    uid: str | None = Field(
        None,
        title="TimepointUid",
        description="Uid of timepoint",
        source="has_timepoint.uid",
    )

    time_unit_uid: str | None = Field(
        None,
        title="TimeUnitUid",
        description="Uid of time unit",
        source="has_timepoint.has_latest_value.has_unit_definition.uid",
    )
    visit_timereference: VisitTimeReferenceNamedTuple | None = Field(
        None, source="has_timepoint.has_latest_value.has_time_reference.uid"
    )

    @validator("visit_timereference", pre=True)
    # pylint: disable=no-self-argument,unused-argument
    def instantiate_visit_timereference(
        cls, value, values
    ) -> VisitTimeReferenceNamedTuple | None:
        if value:
            return StudyVisitTimeReference[value]
        return None

    visit_value: int | None = Field(
        None,
        title="TimepointValue",
        description="Value of timepoint",
        source="has_timepoint.has_latest_value.has_value.has_latest_value.value",
    )


class StudyDay(BaseModel):
    class Config:
        orm_mode = True

    uid: str | None = Field(
        None,
        title="Study day uid",
        description="The uid of study day",
        source="has_study_day.uid",
    )
    value: int | None = Field(
        None,
        title="Study day value",
        description="The value of the study day",
        source="has_study_day.has_latest_value.value",
    )


class StudyDurationDays(BaseModel):
    class Config:
        orm_mode = True

    uid: str | None = Field(
        None,
        title="Study duration days uid",
        description="The uid of study duration days",
        source="has_study_duration_days.uid",
    )
    value: int | None = Field(
        None,
        title="Study duration days value",
        description="The value of the study duration days",
        source="has_study_duration_days.has_latest_value.value",
    )


class StudyWeek(BaseModel):
    class Config:
        orm_mode = True

    uid: str | None = Field(
        None,
        title="Study week uid",
        description="The uid of study week",
        source="has_study_week.uid",
    )
    value: int | None = Field(
        None,
        title="Study week value",
        description="The value of the study week",
        source="has_study_week.has_latest_value.value",
    )


class StudyDurationWeeks(BaseModel):
    class Config:
        orm_mode = True

    uid: str | None = Field(
        None,
        title="Study duration weeks uid",
        description="The uid of study duration weeks",
        source="has_study_duration_weeks.uid",
    )
    value: int | None = Field(
        None,
        title="Study duration weeks value",
        description="The value of the study duration weeks",
        source="has_study_duration_weeks.has_latest_value.value",
    )


class WeekInStudy(BaseModel):
    class Config:
        orm_mode = True

    uid: str | None = Field(
        None,
        title="Week in study uid",
        description="The uid of week in study",
        source="has_week_in_study.uid",
    )
    value: int | None = Field(
        None,
        title="Week in study value",
        description="The value of the week in study",
        source="has_week_in_study.has_latest_value.value",
    )


class VisitName(BaseModel):
    class Config:
        orm_mode = True

    uid: str | None = Field(
        None,
        title="Visit name uid",
        description="The uid of the visit name",
        source="has_visit_name.uid",
    )
    name: str | None = Field(
        None,
        title="Visit name name",
        description="The name of the visit",
        source="has_visit_name.has_latest_value.name",
    )


class StudyEpochSimpleOGM(BaseModel):
    class Config:
        orm_mode = True

    uid: str = Field(
        ...,
        title="Visit name uid",
        description="The uid of the visit name",
        source="study_epoch_has_study_visit.uid",
    )
    study_uid: str = Field(
        ...,
        title="Study Uid",
        description="The uid of the study",
        source="has_after.audit_trail.uid",
    )
    epoch: EpochNamedTuple = Field(
        ...,
        title="Visit name name",
        description="The name of the visit",
        source="study_epoch_has_study_visit.has_epoch.uid",
    )

    @validator("epoch", pre=True)
    # pylint: disable=no-self-argument,unused-argument
    def instantiate_epoch(cls, value, values) -> EpochNamedTuple:
        return StudyEpochEpoch[value]

    order: int = Field(
        ...,
        title="Study epoch order",
        description="The order of epoch",
        source="study_epoch_has_study_visit.order",
    )


class StudyVisitOGM(BaseModel, StudyVisitVO):
    class Config:
        orm_mode = True

    uid: str = Field(..., title="Uid", description="Uid of the Visit", source="uid")

    consecutive_visit_group: str | None = Field(
        None,
        title="Consecutive visit group",
        description="Consecutive visit group",
        source="consecutive_visit_group",
        nullable=True,
    )
    visit_window_min: int | None = Field(
        None,
        title="Visit window min",
        description="Min value of visit window",
        source="visit_window_min",
        nullable=True,
    )
    visit_window_max: int | None = Field(
        None,
        title="Visit window max",
        description="Max value of visit window",
        source="visit_window_max",
        nullable=True,
    )
    window_unit_uid: str | None = Field(
        None,
        title="Window unit uid",
        description="Uid of window unit",
        source="has_window_unit.uid",
        nullable=True,
    )
    description: str | None = Field(
        None,
        title="Description",
        description="Description",
        source="description",
        nullable=True,
    )
    start_rule: str | None = Field(
        None,
        title="Start rule",
        description="The start rule of visit",
        source="start_rule",
        nullable=True,
    )
    end_rule: str | None = Field(
        None,
        title="End rule",
        description="The end rule of visit",
        source="end_rule",
        nullable=True,
    )
    visit_contact_mode: VisitContactModeNamedTuple = Field(
        ...,
        title="Visit contact mode",
        description="The contact mode of study visit",
        source="has_visit_contact_mode.uid",
    )

    @validator("visit_contact_mode", pre=True)
    # pylint: disable=no-self-argument,unused-argument
    def instantiate_visit_contact_mode(
        cls, value, values
    ) -> VisitContactModeNamedTuple:
        return StudyVisitContactMode[value]

    epoch_allocation: VisitEpochAllocationNamedTuple | None = Field(
        None,
        title="Epoch allocation rule",
        description="Epoch allocation rule",
        source="has_epoch_allocation.uid",
        nullable=True,
    )

    @validator("epoch_allocation", pre=True)
    # pylint: disable=no-self-argument,unused-argument
    def instantiate_epoch_allocation(
        cls, value, values
    ) -> VisitEpochAllocationNamedTuple | None:
        if value:
            return StudyVisitEpochAllocation[value]
        return None

    visit_type: VisitTypeNamedTuple = Field(
        ...,
        title="visit_unit_uid",
        description="Uid of visit unit",
        source="has_visit_type.uid",
    )

    @validator("visit_type", pre=True)
    # pylint: disable=no-self-argument,unused-argument
    def instantiate_visit_type(cls, value, values) -> VisitTypeNamedTuple:
        return StudyVisitType[value]

    author: str = Field(
        ...,
        title="User Initials",
        description="Initials of user that created last modification",
        source="has_after.user_initials",
    )
    start_date: datetime | None = Field(
        ...,
        title="start_date",
        description="The most recent point in time when the study visit was edited."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
        source="has_after.date",
    )
    status: StudyStatus = Field(
        ..., title="Status", description="Study visit status", source="status"
    )

    @validator("status", pre=True)
    # pylint: disable=no-self-argument,unused-argument
    def instantiate_study_status(cls, value, values):
        return StudyStatus[value]

    visit_class: VisitClass = Field(
        title="Visit class", description="Visit class", source="visit_class"
    )

    @validator("visit_class", pre=True)
    # pylint: disable=no-self-argument
    def instantiate_visit_class(cls, value):
        return VisitClass[value]

    visit_subclass: VisitSubclass | None = Field(
        None,
        title="Visit subclass",
        description="Visit subclass",
        source="visit_subclass",
        nullable=True,
    )

    @validator("visit_subclass", pre=True)
    # pylint: disable=no-self-argument
    def instantiate_visit_subclass(cls, value):
        if value:
            return VisitSubclass[value]
        return None

    is_global_anchor_visit: bool = Field(
        ...,
        title="Is global anchor visit",
        description="Is global anchor visit",
        source="is_global_anchor_visit",
    )
    is_soa_milestone: bool = Field(
        False,
        title="Is soa milestone",
        source="is_soa_milestone",
    )

    repeating_frequency: VisitRepeatingFrequencyNamedTuple | None = Field(
        None,
        title="Repeating Frequency",
        description="Repeating Frequency",
        source="has_repeating_frequency.uid",
    )

    @validator("repeating_frequency", pre=True)
    # pylint: disable=no-self-argument,unused-argument
    def instantiate_repeating_frequency(
        cls, value, values
    ) -> VisitRepeatingFrequencyNamedTuple:
        if value:
            return StudyVisitRepeatingFrequency[value]
        return None

    timepoint: TimePoint | None = Field(None, nullable=True)
    study_day: StudyDay | None = Field(None, nullable=True)
    study_week: StudyWeek | None = Field(None, nullable=True)
    study_duration_days: StudyDurationDays | None = Field(None, nullable=True)
    study_duration_weeks: StudyDurationWeeks | None = Field(None, nullable=True)
    week_in_study: WeekInStudy | None = Field(None, nullable=True)
    visit_name_sc: VisitName = Field(...)

    visit_number: float = Field(
        ...,
        title="Visit number",
        description="The number of the study visit",
        source="visit_number",
    )
    visit_order: int | None = Field(
        None,
        title="Visit order",
        description="The order of the study visit",
        nullable=True,
    )
    subvisit_number: int | None = Field(
        None, title="Subvisit number", description="Subvisit number", nullable=True
    )
    subvisit_anchor: "StudyVisitOGM | None"
    show_visit: bool = Field(
        ...,
        title="Show visit",
        description="Whether to show visit or not",
        source="show_visit",
    )
    time_unit_object: TimeUnit | None = Field(...)
    window_unit_object: WindowTimeUnit | None = Field(...)
    epoch_connector: StudyEpochSimpleOGM = Field(...)
    day_unit_object: TimeUnit = Field(...)

    @validator("day_unit_object", pre=True, always=True)
    # pylint: disable=no-self-argument,unused-argument
    def validate_day_unit_obj(cls, value, values):
        return TimeUnit(
            name=DAY_UNIT_NAME,
            conversion_factor_to_master=DAY_UNIT_CONVERSION_FACTOR_TO_MASTER,
            from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
        )

    week_unit_object: TimeUnit = Field(...)

    @validator("week_unit_object", pre=True, always=True)
    # pylint: disable=no-self-argument,unused-argument
    def validate_week_unit_obj(cls, value, values):
        return TimeUnit(
            name=WEEK_UNIT_NAME,
            conversion_factor_to_master=WEEK_UNIT_CONVERSION_FACTOR_TO_MASTER,
            from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
        )

    anchor_visit: "StudyVisitOGM | None"

    visit_sublabel: str | None = Field(
        ..., title="Status", description="Study visit status", source="visit_sublabel"
    )
    visit_sublabel_reference: str | None = Field(
        None,
        title="Status",
        description="Study visit status",
        source="visit_sublabel_reference",
        nullable=True,
    )
    visit_sublabel_uid: str | None = Field(
        ...,
        title="Status",
        description="Study visit status",
        source="visit_sublabel_uid",
    )
    vis_unique_number: int | None = Field(
        ...,
        title="unique_visit_number",
        source="unique_visit_number",
    )
    vis_short_name: str | None = Field(
        ...,
        title="visit_short_name",
        source="short_visit_label",
    )


class StudyVisitOGMVer(StudyVisitOGM):
    change_type: str = Field(
        ...,
        title="start_date",
        description="type of action",
        source="has_after.__label__",
    )
    end_date: datetime | None = Field(
        None,
        title="end_date",
        description="The last point in time when the study visit was edited."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
        source="has_before.date",
    )


class SimpleStudyVisit(BaseModel):
    class Config:
        orm_mode = True

    uid: str = Field(..., title="Uid", description="Uid of the visit", source="uid")
    visit_name: str = Field(
        ...,
        title="Visit name",
        description="Name of the visit",
        source="has_visit_name.has_latest_value.name",
    )
    visit_type_name: str = Field(
        ...,
        title="Visit type name",
        description="Name of the visit type",
        source="has_visit_type.has_name_root.has_latest_value.name",
    )


class StudyVisit(StudyVisitEditInput):
    class Config:
        allow_population_by_field_name = True
        orm_mode = True

    study_uid: str
    study_version: str | None = Field(
        None,
        title="study version or date information",
        description="Study version number, if specified, otherwise None.",
    )
    study_epoch_name: str
    # study_epoch_name can be calculated from uid
    epoch_uid: str = Field(
        ...,
        title="The uid of the study epoch",
        description="The uid of the study epoch",
    )

    order: int

    visit_type_name: str

    time_reference_uid: str | None
    time_reference_name: str | None
    time_value: int | None
    time_unit_uid: str | None
    time_unit_name: str | None
    visit_contact_mode_uid: str
    visit_contact_mode_name: str
    epoch_allocation_uid: str | None
    epoch_allocation_name: str | None

    repeating_frequency_uid: str | None
    repeating_frequency_name: str | None

    duration_time: float | None
    duration_time_unit: str | None

    study_day_number: int | None
    study_duration_days: int | None
    study_duration_days_label: str | None
    study_day_label: str | None
    study_week_number: int | None
    study_duration_weeks: int | None
    study_duration_weeks_label: str | None
    study_week_label: str | None
    week_in_study_label: str | None

    visit_number: float = Field(alias="visit_number")
    visit_subnumber: int

    unique_visit_number: int = Field(alias="unique_visit_number")
    visit_subname: str
    visit_sublabel: str | None = Field(alias="visit_sublabel")

    visit_name: str
    visit_short_name: str

    visit_window_unit_name: str | None
    visit_class: str
    visit_subclass: str | None
    is_global_anchor_visit: bool
    is_soa_milestone: bool
    status: str = Field(..., title="Status", description="Study Visit status")
    start_date: datetime = Field(
        ..., title="Creation Date", description="Study Visit creation date"
    )
    end_date: datetime | None = Field(
        None,
        title="Last Date of version",
        description="Study Visit last date of version",
    )
    user_initials: str = Field(
        ...,
        title="User Initials",
        description="Initials of user that created last modification",
    )
    possible_actions: list[str] = Field(
        ..., title="Possible actions", description="List of actions to perform on item"
    )
    study_activity_count: int | None = Field(
        None,
        description="Count of Study Activities assigned to Study Visit",
        nullable=True,
    )
    change_type: str = Field(None, description="Type of Action")


class StudyVisitVersion(StudyVisit):
    changes: dict


class AllowedVisitTypesForEpochType(BaseModel):
    visit_type_uid: str = Field(
        ..., title="visit type uid", description="Visit Type Term uid"
    )
    visit_type_name: str = Field(
        ..., title="visit type name", description="Visit type Term name"
    )


class AllowedTimeReferences(BaseModel):
    time_reference_uid: str
    time_reference_name: str


class VisitConsecutiveGroupInput(BaseModel):
    visits_to_assign: conlist(str, min_items=2) = Field(
        ...,
        title="visits_to_assign",
        description="List of visits to be assigned to the consecutive_visit_group",
    )
    overwrite_visit_from_template: str | None = Field(
        None,
        title="overwrite_visit_from_template",
        description="The uid of the visit from which get properties to overwrite",
    )
