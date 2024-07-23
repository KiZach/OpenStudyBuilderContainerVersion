from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api import exceptions
from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase, ConceptVO
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.exceptions import BusinessLogicException


@dataclass(frozen=True)
class ActivitySubGroupVO(ConceptVO):
    """
    The ActivitySubGroupVO acts as the value object for a single ActivitySubGroup aggregate
    """

    activity_groups: list[str]

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        name_sentence_case: str | None,
        definition: str | None,
        abbreviation: str | None,
        activity_groups: list[str],
    ) -> Self:
        activity_subgroup_vo = cls(
            name=name,
            name_sentence_case=name_sentence_case,
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=True,
            activity_groups=activity_groups,
        )

        return activity_subgroup_vo

    def validate(
        self,
        concept_exists_by_callback: Callable[[str, str, bool], bool],
        activity_group_exists: Callable[[str], bool],
        previous_name: str | None = None,
    ):
        self.validate_name_sentence_case()
        self.duplication_check(
            [("name", self.name, previous_name)],
            concept_exists_by_callback,
            "Activity Subgroup",
        )
        for activity_group in self.activity_groups:
            if not activity_group_exists(activity_group):
                raise BusinessLogicException(
                    "Activity Subgroup tried to connect to non-existent or non-final concepts "
                    f"""[('Concept Name: Activity Group', "uids: {{'{activity_group}'}}")]."""
                )


@dataclass
class ActivitySubGroupAR(ConceptARBase):
    _concept_vo: ActivitySubGroupVO

    @property
    def concept_vo(self) -> ActivitySubGroupVO:
        return self._concept_vo

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @classmethod
    def from_input_values(
        cls,
        author: str,
        concept_vo: ActivitySubGroupVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str | None] = (lambda: None),
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        activity_group_exists: Callable[[str], bool] = lambda _: False,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)

        if not library.is_editable:
            raise exceptions.BusinessLogicException(
                f"The library with the name='{library.name}' does not allow to create objects."
            )

        concept_vo.validate(
            concept_exists_by_callback=concept_exists_by_callback,
            activity_group_exists=activity_group_exists,
        )

        activity_subgroup_ar = cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return activity_subgroup_ar

    def edit_draft(
        self,
        author: str,
        change_description: str | None,
        concept_vo: ActivitySubGroupVO,
        concept_exists_by_callback: Callable[[str, str, bool], bool] | None = None,
        activity_group_exists: Callable[[str], bool] | None = None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            concept_exists_by_callback=concept_exists_by_callback,
            activity_group_exists=activity_group_exists,
            previous_name=self.name,
        )
        if self._concept_vo != concept_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo
