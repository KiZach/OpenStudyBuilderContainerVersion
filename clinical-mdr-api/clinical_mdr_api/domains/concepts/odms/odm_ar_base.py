from dataclasses import dataclass
from typing import AbstractSet

from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    ObjectAction,
    VersioningException,
)


@dataclass
class OdmARBase(ConceptARBase):
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
            return {ObjectAction.REACTIVATE, ObjectAction.DELETE}
        return frozenset()

    def soft_delete(self) -> None:
        if (
            self._item_metadata.major_version == 0
            or self._item_metadata.status == LibraryItemStatus.RETIRED
        ):
            self._is_deleted = True
        else:
            raise VersioningException("Object has been accepted or is not retired")
