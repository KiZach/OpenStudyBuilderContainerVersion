from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api import exceptions
from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase, ConceptVO
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)


@dataclass(frozen=True)
class ActivityGroupVO(ConceptVO):
    """
    The ActivityGroupVO acts as the value object for a single ActivityGroup aggregate
    """

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        name_sentence_case: str | None,
        definition: str | None,
        abbreviation: str | None,
    ) -> Self:
        activity_group_vo = cls(
            name=name,
            name_sentence_case=name_sentence_case,
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=True,
        )

        return activity_group_vo

    def validate(
        self,
        concept_exists_by_callback: Callable[[str, str, bool], bool],
        previous_name: str | None = None,
    ) -> None:
        self.validate_name_sentence_case()
        self.duplication_check(
            [("name", self.name, previous_name)],
            concept_exists_by_callback,
            "Activity Group",
        )


@dataclass
class ActivityGroupAR(ConceptARBase):
    _concept_vo: ActivityGroupVO

    @property
    def concept_vo(self) -> ActivityGroupVO:
        return self._concept_vo

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @classmethod
    def from_input_values(
        cls,
        author: str,
        concept_vo: ActivityGroupVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str | None] = (lambda: None),
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)

        if not library.is_editable:
            raise exceptions.BusinessLogicException(
                f"The library with the name='{library.name}' does not allow to create objects."
            )

        concept_vo.validate(
            concept_exists_by_callback=concept_exists_by_callback,
        )

        activity_group_ar = cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return activity_group_ar

    def edit_draft(
        self,
        author: str,
        change_description: str | None,
        concept_vo: ActivityGroupVO,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            concept_exists_by_callback=concept_exists_by_callback,
            previous_name=self.name,
        )

        if self._concept_vo != concept_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo
