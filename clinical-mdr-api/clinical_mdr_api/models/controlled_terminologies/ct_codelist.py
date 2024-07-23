from typing import Any, Self

from pydantic import Field

from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_name import (
    CTCodelistNameAR,
)
from clinical_mdr_api.models import Library
from clinical_mdr_api.models.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributes,
)
from clinical_mdr_api.models.controlled_terminologies.ct_codelist_name import (
    CTCodelistName,
)
from clinical_mdr_api.models.utils import BaseModel


class CTCodelist(BaseModel):
    @classmethod
    def from_ct_codelist_ar(
        cls,
        ct_codelist_name_ar: CTCodelistNameAR,
        ct_codelist_attributes_ar: CTCodelistAttributesAR,
    ) -> Self:
        return cls(
            catalogue_name=ct_codelist_attributes_ar.ct_codelist_vo.catalogue_name,
            codelist_uid=ct_codelist_attributes_ar.uid,
            parent_codelist_uid=ct_codelist_attributes_ar._ct_codelist_attributes_vo.parent_codelist_uid,
            child_codelist_uids=ct_codelist_attributes_ar._ct_codelist_attributes_vo.child_codelist_uids
            if ct_codelist_attributes_ar._ct_codelist_attributes_vo.child_codelist_uids
            else [],
            name=ct_codelist_attributes_ar.name,
            submission_value=ct_codelist_attributes_ar.ct_codelist_vo.submission_value,
            nci_preferred_name=ct_codelist_attributes_ar.ct_codelist_vo.preferred_term,
            definition=ct_codelist_attributes_ar.ct_codelist_vo.definition,
            extensible=ct_codelist_attributes_ar.ct_codelist_vo.extensible,
            library_name=Library.from_library_vo(
                ct_codelist_attributes_ar.library
            ).name,
            sponsor_preferred_name=ct_codelist_name_ar.name,
            template_parameter=ct_codelist_name_ar.ct_codelist_vo.is_template_parameter,
            possible_actions=sorted(
                [_.value for _ in ct_codelist_attributes_ar.get_possible_actions()]
            ),
        )

    catalogue_name: str = Field(
        ...,
        title="catalogue_name",
        description="",
    )

    codelist_uid: str = Field(
        ...,
        title="codelist_uid",
        description="",
    )

    parent_codelist_uid: str | None = Field(
        None, title="parent_codelist_uid", description="", nullable=True
    )

    child_codelist_uids: list[str] = Field(
        [],
        title="child_codelist_uids",
        description="",
    )

    name: str = Field(
        ...,
        title="name",
        description="",
    )

    submission_value: str = Field(
        ...,
        title="submission_value",
        description="",
    )

    nci_preferred_name: str = Field(
        ...,
        title="nci_preferred_name",
        description="",
    )

    definition: str = Field(
        ...,
        title="definition",
        description="",
    )

    extensible: bool = Field(
        ...,
        title="extensible",
        description="",
    )

    sponsor_preferred_name: str = Field(
        ...,
        title="sponsor_preferred_name",
        description="",
    )

    template_parameter: bool = Field(
        ...,
        title="template_parameter",
        description="",
    )

    library_name: str
    possible_actions: list[str] = Field(
        [],
        description=(
            "Holds those actions that can be performed on the CTCodelistAttributes. "
            "Actions are: 'approve', 'edit', 'new_version'."
        ),
    )


class CTCodelistTermInput(BaseModel):
    term_uid: str = Field(
        ...,
        title="term_uid",
        description="",
    )
    order: int | None = Field(
        999999,
        title="order",
        description="",
    )


class CTCodelistCreateInput(BaseModel):
    catalogue_name: str = Field(
        ...,
        title="catalogue_name",
        description="",
    )

    name: str = Field(
        ...,
        title="name",
        description="",
    )

    submission_value: str = Field(
        ...,
        title="submission_value",
        description="",
    )

    nci_preferred_name: str = Field(
        ...,
        title="nci_preferred_name",
        description="",
    )

    definition: str = Field(
        ...,
        title="definition",
        description="",
    )

    extensible: bool = Field(
        ...,
        title="extensible",
        description="",
    )

    sponsor_preferred_name: str = Field(
        ...,
        title="sponsor_preferred_name",
        description="",
    )

    template_parameter: bool = Field(
        ...,
        title="template_parameter",
        description="",
    )

    parent_codelist_uid: str | None = Field(
        None,
        title="parent_codelist_uid",
        description="",
    )

    terms: list[CTCodelistTermInput]

    library_name: str


class CTCodelistNameAndAttributes(BaseModel):
    @classmethod
    def from_ct_codelist_ar(
        cls,
        ct_codelist_name_ar: CTCodelistNameAR,
        ct_codelist_attributes_ar: CTCodelistAttributesAR,
    ) -> Self:
        codelist_name_and_attributes = cls(
            catalogue_name=ct_codelist_attributes_ar.ct_codelist_vo.catalogue_name,
            codelist_uid=ct_codelist_attributes_ar.uid,
            parent_codelist_uid=ct_codelist_attributes_ar._ct_codelist_attributes_vo.parent_codelist_uid,
            child_codelist_uids=ct_codelist_attributes_ar._ct_codelist_attributes_vo.child_codelist_uids,
            library_name=Library.from_library_vo(
                ct_codelist_attributes_ar.library
            ).name,
            name=CTCodelistName.from_ct_codelist_ar_without_common_codelist_fields(
                ct_codelist_name_ar
            ),
            attributes=CTCodelistAttributes.from_ct_codelist_ar_without_common_codelist_fields(
                ct_codelist_attributes_ar
            ),
        )

        return codelist_name_and_attributes

    catalogue_name: str = Field(
        ...,
        title="catalogue_name",
        description="",
    )

    codelist_uid: str = Field(
        ...,
        title="codelist_uid",
        description="",
    )

    parent_codelist_uid: str = Field(
        None, title="parent_codelist_uid", description="", nullable=True
    )

    child_codelist_uids: list[Any] = Field(
        [],
        title="child_codelist_uids",
        description="",
    )

    library_name: str | None = Field(None, nullable=True)

    name: CTCodelistName = Field(
        ...,
        title="CTCodelistName",
        description="",
    )

    attributes: CTCodelistAttributes = Field(
        ...,
        title="CTCodelistAttributes",
        description="",
    )
