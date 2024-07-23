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
class IngredientVO:
    active_substance_uid: str
    external_id: str | None = None
    strength_uid: str | None = None
    half_life_uid: str | None = None
    lag_time_uids: list[str] | None = None

    @classmethod
    def from_repository_values(
        cls,
        active_substance_uid: str,
        external_id: str | None,
        strength_uid: str | None = None,
        half_life_uid: str | None = None,
        lag_time_uids: list[str] | None = None,
    ) -> Self:
        ingredient_vo = cls(
            external_id=external_id,
            active_substance_uid=active_substance_uid,
            strength_uid=strength_uid,
            half_life_uid=half_life_uid,
            lag_time_uids=lag_time_uids,
        )

        return ingredient_vo

    def validate(
        self,
        numeric_value_exists_callback: Callable[[str], bool],
        lag_time_exists_callback: Callable[[str], bool],
        active_substance_exists_callback: Callable[[str], bool],
    ):
        if not active_substance_exists_callback(self.active_substance_uid):
            raise exceptions.ValidationException(
                f"{type(self).__name__} tried to connect to non-existent active substance identified by uid ({self.active_substance_uid})"
            )

        if self.strength_uid:
            if not numeric_value_exists_callback(self.strength_uid):
                raise exceptions.ValidationException(
                    f"{type(self).__name__} tried to connect to non-existent strength value identified by uid ({self.strength_uid})"
                )

        if self.half_life_uid:
            if not numeric_value_exists_callback(self.half_life_uid):
                raise exceptions.ValidationException(
                    f"{type(self).__name__} tried to connect to non-existent half-life value identified by uid ({self.half_life_uid})"
                )

        for lag_time_uid in self.lag_time_uids:
            if not lag_time_exists_callback(lag_time_uid):
                raise exceptions.ValidationException(
                    f"{type(self).__name__} tried to connect to non-existent lag-time identified by uid ({lag_time_uid})"
                )


@dataclass(frozen=True)
class FormulationVO:
    name: str
    external_id: str | None = None
    ingredients: list[IngredientVO] | None = None

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        external_id: str | None,
        ingredients: list[IngredientVO] = None,
    ) -> Self:
        formulation_vo = cls(
            external_id=external_id,
            name=name,
            ingredients=ingredients if ingredients else [],
        )

        return formulation_vo

    def validate(
        self,
        numeric_value_exists_callback: Callable[[str], bool],
        lag_time_exists_callback: Callable[[str], bool],
        active_substance_exists_callback: Callable[[str], bool],
    ):
        for ingredient in self.ingredients:
            ingredient.validate(
                numeric_value_exists_callback=numeric_value_exists_callback,
                lag_time_exists_callback=lag_time_exists_callback,
                active_substance_exists_callback=active_substance_exists_callback,
            )


@dataclass(frozen=True)
class PharmaceuticalProductVO(ConceptVO):
    """
    The PharmaceuticalProductVO acts as the single value object for PharmaceuticalProductAR aggregate.
    """

    external_id: str | None
    dosage_form_uids: list[str] | None
    route_of_administration_uids: list[str] | None
    formulations: list[FormulationVO] | None

    @classmethod
    def from_repository_values(
        cls,
        external_id: str | None,
        dosage_form_uids: list[str] | None,
        route_of_administration_uids: list[str] | None,
        formulations: list[FormulationVO] | None,
    ) -> Self:
        pharmaceutical_product_vo = cls(
            external_id=external_id,
            dosage_form_uids=dosage_form_uids,
            route_of_administration_uids=route_of_administration_uids,
            formulations=formulations,
            name="",
            name_sentence_case="",
            definition="",
            abbreviation="",
            is_template_parameter=False,
        )

        return pharmaceutical_product_vo

    def validate(
        self,
        uid: str | None,
        pharmaceutical_product_uid_by_property_value_callback: Callable[
            [str, str], str
        ],
        ct_term_exists_callback: Callable[[str], bool],
        numeric_value_exists_callback: Callable[[str], bool],
        lag_time_exists_callback: Callable[[str], bool],
        active_substance_exists_callback: Callable[[str], bool],
    ):
        self.validate_uniqueness(
            lookup_callback=pharmaceutical_product_uid_by_property_value_callback,
            uid=uid,
            property_name="external_id",
            value=self.external_id,
            error_message=f"PharmaceuticalProduct with external_id ({self.external_id}) already exists",
        )

        for dosage_form_uid in self.dosage_form_uids:
            if not ct_term_exists_callback(dosage_form_uid):
                raise exceptions.ValidationException(
                    f"{type(self).__name__} tried to connect to non-existent or non-final dosage form identified by uid ({dosage_form_uid})"
                )

        for route_of_administration_uid in self.route_of_administration_uids:
            if not ct_term_exists_callback(route_of_administration_uid):
                raise exceptions.ValidationException(
                    f"{type(self).__name__} tried to connect to non-existent or non-final "
                    f"route of administration identified by uid ({route_of_administration_uid})"
                )
        for formulation in self.formulations:
            formulation.validate(
                numeric_value_exists_callback=numeric_value_exists_callback,
                lag_time_exists_callback=lag_time_exists_callback,
                active_substance_exists_callback=active_substance_exists_callback,
            )


class PharmaceuticalProductAR(ConceptARBase):
    _external_id: str | None
    _concept_vo: PharmaceuticalProductVO

    @property
    def concept_vo(self) -> PharmaceuticalProductVO:
        return self._concept_vo

    @property
    def name(self) -> str:
        return self.concept_vo.name

    @classmethod
    def from_input_values(
        cls,
        author: str,
        concept_vo: PharmaceuticalProductVO,
        library: LibraryVO,
        pharmaceutical_product_uid_by_property_value_callback: Callable[
            [str, str], str
        ],
        ct_term_exists_callback: Callable[[str], bool],
        numeric_value_exists_callback: Callable[[str], bool],
        lag_time_exists_callback: Callable[[str], bool],
        active_substance_exists_callback: Callable[[str], bool],
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
            pharmaceutical_product_uid_by_property_value_callback=pharmaceutical_product_uid_by_property_value_callback,
            ct_term_exists_callback=ct_term_exists_callback,
            numeric_value_exists_callback=numeric_value_exists_callback,
            lag_time_exists_callback=lag_time_exists_callback,
            active_substance_exists_callback=active_substance_exists_callback,
        )

        pharmaceutical_product_ar = cls(
            _uid=uid,
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return pharmaceutical_product_ar

    def edit_draft(
        self,
        author: str,
        change_description: str | None,
        concept_vo: PharmaceuticalProductVO,
        concept_exists_by_callback: Callable[[str, str], str] | None = None,
        ct_term_exists_callback: Callable[[str], bool] | None = None,
        numeric_value_exists_callback: Callable[[str], bool] | None = None,
        lag_time_exists_callback: Callable[[str], bool] | None = None,
        active_substance_exists_callback: Callable[[str], bool] | None = None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            self.uid,
            pharmaceutical_product_uid_by_property_value_callback=concept_exists_by_callback,
            ct_term_exists_callback=ct_term_exists_callback,
            numeric_value_exists_callback=numeric_value_exists_callback,
            lag_time_exists_callback=lag_time_exists_callback,
            active_substance_exists_callback=active_substance_exists_callback,
        )

        if DeepDiff(self._concept_vo, concept_vo, ignore_order=True):
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo
