from typing import Callable, Self

from pydantic import Field, validator

from clinical_mdr_api.domains.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClassAR,
)
from clinical_mdr_api.domains.biomedical_concepts.activity_item_class import (
    ActivityItemClassAR,
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

    uid: str = Field(
        ...,
        title="parent_class",
        description="",
        source="has_activity_instance_class.uid",
    )
    name: str = Field(
        ...,
        title="parent_class",
        description="",
        source="has_activity_instance_class.has_latest_value.name",
    )


class SimpleDataTypeTerm(BaseModel):
    class Config:
        orm_mode = True

    uid: str = Field(
        ...,
        title="parent_class",
        description="",
        source="has_latest_value.has_data_type.uid",
    )
    name: str | None = Field(
        None,
        title="parent_class",
        description="",
        source="has_latest_value.has_data_type.has_name_root.has_latest_value.name",
    )


class SimpleRoleTerm(BaseModel):
    class Config:
        orm_mode = True

    uid: str = Field(
        ...,
        title="parent_class",
        description="",
        source="has_latest_value.has_role.uid",
    )
    name: str | None = Field(
        None,
        title="parent_class",
        description="",
        source="has_latest_value.has_role.has_name_root.has_latest_value.name",
    )


class SimpleVariableClass(BaseModel):
    class Config:
        orm_mode = True

    uid: str = Field(
        ...,
        title="mapped_variable_class",
        description="",
        source="maps_variable_class.uid",
    )


class ActivityItemClass(VersionProperties):
    class Config:
        orm_mode = True

    uid: str = Field(
        None,
        title="uid",
        description="",
        source="uid",
    )
    name: str = Field(
        None, title="name", description="", source="has_latest_value.name"
    )
    definition: str | None = Field(
        None, title="definition", description="", source="has_latest_value.definition"
    )
    order: int = Field(
        ..., title="order", description="", source="has_latest_value.order"
    )
    mandatory: bool = Field(
        ...,
        title="is_domain_specific",
        description="",
        source="has_latest_value.mandatory",
    )
    data_type: SimpleDataTypeTerm = Field(...)
    role: SimpleRoleTerm = Field(...)
    activity_instance_classes: list[CompactActivityInstanceClass] = Field(...)
    variable_classes: list[SimpleVariableClass] | None = Field(None)
    library_name: str = Field(
        ...,
        title="library_name",
        description="",
        source="has_library.name",
    )
    nci_concept_id: str | None = Field(
        None,
        title="nci_concept_id",
        description="",
        source="has_latest_value.nci_concept_id",
    )
    possible_actions: list[str] = Field(
        ...,
        description=(
            "Holds those actions that can be performed on the ActivityItemClasses. "
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
    def from_activity_item_class_ar(
        cls,
        activity_item_class_ar: ActivityItemClassAR,
        find_activity_instance_class_by_uid: Callable[
            [str], ActivityInstanceClassAR | None
        ],
    ) -> Self:
        activity_instance_classes = [
            find_activity_instance_class_by_uid(activity_instance_class_uid)
            for activity_instance_class_uid in activity_item_class_ar.activity_item_class_vo.activity_instance_class_uids
        ]
        return cls(
            uid=activity_item_class_ar.uid,
            name=activity_item_class_ar.name,
            definition=activity_item_class_ar.definition,
            nci_concept_id=activity_item_class_ar.nci_concept_id,
            order=activity_item_class_ar.activity_item_class_vo.order,
            mandatory=activity_item_class_ar.activity_item_class_vo.mandatory,
            activity_instance_classes=[
                CompactActivityInstanceClass(
                    uid=activity_instance_class.uid, name=activity_instance_class.name
                )
                for activity_instance_class in activity_instance_classes
            ],
            data_type=SimpleDataTypeTerm(
                uid=activity_item_class_ar.activity_item_class_vo.data_type_uid,
                name=activity_item_class_ar.activity_item_class_vo.data_type_name,
            ),
            role=SimpleRoleTerm(
                uid=activity_item_class_ar.activity_item_class_vo.role_uid,
                name=activity_item_class_ar.activity_item_class_vo.role_name,
            ),
            variable_classes=[
                SimpleVariableClass(uid=variable_class_uid)
                for variable_class_uid in activity_item_class_ar.activity_item_class_vo.variable_class_uids
            ]
            if activity_item_class_ar.activity_item_class_vo.variable_class_uids
            else [],
            library_name=Library.from_library_vo(activity_item_class_ar.library).name,
            start_date=activity_item_class_ar.item_metadata.start_date,
            end_date=activity_item_class_ar.item_metadata.end_date,
            status=activity_item_class_ar.item_metadata.status.value,
            version=activity_item_class_ar.item_metadata.version,
            change_description=activity_item_class_ar.item_metadata.change_description,
            user_initials=activity_item_class_ar.item_metadata.user_initials,
            possible_actions=sorted(
                [_.value for _ in activity_item_class_ar.get_possible_actions()]
            ),
        )


class ActivityItemClassCreateInput(BaseModel):
    name: str
    definition: str | None
    nci_concept_id: str | None
    order: int
    mandatory: bool
    activity_instance_class_uids: list[str]
    role_uid: str
    data_type_uid: str
    library_name: str


class ActivityItemClassEditInput(ActivityItemClassCreateInput):
    name: str | None = None
    definition: str | None = None
    nci_concept_id: str | None = None
    order: int | None = None
    mandatory: bool | None = None
    activity_instance_class_uids: list[str] = []
    library_name: str | None = None
    change_description: str | None = None
    role_uid: str | None = None
    data_type_uid: str | None = None


class ActivityItemClassMappingInput(BaseModel):
    variable_class_uids: list[str] = []


class ActivityItemClassVersion(ActivityItemClass):
    """
    Class for storing ActivityItemClass and calculation of differences
    """

    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )
