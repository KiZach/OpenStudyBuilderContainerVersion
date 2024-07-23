from dataclasses import dataclass
from datetime import datetime
from typing import AbstractSet, Callable, Self

from clinical_mdr_api import exceptions
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import (
    CTTermCodelistVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
    ObjectAction,
)


@dataclass(frozen=True)
class CTTermAttributesVO:
    """
    The CTTermAttributesVO acts as the value object for a single CTTerm attribute
    """

    codelists: list[CTTermCodelistVO] | None
    catalogue_name: str
    concept_id: str | None
    code_submission_value: str | None
    name_submission_value: str | None
    preferred_term: str | None
    definition: str | None

    @classmethod
    def from_repository_values(
        cls,
        codelists: list[CTTermCodelistVO],
        catalogue_name: str,
        concept_id: str | None,
        code_submission_value: str | None,
        name_submission_value: str | None,
        preferred_term: str | None,
        definition: str | None,
    ) -> Self:
        ct_term_attributes_vo = cls(
            codelists=codelists,
            catalogue_name=catalogue_name,
            concept_id=concept_id,
            code_submission_value=code_submission_value,
            name_submission_value=name_submission_value,
            preferred_term=preferred_term,
            definition=definition,
        )
        return ct_term_attributes_vo

    @classmethod
    def from_input_values(
        cls,
        codelists: list[CTTermCodelistVO],
        catalogue_name: str,
        code_submission_value: str | None,
        name_submission_value: str | None,
        preferred_term: str | None,
        definition: str | None,
        codelist_exists_callback: Callable[[str], bool],
        catalogue_exists_callback: Callable[[str], bool],
        term_exists_by_name_callback: Callable[[str], bool] = lambda _: False,
        term_exists_by_code_submission_value_callback: Callable[
            [str], bool
        ] = lambda _: False,
    ) -> Self:
        for codelist in codelists:
            if not codelist_exists_callback(codelist.codelist_uid):
                raise exceptions.ValidationException(
                    f"There is no codelist identified by provided codelist uid ({codelist.codelist_uid})"
                )
        if not catalogue_exists_callback(catalogue_name):
            raise exceptions.ValidationException(
                f"There is no catalogue identified by provided catalogue name ({catalogue_name})"
            )
        if term_exists_by_name_callback(name_submission_value):
            raise exceptions.ValidationException(
                f"CTTermAttributes with name ({name_submission_value}) already exists"
            )
        if term_exists_by_code_submission_value_callback(code_submission_value):
            raise exceptions.ValidationException(
                f"CTTermAttributes with code_submission_value ({code_submission_value}) already exists"
            )

        ct_term_attribute_vo = cls(
            codelists=codelists,
            catalogue_name=catalogue_name,
            concept_id=None,
            code_submission_value=code_submission_value,
            name_submission_value=name_submission_value,
            preferred_term=preferred_term,
            definition=definition,
        )
        return ct_term_attribute_vo


@dataclass
class CTTermAttributesAR(LibraryItemAggregateRootBase):
    _ct_term_attributes_vo: CTTermAttributesVO

    @property
    def name(self) -> str:
        return self._ct_term_attributes_vo.name_submission_value

    @property
    def ct_term_vo(self) -> CTTermAttributesVO:
        return self._ct_term_attributes_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        ct_term_attributes_vo: CTTermAttributesVO,
        library: LibraryVO | None,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        ct_term_ar = cls(
            _uid=uid,
            _ct_term_attributes_vo=ct_term_attributes_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return ct_term_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author: str,
        ct_term_attributes_vo: CTTermAttributesVO,
        library: LibraryVO,
        start_date: datetime | None = None,
        generate_uid_callback: Callable[[], str | None] = (lambda: None),
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author=author, start_date=start_date
        )
        if not library.is_editable:
            raise exceptions.BusinessLogicException(
                f"The library with the name='{library.name}' does not allow to create objects."
            )
        return cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _ct_term_attributes_vo=ct_term_attributes_vo,
        )

    def edit_draft(
        self,
        author: str,
        change_description: str | None,
        ct_term_vo: CTTermAttributesVO,
        term_exists_by_name_callback: Callable[[str], bool],
        term_exists_by_code_submission_value_callback: Callable[[str], bool],
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        if (
            term_exists_by_name_callback(ct_term_vo.name_submission_value)
            and self.ct_term_vo.name_submission_value
            != ct_term_vo.name_submission_value
        ):
            raise exceptions.ValidationException(
                f"CTTermAttributes with name ({ct_term_vo.name_submission_value}) already exists."
            )
        if (
            term_exists_by_code_submission_value_callback(
                ct_term_vo.code_submission_value
            )
            and self.ct_term_vo.code_submission_value
            != ct_term_vo.code_submission_value
        ):
            raise exceptions.ValidationException(
                f"CTTermAttributes with code_submission_value ({ct_term_vo.code_submission_value}) already exists."
            )
        if self._ct_term_attributes_vo != ct_term_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._ct_term_attributes_vo = ct_term_vo

    def create_new_version(self, author: str) -> None:
        """
        Puts object into DRAFT status with relevant changes to version numbers.
        """
        super()._create_new_version(author=author)

    def get_possible_actions(self) -> AbstractSet[ObjectAction]:
        """
        Returns list of possible actions
        """
        if self.library.is_editable:
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
