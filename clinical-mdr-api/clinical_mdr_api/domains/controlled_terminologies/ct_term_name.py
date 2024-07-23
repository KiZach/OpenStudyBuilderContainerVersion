from dataclasses import dataclass
from datetime import datetime
from typing import AbstractSet, Callable, Self

from clinical_mdr_api import exceptions
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
    ObjectAction,
)


@dataclass(frozen=True)
class CTTermCodelistVO:
    codelist_uid: str
    order: int | None


@dataclass(frozen=True)
class CTTermNameVO:
    """
    The CTTermNameVO acts as the value object for a single CTTerm name
    """

    name: str | None
    name_sentence_case: str | None
    catalogue_name: str
    codelists: list[CTTermCodelistVO] | None

    @classmethod
    def from_repository_values(
        cls,
        codelists: list[CTTermCodelistVO],
        name: str | None,
        name_sentence_case: str | None,
        catalogue_name: str,
    ) -> Self:
        ct_term_name_vo = cls(
            codelists=codelists,
            catalogue_name=catalogue_name,
            name=name,
            name_sentence_case=name_sentence_case,
        )

        return ct_term_name_vo

    @classmethod
    def from_input_values(
        cls,
        codelists: list[CTTermCodelistVO],
        name: str | None,
        name_sentence_case: str | None,
        catalogue_name: str,
        codelist_exists_callback: Callable[[str], bool],
        catalogue_exists_callback: Callable[[str], bool],
        term_exists_by_name_in_codelists_callback: Callable[
            [str, list[str]], bool
        ] = lambda x, y: False,
    ) -> Self:
        for codelist in codelists:
            if not codelist_exists_callback(codelist.codelist_uid):
                raise exceptions.ValidationException(
                    f"There is no codelist identified by provided codelist uid ({ codelist.codelist_uid})"
                )
        if not catalogue_exists_callback(catalogue_name):
            raise exceptions.ValidationException(
                f"There is no catalogue identified by provided catalogue name ({catalogue_name})"
            )

        if term_exists_by_name_in_codelists_callback(
            name, [codelist.codelist_uid for codelist in codelists]
        ):
            raise exceptions.ValidationException(
                f"CTTermName with name ({name}) already exists"
            )
        ct_term_name_vo = cls(
            codelists=codelists,
            catalogue_name=catalogue_name,
            name=name,
            name_sentence_case=name_sentence_case,
        )

        return ct_term_name_vo


@dataclass
class CTTermNameAR(LibraryItemAggregateRootBase):
    _ct_term_name_vo: CTTermNameVO

    @property
    def name(self) -> str:
        return self._ct_term_name_vo.name

    @property
    def ct_term_vo(self) -> CTTermNameVO:
        return self._ct_term_name_vo

    def _is_edit_allowed_in_non_editable_library(self) -> bool:
        return True

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        ct_term_name_vo: CTTermNameVO,
        library: LibraryVO | None,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        ct_term_ar = cls(
            _uid=uid,
            _ct_term_name_vo=ct_term_name_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return ct_term_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author: str,
        ct_term_name_vo: CTTermNameVO,
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
            _ct_term_name_vo=ct_term_name_vo,
        )

    def edit_draft(
        self,
        author: str,
        change_description: str | None,
        ct_term_vo: CTTermNameVO,
        term_exists_by_name_in_codelists_callback: Callable[[str, list[str]], bool],
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        if (
            term_exists_by_name_in_codelists_callback(
                ct_term_vo.name,
                [codelist.codelist_uid for codelist in self.ct_term_vo.codelists],
            )
            and self.ct_term_vo.name != ct_term_vo.name
        ):
            raise exceptions.ValidationException(
                f"CTTermName with name ({ct_term_vo.name}) already exists."
            )
        if self._ct_term_name_vo != ct_term_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._ct_term_name_vo = ct_term_vo

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

    def set_new_order(self, codelist_uid: str, new_order: int) -> None:
        ct_term_vo = CTTermNameVO.from_input_values(
            codelists=[CTTermCodelistVO(codelist_uid=codelist_uid, order=new_order)],
            catalogue_name=self.ct_term_vo.catalogue_name,
            name=self.name,
            name_sentence_case=self.ct_term_vo.name_sentence_case,
            # passing always True callbacks, as we can't change catalogue
            # in scope of CTTermName or CTTermAttributes, it can be only changed via CTTermRoot
            codelist_exists_callback=lambda _: True,
            catalogue_exists_callback=lambda _: True,
        )
        self._ct_term_name_vo = ct_term_vo
