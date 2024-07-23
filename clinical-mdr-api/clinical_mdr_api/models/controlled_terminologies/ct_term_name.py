from datetime import datetime
from typing import Self

from pydantic import Field

from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.models.controlled_terminologies.ct_term_codelist import (
    CTTermCodelist,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel


class CTTermName(BaseModel):
    @classmethod
    def from_ct_term_ar(cls, ct_term_name_ar: CTTermNameAR) -> Self:
        return cls(
            term_uid=ct_term_name_ar.uid,
            catalogue_name=ct_term_name_ar.ct_term_vo.catalogue_name,
            codelists=[
                CTTermCodelist(
                    codelist_uid=x.codelist_uid,
                    order=x.order,
                )
                for x in ct_term_name_ar.ct_term_vo.codelists
            ],
            sponsor_preferred_name=ct_term_name_ar.ct_term_vo.name,
            sponsor_preferred_name_sentence_case=ct_term_name_ar.ct_term_vo.name_sentence_case,
            library_name=Library.from_library_vo(ct_term_name_ar.library).name,
            possible_actions=sorted(
                [_.value for _ in ct_term_name_ar.get_possible_actions()]
            ),
            start_date=ct_term_name_ar.item_metadata.start_date,
            end_date=ct_term_name_ar.item_metadata.end_date,
            status=ct_term_name_ar.item_metadata.status.value,
            version=ct_term_name_ar.item_metadata.version,
            change_description=ct_term_name_ar.item_metadata.change_description,
            user_initials=ct_term_name_ar.item_metadata.user_initials,
        )

    @classmethod
    def from_ct_term_ar_without_common_term_fields(
        cls, ct_term_name_ar: CTTermNameAR
    ) -> Self:
        return cls(
            sponsor_preferred_name=ct_term_name_ar.ct_term_vo.name,
            sponsor_preferred_name_sentence_case=ct_term_name_ar.ct_term_vo.name_sentence_case,
            codelists=[
                CTTermCodelist(
                    codelist_uid=x.codelist_uid,
                    order=x.order,
                )
                for x in ct_term_name_ar.ct_term_vo.codelists
            ],
            possible_actions=sorted(
                [_.value for _ in ct_term_name_ar.get_possible_actions()]
            ),
            start_date=ct_term_name_ar.item_metadata.start_date,
            end_date=ct_term_name_ar.item_metadata.end_date,
            status=ct_term_name_ar.item_metadata.status.value,
            version=ct_term_name_ar.item_metadata.version,
            change_description=ct_term_name_ar.item_metadata.change_description,
            user_initials=ct_term_name_ar.item_metadata.user_initials,
        )

    term_uid: str | None = Field(
        None,
        title="term_uid",
        description="",
        nullable=True,
    )

    catalogue_name: str | None = Field(
        None,
        title="catalogue_name",
        description="",
        nullable=True,
    )

    codelists: list[CTTermCodelist] = Field(
        [],
        title="codelists",
        description="",
    )

    sponsor_preferred_name: str = Field(
        ...,
        title="sponsor_preferred_name",
        description="",
    )

    sponsor_preferred_name_sentence_case: str = Field(
        ...,
        title="sponsor_preferred_name_sentence_case",
        description="",
    )

    library_name: str | None = Field(None, nullable=True)
    start_date: datetime | None = Field(None, nullable=True)
    end_date: datetime | None = Field(None, nullable=True)
    status: str | None = Field(None, nullable=True)
    version: str | None = Field(None, nullable=True)
    change_description: str | None = Field(None, nullable=True)
    user_initials: str | None = Field(None, nullable=True)
    possible_actions: list[str] = Field(
        [],
        description=(
            "Holds those actions that can be performed on the CTTermName. "
            "Actions are: 'approve', 'edit', 'new_version'."
        ),
    )


class CTTermNameSimple(BaseModel):
    term_uid: str = Field(
        ...,
        title="term_uid",
        description="",
    )

    sponsor_preferred_name: str = Field(
        ...,
        title="sponsor_preferred_name",
        description="",
    )


class CTTermNameVersion(CTTermName):
    """
    Class for storing CTTermName and calculation of differences
    """

    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )


class CTTermNameInput(BaseModel):
    sponsor_preferred_name: str | None = Field(
        None,
        title="sponsor_preferred_name",
        description="",
    )

    sponsor_preferred_name_sentence_case: str | None = Field(
        None,
        title="sponsor_preferred_name_sentence_case",
        description="",
    )


class CTTermNameEditInput(CTTermNameInput):
    change_description: str = Field(None, title="change_description", description="")
