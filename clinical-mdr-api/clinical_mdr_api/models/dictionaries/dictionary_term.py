from datetime import datetime
from typing import Any, Callable, Self

from pydantic import Field

from clinical_mdr_api.domains.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.domains.dictionaries.dictionary_term_substance import (
    DictionaryTermSubstanceAR,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleDictionaryTermModel,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel


class DictionaryTerm(BaseModel):
    @classmethod
    def from_dictionary_term_ar(
        cls, dictionary_term_ar: DictionaryTermAR
    ) -> Self | None:
        if not dictionary_term_ar:
            return None
        return cls(
            term_uid=dictionary_term_ar.uid,
            dictionary_id=dictionary_term_ar.dictionary_term_vo.dictionary_id,
            name=dictionary_term_ar.name,
            name_sentence_case=dictionary_term_ar.dictionary_term_vo.name_sentence_case,
            abbreviation=dictionary_term_ar.dictionary_term_vo.abbreviation,
            definition=dictionary_term_ar.dictionary_term_vo.definition,
            library_name=Library.from_library_vo(dictionary_term_ar.library).name,
            start_date=dictionary_term_ar.item_metadata.start_date,
            end_date=dictionary_term_ar.item_metadata.end_date,
            status=dictionary_term_ar.item_metadata.status.value,
            version=dictionary_term_ar.item_metadata.version,
            change_description=dictionary_term_ar.item_metadata.change_description,
            user_initials=dictionary_term_ar.item_metadata.user_initials,
            possible_actions=sorted(
                [_.value for _ in dictionary_term_ar.get_possible_actions()]
            ),
        )

    term_uid: str
    dictionary_id: str
    name: str
    name_sentence_case: str
    abbreviation: str | None
    definition: str | None

    possible_actions: list[str] = Field(
        ...,
        description=(
            "Holds those actions that can be performed on the DictionaryTerm. "
            "Actions are: 'approve', 'edit', 'new_version'."
        ),
    )

    library_name: str
    start_date: datetime | None = Field(None, nullable=True)
    end_date: datetime | None = Field(None, nullable=True)
    status: str | None = Field(None, nullable=True)
    version: str | None = Field(None, nullable=True)
    change_description: str | None = Field(None, nullable=True)
    user_initials: str | None = Field(None, nullable=True)


class DictionaryTermEditInput(BaseModel):
    dictionary_id: str | None = None
    name: str | None = None
    name_sentence_case: str | None = None
    abbreviation: str | None = None
    definition: str | None = None
    change_description: str = Field(None, title="change_description", description="")


class DictionaryTermCreateInput(BaseModel):
    dictionary_id: str
    name: str
    name_sentence_case: str | None = None
    abbreviation: str | None = None
    definition: str | None = None
    codelist_uid: str = Field(..., title="codelist_uid", description="")
    library_name: str


class DictionaryTermSubstance(DictionaryTerm):
    pclass: SimpleDictionaryTermModel | None

    @classmethod
    def from_dictionary_term_ar(
        cls,
        dictionary_term_ar: DictionaryTermSubstanceAR,
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
    ) -> Self | None:
        if not dictionary_term_ar:
            return None
        return cls(
            term_uid=dictionary_term_ar.uid,
            dictionary_id=dictionary_term_ar.dictionary_term_vo.dictionary_id,
            name=dictionary_term_ar.name,
            name_sentence_case=dictionary_term_ar.dictionary_term_vo.name_sentence_case,
            abbreviation=dictionary_term_ar.dictionary_term_vo.abbreviation,
            definition=dictionary_term_ar.dictionary_term_vo.definition,
            library_name=Library.from_library_vo(dictionary_term_ar.library).name,
            pclass=SimpleDictionaryTermModel.from_ct_code(
                c_code=dictionary_term_ar.dictionary_term_vo.pclass_uid,
                find_term_by_uid=find_dictionary_term_by_uid,
            ),
            start_date=dictionary_term_ar.item_metadata.start_date,
            end_date=dictionary_term_ar.item_metadata.end_date,
            status=dictionary_term_ar.item_metadata.status.value,
            version=dictionary_term_ar.item_metadata.version,
            change_description=dictionary_term_ar.item_metadata.change_description,
            user_initials=dictionary_term_ar.item_metadata.user_initials,
            possible_actions=sorted(
                [_.value for _ in dictionary_term_ar.get_possible_actions()]
            ),
        )


class CompoundSubstance(BaseModel):
    substance_term_uid: str
    substance_name: str
    substance_unii: str
    pclass_term_uid: str | None
    pclass_name: str | None
    pclass_id: str | None

    @classmethod
    def from_term_uid(
        cls,
        uid: str,
        find_term_by_uid: Callable[[str], Any | None],
        find_substance_by_uid: Callable[[str], Any | None],
    ) -> Self | None:
        substance = None
        if uid is not None:
            substance_term: DictionaryTermSubstanceAR = find_substance_by_uid(uid)

            if substance_term is not None:
                pclass_term: SimpleDictionaryTermModel = (
                    SimpleDictionaryTermModel.from_ct_code(
                        c_code=substance_term.dictionary_term_vo.pclass_uid,
                        find_term_by_uid=find_term_by_uid,
                    )
                )

                substance = cls(
                    substance_term_uid=uid,
                    substance_name=substance_term.dictionary_term_vo.name,
                    substance_unii=substance_term.dictionary_term_vo.dictionary_id,
                    pclass_term_uid=pclass_term.term_uid if pclass_term else None,
                    pclass_name=pclass_term.name if pclass_term else None,
                    pclass_id=pclass_term.dictionary_id if pclass_term else None,
                )

        return substance


class DictionaryTermSubstanceCreateInput(DictionaryTermCreateInput):
    pclass_uid: str | None = None


class DictionaryTermSubstanceEditInput(DictionaryTermEditInput):
    pclass_uid: str | None = None


class DictionaryTermVersion(DictionaryTerm):
    """
    Class for storing DictionaryTerm and calculation of differences
    """

    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )
