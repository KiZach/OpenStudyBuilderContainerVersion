import datetime
from typing import Callable, Self

from pydantic import Field, validator

from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.domains.concepts.activities.activity import ActivityAR
from clinical_mdr_api.domains.concepts.activities.activity_group import ActivityGroupAR
from clinical_mdr_api.domains.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
)
from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    ObjectAction,
)
from clinical_mdr_api.models.concepts.concept import Concept, ConceptInput
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel


class ActivityHierarchySimpleModel(BaseModel):
    @classmethod
    def from_activity_uid(
        cls, uid: str, find_activity_by_uid: Callable[[str], ConceptARBase | None]
    ) -> Self | None:
        if uid is not None:
            activity = find_activity_by_uid(uid)

            if activity is not None:
                simple_activity_model = cls(uid=uid, name=activity.concept_vo.name)
            else:
                simple_activity_model = cls(uid=uid, name=None)
        else:
            simple_activity_model = None
        return simple_activity_model

    uid: str = Field(
        ...,
        title="uid",
        description="",
    )
    name: str | None = Field(None, title="name", description="")


class ActivityGroupingHierarchySimpleModel(BaseModel):
    class Config:
        orm_mode = True

    activity_group_uid: str = Field(
        ...,
        title="uid",
        description="",
        source="has_latest_value.has_grouping.in_subgroup.in_group.has_version.uid",
    )
    activity_group_name: str = Field(
        ...,
        title="name",
        description="",
        source="has_latest_value.has_grouping.in_subgroup.in_group.name",
    )
    activity_subgroup_uid: str = Field(
        ...,
        title="uid",
        description="",
        source="has_latest_value.has_grouping.in_subgroup.has_group.has_version.uid",
    )
    activity_subgroup_name: str = Field(
        ...,
        title="uid",
        description="",
        source="has_latest_value.has_grouping.in_subgroup.has_group.name",
    )


class ActivityBase(Concept):
    possible_actions: list[str] = Field(
        ...,
        description=(
            "Holds those actions that can be performed on the ActivityInstances. "
            "Actions are: 'approve', 'edit', 'new_version'."
        ),
    )

    @validator("possible_actions", pre=True, always=True)
    # pylint: disable=no-self-argument,unused-argument
    def validate_possible_actions(cls, value, values):
        if values["status"] == LibraryItemStatus.DRAFT.value and values[
            "version"
        ].startswith("0"):
            return [
                ObjectAction.APPROVE.value,
                ObjectAction.DELETE.value,
                ObjectAction.EDIT.value,
            ]
        if values["status"] == LibraryItemStatus.DRAFT.value:
            return [ObjectAction.APPROVE.value, ObjectAction.EDIT.value]
        if values["status"] == LibraryItemStatus.FINAL.value:
            return [
                ObjectAction.INACTIVATE.value,
                ObjectAction.NEWVERSION.value,
            ]
        if values["status"] == LibraryItemStatus.RETIRED.value:
            return [ObjectAction.REACTIVATE.value]
        return []


class Activity(ActivityBase):
    nci_concept_id: str | None = None

    @classmethod
    def from_activity_ar(
        cls,
        activity_ar: ActivityAR,
        find_activity_subgroup_by_uid: Callable[[str], ActivitySubGroupAR | None],
        find_activity_group_by_uid: Callable[[str], ActivityGroupAR | None],
    ) -> Self:
        activity_groupings = []
        for activity_grouping in activity_ar.concept_vo.activity_groupings:
            activity_group = ActivityHierarchySimpleModel.from_activity_uid(
                uid=activity_grouping.activity_group_uid,
                find_activity_by_uid=find_activity_group_by_uid,
            )
            activity_subgroup = ActivityHierarchySimpleModel.from_activity_uid(
                uid=activity_grouping.activity_subgroup_uid,
                find_activity_by_uid=find_activity_subgroup_by_uid,
            )
            activity_groupings.append(
                ActivityGroupingHierarchySimpleModel(
                    activity_group_uid=activity_group.uid,
                    activity_group_name=activity_group.name,
                    activity_subgroup_uid=activity_subgroup.uid,
                    activity_subgroup_name=activity_subgroup.name,
                )
            )
        return cls(
            uid=activity_ar.uid,
            nci_concept_id=activity_ar.concept_vo.nci_concept_id,
            name=activity_ar.name,
            name_sentence_case=activity_ar.concept_vo.name_sentence_case,
            definition=activity_ar.concept_vo.definition,
            abbreviation=activity_ar.concept_vo.abbreviation,
            activity_groupings=sorted(
                activity_groupings,
                key=lambda item: (
                    item.activity_subgroup_name,
                    item.activity_group_name,
                ),
            ),
            library_name=Library.from_library_vo(activity_ar.library).name,
            start_date=activity_ar.item_metadata.start_date,
            end_date=activity_ar.item_metadata.end_date,
            status=activity_ar.item_metadata.status.value,
            version=activity_ar.item_metadata.version,
            change_description=activity_ar.item_metadata.change_description,
            user_initials=activity_ar.item_metadata.user_initials,
            possible_actions=sorted(
                [_.value for _ in activity_ar.get_possible_actions()]
            ),
            request_rationale=activity_ar.concept_vo.request_rationale,
            is_request_final=activity_ar.concept_vo.is_request_final,
            is_request_rejected=activity_ar.concept_vo.is_request_rejected,
            reason_for_rejecting=activity_ar.concept_vo.reason_for_rejecting,
            contact_person=activity_ar.concept_vo.contact_person,
            requester_study_id=activity_ar.concept_vo.requester_study_id,
            replaced_by_activity=activity_ar.concept_vo.replaced_by_activity,
            is_data_collected=activity_ar.concept_vo.is_data_collected
            if activity_ar.concept_vo.is_data_collected
            else False,
            is_multiple_selection_allowed=activity_ar.concept_vo.is_multiple_selection_allowed
            if activity_ar.concept_vo.is_multiple_selection_allowed is not None
            else True,
            is_finalized=activity_ar.concept_vo.is_finalized,
            is_used_by_legacy_instances=activity_ar.concept_vo.is_used_by_legacy_instances,
        )

    activity_groupings: list[ActivityGroupingHierarchySimpleModel] = Field(
        [],
        title="Activity Groupings",
        description="Activity Groupings",
    )
    request_rationale: str | None = Field(
        None,
        title="The rationale of the activity request",
        description="The rationale of the activity request",
        nullable=True,
        remove_from_wildcard=True,
    )
    is_request_final: bool = Field(
        False,
        title="The flag indicating if activity request is finalized",
        description="The flag indicating if activity request is finalized",
        nullable=False,
        remove_from_wildcard=True,
    )
    is_request_rejected: bool = Field(
        False,
        title="The flag indicating if activity request is rejected",
        nullable=False,
        remove_from_wildcard=True,
    )
    contact_person: str | None = Field(
        None,
        title="The person to contact with about rejection",
        nullable=True,
        remove_from_wildcard=True,
    )
    reason_for_rejecting: str | None = Field(
        None,
        title="The reason why request was rejected",
        nullable=True,
        remove_from_wildcard=True,
    )
    requester_study_id: str | None = Field(
        None,
        title="The study_id of the Study which requested an Activity request",
        description="The study_id of the Study which requested an Activity request",
        nullable=True,
        remove_from_wildcard=True,
    )
    replaced_by_activity: str | None = Field(
        None,
        title="The uid of the replacing Activity",
        description="The uid of the replacing Activity",
        nullable=True,
        remove_from_wildcard=True,
    )
    is_data_collected: bool = Field(
        False,
        title="Boolean flag indicating whether data is collected for this activity",
        description="Boolean flag indicating whether data is collected for this activity",
        nullable=False,
    )
    is_multiple_selection_allowed: bool = Field(
        True,
        title="Boolean flag indicating whether multiple selections are allowed for this activity",
        description="Boolean flag indicating whether multiple selections are allowed for this activity",
        nullable=False,
    )
    is_finalized: bool = Field(
        False,
        title="Computed boolean value based on is_request_rejected and replaced_by_activity",
        description="Evaluates to false, if is_request_rejected is false and replaced_by_activity is null else true",
        nullable=False,
    )
    is_used_by_legacy_instances: bool = Field(
        False,
        title="True if all instances linked to given Activity are legacy_used.",
        nullable=False,
    )


class ActivityForStudyActivity(Activity):
    activity_groupings: list[ActivityGroupingHierarchySimpleModel] = Field(
        [],
        title="Activity Groupings",
        description="Activity Groupings",
        remove_from_wildcard=True,
    )


class ActivityCommonInput(ConceptInput):
    name: str | None = Field(
        None,
        title="name",
        description="The name or the actual value. E.g. 'Systolic Blood Pressure', 'Body Temperature', 'Metformin', ...",
    )
    name_sentence_case: str | None = Field(
        None,
        title="name_sentence_case",
        description="",
    )


class ActivityGrouping(BaseModel):
    activity_group_uid: str
    activity_subgroup_uid: str


class ActivityInput(ActivityCommonInput):
    nci_concept_id: str | None = None
    activity_groupings: list[ActivityGrouping] | None = None
    request_rationale: str | None = None
    is_request_final: bool = False
    is_data_collected: bool = False
    is_multiple_selection_allowed: bool = True


class ActivityEditInput(ActivityInput):
    change_description: str = Field(None, title="change_description", description="")


class ActivityCreateInput(ActivityInput):
    library_name: str


class ActivityRequestRejectInput(BaseModel):
    contact_person: str
    reason_for_rejecting: str


class ActivityFromRequestInput(ActivityInput):
    activity_request_uid: str


class ActivityVersion(Activity):
    """
    Class for storing Activity and calculation of differences
    """

    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )


class SimpleActivity(BaseModel):
    nci_concept_id: str | None = Field(
        None,
        title="nci_concept_id",
        description="",
    )
    name: str | None = Field(
        None,
        title="name",
        description="",
    )
    name_sentence_case: str | None = Field(
        None,
        title="name_sentence_case",
        description="",
    )
    definition: str | None = Field(
        None,
        title="definition",
        description="",
    )
    abbreviation: str | None = Field(
        None,
        title="abbreviation",
        description="",
    )
    is_data_collected: bool = Field(
        False,
        title="Boolean flag indicating whether data is collected for this activity",
        description="Boolean flag indicating whether data is collected for this activity",
        nullable=False,
    )
    is_multiple_selection_allowed: bool = Field(
        True,
        title="Boolean flag indicating whether multiple selections are allowed for this activity",
        description="Boolean flag indicating whether multiple selections are allowed for this activity",
        nullable=False,
    )
    library_name: str | None = Field(
        None,
        title="library_name",
        description="",
    )
    version: str | None = Field(None, title="version")
    status: str | None = Field(None, title="status")
    start_date: datetime.datetime | None = Field(None, title="start date")
    end_date: datetime.datetime | None = Field(None, title="end date")


class SimpleActivitySubGroup(BaseModel):
    name: str | None = Field(None, title="name", description="")
    definition: str | None = Field(None, title="name", description="")


class SimpleActivityGroup(BaseModel):
    name: str | None = Field(None, title="name", description="")
    definition: str | None = Field(None, title="name", description="")


class SimpleActivityGrouping(BaseModel):
    activity_group: SimpleActivityGroup
    activity_subgroup: SimpleActivitySubGroup


class SimpleActivityInstanceClass(BaseModel):
    name: str = Field(..., title="name", description="")


class SimpleActivityInstance(BaseModel):
    uid: str
    nci_concept_id: str | None = Field(None, title="name", description="")
    name: str = Field(..., title="name", description="")
    name_sentence_case: str | None = Field(None, title="name", description="")
    abbreviation: str | None = Field(None, title="name", description="")
    definition: str | None = Field(None, title="name", description="")
    adam_param_code: str | None = Field(None, title="name", description="")
    is_required_for_activity: bool = Field(
        False, title="is_required_for_activity", description=""
    )
    is_default_selected_for_activity: bool = Field(
        False, title="is_default_selected_for_activity", description=""
    )
    is_data_sharing: bool = Field(False, title="is_data_sharing", description="")
    is_legacy_usage: bool = Field(False, title="is_legacy_usage", description="")
    is_derived: bool = Field(False, title="is_derived", description="")
    topic_code: str | None = Field(None, title="name", description="")
    library_name: str = Field(..., title="name", description="")
    activity_instance_class: SimpleActivityInstanceClass = Field(...)
    version: str | None = Field(None, title="version")
    status: str | None = Field(None, title="status")
    start_date: datetime.datetime | None = Field(None, title="start date")
    end_date: datetime.datetime | None = Field(None, title="end date")


class ActivityOverview(BaseModel):
    activity: SimpleActivity = Field(...)
    activity_groupings: list[SimpleActivityGrouping] = Field(...)
    activity_instances: list[SimpleActivityInstance] = Field(...)
    all_versions: list[str] = Field(...)

    @classmethod
    def from_repository_input(cls, overview: dict):
        return cls(
            activity=SimpleActivity(
                nci_concept_id=overview.get("activity_value").get("nci_concept_id"),
                name=overview.get("activity_value").get("name"),
                name_sentence_case=overview.get("activity_value").get(
                    "name_sentence_case"
                ),
                definition=overview.get("activity_value").get("definition"),
                abbreviation=overview.get("activity_value").get("abbreviation"),
                is_data_collected=overview.get("activity_value").get(
                    "is_data_collected", False
                ),
                is_multiple_selection_allowed=overview.get("activity_value").get(
                    "is_multiple_selection_allowed", True
                ),
                library_name=overview.get("activity_library_name"),
                version=overview.get("has_version", {}).get("version"),
                status=overview.get("has_version", {}).get("status"),
                start_date=convert_to_datetime(
                    overview.get("has_version", {}).get("start_date")
                ),
                end_date=convert_to_datetime(
                    overview.get("has_version", {}).get("end_date")
                ),
            ),
            activity_groupings=[
                SimpleActivityGrouping(
                    activity_group=SimpleActivityGroup(
                        name=activity_grouping.get("activity_group_value").get("name"),
                        definition=activity_grouping.get("activity_group_value").get(
                            "definition"
                        ),
                    ),
                    activity_subgroup=SimpleActivitySubGroup(
                        name=activity_grouping.get("activity_subgroup_value").get(
                            "name"
                        ),
                        definition=activity_grouping.get("activity_subgroup_value").get(
                            "definition"
                        ),
                    ),
                )
                for activity_grouping in overview.get("hierarchy")
            ],
            activity_instances=[
                SimpleActivityInstance(
                    uid=activity_instance.get("uid"),
                    nci_concept_id=activity_instance.get("nci_concept_id"),
                    name=activity_instance.get("name"),
                    name_sentence_case=activity_instance.get("name_sentence_case"),
                    abbreviation=activity_instance.get("abbreviation"),
                    definition=activity_instance.get("definition"),
                    adam_param_code=activity_instance.get("adam_param_code"),
                    is_required_for_activity=activity_instance.get(
                        "is_required_for_activity", False
                    ),
                    is_default_selected_for_activity=activity_instance.get(
                        "is_default_selected_for_activity", False
                    ),
                    is_data_sharing=activity_instance.get("is_data_sharing", False),
                    is_legacy_usage=activity_instance.get("is_legacy_usage", False),
                    is_derived=activity_instance.get("is_derived", False),
                    topic_code=activity_instance.get("topic_code"),
                    library_name=activity_instance.get(
                        "activity_instance_library_name"
                    ),
                    activity_instance_class=SimpleActivityInstanceClass(
                        name=activity_instance.get("activity_instance_class").get(
                            "name"
                        )
                    ),
                    version=activity_instance.get("version", {}).get("version"),
                    status=activity_instance.get("version", {}).get("status"),
                )
                for activity_instance in overview.get("activity_instances")
            ],
            all_versions=overview.get("all_versions"),
        )
