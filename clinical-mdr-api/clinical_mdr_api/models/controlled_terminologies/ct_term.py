from typing import Any, Callable, Self

from pydantic import Field

from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.models.controlled_terminologies.ct_term_attributes import (
    CTTermAttributes,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term_codelist import (
    CTTermCodelist,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term_name import CTTermName
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel


class CTTerm(BaseModel):
    @classmethod
    def from_ct_term_ars(
        cls, ct_term_name_ar: CTTermNameAR, ct_term_attributes_ar: CTTermAttributesAR
    ) -> Self:
        return cls(
            term_uid=ct_term_attributes_ar.uid,
            catalogue_name=ct_term_attributes_ar.ct_term_vo.catalogue_name,
            codelists=[
                CTTermCodelist(
                    codelist_uid=x.codelist_uid,
                    order=x.order,
                )
                for x in ct_term_name_ar.ct_term_vo.codelists
            ],
            concept_id=ct_term_attributes_ar.ct_term_vo.concept_id,
            code_submission_value=ct_term_attributes_ar.ct_term_vo.code_submission_value,
            name_submission_value=ct_term_attributes_ar.ct_term_vo.name_submission_value,
            nci_preferred_name=ct_term_attributes_ar.ct_term_vo.preferred_term,
            definition=ct_term_attributes_ar.ct_term_vo.definition,
            library_name=Library.from_library_vo(ct_term_attributes_ar.library).name,
            sponsor_preferred_name=ct_term_name_ar.ct_term_vo.name,
            sponsor_preferred_name_sentence_case=ct_term_name_ar.ct_term_vo.name_sentence_case,
            possible_actions=sorted(
                [_.value for _ in ct_term_attributes_ar.get_possible_actions()]
            ),
        )

    term_uid: str = Field(
        ...,
        title="term_uid",
        description="",
    )

    catalogue_name: str = Field(
        ...,
        title="catalogue_name",
        description="",
    )

    codelists: list[CTTermCodelist] = Field(
        [],
        title="codelists",
        description="",
    )

    concept_id: str | None = Field(
        None, title="concept_id", description="", nullable=True
    )

    code_submission_value: str | None = Field(
        None, title="code_submission_value", description="", nullable=True
    )

    name_submission_value: str | None = Field(
        None,
        title="name_submission_value",
        description="",
        nullable=True,
    )

    nci_preferred_name: str = Field(
        ...,
        title="nci_preferred_name",
        description="",
    )

    definition: str = Field(
        ..., title="definition", description="", remove_from_wildcard=True
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

    library_name: str
    possible_actions: list[str] = Field(
        [],
        description=(
            "Holds those actions that can be performed on the CTTerm. "
            "Actions are: 'approve', 'edit', 'new_version'."
        ),
    )


class CTTermCreateInput(BaseModel):
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

    code_submission_value: str = Field(
        ...,
        title="code_submission_value",
        description="",
    )

    name_submission_value: str | None = Field(
        None,
        title="name_submission_value",
        description="",
        nullable=True,
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
    order: int | None = Field(999999, title="order", description="", nullable=True)
    library_name: str = Field(
        ...,
        title="library_name",
        description="",
    )


class CTTermNameAndAttributes(BaseModel):
    @classmethod
    def from_ct_term_ars(
        cls, ct_term_name_ar: CTTermNameAR, ct_term_attributes_ar: CTTermAttributesAR
    ) -> Self:
        if not ct_term_name_ar or not ct_term_attributes_ar:
            return None
        term_name_and_attributes = cls(
            term_uid=ct_term_attributes_ar.uid,
            catalogue_name=ct_term_attributes_ar.ct_term_vo.catalogue_name,
            library_name=(
                Library.from_library_vo(ct_term_attributes_ar.library).name
                if ct_term_attributes_ar.library
                else None
            ),
            name=CTTermName.from_ct_term_ar_without_common_term_fields(ct_term_name_ar),
            attributes=CTTermAttributes.from_ct_term_ar_without_common_term_fields(
                ct_term_attributes_ar
            ),
        )
        term_name_and_attributes.codelists = [
            CTTermCodelist(
                codelist_uid=x.codelist_uid,
                order=x.order,
            )
            for x in ct_term_name_ar.ct_term_vo.codelists
        ]

        return term_name_and_attributes

    term_uid: str = Field(
        ...,
        title="term_uid",
        description="",
    )
    catalogue_name: str = Field(
        ...,
        title="catalogue_name",
        description="",
    )
    codelists: list[CTTermCodelist] = Field(
        [],
        title="codelists",
        description="",
    )

    library_name: str | None = Field(None, nullable=True)

    name: CTTermName = Field(
        ...,
        title="CTTermName",
        description="",
    )

    attributes: CTTermAttributes = Field(
        ...,
        title="CTTermAttributes",
        description="",
    )


class CTTermNewOrder(BaseModel):
    codelist_uid: str = Field(
        ...,
        title="codelist_uid",
        description="",
    )
    new_order: int = Field(
        999999,
        title="new_order",
        description="",
    )


class SimpleCTTermAttributes(BaseModel):
    @classmethod
    def from_term_uid(
        cls, uid: str, find_term_by_uid: Callable[[str], Any | None]
    ) -> Self | None:
        term_model = None
        if uid is not None:
            term = find_term_by_uid(uid)
            if term is not None:
                term_model = cls(
                    uid=uid,
                    code_submission_value=term.ct_term_vo.code_submission_value,
                    preferred_term=term.ct_term_vo.preferred_term,
                )
            else:
                term_model = cls(
                    uid=uid, code_submission_value=None, preferred_term=None
                )
        else:
            term_model = None
        return term_model

    uid: str = Field(..., title="uid", description="")
    code_submission_value: str | None = Field(
        None, title="code_submission_value", description="", nullable=True
    )
    preferred_term: str | None = Field(
        None, title="preferred_term", description="", nullable=True
    )


class SimpleTermModel(BaseModel):
    @classmethod
    def from_ct_code(
        cls,
        c_code: str,
        find_term_by_uid: Callable[[str], Any | None],
        at_specific_date=None,
    ) -> Self | None:
        simple_term_model = None
        if c_code is not None:
            if "ct_term_generic_repository" in find_term_by_uid.__module__:
                term = find_term_by_uid(c_code, at_specific_date=at_specific_date)
            else:
                term = find_term_by_uid(c_code)

            if term is not None:
                if hasattr(term, "ct_term_vo"):
                    simple_term_model = cls(term_uid=c_code, name=term.ct_term_vo.name)
                elif hasattr(term, "dictionary_term_vo"):
                    simple_term_model = SimpleDictionaryTermModel(
                        term_uid=c_code,
                        name=term.dictionary_term_vo.name,
                        dictionary_id=getattr(
                            term.dictionary_term_vo, "dictionary_id", None
                        ),
                    )
            else:
                simple_term_model = cls(term_uid=c_code, name=None)
        else:
            simple_term_model = None
        return simple_term_model

    term_uid: str = Field(..., title="term_uid", description="")
    name: str | None = Field(None, title="name", description="", nullable=True)


class SimpleDictionaryTermModel(SimpleTermModel):
    dictionary_id: str | None = Field(
        None,
        title="dictionary_id",
        description="Id if item in the external dictionary",
        nullable=True,
    )


class SimpleTermName(BaseModel):
    sponsor_preferred_name: str = Field(
        ..., title="sponsor_preferred_name", description=""
    )
    sponsor_preferred_name_sentence_case: str = Field(
        ..., title="sponsor_preferred_name_sentence_case", description=""
    )


class SimpleTermAttributes(BaseModel):
    code_submission_value: str | None = Field(
        None, title="code_submission_value", description="", nullable=True
    )
    nci_preferred_name: str | None = Field(
        None, title="nci_preferred_name", description="", nullable=True
    )


class SimpleCTTermNameAndAttributes(BaseModel):
    term_uid: str = Field(..., title="term_uid", description="")
    name: SimpleTermName = Field(
        ...,
        title="SimpleTermName",
        description="",
    )
    attributes: SimpleTermAttributes = Field(
        ...,
        title="SimpleTermAttributes",
        description="",
    )
