from typing import Callable, Self

from pydantic import Field

from clinical_mdr_api.domains.concepts.compound import CompoundAR
from clinical_mdr_api.domains.concepts.medicinal_product import MedicinalProductAR
from clinical_mdr_api.domains.concepts.pharmaceutical_product import (
    PharmaceuticalProductAR,
)
from clinical_mdr_api.domains.concepts.simple_concepts.numeric_value import (
    NumericValueAR,
)
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.models.concepts.compound import SimpleCompound
from clinical_mdr_api.models.concepts.concept import (
    SimpleNumericValueWithUnit,
    VersionProperties,
)
from clinical_mdr_api.models.concepts.pharmaceutical_product import (
    SimplePharmaceuticalProduct,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import SimpleTermModel
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel


class MedicinalProduct(VersionProperties):
    uid: str
    name: str = Field(
        ...,
    )
    name_sentence_case: str | None = Field(
        None,
        nullable=True,
    )
    external_id: str | None = Field(None, nullable=True)
    library_name: str
    compound: SimpleCompound
    pharmaceutical_products: list[SimplePharmaceuticalProduct] = []

    dose_values: list[SimpleNumericValueWithUnit] = []
    dose_frequencies: list[SimpleTermModel] = []
    delivery_devices: list[SimpleTermModel] = []
    dispensers: list[SimpleTermModel] = []

    possible_actions: list[str] = Field(
        ...,
        description=(
            "Holds those actions that can be performed on MedicinalProducts. "
            "Actions are: 'approve', 'edit', 'new_version'."
        ),
    )

    @classmethod
    def from_medicinal_product_ar(
        cls,
        medicinal_product_ar: MedicinalProductAR,
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
        find_numeric_value_by_uid: Callable[[str], NumericValueAR | None],
        find_unit_by_uid: Callable[[str], UnitDefinitionAR | None],
        find_compound_by_uid: Callable[[str], CompoundAR | None],
        find_pharmaceutical_product_by_uid: Callable[
            [str], PharmaceuticalProductAR | None
        ],
    ) -> Self:
        return cls(
            uid=medicinal_product_ar.uid,
            external_id=medicinal_product_ar.concept_vo.external_id,
            name=medicinal_product_ar.concept_vo.name,
            name_sentence_case=medicinal_product_ar.concept_vo.name_sentence_case,
            compound=SimpleCompound.from_uid(
                uid=medicinal_product_ar.concept_vo.compound_uid,
                find_by_uid=find_compound_by_uid,
            ),
            pharmaceutical_products=sorted(
                [
                    SimplePharmaceuticalProduct.from_uid(
                        uid=uid,
                        find_by_uid=find_pharmaceutical_product_by_uid,
                    )
                    for uid in medicinal_product_ar.concept_vo.pharmaceutical_product_uids
                ],
                key=lambda item: item.external_id if item.external_id else "",
            ),
            dose_values=sorted(
                [
                    SimpleNumericValueWithUnit.from_concept_uid(
                        uid=uid,
                        find_unit_by_uid=find_unit_by_uid,
                        find_numeric_value_by_uid=find_numeric_value_by_uid,
                    )
                    for uid in medicinal_product_ar.concept_vo.dose_value_uids
                ],
                key=lambda item: item.value,
            ),
            dose_frequencies=sorted(
                [
                    SimpleTermModel.from_ct_code(
                        c_code=uid,
                        find_term_by_uid=find_term_by_uid,
                    )
                    for uid in medicinal_product_ar.concept_vo.dose_frequency_uids
                ],
                key=lambda item: item.name if item.name else "",
            ),
            delivery_devices=sorted(
                [
                    SimpleTermModel.from_ct_code(
                        c_code=uid,
                        find_term_by_uid=find_term_by_uid,
                    )
                    for uid in medicinal_product_ar.concept_vo.delivery_device_uids
                ],
                key=lambda item: item.name if item.name else "",
            ),
            dispensers=sorted(
                [
                    SimpleTermModel.from_ct_code(
                        c_code=uid,
                        find_term_by_uid=find_term_by_uid,
                    )
                    for uid in medicinal_product_ar.concept_vo.dispenser_uids
                ],
                key=lambda item: item.name if item.name else "",
            ),
            library_name=Library.from_library_vo(medicinal_product_ar.library).name,
            start_date=medicinal_product_ar.item_metadata.start_date,
            end_date=medicinal_product_ar.item_metadata.end_date,
            status=medicinal_product_ar.item_metadata.status.value,
            version=medicinal_product_ar.item_metadata.version,
            change_description=medicinal_product_ar.item_metadata.change_description,
            user_initials=medicinal_product_ar.item_metadata.user_initials,
            possible_actions=sorted(
                [_.value for _ in medicinal_product_ar.get_possible_actions()]
            ),
        )


class MedicinalProductCreateInput(BaseModel):
    external_id: str | None = None
    name: str
    name_sentence_case: str | None = None
    library_name: str
    dose_value_uids: list[str] = []
    dose_frequency_uids: list[str] = []
    delivery_device_uids: list[str] = []
    dispenser_uids: list[str] = []
    compound_uid: str
    pharmaceutical_product_uids: list[str] = []


class MedicinalProductEditInput(BaseModel):
    external_id: str | None = None
    name: str | None = None
    name_sentence_case: str | None = None
    library_name: str | None = None
    dose_value_uids: list[str] | None = None
    dose_frequency_uids: list[str] | None = None
    delivery_device_uids: list[str] | None = None
    dispenser_uids: list[str] | None = None
    compound_uid: str | None = None
    pharmaceutical_product_uids: list[str] | None = None
    change_description: str


class MedicinalProductVersion(MedicinalProduct):
    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )
