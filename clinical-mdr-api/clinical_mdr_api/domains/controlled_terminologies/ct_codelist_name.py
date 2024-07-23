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
class CTCodelistNameVO:
    """
    The CTCodelistNameVO acts as the value object for a single CTCodelist name
    """

    name: str | None
    catalogue_name: str
    is_template_parameter: bool | None

    @classmethod
    def from_repository_values(
        cls,
        name: str | None,
        catalogue_name: str,
        is_template_parameter: bool | None,
    ) -> Self:
        ct_codelist_name_vo = cls(
            name=name,
            catalogue_name=catalogue_name,
            is_template_parameter=is_template_parameter,
        )

        return ct_codelist_name_vo

    @classmethod
    def from_input_values(
        cls,
        name: str | None,
        catalogue_name: str,
        is_template_parameter: bool | None,
        catalogue_exists_callback: Callable[[str], bool],
        codelist_exists_by_name_callback: Callable[[str], bool] = lambda _: False,
    ) -> Self:
        if not catalogue_exists_callback(catalogue_name):
            raise exceptions.ValidationException(
                f"There is no catalogue identified by provided catalogue name ({catalogue_name})"
            )
        if codelist_exists_by_name_callback(name):
            raise exceptions.ValidationException(
                f"CTCodelistName with name ({name}) already exists"
            )

        ct_codelist_name_vo = cls(
            name=name,
            catalogue_name=catalogue_name,
            is_template_parameter=is_template_parameter,
        )

        return ct_codelist_name_vo


@dataclass
class CTCodelistNameAR(LibraryItemAggregateRootBase):
    _ct_codelist_name_vo: CTCodelistNameVO

    @property
    def name(self) -> str:
        return self._ct_codelist_name_vo.name

    @property
    def ct_codelist_vo(self) -> CTCodelistNameVO:
        return self._ct_codelist_name_vo

    def _is_edit_allowed_in_non_editable_library(self) -> bool:
        return True

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        ct_codelist_name_vo: CTCodelistNameVO,
        library: LibraryVO | None,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        ct_codelist_ar = cls(
            _uid=uid,
            _ct_codelist_name_vo=ct_codelist_name_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return ct_codelist_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author: str,
        ct_codelist_name_vo: CTCodelistNameVO,
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
            _ct_codelist_name_vo=ct_codelist_name_vo,
        )

    def edit_draft(
        self,
        author: str,
        change_description: str | None,
        ct_codelist_vo: CTCodelistNameVO,
        codelist_exists_by_name_callback: Callable[[str], bool],
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        if (
            codelist_exists_by_name_callback(ct_codelist_vo.name)
            and self.name != ct_codelist_vo.name
        ):
            raise exceptions.ValidationException(
                f"CTCodelistName with name ({ct_codelist_vo.name}) already exists."
            )
        if self._ct_codelist_name_vo != ct_codelist_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._ct_codelist_name_vo = ct_codelist_vo

    def create_new_version(self, author: str) -> None:
        """
        Puts object into DRAFT status with relevant changes to version numbers.
        """
        super()._create_new_version(author=author)

    def get_possible_actions(self) -> AbstractSet[ObjectAction]:
        """
        Returns list of possible actions
        """
        if self._item_metadata.status == LibraryItemStatus.DRAFT:
            return {ObjectAction.APPROVE, ObjectAction.EDIT}
        if self._item_metadata.status == LibraryItemStatus.FINAL:
            return {ObjectAction.NEWVERSION}
        return frozenset()

    def inactivate(self, author: str, change_description: str | None = None):
        """
        Inactivates latest version.
        """
        raise NotImplementedError()

    def reactivate(self, author: str, change_description: str | None = None):
        """
        Reactivates latest retired version and sets the version to draft.
        """
        raise NotImplementedError()

    def soft_delete(self):
        raise NotImplementedError()
