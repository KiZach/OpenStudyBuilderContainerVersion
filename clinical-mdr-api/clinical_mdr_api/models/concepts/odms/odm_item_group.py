from typing import Callable, Self

from pydantic import BaseModel, Field, validator

from clinical_mdr_api.domains.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
)
from clinical_mdr_api.domains.concepts.odms.alias import OdmAliasAR
from clinical_mdr_api.domains.concepts.odms.description import OdmDescriptionAR
from clinical_mdr_api.domains.concepts.odms.item import OdmItemRefVO
from clinical_mdr_api.domains.concepts.odms.item_group import (
    OdmItemGroupAR,
    OdmItemGroupRefVO,
)
from clinical_mdr_api.domains.concepts.odms.vendor_attribute import (
    OdmVendorAttributeAR,
    OdmVendorAttributeRelationVO,
    OdmVendorElementAttributeRelationVO,
)
from clinical_mdr_api.domains.concepts.odms.vendor_element import (
    OdmVendorElementRelationVO,
)
from clinical_mdr_api.domains.concepts.utils import RelationType
from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.models.concepts.activities.activity import (
    ActivityHierarchySimpleModel,
)
from clinical_mdr_api.models.concepts.concept import (
    ConceptModel,
    ConceptPatchInput,
    ConceptPostInput,
)
from clinical_mdr_api.models.concepts.odms.odm_alias import OdmAliasSimpleModel
from clinical_mdr_api.models.concepts.odms.odm_common_models import (
    OdmRefVendor,
    OdmRefVendorAttributeModel,
    OdmRefVendorPostInput,
)
from clinical_mdr_api.models.concepts.odms.odm_description import (
    OdmDescriptionBatchPatchInput,
    OdmDescriptionPostInput,
    OdmDescriptionSimpleModel,
)
from clinical_mdr_api.models.concepts.odms.odm_item import OdmItemRefModel
from clinical_mdr_api.models.concepts.odms.odm_vendor_attribute import (
    OdmVendorAttributeRelationModel,
    OdmVendorElementAttributeRelationModel,
)
from clinical_mdr_api.models.concepts.odms.odm_vendor_element import (
    OdmVendorElementRelationModel,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermAttributes,
)
from clinical_mdr_api.models.validators import validate_string_represents_boolean
from clinical_mdr_api.utils import booltostr


class OdmItemGroup(ConceptModel):
    oid: str | None
    repeating: str | None = Field(None, nullable=True)
    is_reference_data: str | None = Field(None, nullable=True)
    sas_dataset_name: str | None = Field(None, nullable=True)
    origin: str | None = Field(None, nullable=True)
    purpose: str | None = Field(None, nullable=True)
    comment: str | None = Field(None, nullable=True)
    descriptions: list[OdmDescriptionSimpleModel]
    aliases: list[OdmAliasSimpleModel]
    sdtm_domains: list[SimpleCTTermAttributes]
    activity_subgroups: list[ActivityHierarchySimpleModel]
    items: list[OdmItemRefModel]
    vendor_elements: list[OdmVendorElementRelationModel]
    vendor_attributes: list[OdmVendorAttributeRelationModel]
    vendor_element_attributes: list[OdmVendorElementAttributeRelationModel]
    possible_actions: list[str]

    _validate_string_represents_boolean = validator(
        "repeating", "is_reference_data", pre=True, allow_reuse=True
    )(validate_string_represents_boolean)

    @classmethod
    def from_odm_item_group_ar(
        cls,
        odm_item_group_ar: OdmItemGroupAR,
        find_odm_description_by_uid: Callable[[str], OdmDescriptionAR | None],
        find_odm_alias_by_uid: Callable[[str], OdmAliasAR | None],
        find_term_by_uid: Callable[[str], CTTermAttributesAR | None],
        find_activity_subgroup_by_uid: Callable[[str], ActivitySubGroupAR | None],
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmVendorAttributeAR | None],
        find_odm_item_by_uid_with_item_group_relation: Callable[
            [str, str], OdmItemRefVO | None
        ],
        find_odm_vendor_element_by_uid_with_odm_element_relation: Callable[
            [str, str, RelationType], OdmVendorElementRelationVO | None
        ],
        find_odm_vendor_attribute_by_uid_with_odm_element_relation: Callable[
            [str, str, RelationType, bool],
            OdmVendorAttributeRelationVO | OdmVendorElementAttributeRelationVO | None,
        ],
    ) -> Self:
        return cls(
            uid=odm_item_group_ar._uid,
            oid=odm_item_group_ar.concept_vo.oid,
            name=odm_item_group_ar.concept_vo.name,
            repeating=booltostr(odm_item_group_ar.concept_vo.repeating),
            is_reference_data=booltostr(odm_item_group_ar.concept_vo.is_reference_data),
            sas_dataset_name=odm_item_group_ar.concept_vo.sas_dataset_name,
            origin=odm_item_group_ar.concept_vo.origin,
            purpose=odm_item_group_ar.concept_vo.purpose,
            comment=odm_item_group_ar.concept_vo.comment,
            library_name=odm_item_group_ar.library.name,
            start_date=odm_item_group_ar.item_metadata.start_date,
            end_date=odm_item_group_ar.item_metadata.end_date,
            status=odm_item_group_ar.item_metadata.status.value,
            version=odm_item_group_ar.item_metadata.version,
            change_description=odm_item_group_ar.item_metadata.change_description,
            user_initials=odm_item_group_ar.item_metadata.user_initials,
            descriptions=sorted(
                [
                    OdmDescriptionSimpleModel.from_odm_description_uid(
                        uid=description_uid,
                        find_odm_description_by_uid=find_odm_description_by_uid,
                    )
                    for description_uid in odm_item_group_ar.concept_vo.description_uids
                ],
                key=lambda item: item.name,
            ),
            aliases=sorted(
                [
                    OdmAliasSimpleModel.from_odm_alias_uid(
                        uid=alias_uid,
                        find_odm_alias_by_uid=find_odm_alias_by_uid,
                    )
                    for alias_uid in odm_item_group_ar.concept_vo.alias_uids
                ],
                key=lambda item: item.name,
            ),
            sdtm_domains=sorted(
                [
                    SimpleCTTermAttributes.from_term_uid(
                        uid=sdtm_domain_uid,
                        find_term_by_uid=find_term_by_uid,
                    )
                    for sdtm_domain_uid in odm_item_group_ar.concept_vo.sdtm_domain_uids
                ],
                key=lambda item: item.code_submission_value,
            ),
            activity_subgroups=sorted(
                [
                    ActivityHierarchySimpleModel.from_activity_uid(
                        uid=activity_subgroup_uid,
                        find_activity_by_uid=find_activity_subgroup_by_uid,
                    )
                    for activity_subgroup_uid in odm_item_group_ar.concept_vo.activity_subgroup_uids
                ],
                key=lambda item: item.name,
            ),
            items=sorted(
                [
                    OdmItemRefModel.from_odm_item_uid(
                        uid=item_uid,
                        item_group_uid=odm_item_group_ar._uid,
                        find_odm_item_by_uid_with_item_group_relation=find_odm_item_by_uid_with_item_group_relation,
                        find_odm_vendor_attribute_by_uid=find_odm_vendor_attribute_by_uid,
                    )
                    for item_uid in odm_item_group_ar.concept_vo.item_uids
                ],
                key=lambda item: item.order_number,
            ),
            vendor_elements=sorted(
                [
                    OdmVendorElementRelationModel.from_uid(
                        uid=vendor_element_uid,
                        odm_element_uid=odm_item_group_ar._uid,
                        odm_element_type=RelationType.ITEM_GROUP,
                        find_by_uid_with_odm_element_relation=find_odm_vendor_element_by_uid_with_odm_element_relation,
                    )
                    for vendor_element_uid in odm_item_group_ar.concept_vo.vendor_element_uids
                ],
                key=lambda item: item.name,
            ),
            vendor_attributes=sorted(
                [
                    OdmVendorAttributeRelationModel.from_uid(
                        uid=vendor_attribute_uid,
                        odm_element_uid=odm_item_group_ar._uid,
                        odm_element_type=RelationType.ITEM_GROUP,
                        find_by_uid_with_odm_element_relation=find_odm_vendor_attribute_by_uid_with_odm_element_relation,
                        vendor_element_attribute=False,
                    )
                    for vendor_attribute_uid in odm_item_group_ar.concept_vo.vendor_attribute_uids
                ],
                key=lambda item: item.name,
            ),
            vendor_element_attributes=sorted(
                [
                    OdmVendorElementAttributeRelationModel.from_uid(
                        uid=vendor_element_attribute_uid,
                        odm_element_uid=odm_item_group_ar._uid,
                        odm_element_type=RelationType.ITEM_GROUP,
                        find_by_uid_with_odm_element_relation=find_odm_vendor_attribute_by_uid_with_odm_element_relation,
                    )
                    for vendor_element_attribute_uid in odm_item_group_ar.concept_vo.vendor_element_attribute_uids
                ],
                key=lambda item: item.name,
            ),
            possible_actions=sorted(
                [_.value for _ in odm_item_group_ar.get_possible_actions()]
            ),
        )


class OdmItemGroupRefModel(BaseModel):
    @classmethod
    def from_odm_item_group_uid(
        cls,
        uid: str,
        form_uid: str,
        find_odm_item_group_by_uid_with_form_relation: Callable[
            [str, str], OdmItemGroupRefVO | None
        ],
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmVendorAttributeAR | None],
    ) -> Self | None:
        if uid is not None:
            odm_item_group_ref_vo = find_odm_item_group_by_uid_with_form_relation(
                uid, form_uid
            )
            if odm_item_group_ref_vo is not None:
                odm_item_group_ref_model = cls(
                    uid=uid,
                    oid=odm_item_group_ref_vo.oid,
                    name=odm_item_group_ref_vo.name,
                    order_number=odm_item_group_ref_vo.order_number,
                    mandatory=odm_item_group_ref_vo.mandatory,
                    collection_exception_condition_oid=odm_item_group_ref_vo.collection_exception_condition_oid,
                    vendor=OdmRefVendor(
                        attributes=[
                            OdmRefVendorAttributeModel.from_uid(
                                uid=attribute["uid"],
                                value=attribute["value"],
                                find_odm_vendor_attribute_by_uid=find_odm_vendor_attribute_by_uid,
                            )
                            for attribute in odm_item_group_ref_vo.vendor["attributes"]
                        ]
                        if odm_item_group_ref_vo.vendor
                        else [],
                    ),
                )
            else:
                odm_item_group_ref_model = cls(
                    uid=uid,
                    oid=None,
                    name=None,
                    order_number=None,
                    mandatory=None,
                    collection_exception_condition_oid=None,
                    vendor=OdmRefVendor(attributes=[]),
                )
        else:
            odm_item_group_ref_model = None
        return odm_item_group_ref_model

    uid: str = Field(..., title="uid", description="")
    oid: str | None = Field(None, title="oid", description="")
    name: str | None = Field(None, title="name", description="")
    order_number: int | None = Field(None, title="order_number", description="")
    mandatory: str | None = Field(None, title="mandatory", description="")
    collection_exception_condition_oid: str | None = Field(
        None, title="collection_exception_condition_oid", description=""
    )
    vendor: OdmRefVendor = Field(title="vendor", description="")


class OdmItemGroupPostInput(ConceptPostInput):
    oid: str | None
    repeating: str
    is_reference_data: str | None
    sas_dataset_name: str | None
    origin: str | None
    purpose: str | None
    comment: str | None = None
    descriptions: list[OdmDescriptionPostInput | str]
    alias_uids: list[str]
    sdtm_domain_uids: list[str]

    _validate_string_represents_boolean = validator(
        "repeating", "is_reference_data", pre=True, allow_reuse=True
    )(validate_string_represents_boolean)


class OdmItemGroupPatchInput(ConceptPatchInput):
    oid: str | None
    repeating: str | None
    is_reference_data: str | None
    sas_dataset_name: str | None
    origin: str | None
    purpose: str | None
    comment: str | None
    descriptions: list[OdmDescriptionBatchPatchInput | OdmDescriptionPostInput | str]
    alias_uids: list[str]
    sdtm_domain_uids: list[str]

    _validate_string_represents_boolean = validator(
        "repeating", "is_reference_data", pre=True, allow_reuse=True
    )(validate_string_represents_boolean)


class OdmItemGroupActivitySubGroupPostInput(BaseModel):
    uid: str


class OdmItemGroupItemPostInput(BaseModel):
    uid: str
    order_number: int
    mandatory: str
    key_sequence: str
    method_oid: str | None
    imputation_method_oid: str
    role: str
    role_codelist_oid: str
    collection_exception_condition_oid: str | None
    vendor: OdmRefVendorPostInput


class OdmItemGroupVersion(OdmItemGroup):
    """
    Class for storing OdmItemGroup and calculation of differences
    """

    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )
