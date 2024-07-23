from datetime import datetime
from typing import Callable, Self

from pydantic import Field

from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.domains.concepts.activities.activity import ActivityAR
from clinical_mdr_api.domains.concepts.activities.activity_group import ActivityGroupAR
from clinical_mdr_api.domains.concepts.activities.activity_instance import (
    ActivityInstanceAR,
)
from clinical_mdr_api.domains.concepts.activities.activity_item import LibraryItem
from clinical_mdr_api.domains.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
)
from clinical_mdr_api.models import Library
from clinical_mdr_api.models.biomedical_concepts.activity_instance_class import (
    CompactActivityInstanceClass,
)
from clinical_mdr_api.models.concepts.activities.activity import (
    ActivityBase,
    ActivityGrouping,
    ActivityHierarchySimpleModel,
    SimpleActivityGroup,
    SimpleActivityGrouping,
    SimpleActivityInstance,
    SimpleActivityInstanceClass,
    SimpleActivitySubGroup,
)
from clinical_mdr_api.models.concepts.activities.activity_item import (
    ActivityItem,
    ActivityItemCreateInput,
    CompactActivityItemClass,
    CompactCTTerm,
    CompactUnitDefinition,
)
from clinical_mdr_api.models.concepts.concept import ConceptInput
from clinical_mdr_api.models.utils import BaseModel


class ActivityInstanceHierarchySimpleModel(BaseModel):
    activity: ActivityHierarchySimpleModel
    activity_subgroup: ActivityHierarchySimpleModel
    activity_group: ActivityHierarchySimpleModel


class ActivityInstanceGrouping(ActivityGrouping):
    activity_uid: str


class ActivityInstance(ActivityBase):
    nci_concept_id: str | None = None

    @classmethod
    def from_activity_ar(
        cls,
        activity_ar: ActivityInstanceAR,
        find_activity_hierarchy_by_uid: Callable[[str], ActivityAR | None],
        find_activity_subgroup_by_uid: Callable[[str], ActivitySubGroupAR | None],
        find_activity_group_by_uid: Callable[[str], ActivityGroupAR | None],
    ) -> Self:
        activity_items = []
        for activity_item in activity_ar.concept_vo.activity_items:
            ct_terms = []
            unit_definitions = []
            for unit in activity_item.unit_definitions:
                unit_definitions.append(
                    CompactUnitDefinition(uid=unit.uid, name=unit.name)
                )
            for term in activity_item.ct_terms:
                ct_terms.append(CompactCTTerm(uid=term.uid, name=term.name))
            activity_items.append(
                ActivityItem(
                    activity_item_class=CompactActivityItemClass(
                        uid=activity_item.activity_item_class_uid,
                        name=activity_item.activity_item_class_name,
                    ),
                    ct_terms=ct_terms,
                    unit_definitions=unit_definitions,
                )
            )

        return cls(
            uid=activity_ar.uid,
            name=activity_ar.name,
            name_sentence_case=activity_ar.concept_vo.name_sentence_case,
            definition=activity_ar.concept_vo.definition,
            abbreviation=activity_ar.concept_vo.abbreviation,
            topic_code=activity_ar.concept_vo.topic_code,
            adam_param_code=activity_ar.concept_vo.adam_param_code,
            is_required_for_activity=activity_ar.concept_vo.is_required_for_activity,
            is_default_selected_for_activity=activity_ar.concept_vo.is_default_selected_for_activity,
            is_data_sharing=activity_ar.concept_vo.is_data_sharing,
            is_legacy_usage=activity_ar.concept_vo.is_legacy_usage,
            is_derived=activity_ar.concept_vo.is_derived,
            nci_concept_id=activity_ar.concept_vo.nci_concept_id,
            legacy_description=activity_ar.concept_vo.legacy_description,
            activity_groupings=[
                ActivityInstanceHierarchySimpleModel(
                    activity_group=ActivityHierarchySimpleModel.from_activity_uid(
                        uid=activity_grouping.activity_group_uid,
                        find_activity_by_uid=find_activity_group_by_uid,
                    ),
                    activity_subgroup=ActivityHierarchySimpleModel.from_activity_uid(
                        uid=activity_grouping.activity_subgroup_uid,
                        find_activity_by_uid=find_activity_subgroup_by_uid,
                    ),
                    activity=ActivityHierarchySimpleModel.from_activity_uid(
                        uid=activity_grouping.activity_uid,
                        find_activity_by_uid=find_activity_hierarchy_by_uid,
                    ),
                )
                for activity_grouping in activity_ar.concept_vo.activity_groupings
            ],
            activity_name=activity_ar.concept_vo.activity_name,
            activity_instance_class=CompactActivityInstanceClass(
                uid=activity_ar.concept_vo.activity_instance_class_uid,
                name=activity_ar.concept_vo.activity_instance_class_name,
            ),
            activity_items=activity_items,
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
        )

    topic_code: str | None = Field(
        None,
        title="topic_code",
        description="",
    )
    adam_param_code: str | None = Field(
        None,
        title="adam_param_code",
        description="",
    )
    is_required_for_activity: bool = Field(False)
    is_default_selected_for_activity: bool = Field(False)
    is_data_sharing: bool = Field(False)
    is_legacy_usage: bool = Field(False)
    is_derived: bool = Field(False)
    legacy_description: str | None = Field(
        None,
        title="legacy_description",
        description="",
    )
    activity_groupings: list[ActivityInstanceHierarchySimpleModel] = Field(
        ...,
        title="activity_groupings",
    )
    activity_name: str | None = Field(
        None,
        title="activity_name",
        description="",
    )
    activity_instance_class: CompactActivityInstanceClass = Field(
        ...,
        title="The class of an activity instance",
        description="The uid and the name of the linked activity instance class",
    )
    activity_items: list[ActivityItem] = Field(
        ...,
        title="activity_items",
        description="List of activity items",
    )
    start_date: datetime
    end_date: datetime | None = Field(None, nullable=True)
    status: str
    version: str
    change_description: str
    user_initials: str
    possible_actions: list[str] = Field(
        ...,
        description=(
            "Holds those actions that can be performed on the ActivityInstances. "
            "Actions are: 'approve', 'edit', 'new_version'."
        ),
    )


class ActivityInstanceCreateInput(ConceptInput):
    nci_concept_id: str | None = Field(
        None,
        title="nci_concept_id",
        description="NCI Concept ID",
    )
    name: str = Field(
        ...,
        title="name",
        description="The name or the actual value. E.g. 'Systolic Blood Pressure', 'Body Temperature', 'Metformin', ...",
    )
    name_sentence_case: str | None = Field(
        None,
        title="name_sentence_case",
        description="",
    )
    topic_code: str | None = Field(
        None,
        title="topic_code",
        description="",
    )
    adam_param_code: str | None = Field(
        None,
        title="adam_param_code",
        description="",
    )
    is_required_for_activity: bool = Field(False)
    is_default_selected_for_activity: bool = Field(False)
    is_data_sharing: bool = Field(False)
    is_legacy_usage: bool = Field(False)
    is_derived: bool = Field(False)
    legacy_description: str | None = Field(
        None,
        title="legacy_description",
        description="",
    )
    activity_groupings: list[ActivityInstanceGrouping] | None = Field(
        None,
        title="activity_groupings",
        description="",
    )
    activity_instance_class_uid: str = Field(
        ...,
        title="activity_instance_class_uid",
        description="",
    )
    activity_items: list[ActivityItemCreateInput] | None = Field(
        None,
        title="activity_items",
        description="",
    )
    library_name: str


class ActivityInstanceEditInput(ConceptInput):
    nci_concept_id: str | None = Field(
        None,
        title="nci_concept_id",
        description="NCI Concept ID",
    )
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
    topic_code: str | None = Field(
        None,
        title="topic_code",
        description="",
    )
    adam_param_code: str | None = Field(
        None,
        title="adam_param_code",
        description="",
    )
    is_required_for_activity: bool | None = Field(None)
    is_default_selected_for_activity: bool | None = Field(None)
    is_data_sharing: bool | None = Field(None)
    is_legacy_usage: bool | None = Field(None)
    is_derived: bool | None = Field(None)
    legacy_description: str | None = Field(
        None,
        title="legacy_description",
        description="",
    )
    activity_instance_class_uid: str | None = Field(
        None,
        title="activity_instance_class_uid",
        description="",
    )
    activity_groupings: list[ActivityInstanceGrouping] | None = Field(
        None,
        title="activity_groupings",
        description="",
    )
    activity_items: list[ActivityItemCreateInput] | None = Field(
        None,
        title="activity_items",
        description="",
    )
    change_description: str = Field(..., title="change_description", description="")


class ActivityInstanceVersion(ActivityInstance):
    """
    Class for storing ActivityInstance and calculation of differences
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
    uid: str = Field(
        ...,
        title="uid",
        description="",
    )
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
    definition: str | None = Field(
        None,
        title="name",
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
        title="name",
        description="",
    )
    version: str | None = Field(None, title="version")
    status: str | None = Field(None, title="status")


class SimpleActivityItemClass(BaseModel):
    name: str = Field(..., title="name", description="")
    order: int = Field(..., title="order", description="")
    mandatory: bool = Field(..., title="mandatory", description="")
    role_name: str = Field(..., title="role_name", description="")
    data_type_name: str = Field(..., title="data_type_name", description="")


class SimplifiedActivityItem(BaseModel):
    class Config:
        orm_mode = True

    ct_terms: list[LibraryItem] = Field([], title="ct_terms", description="")
    unit_definitions: list[LibraryItem] = Field(
        [], title="unit_definitions", description=""
    )
    activity_item_class: SimpleActivityItemClass = Field(...)


class SimpleActivityInstanceGrouping(SimpleActivityGrouping):
    activity: SimpleActivity = Field(...)


class ActivityInstanceOverview(BaseModel):
    activity_groupings: list[SimpleActivityInstanceGrouping] = Field(...)
    activity_instance: SimpleActivityInstance = Field(...)
    activity_items: list[SimplifiedActivityItem] = Field(...)
    all_versions: list[str] = Field(...)

    @classmethod
    def from_repository_input(cls, overview: dict):
        activity_items = []
        for activity_item in overview.get("activity_items"):
            units = [
                LibraryItem(name=unit.get("name"), uid=unit.get("uid"))
                for unit in activity_item.get("unit_definitions", {})
            ]
            terms = [
                LibraryItem(name=term.get("name"), uid=term.get("uid"))
                for term in activity_item.get("ct_terms", {})
            ]
            activity_items.append(
                SimplifiedActivityItem(
                    ct_terms=terms,
                    unit_definitions=units,
                    activity_item_class=SimpleActivityItemClass(
                        name=activity_item.get("activity_item_class").get("name"),
                        order=activity_item.get("activity_item_class").get("order"),
                        mandatory=activity_item.get("activity_item_class").get(
                            "mandatory"
                        ),
                        role_name=activity_item.get("activity_item_class_role"),
                        data_type_name=activity_item.get(
                            "activity_item_class_data_type"
                        ),
                    ),
                )
            )

        return cls(
            activity_groupings=[
                SimpleActivityInstanceGrouping(
                    activity=SimpleActivity(
                        uid=activity_grouping.get("uid"),
                        name=activity_grouping.get("activity_value").get("name"),
                        definition=activity_grouping.get("activity_value").get(
                            "definition"
                        ),
                        nci_concept_id=activity_grouping.get("activity_value").get(
                            "nci_concept_id"
                        ),
                        is_data_collected=activity_grouping.get("activity_value").get(
                            "is_data_collected", False
                        ),
                        is_multiple_selection_allowed=activity_grouping.get(
                            "activity_value"
                        ).get("is_multiple_selection_allowed", True),
                        library_name=activity_grouping.get("activity_library_name"),
                        version=activity_grouping.get("version", {}).get("version"),
                        status=activity_grouping.get("version", {}).get("status"),
                    ),
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
            activity_instance=SimpleActivityInstance(
                uid=overview.get("activity_instance_root").get("uid"),
                name=overview.get("activity_instance_value").get("name"),
                name_sentence_case=overview.get("activity_instance_value").get(
                    "name_sentence_case"
                ),
                abbreviation=overview.get("activity_instance_value").get(
                    "abbreviation"
                ),
                definition=overview.get("activity_instance_value").get("definition"),
                nci_concept_id=overview.get("activity_instance_value").get(
                    "nci_concept_id"
                ),
                adam_param_code=overview.get("activity_instance_value").get(
                    "adam_param_code"
                ),
                is_required_for_activity=overview.get("activity_instance_value").get(
                    "is_required_for_activity", False
                ),
                is_default_selected_for_activity=overview.get(
                    "activity_instance_value"
                ).get("is_default_selected_for_activity", False),
                is_data_sharing=overview.get("activity_instance_value").get(
                    "is_data_sharing", False
                ),
                is_legacy_usage=overview.get("activity_instance_value").get(
                    "is_legacy_usage", False
                ),
                is_derived=overview.get("activity_instance_value").get(
                    "is_derived", False
                ),
                topic_code=overview.get("activity_instance_value").get("topic_code"),
                library_name=overview.get("instance_library_name"),
                activity_instance_class=SimpleActivityInstanceClass(
                    name=overview.get("activity_instance_class").get("name")
                ),
                status=overview.get("has_version", {}).get("status"),
                version=overview.get("has_version", {}).get("version"),
                start_date=convert_to_datetime(
                    overview.get("has_version", {}).get("start_date")
                ),
                end_date=convert_to_datetime(
                    overview.get("has_version", {}).get("end_date")
                ),
            ),
            activity_items=activity_items,
            all_versions=overview.get("all_versions"),
        )
