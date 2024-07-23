from dataclasses import dataclass, field
from typing import AbstractSet, Any, Callable, Self

from clinical_mdr_api import exceptions
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
    ObjectAction,
)


@dataclass(frozen=True)
class DictionaryTermVO:
    """
    The DictionaryTermVO acts as the value object for a single DictionaryTermAR item
    """

    codelist_uid: str
    dictionary_id: str
    name: str
    name_sentence_case: str
    abbreviation: str | None
    definition: str | None

    @classmethod
    def from_repository_values(
        cls,
        codelist_uid: str,
        dictionary_id: str,
        name: str,
        name_sentence_case: str,
        abbreviation: str | None,
        definition: str | None,
    ) -> Self:
        dictionary_term_vo = cls(
            codelist_uid=codelist_uid,
            dictionary_id=dictionary_id,
            name=name,
            name_sentence_case=name_sentence_case,
            abbreviation=abbreviation,
            definition=definition,
        )

        return dictionary_term_vo

    @classmethod
    def from_input_values(
        cls,
        codelist_uid: str,
        dictionary_id: str,
        name: str,
        name_sentence_case: str,
        abbreviation: str | None,
        definition: str | None,
    ) -> Self:
        return cls.from_repository_values(
            codelist_uid=codelist_uid,
            dictionary_id=dictionary_id,
            name=name,
            name_sentence_case=name_sentence_case,
            abbreviation=abbreviation,
            definition=definition,
        )

    def validate(
        self,
        term_exists_by_name_callback: Callable[[str, str], bool],
        previous_name: str | None = None,
    ) -> None:
        if (
            term_exists_by_name_callback(self.name, self.codelist_uid)
            and self.name != previous_name
        ):
            raise exceptions.ValidationException(
                f"DictionaryTerm with name ({self.name}) already exists in DictionaryCodelist identified by ({self.codelist_uid})"
            )
        if self.name_sentence_case.lower() != self.name.lower():
            raise exceptions.ValidationException(
                f"{self.name_sentence_case} is not an independent case version of {self.name}"
            )


@dataclass
class DictionaryTermAR(LibraryItemAggregateRootBase):
    _dictionary_term_vo: DictionaryTermVO
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    @property
    def name(self) -> str:
        return self._dictionary_term_vo.name

    @property
    def dictionary_term_vo(self) -> DictionaryTermVO:
        return self._dictionary_term_vo

    @dictionary_term_vo.setter
    def dictionary_term_vo(self, dictionary_term_vo: DictionaryTermVO):
        self._dictionary_term_vo = dictionary_term_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        dictionary_term_vo: DictionaryTermVO,
        library: LibraryVO | None,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        dictionary_codelist_ar = cls(
            _uid=uid,
            _dictionary_term_vo=dictionary_term_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return dictionary_codelist_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author: str,
        dictionary_term_vo: DictionaryTermVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str | None] = (lambda: None),
        term_exists_by_name_callback: Callable[[str, str], bool],
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)
        if not library.is_editable:
            raise exceptions.BusinessLogicException(
                f"The library with the name='{library.name}' does not allow to create objects."
            )

        dictionary_term_vo.validate(
            term_exists_by_name_callback=term_exists_by_name_callback
        )

        return cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _dictionary_term_vo=dictionary_term_vo,
        )

    def edit_draft(
        self,
        author: str,
        change_description: str | None,
        dictionary_term_vo: DictionaryTermVO,
        term_exists_by_name_callback: Callable[[str, str], bool],
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        dictionary_term_vo.validate(
            term_exists_by_name_callback=term_exists_by_name_callback,
            previous_name=self.name,
        )
        if self._dictionary_term_vo != dictionary_term_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self.dictionary_term_vo = dictionary_term_vo

    def create_new_version(self, author: str) -> None:
        """
        Puts object into DRAFT status with relevant changes to version numbers.
        """
        super()._create_new_version(author=author)

    def get_possible_actions(self) -> AbstractSet[ObjectAction]:
        """
        Returns list of possible actions
        """
        if (
            self._item_metadata.status == LibraryItemStatus.DRAFT
            and self._item_metadata.major_version == 0
        ):
            return {ObjectAction.APPROVE, ObjectAction.EDIT, ObjectAction.DELETE}
        if self._item_metadata.status == LibraryItemStatus.DRAFT:
            return {ObjectAction.APPROVE, ObjectAction.EDIT}
        if self._item_metadata.status == LibraryItemStatus.FINAL:
            return {ObjectAction.NEWVERSION, ObjectAction.INACTIVATE}
        if self._item_metadata.status == LibraryItemStatus.RETIRED:
            return {ObjectAction.REACTIVATE}
        return frozenset()
