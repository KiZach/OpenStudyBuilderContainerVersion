from dataclasses import dataclass
from typing import Callable, Self

from deepdiff import DeepDiff

from clinical_mdr_api import exceptions
from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase, ConceptVO
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)


@dataclass(frozen=True)
class MedicinalProductVO(ConceptVO):
    """
    The MedicinalProductVO acts as the single value object for MedicinalProductAR aggregate.
    """

    compound_uid: str
    external_id: str | None
    pharmaceutical_product_uids: list[str] | None = None
    delivery_device_uids: list[str] | None = None
    dispenser_uids: list[str] | None = None
    dose_value_uids: list[str] | None = None
    dose_frequency_uids: list[str] | None = None

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        name_sentence_case: str | None,
        external_id: str | None,
        compound_uid: str | None,
        pharmaceutical_product_uids: list[str] | None,
        delivery_device_uids: list[str] | None,
        dispenser_uids: list[str] | None,
        dose_value_uids: list[str] | None,
        dose_frequency_uids: list[str] | None,
    ) -> Self:
        medicinal_product_vo = cls(
            external_id=external_id,
            compound_uid=compound_uid,
            pharmaceutical_product_uids=pharmaceutical_product_uids,
            delivery_device_uids=delivery_device_uids,
            dispenser_uids=dispenser_uids,
            dose_value_uids=dose_value_uids,
            dose_frequency_uids=dose_frequency_uids,
            name=name,
            name_sentence_case=name_sentence_case,
            definition="",
            abbreviation="",
            is_template_parameter=False,
        )

        return medicinal_product_vo

    def validate(
        self,
        uid: str | None,
        medicinal_product_uid_by_property_value_callback: Callable[[str, str], str],
        ct_term_exists_callback: Callable[[str], bool],
        numeric_value_exists_callback: Callable[[str], bool],
        compound_exists_callback: Callable[[str], bool],
        pharmaceutical_product_exists_callback: Callable[[str], bool],
    ):
        self.validate_uniqueness(
            lookup_callback=medicinal_product_uid_by_property_value_callback,
            uid=uid,
            property_name="external_id",
            value=self.external_id,
            error_message=f"MedicinalProduct with external_id ({self.external_id}) already exists",
        )
        if not compound_exists_callback(self.compound_uid):
            raise exceptions.ValidationException(
                f"{type(self).__name__} tried to connect to non-existent compound identified by uid ({self.compound_uid})"
            )
        for p_uid in self.pharmaceutical_product_uids:
            if not pharmaceutical_product_exists_callback(p_uid):
                raise exceptions.ValidationException(
                    f"{type(self).__name__} tried to connect to non-existent pharmaceutical product identified by uid ({p_uid})"
                )

        for device_uid in self.delivery_device_uids:
            if not ct_term_exists_callback(device_uid):
                raise exceptions.ValidationException(
                    f"{type(self).__name__} tried to connect to non-existent delivery device identified by uid ({device_uid})"
                )
        for dispenser_uid in self.dispenser_uids:
            if not ct_term_exists_callback(dispenser_uid):
                raise exceptions.ValidationException(
                    f"{type(self).__name__} tried to connect to non-existent dispenser identified by uid ({dispenser_uid})"
                )
        for dose_value_uid in self.dose_value_uids:
            if not numeric_value_exists_callback(dose_value_uid):
                raise exceptions.ValidationException(
                    f"{type(self).__name__} tried to connect to non-existent dose value identified by uid ({dose_value_uid})"
                )
        for dose_frequency_uid in self.dose_frequency_uids:
            if not ct_term_exists_callback(dose_frequency_uid):
                raise exceptions.ValidationException(
                    f"{type(self).__name__} tried to connect to non-existent dose frequency identified by uid ({dose_frequency_uid})"
                )


class MedicinalProductAR(ConceptARBase):
    _external_id: str | None
    _concept_vo: MedicinalProductVO

    @property
    def concept_vo(self) -> MedicinalProductVO:
        return self._concept_vo

    @property
    def name(self) -> str:
        return self.concept_vo.name

    @classmethod
    def from_input_values(
        cls,
        author: str,
        concept_vo: MedicinalProductVO,
        library: LibraryVO,
        medicinal_product_uid_by_property_value_callback: Callable[[str, str], str],
        ct_term_exists_callback: Callable[[str], bool],
        numeric_value_exists_callback: Callable[[str], bool],
        compound_exists_callback: Callable[[str], bool],
        pharmaceutical_product_exists_callback: Callable[[str], bool],
        generate_uid_callback: Callable[[], str | None] = (lambda: None),
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)
        uid = generate_uid_callback()

        if not library.is_editable:
            raise exceptions.BusinessLogicException(
                f"The library with the name='{library.name}' does not allow to create objects."
            )

        concept_vo.validate(
            uid=uid,
            medicinal_product_uid_by_property_value_callback=medicinal_product_uid_by_property_value_callback,
            ct_term_exists_callback=ct_term_exists_callback,
            numeric_value_exists_callback=numeric_value_exists_callback,
            compound_exists_callback=compound_exists_callback,
            pharmaceutical_product_exists_callback=pharmaceutical_product_exists_callback,
        )

        medicinal_product_ar = cls(
            _uid=uid,
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return medicinal_product_ar

    def edit_draft(
        self,
        author: str,
        change_description: str | None,
        concept_vo: MedicinalProductVO,
        concept_exists_by_callback: Callable[[str, str], str] | None = None,
        ct_term_exists_callback: Callable[[str], bool] | None = None,
        numeric_value_exists_callback: Callable[[str], bool] | None = None,
        compound_exists_callback: Callable[[str], bool] | None = None,
        pharmaceutical_product_exists_callback: Callable[[str], bool] | None = None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            self.uid,
            medicinal_product_uid_by_property_value_callback=concept_exists_by_callback,
            ct_term_exists_callback=ct_term_exists_callback,
            numeric_value_exists_callback=numeric_value_exists_callback,
            compound_exists_callback=compound_exists_callback,
            pharmaceutical_product_exists_callback=pharmaceutical_product_exists_callback,
        )

        if DeepDiff(self._concept_vo, concept_vo, ignore_order=True):
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo
