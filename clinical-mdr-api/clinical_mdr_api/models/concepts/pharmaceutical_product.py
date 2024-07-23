from typing import Callable, Self

from pydantic import Field

from clinical_mdr_api.domains.concepts.active_substance import ActiveSubstanceAR
from clinical_mdr_api.domains.concepts.pharmaceutical_product import (
    PharmaceuticalProductAR,
)
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
from clinical_mdr_api.models.concepts.active_substance import SimpleActiveSubstance
from clinical_mdr_api.models.concepts.concept import (
    SimpleLagTime,
    SimpleNumericValueWithUnit,
    VersionProperties,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import SimpleTermModel
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel


class Ingredient(BaseModel):
    external_id: str | None = None
    active_substance: SimpleActiveSubstance
    strength: SimpleNumericValueWithUnit | None = None
    half_life: SimpleNumericValueWithUnit | None = None
    lag_times: list[SimpleLagTime] = []


class IngredientCreateInput(BaseModel):
    active_substance_uid: str
    external_id: str | None = None
    strength_uid: str | None = None
    half_life_uid: str | None = None
    lag_time_uids: list[str] = []


class IngredientEditInput(BaseModel):
    active_substance_uid: str | None = None
    external_id: str | None = None
    strength_uid: str | None = None
    half_life_uid: str | None = None
    lag_time_uids: list[str] | None = None


class Formulation(BaseModel):
    external_id: str | None = None
    name: str
    ingredients: list[Ingredient] = []


class FormulationCreateInput(BaseModel):
    external_id: str | None = None
    name: str
    ingredients: list[IngredientCreateInput] | None = None


class FormulationEditInput(BaseModel):
    external_id: str | None = None
    name: str | None = None
    ingredients: list[IngredientEditInput] = []


class PharmaceuticalProduct(VersionProperties):
    uid: str

    external_id: str | None = Field(None, nullable=True)
    library_name: str

    dosage_forms: list[SimpleTermModel] | None
    routes_of_administration: list[SimpleTermModel] | None
    formulations: list[Formulation]

    possible_actions: list[str] = Field(
        ...,
        description=(
            "Holds those actions that can be performed on PharmaceuticalProducts. "
            "Actions are: 'approve', 'edit', 'new_version'."
        ),
    )

    @classmethod
    def from_pharmaceutical_product_ar(
        cls,
        pharmaceutical_product_ar: PharmaceuticalProductAR,
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
        find_numeric_value_by_uid: Callable[[str], NumericValueAR | None],
        find_lag_time_by_uid: Callable[[str], LagTimeAR | None],
        find_unit_by_uid: Callable[[str], UnitDefinitionAR | None],
        find_active_substance_by_uid: Callable[[str], ActiveSubstanceAR | None],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        find_substance_term_by_uid: Callable[[str], DictionaryTermSubstanceAR | None],
    ) -> Self:
        return cls(
            uid=pharmaceutical_product_ar.uid,
            external_id=pharmaceutical_product_ar.concept_vo.external_id,
            dosage_forms=sorted(
                [
                    SimpleTermModel.from_ct_code(
                        c_code=uid,
                        find_term_by_uid=find_term_by_uid,
                    )
                    for uid in pharmaceutical_product_ar.concept_vo.dosage_form_uids
                ],
                key=lambda item: item.name if item.name else "",
            ),
            routes_of_administration=sorted(
                [
                    SimpleTermModel.from_ct_code(
                        c_code=uid,
                        find_term_by_uid=find_term_by_uid,
                    )
                    for uid in pharmaceutical_product_ar.concept_vo.route_of_administration_uids
                ],
                key=lambda item: item.name if item.name else "",
            ),
            formulations=sorted(
                [
                    Formulation(
                        external_id=formulation.external_id,
                        name=formulation.name,
                        ingredients=sorted(
                            [
                                Ingredient(
                                    external_id=ingredient.external_id,
                                    active_substance=SimpleActiveSubstance.from_concept_uid(
                                        uid=ingredient.active_substance_uid,
                                        find_by_uid=find_active_substance_by_uid,
                                        find_dictionary_term_by_uid=find_dictionary_term_by_uid,
                                        find_substance_term_by_uid=find_substance_term_by_uid,
                                    ),
                                    strength=SimpleNumericValueWithUnit.from_concept_uid(
                                        uid=ingredient.strength_uid,
                                        find_unit_by_uid=find_unit_by_uid,
                                        find_numeric_value_by_uid=find_numeric_value_by_uid,
                                    )
                                    if ingredient.strength_uid
                                    else None,
                                    half_life=SimpleNumericValueWithUnit.from_concept_uid(
                                        uid=ingredient.half_life_uid,
                                        find_unit_by_uid=find_unit_by_uid,
                                        find_numeric_value_by_uid=find_numeric_value_by_uid,
                                    )
                                    if ingredient.half_life_uid
                                    else None,
                                    lag_times=sorted(
                                        [
                                            SimpleLagTime.from_concept_uid(
                                                uid=uid,
                                                find_unit_by_uid=find_unit_by_uid,
                                                find_lag_time_by_uid=find_lag_time_by_uid,
                                                find_term_by_uid=find_term_by_uid,
                                            )
                                            for uid in ingredient.lag_time_uids
                                        ],
                                        key=lambda item: item.value,
                                    ),
                                )
                                for ingredient in formulation.ingredients
                            ],
                            key=lambda item: item.active_substance.analyte_number
                            if item.active_substance.analyte_number
                            else item.active_substance.uid,
                        ),
                    )
                    for formulation in pharmaceutical_product_ar.concept_vo.formulations
                ],
                key=lambda item: item.name,
            ),
            library_name=Library.from_library_vo(
                pharmaceutical_product_ar.library
            ).name,
            start_date=pharmaceutical_product_ar.item_metadata.start_date,
            end_date=pharmaceutical_product_ar.item_metadata.end_date,
            status=pharmaceutical_product_ar.item_metadata.status.value,
            version=pharmaceutical_product_ar.item_metadata.version,
            change_description=pharmaceutical_product_ar.item_metadata.change_description,
            user_initials=pharmaceutical_product_ar.item_metadata.user_initials,
            possible_actions=sorted(
                [_.value for _ in pharmaceutical_product_ar.get_possible_actions()]
            ),
        )


class SimplePharmaceuticalProduct(BaseModel):
    @classmethod
    def from_uid(
        cls, uid: str, find_by_uid: Callable[[str], PharmaceuticalProductAR | None]
    ) -> Self | None:
        item = None
        if uid is not None:
            item_ar: PharmaceuticalProductAR = find_by_uid(uid)
            if item_ar is not None:
                item = cls(uid=uid, external_id=item_ar.concept_vo.external_id)

        return item

    uid: str = Field(..., title="uid", description="")
    external_id: str = Field(None, title="external_id", description="", nullable=True)

    @classmethod
    def from_item_ar(cls, item_ar: PharmaceuticalProductAR) -> Self:
        return cls(
            uid=item_ar.uid,
            name=item_ar.name,
        )


class PharmaceuticalProductCreateInput(BaseModel):
    external_id: str | None = None
    library_name: str
    dosage_form_uids: list[str] = []
    route_of_administration_uids: list[str] = []
    formulations: list[FormulationCreateInput] = []


class PharmaceuticalProductEditInput(BaseModel):
    external_id: str | None = None
    library_name: str | None = None
    dosage_form_uids: list[str] = []
    route_of_administration_uids: list[str] = []
    formulations: list[FormulationEditInput] = []
    change_description: str


class PharmaceuticalProductVersion(PharmaceuticalProduct):
    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )
