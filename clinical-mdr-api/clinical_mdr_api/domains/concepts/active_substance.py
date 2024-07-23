from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api import exceptions
from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase, ConceptVO
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)


@dataclass(frozen=True)
class ActiveSubstanceVO(ConceptVO):
    """
    The ActiveSubstanceVO acts as the single value object for ActiveSubstanceAR aggregate.
    """

    analyte_number: str | None
    short_number: str | None
    long_number: str | None
    inn: str | None
    external_id: str | None
    unii_term_uid: str | None

    @classmethod
    def from_repository_values(
        cls,
        analyte_number: str | None,
        short_number: str | None,
        long_number: str | None,
        inn: str | None,
        external_id: str | None,
        unii_term_uid: str | None,
    ) -> Self:
        active_substance_vo = cls(
            analyte_number=analyte_number,
            short_number=short_number,
            long_number=long_number,
            inn=inn,
            external_id=external_id,
            unii_term_uid=unii_term_uid,
            name="",
            name_sentence_case="",
            definition="",
            abbreviation="",
            is_template_parameter=False,
        )

        return active_substance_vo

    def validate(
        self,
        uid: str | None,
        active_substance_uid_by_property_value_callback: Callable[[str, str], str],
        dictionary_term_exists_callback: Callable[[str], bool],
    ):
        self.validate_uniqueness(
            lookup_callback=active_substance_uid_by_property_value_callback,
            uid=uid,
            property_name="analyte_number",
            value=self.analyte_number,
            error_message=f"ActiveSubstance with analyte number ({self.analyte_number}) already exists",
        )

        self.validate_uniqueness(
            lookup_callback=active_substance_uid_by_property_value_callback,
            uid=uid,
            property_name="short_number",
            value=self.short_number,
            error_message=f"ActiveSubstance with short number ({self.short_number}) already exists",
        )

        self.validate_uniqueness(
            lookup_callback=active_substance_uid_by_property_value_callback,
            uid=uid,
            property_name="long_number",
            value=self.long_number,
            error_message=f"ActiveSubstance with long number ({self.long_number}) already exists",
        )

        self.validate_uniqueness(
            lookup_callback=active_substance_uid_by_property_value_callback,
            uid=uid,
            property_name="external_id",
            value=self.external_id,
            error_message=f"ActiveSubstance with external_id ({self.external_id}) already exists",
        )

        if self.unii_term_uid and not dictionary_term_exists_callback(
            self.unii_term_uid
        ):
            raise exceptions.ValidationException(
                f"{type(self).__name__} tried to connect to non existing UNII term identified by uid ({self.unii_term_uid})"
            )


class ActiveSubstanceAR(ConceptARBase):
    _external_id: str | None
    _concept_vo: ActiveSubstanceVO

    @property
    def concept_vo(self) -> ActiveSubstanceVO:
        return self._concept_vo

    @property
    def name(self) -> str:
        return self.concept_vo.name

    @classmethod
    def from_input_values(
        cls,
        author: str,
        concept_vo: ActiveSubstanceVO,
        library: LibraryVO,
        active_substance_uid_by_property_value_callback: Callable[[str, str], str],
        dictionary_term_exists_callback: Callable[[str], bool],
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
            active_substance_uid_by_property_value_callback=active_substance_uid_by_property_value_callback,
            dictionary_term_exists_callback=dictionary_term_exists_callback,
        )

        active_substance_ar = cls(
            _uid=uid,
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return active_substance_ar

    def edit_draft(
        self,
        author: str,
        change_description: str | None,
        concept_vo: ActiveSubstanceVO,
        concept_exists_by_callback: Callable[[str, str], str] | None = None,
        dictionary_term_exists_callback: Callable[[str], bool] | None = None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            self.uid,
            active_substance_uid_by_property_value_callback=concept_exists_by_callback,
            dictionary_term_exists_callback=dictionary_term_exists_callback,
        )

        if self._concept_vo != concept_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo
