from typing import Callable, Self

from pydantic import Field

from clinical_mdr_api.domains.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.models.concepts.activities.activity import (
    ActivityBase,
    ActivityCommonInput,
    ActivityHierarchySimpleModel,
)
from clinical_mdr_api.models.libraries.library import Library


class ActivitySubGroup(ActivityBase):
    @classmethod
    def from_activity_ar(
        cls,
        activity_subgroup_ar: ActivitySubGroupAR,
        find_activity_by_uid: Callable[[str], CTTermNameAR | None],
    ) -> Self:
        return cls(
            uid=activity_subgroup_ar.uid,
            name=activity_subgroup_ar.name,
            name_sentence_case=activity_subgroup_ar.concept_vo.name_sentence_case,
            definition=activity_subgroup_ar.concept_vo.definition,
            abbreviation=activity_subgroup_ar.concept_vo.abbreviation,
            activity_groups=[
                ActivityHierarchySimpleModel.from_activity_uid(
                    uid=activity_group_uid,
                    find_activity_by_uid=find_activity_by_uid,
                )
                for activity_group_uid in activity_subgroup_ar.concept_vo.activity_groups
            ],
            library_name=Library.from_library_vo(activity_subgroup_ar.library).name,
            start_date=activity_subgroup_ar.item_metadata.start_date,
            end_date=activity_subgroup_ar.item_metadata.end_date,
            status=activity_subgroup_ar.item_metadata.status.value,
            version=activity_subgroup_ar.item_metadata.version,
            change_description=activity_subgroup_ar.item_metadata.change_description,
            user_initials=activity_subgroup_ar.item_metadata.user_initials,
            possible_actions=sorted(
                [_.value for _ in activity_subgroup_ar.get_possible_actions()]
            ),
        )

    activity_groups: list[ActivityHierarchySimpleModel]


class ActivitySubGroupInput(ActivityCommonInput):
    activity_groups: list[str] | None = None


class ActivitySubGroupEditInput(ActivitySubGroupInput):
    change_description: str = Field(None, title="change_description", description="")


class ActivitySubGroupCreateInput(ActivitySubGroupInput):
    library_name: str


class ActivitySubGroupVersion(ActivitySubGroup):
    """
    Class for storing ActivitySubGroup and calculation of differences
    """

    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )
