from typing import Callable, Self

from pydantic import Field

from clinical_mdr_api.domains.concepts.active_substance import ActiveSubstanceAR
from clinical_mdr_api.domains.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.domains.dictionaries.dictionary_term_substance import (
    DictionaryTermSubstanceAR,
)
from clinical_mdr_api.models import Library
from clinical_mdr_api.models.concepts.concept import VersionProperties
from clinical_mdr_api.models.dictionaries.dictionary_term import CompoundSubstance
from clinical_mdr_api.models.utils import BaseModel


class ActiveSubstance(VersionProperties):
    uid: str

    analyte_number: str | None = Field(None, nullable=True)
    short_number: str | None = Field(None, nullable=True)
    long_number: str | None = Field(None, nullable=True)
    inn: str | None = Field(None, nullable=True)
    external_id: str | None = Field(None, nullable=True)
    library_name: str
    unii: CompoundSubstance | None = Field(None, nullable=True)
    possible_actions: list[str] = Field(
        ...,
        description=(
            "Holds those actions that can be performed on ActiveSubstances. "
            "Actions are: 'approve', 'edit', 'new_version'."
        ),
    )

    @classmethod
    def from_active_substance_ar(
        cls,
        active_substance_ar: ActiveSubstanceAR,
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        find_substance_term_by_uid: Callable[[str], DictionaryTermSubstanceAR | None],
    ) -> Self:
        return cls(
            uid=active_substance_ar.uid,
            unii=CompoundSubstance.from_term_uid(
                uid=active_substance_ar.concept_vo.unii_term_uid,
                find_term_by_uid=find_dictionary_term_by_uid,
                find_substance_by_uid=find_substance_term_by_uid,
            )
            if active_substance_ar.concept_vo.unii_term_uid
            else None,
            analyte_number=active_substance_ar.concept_vo.analyte_number,
            short_number=active_substance_ar.concept_vo.short_number,
            long_number=active_substance_ar.concept_vo.long_number,
            inn=active_substance_ar.concept_vo.inn,
            external_id=active_substance_ar.concept_vo.external_id,
            library_name=Library.from_library_vo(active_substance_ar.library).name,
            start_date=active_substance_ar.item_metadata.start_date,
            end_date=active_substance_ar.item_metadata.end_date,
            status=active_substance_ar.item_metadata.status.value,
            version=active_substance_ar.item_metadata.version,
            change_description=active_substance_ar.item_metadata.change_description,
            user_initials=active_substance_ar.item_metadata.user_initials,
            possible_actions=sorted(
                [_.value for _ in active_substance_ar.get_possible_actions()]
            ),
        )


class ActiveSubstanceCreateInput(BaseModel):
    external_id: str | None = None
    analyte_number: str | None = None
    short_number: str | None = None
    long_number: str | None = None
    inn: str | None = None
    library_name: str
    unii_term_uid: str | None = None


class ActiveSubstanceEditInput(BaseModel):
    external_id: str | None = None
    analyte_number: str | None = None
    short_number: str | None = None
    long_number: str | None = None
    inn: str | None = None
    library_name: str | None = None
    unii_term_uid: str | None = None
    change_description: str


class ActiveSubstanceVersion(ActiveSubstance):
    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )


class SimpleActiveSubstance(BaseModel):
    uid: str
    analyte_number: str | None = Field(None, nullable=True)
    short_number: str | None = Field(None, nullable=True)
    long_number: str | None = Field(None, nullable=True)
    inn: str | None = Field(None, nullable=True)
    external_id: str | None = Field(None, nullable=True)
    unii: CompoundSubstance | None = Field(None, nullable=True)

    @classmethod
    def from_concept_uid(
        cls,
        uid: str,
        find_by_uid: Callable[[str], ActiveSubstanceAR | None],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        find_substance_term_by_uid: Callable[[str], DictionaryTermSubstanceAR | None],
    ) -> Self | None:
        concept = None
        if uid is not None:
            val: ActiveSubstanceAR = find_by_uid(uid)

            if val is not None:
                concept = SimpleActiveSubstance(
                    uid=val.uid,
                    analyte_number=val.concept_vo.analyte_number,
                    short_number=val.concept_vo.short_number,
                    long_number=val.concept_vo.long_number,
                    inn=val.concept_vo.inn,
                    external_id=val.concept_vo.external_id,
                    unii=CompoundSubstance.from_term_uid(
                        uid=val.concept_vo.unii_term_uid,
                        find_term_by_uid=find_dictionary_term_by_uid,
                        find_substance_by_uid=find_substance_term_by_uid,
                    ),
                )

        return concept
