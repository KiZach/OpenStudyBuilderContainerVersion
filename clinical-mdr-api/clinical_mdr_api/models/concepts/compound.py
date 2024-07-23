from typing import Callable, Self

from pydantic import Field

from clinical_mdr_api.domains.brands.brand import BrandAR
from clinical_mdr_api.domains.clinical_programmes.clinical_programme import (
    ClinicalProgrammeAR,
)
from clinical_mdr_api.domains.concepts.compound import CompoundAR
from clinical_mdr_api.domains.concepts.simple_concepts.lag_time import LagTimeAR
from clinical_mdr_api.domains.concepts.simple_concepts.numeric_value import (
    NumericValueAR,
)
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.domains.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.domains.dictionaries.dictionary_term_substance import (
    DictionaryTermSubstanceAR,
)
from clinical_mdr_api.domains.projects.project import ProjectAR
from clinical_mdr_api.models import Library, Project
from clinical_mdr_api.models.brands.brand import Brand
from clinical_mdr_api.models.concepts.concept import (
    Concept,
    ConceptInput,
    SimpleLagTime,
    SimpleNumericValueWithUnit,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import SimpleTermModel
from clinical_mdr_api.models.dictionaries.dictionary_term import CompoundSubstance
from clinical_mdr_api.models.utils import BaseModel


class Compound(Concept):
    possible_actions: list[str] = Field(
        ...,
        description=(
            "Holds those actions that can be performed on Compounds. "
            "Actions are: 'approve', 'edit', 'new_version'."
        ),
    )

    analyte_number: str | None = Field(None, nullable=True)
    nnc_short_number: str | None = Field(None, nullable=True)
    nnc_long_number: str | None = Field(None, nullable=True)
    is_sponsor_compound: bool | None = True
    is_name_inn: bool | None = True
    substances: list[CompoundSubstance] | None
    dose_values: list[SimpleNumericValueWithUnit] | None
    strength_values: list[SimpleNumericValueWithUnit] | None
    lag_times: list[SimpleLagTime] | None
    delivery_devices: list[SimpleTermModel] | None
    dispensers: list[SimpleTermModel] | None
    projects: list[Project] | None
    brands: list[Brand] | None
    half_life: SimpleNumericValueWithUnit | None
    dose_frequencies: list[SimpleTermModel] | None
    dosage_forms: list[SimpleTermModel] | None
    routes_of_administration: list[SimpleTermModel] | None

    @classmethod
    def from_compound_ar(
        cls,
        compound_ar: CompoundAR,
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        find_substance_term_by_uid: Callable[[str], DictionaryTermSubstanceAR | None],
        find_numeric_value_by_uid: Callable[[str], NumericValueAR | None],
        find_lag_time_by_uid: Callable[[str], LagTimeAR | None],
        find_unit_by_uid: Callable[[str], UnitDefinitionAR | None],
        find_project_by_uid: Callable[[str], ProjectAR | None],
        find_brand_by_uid: Callable[[str], BrandAR | None],
        find_clinical_programme_by_uid: Callable[[str], ClinicalProgrammeAR | None],
    ) -> Self:
        return cls(
            uid=compound_ar.uid,
            name=compound_ar.name,
            name_sentence_case=compound_ar.concept_vo.name_sentence_case,
            definition=compound_ar.concept_vo.definition,
            abbreviation=compound_ar.concept_vo.abbreviation,
            dose_values=sorted(
                [
                    SimpleNumericValueWithUnit.from_concept_uid(
                        uid=uid,
                        find_unit_by_uid=find_unit_by_uid,
                        find_numeric_value_by_uid=find_numeric_value_by_uid,
                    )
                    for uid in compound_ar.concept_vo.dose_values_uids
                ],
                key=lambda item: item.value,
            ),
            strength_values=sorted(
                [
                    SimpleNumericValueWithUnit.from_concept_uid(
                        uid=uid,
                        find_unit_by_uid=find_unit_by_uid,
                        find_numeric_value_by_uid=find_numeric_value_by_uid,
                    )
                    for uid in compound_ar.concept_vo.strength_values_uids
                ],
                key=lambda item: item.value,
            ),
            lag_times=sorted(
                [
                    SimpleLagTime.from_concept_uid(
                        uid=uid,
                        find_unit_by_uid=find_unit_by_uid,
                        find_lag_time_by_uid=find_lag_time_by_uid,
                        find_term_by_uid=find_term_by_uid,
                    )
                    for uid in compound_ar.concept_vo.lag_time_uids
                ],
                key=lambda item: item.value,
            ),
            delivery_devices=sorted(
                [
                    SimpleTermModel.from_ct_code(
                        c_code=uid,
                        find_term_by_uid=find_term_by_uid,
                    )
                    for uid in compound_ar.concept_vo.delivery_devices_uids
                ],
                key=lambda item: item.name,
            ),
            dispensers=sorted(
                [
                    SimpleTermModel.from_ct_code(
                        c_code=uid,
                        find_term_by_uid=find_term_by_uid,
                    )
                    for uid in compound_ar.concept_vo.dispensers_uids
                ],
                key=lambda item: item.name,
            ),
            projects=sorted(
                [
                    Project.from_uid(
                        uid=uid,
                        find_by_uid=find_project_by_uid,
                        find_clinical_programme_by_uid=find_clinical_programme_by_uid,
                    )
                    for uid in compound_ar.concept_vo.projects_uids
                ],
                key=lambda item: item.name,
            ),
            brands=sorted(
                [
                    Brand.from_uid(
                        uid=uid,
                        find_by_uid=find_brand_by_uid,
                    )
                    for uid in compound_ar.concept_vo.brands_uids
                ],
                key=lambda item: item.name,
            ),
            half_life=SimpleNumericValueWithUnit.from_concept_uid(
                uid=compound_ar.concept_vo.half_life_uid,
                find_unit_by_uid=find_unit_by_uid,
                find_numeric_value_by_uid=find_numeric_value_by_uid,
            ),
            dose_frequencies=sorted(
                [
                    SimpleTermModel.from_ct_code(
                        c_code=uid,
                        find_term_by_uid=find_term_by_uid,
                    )
                    for uid in compound_ar.concept_vo.dose_frequency_uids
                ],
                key=lambda item: item.name if item.name else "",
            ),
            dosage_forms=sorted(
                [
                    SimpleTermModel.from_ct_code(
                        c_code=uid,
                        find_term_by_uid=find_term_by_uid,
                    )
                    for uid in compound_ar.concept_vo.dosage_form_uids
                ],
                key=lambda item: item.name if item.name else "",
            ),
            routes_of_administration=sorted(
                [
                    SimpleTermModel.from_ct_code(
                        c_code=uid,
                        find_term_by_uid=find_term_by_uid,
                    )
                    for uid in compound_ar.concept_vo.route_of_administration_uids
                ],
                key=lambda item: item.name if item.name else "",
            ),
            analyte_number=compound_ar.concept_vo.analyte_number,
            nnc_short_number=compound_ar.concept_vo.nnc_short_number,
            nnc_long_number=compound_ar.concept_vo.nnc_long_number,
            is_sponsor_compound=compound_ar.concept_vo.is_sponsor_compound,
            is_name_inn=compound_ar.concept_vo.is_name_inn,
            substances=sorted(
                [
                    CompoundSubstance.from_term_uid(
                        uid=unii_uid,
                        find_term_by_uid=find_dictionary_term_by_uid,
                        find_substance_by_uid=find_substance_term_by_uid,
                    )
                    for unii_uid in compound_ar.concept_vo.substance_terms_uids
                ],
                key=lambda item: item.substance_name,
            ),
            library_name=Library.from_library_vo(compound_ar.library).name,
            start_date=compound_ar.item_metadata.start_date,
            end_date=compound_ar.item_metadata.end_date,
            status=compound_ar.item_metadata.status.value,
            version=compound_ar.item_metadata.version,
            change_description=compound_ar.item_metadata.change_description,
            user_initials=compound_ar.item_metadata.user_initials,
            possible_actions=sorted(
                [_.value for _ in compound_ar.get_possible_actions()]
            ),
        )


class SimpleCompound(BaseModel):
    @classmethod
    def from_uid(
        cls, uid: str, find_by_uid: Callable[[str], CompoundAR | None]
    ) -> Self | None:
        simple_compound_model = None
        if uid is not None:
            compound_ar: CompoundAR = find_by_uid(uid)
            if compound_ar is not None:
                simple_compound_model = cls(uid=uid, name=compound_ar.concept_vo.name)

        return simple_compound_model

    uid: str = Field(..., title="uid", description="")
    name: str = Field(..., title="name", description="")

    @classmethod
    def from_compound_ar(cls, compound_ar: CompoundAR) -> Self:
        return cls(
            uid=compound_ar.uid,
            name=compound_ar.name,
        )


class CompoundCreateInput(ConceptInput):
    analyte_number: str | None = None
    nnc_short_number: str | None = None
    nnc_long_number: str | None = None
    is_sponsor_compound: bool = True
    is_name_inn: bool = True
    substance_terms_uids: list[str] | None = []
    dose_values_uids: list[str] = []
    strength_values_uids: list[str] = []
    lag_times_uids: list[str] = []
    delivery_devices_uids: list[str] = []
    dispensers_uids: list[str] = []
    projects_uids: list[str] = []
    brands_uids: list[str] = []
    dose_frequency_uids: list[str] = []
    dosage_form_uids: list[str] = []
    route_of_administration_uids: list[str] = []
    half_life_uid: str | None = None


class CompoundEditInput(ConceptInput):
    analyte_number: str | None
    nnc_short_number: str | None
    nnc_long_number: str | None
    is_sponsor_compound: bool | None
    is_name_inn: bool | None
    substance_terms_uids: list[str] | None = []
    dose_values_uids: list[str] | None = []
    strength_values_uids: list[str] | None = []
    lag_times_uids: list[str] | None = []
    delivery_devices_uids: list[str] | None = []
    dispensers_uids: list[str] | None = []
    projects_uids: list[str] | None = []
    brands_uids: list[str] | None = []
    half_life_uid: str | None
    dose_frequency_uids: list[str] | None = []
    dosage_form_uids: list[str] | None = []
    route_of_administration_uids: list[str] | None = []
    change_description: str


class CompoundVersion(Compound):
    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )
