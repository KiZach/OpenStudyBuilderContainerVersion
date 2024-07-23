from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api import exceptions
from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase, ConceptVO
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)


@dataclass(frozen=True)
class CompoundAliasVO(ConceptVO):
    """
    The CompoundAliasVO acts as the single value object for CompoundAliasAR aggregate.
    """

    compound_uid: str
    is_preferred_synonym: bool = False

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        name_sentence_case: str | None,
        definition: str | None,
        abbreviation: str | None,
        is_preferred_synonym: bool,
        compound_uid: str,
    ) -> Self:
        compound_alias_vo = cls(
            name=name,
            name_sentence_case=name_sentence_case,
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=True,
            is_preferred_synonym=is_preferred_synonym,
            compound_uid=compound_uid,
        )

        return compound_alias_vo

    def validate(
        self,
        uid: str | None,
        compound_exists_callback: Callable[[str], bool],
        compound_alias_uid_by_property_value_callback: Callable[[str, str], str],
        compound_existing_preferred_synonyms_callback: Callable[[str], list[str]],
    ):
        self.validate_uniqueness(
            lookup_callback=compound_alias_uid_by_property_value_callback,
            uid=uid,
            property_name="name",
            value=self.name,
            error_message=f"Compound alias with name ({self.name}) already exists",
        )

        self.validate_uniqueness(
            lookup_callback=compound_alias_uid_by_property_value_callback,
            uid=uid,
            property_name="name_sentence_case",
            value=self.name_sentence_case,
            error_message=f"Compound alias with name sentence case ({self.name_sentence_case}) already exists",
        )

        self.validate_uniqueness(
            lookup_callback=compound_alias_uid_by_property_value_callback,
            uid=uid,
            property_name="abbreviation",
            value=self.abbreviation,
            error_message=f"Compound alias with abbreviation ({self.abbreviation}) already exists",
        )

        if not compound_exists_callback(self.compound_uid):
            raise exceptions.ValidationException(
                f"{type(self).__name__} tried to connect to non-existent compound identified by uid ({self.compound_uid})"
            )

        if self.is_preferred_synonym:
            existing_preferred_synonyms = compound_existing_preferred_synonyms_callback(
                self.compound_uid
            )
            if existing_preferred_synonyms and existing_preferred_synonyms != [uid]:
                raise exceptions.ValidationException(
                    f"Preferred synonym(s) already defined for compound with uid '{self.compound_uid}'"
                )


class CompoundAliasAR(ConceptARBase):
    _concept_vo: CompoundAliasVO

    @property
    def concept_vo(self) -> CompoundAliasVO:
        return self._concept_vo

    @property
    def name(self) -> str:
        return self.concept_vo.name

    @classmethod
    def from_input_values(
        cls,
        author: str,
        concept_vo: CompoundAliasVO,
        library: LibraryVO,
        compound_alias_uid_by_property_value_callback: Callable[[str, str], str],
        compound_exists_callback: Callable[[str], bool],
        compound_existing_preferred_synonyms_callback: Callable[[str], list[str]],
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
            compound_alias_uid_by_property_value_callback=compound_alias_uid_by_property_value_callback,
            compound_exists_callback=compound_exists_callback,
            compound_existing_preferred_synonyms_callback=compound_existing_preferred_synonyms_callback,
        )

        compound_alias_ar = cls(
            _uid=uid,
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return compound_alias_ar

    def edit_draft(
        self,
        author: str,
        change_description: str | None,
        concept_vo: CompoundAliasVO,
        concept_exists_by_callback: Callable[[str, str, bool], bool] | None = None,
        compound_existing_preferred_synonyms_callback: Callable[[str], list[str]]
        | None = None,
        compound_exists_callback: Callable[[str], bool] | None = None,
        compound_alias_uid_by_property_value_callback: Callable[[str, str], str]
        | None = None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            self.uid,
            compound_alias_uid_by_property_value_callback=compound_alias_uid_by_property_value_callback,
            compound_exists_callback=compound_exists_callback,
            compound_existing_preferred_synonyms_callback=compound_existing_preferred_synonyms_callback,
        )

        if self._concept_vo != concept_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo
