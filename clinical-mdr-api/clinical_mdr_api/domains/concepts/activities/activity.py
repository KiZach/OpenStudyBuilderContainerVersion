from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api.domains.concepts.concept_base import (
    ConceptARBase,
    ConceptVO,
    _ConceptVOType,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.exceptions import BusinessLogicException


@dataclass(frozen=True)
class ActivityGroupingVO:
    activity_subgroup_uid: str
    activity_group_uid: str


@dataclass(frozen=True)
class ActivityVO(ConceptVO):
    """
    The ActivityVO acts as the value object for a single Activity aggregate
    """

    nci_concept_id: str | None
    activity_groupings: list[ActivityGroupingVO]

    # ActivityRequest related
    request_rationale: str | None
    replaced_by_activity: str | None
    requester_study_id: str | None
    reason_for_rejecting: str | None
    contact_person: str | None
    is_request_final: bool = False
    is_request_rejected: bool = False
    # ActivityRequest related

    is_data_collected: bool = False
    is_multiple_selection_allowed: bool = True
    is_finalized: bool = False
    is_used_by_legacy_instances: bool = False

    @classmethod
    def from_repository_values(
        cls,
        nci_concept_id: str | None,
        name: str,
        name_sentence_case: str | None,
        definition: str | None,
        abbreviation: str | None,
        activity_groupings: list[ActivityGroupingVO],
        request_rationale: str | None,
        is_request_final: bool = False,
        replaced_by_activity: str | None = None,
        requester_study_id: str | None = None,
        reason_for_rejecting: str | None = None,
        contact_person: str | None = None,
        is_request_rejected: bool = False,
        is_data_collected: bool = False,
        is_multiple_selection_allowed: bool = True,
        is_finalized: bool = False,
        is_used_by_legacy_instances: bool = False,
    ) -> Self:
        activity_vo = cls(
            nci_concept_id=nci_concept_id,
            name=name,
            name_sentence_case=name_sentence_case,
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=True,
            activity_groupings=activity_groupings,
            request_rationale=request_rationale,
            is_request_final=is_request_final,
            requester_study_id=requester_study_id,
            replaced_by_activity=replaced_by_activity,
            reason_for_rejecting=reason_for_rejecting,
            contact_person=contact_person,
            is_request_rejected=is_request_rejected,
            is_data_collected=is_data_collected,
            is_multiple_selection_allowed=is_multiple_selection_allowed,
            is_finalized=is_finalized,
            is_used_by_legacy_instances=is_used_by_legacy_instances,
        )

        return activity_vo

    def validate(
        self,
        activity_exists_by_name_callback: Callable[[str, str], bool],
        activity_subgroup_exists: Callable[[str], bool],
        activity_group_exists: Callable[[str], bool],
        previous_name: str | None = None,
        library_name: str | None = None,
    ) -> None:
        self.validate_name_sentence_case()
        ex = activity_exists_by_name_callback(library_name, self.name)
        if ex and previous_name != self.name:
            raise BusinessLogicException(
                f"Activity with ['name: {self.name}'] already exists."
            )
        for activity_grouping in self.activity_groupings:
            if not activity_subgroup_exists(activity_grouping.activity_subgroup_uid):
                raise BusinessLogicException(
                    "Activity tried to connect to non-existent or non-final concepts "
                    f"""[('Concept Name: Activity Subgroup', "uids: {{'{activity_grouping.activity_subgroup_uid}'}}")]."""
                )
            if not activity_group_exists(activity_grouping.activity_group_uid):
                raise BusinessLogicException(
                    "Activity tried to connect to non-existent or non-final concepts "
                    f"""[('Concept Name: Activity Group', "uids: {{'{activity_grouping.activity_group_uid}'}}")]."""
                )


@dataclass
class ActivityAR(ConceptARBase):
    _concept_vo: ActivityVO

    @property
    def concept_vo(self) -> _ConceptVOType:
        return self._concept_vo

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @classmethod
    def from_input_values(
        cls,
        author: str,
        concept_vo: ActivityVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str | None] = (lambda: None),
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        concept_exists_by_library_and_name_callback: Callable[
            [str, str], bool
        ] = lambda _: True,
        activity_subgroup_exists: Callable[[str], bool] = lambda _: False,
        activity_group_exists: Callable[[str], bool] = lambda _: False,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)

        if not library.is_editable:
            raise BusinessLogicException(
                f"The library with the name='{library.name}' does not allow to create objects."
            )
        concept_vo.validate(
            activity_exists_by_name_callback=concept_exists_by_library_and_name_callback,
            activity_subgroup_exists=activity_subgroup_exists,
            activity_group_exists=activity_group_exists,
            library_name=library.name,
        )

        activity_ar = cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return activity_ar

    def edit_draft(
        self,
        author: str,
        change_description: str | None,
        concept_vo: ActivityVO,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        concept_exists_by_library_and_name_callback: Callable[
            [str, str], bool
        ] = lambda x, y, z: True,
        activity_subgroup_exists: Callable[[str], bool] | None = None,
        activity_group_exists: Callable[[str], bool] = lambda _: False,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            activity_exists_by_name_callback=concept_exists_by_library_and_name_callback,
            activity_subgroup_exists=activity_subgroup_exists,
            activity_group_exists=activity_group_exists,
            previous_name=self.name,
            library_name=self.library.name,
        )
        if self._concept_vo != concept_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo
