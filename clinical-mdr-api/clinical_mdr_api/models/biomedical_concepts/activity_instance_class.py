from typing import Callable, Self

from pydantic import Field, validator

from clinical_mdr_api.domains.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClassAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    ObjectAction,
)
from clinical_mdr_api.models import Library
from clinical_mdr_api.models.concepts.concept import VersionProperties
from clinical_mdr_api.models.utils import BaseModel


class CompactActivityInstanceClass(BaseModel):
    class Config:
        orm_mode = True

    uid: str | None = Field(
        None,
        title="The uid of the parent class",
        description="",
        source="parent_class.uid",
    )
    name: str | None = Field(
        None,
        title="The name of the parent class",
        description="",
        source="parent_class.has_latest_value.name",
    )


class SimpleDatasetClass(BaseModel):
    class Config:
        orm_mode = True

    uid: str = Field(
        ...,
        title="mapped_dataset_class",
        description="",
        source="maps_dataset_class.uid",
    )


class ActivityInstanceClass(VersionProperties):
    class Config:
        orm_mode = True

    uid: str = Field(
        None,
        title="uid",
        description="",
        source="uid",
    )
    name: str | None = Field(
        None, title="name", description="", source="has_latest_value.name"
    )
    order: int | None = Field(
        None, title="order", description="", source="has_latest_value.order"
    )
    definition: str | None = Field(
        None, title="definition", description="", source="has_latest_value.definition"
    )
    is_domain_specific: bool | None = Field(
        None,
        title="is_domain_specific",
        description="",
        source="has_latest_value.is_domain_specific",
    )
    parent_class: CompactActivityInstanceClass | None = Field(None)
    dataset_classes: list[SimpleDatasetClass] | None = Field(None)
    library_name: str = Field(
        None,
        title="library_name",
        description="",
        source="has_library.name",
    )
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

    @classmethod
    def from_activity_instance_class_ar(
        cls,
        activity_instance_class_ar: ActivityInstanceClassAR,
        find_activity_instance_class_by_uid: Callable[
            [str], ActivityInstanceClassAR | None
        ],
    ) -> Self:
        parent_class = find_activity_instance_class_by_uid(
            activity_instance_class_ar.activity_instance_class_vo.parent_uid
        )
        return cls(
            uid=activity_instance_class_ar.uid,
            name=activity_instance_class_ar.name,
            order=activity_instance_class_ar.activity_instance_class_vo.order,
            definition=activity_instance_class_ar.activity_instance_class_vo.definition,
            is_domain_specific=activity_instance_class_ar.activity_instance_class_vo.is_domain_specific,
            parent_class=CompactActivityInstanceClass(
                uid=parent_class.uid, name=parent_class.name
            )
            if parent_class
            else None,
            dataset_classes=[
                SimpleDatasetClass(uid=dataset_class.uid)
                for dataset_class in activity_instance_class_ar.activity_instance_class_vo.dataset_class_uids
            ]
            if activity_instance_class_ar.activity_instance_class_vo.dataset_class_uids
            else [],
            library_name=Library.from_library_vo(
                activity_instance_class_ar.library
            ).name,
            start_date=activity_instance_class_ar.item_metadata.start_date,
            end_date=activity_instance_class_ar.item_metadata.end_date,
            status=activity_instance_class_ar.item_metadata.status.value,
            version=activity_instance_class_ar.item_metadata.version,
            change_description=activity_instance_class_ar.item_metadata.change_description,
            user_initials=activity_instance_class_ar.item_metadata.user_initials,
            possible_actions=sorted(
                [_.value for _ in activity_instance_class_ar.get_possible_actions()]
            ),
        )


class ActivityInstanceClassInput(BaseModel):
    name: str | None = None
    order: int | None = None
    definition: str | None = None
    is_domain_specific: bool | None = None
    parent_uid: str | None = None
    library_name: str | None = None
    change_description: str | None = None


class ActivityInstanceClassMappingInput(BaseModel):
    dataset_class_uids: list[str] = []


class ActivityInstanceClassVersion(ActivityInstanceClass):
    """
    Class for storing ActivityInstanceClass and calculation of differences
    """

    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )
