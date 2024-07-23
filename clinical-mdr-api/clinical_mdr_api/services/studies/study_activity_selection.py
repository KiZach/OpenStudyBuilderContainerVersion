from datetime import datetime
from typing import Callable

from fastapi import status
from neomodel import db

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.config import REQUESTED_LIBRARY_NAME
from clinical_mdr_api.domain_repositories.concepts.activities.activity_repository import (
    ActivityRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_repository import (
    SelectionHistory,
    StudySelectionActivityRepository,
)
from clinical_mdr_api.domains.concepts.activities.activity import (
    ActivityAR,
    ActivityGroupingVO,
    ActivityVO,
)
from clinical_mdr_api.domains.concepts.activities.activity_group import ActivityGroupAR
from clinical_mdr_api.domains.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity import (
    StudySelectionActivityAR,
    StudySelectionActivityVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity_group import (
    StudySelectionActivityGroupVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity_instance import (
    StudySelectionActivityInstanceVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity_subgroup import (
    StudySelectionActivitySubGroupVO,
)
from clinical_mdr_api.domains.study_selections.study_soa_group_selection import (
    StudySoAGroupVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models import DetailedSoAHistory
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    fill_missing_values_in_base_model_from_reference_base_model,
)
from clinical_mdr_api.services.concepts.activities.activity_group_service import (
    ActivityGroupService,
)
from clinical_mdr_api.services.concepts.activities.activity_service import (
    ActivityService,
)
from clinical_mdr_api.services.concepts.activities.activity_sub_group_service import (
    ActivitySubGroupService,
)
from clinical_mdr_api.services.studies.study_activity_instruction import (
    StudyActivityInstructionService,
)
from clinical_mdr_api.services.studies.study_activity_schedule import (
    StudyActivityScheduleService,
)
from clinical_mdr_api.services.studies.study_activity_selection_base import (
    StudyActivitySelectionBaseService,
)


class StudyActivitySelectionService(StudyActivitySelectionBaseService):
    _repos: MetaRepository
    repository_interface = StudySelectionActivityRepository
    selected_object_repository_interface = ActivityRepository

    _vo_to_ar_filter_map = {
        "order": "activity_order",
        "activity.name": "activity_name",
        "study_activity_group.activity_group_name": "activity_group_name",
        "study_activity_subgroup.activity_subgroup_name": "activity_subgroup_name",
        "start_date": "start_date",
        "user_initials": "user_initials",
        "activity.library_name": "activity_library_name",
    }

    def _get_selected_object_exist_check(self) -> Callable[[str], bool]:
        return self.selected_object_repository.final_or_replaced_retired_activity_exists

    def _transform_from_vo_to_response_model(
        self,
        study_uid: str,
        specific_selection: StudySelectionActivityVO,
        order: int,
        terms_at_specific_datetime: datetime | None,
        accepted_version: bool = False,
        study_value_version: str | None = None,
    ) -> models.StudySelectionActivity:
        return models.StudySelectionActivity.from_study_selection_activity_vo_and_order(
            study_uid=study_uid,
            specific_selection=specific_selection,
            activity_order=order,
            accepted_version=accepted_version,
            get_activity_by_uid_callback=self._transform_latest_activity_model,
            get_activity_by_uid_version_callback=self._transform_activity_model,
            get_ct_term_flowchart_group=self._find_by_uid_or_raise_not_found,
            study_value_version=study_value_version,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    def update_study_activities(self, study_uid: str, study_selection_uid: str):
        pass

    def _create_value_object(
        self,
        study_uid: str,
        selection_create_input: models.StudySelectionActivityCreateInput,
        **kwargs,
    ):
        study_soa_group_selection_uid = kwargs.get("study_soa_group_selection_uid")
        study_activity_subgroup_selection_uid = kwargs.get(
            "study_activity_subgroup_selection_uid"
        )
        study_activity_group_selection_uid = kwargs.get(
            "study_activity_group_selection_uid"
        )

        activity_service = ActivityService()
        activity_uid = selection_create_input.activity_uid
        activity_ar = activity_service.repository.find_by_uid_2(
            activity_uid, for_update=True
        )
        if not activity_ar:
            raise exceptions.NotFoundException(
                f"There is no activity identified by provided uid ({activity_uid})"
            )
        if activity_ar.library.name != REQUESTED_LIBRARY_NAME and (
            selection_create_input.activity_subgroup_uid is None
            or selection_create_input.activity_group_uid is None
        ):
            raise exceptions.BusinessLogicException(
                "Only StudyActivity placeholder can link to None ActivitySubGroup or None ActivityGroup"
            )
        if activity_ar.item_metadata.status in [
            LibraryItemStatus.DRAFT,
            LibraryItemStatus.RETIRED,
        ]:
            raise exceptions.BusinessLogicException(
                f"There is no approved activity identified by provided uid ({activity_uid})"
            )
        if (
            selection_create_input.activity_subgroup_uid
            and selection_create_input.activity_subgroup_uid
            not in [
                grouping.activity_subgroup_uid
                for grouping in activity_ar.concept_vo.activity_groupings
            ]
        ):
            raise exceptions.BusinessLogicException(
                f"The specified subgroup ({selection_create_input.activity_subgroup_uid}) is not linked with ({activity_ar.name}) Activity"
            )
        if (
            selection_create_input.activity_group_uid
            and selection_create_input.activity_group_uid
            not in [
                grouping.activity_group_uid
                for grouping in activity_ar.concept_vo.activity_groupings
            ]
        ):
            raise exceptions.BusinessLogicException(
                f"The specified group ({selection_create_input.activity_group_uid}) is not linked with ({activity_ar.name}) Activity"
            )
        # create new VO to add
        new_selection = StudySelectionActivityVO.from_input_values(
            study_uid=study_uid,
            user_initials=self.author,
            activity_uid=activity_uid,
            activity_name=activity_ar.name,
            activity_version=activity_ar.item_metadata.version,
            activity_library_name=activity_ar.library.name,
            soa_group_term_uid=selection_create_input.soa_group_term_uid,
            study_soa_group_uid=study_soa_group_selection_uid,
            study_activity_subgroup_uid=study_activity_subgroup_selection_uid,
            study_activity_group_uid=study_activity_group_selection_uid,
            activity_order=None,
            generate_uid_callback=self.repository.generate_uid,
            activity_subgroup_uid=selection_create_input.activity_subgroup_uid,
            activity_group_uid=selection_create_input.activity_group_uid,
        )
        return new_selection

    def _transform_all_to_response_model(
        self,
        study_selection: StudySelectionActivityAR,
        study_value_version: str | None = None,
    ) -> list[models.StudySelectionActivity]:
        result = []
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_selection.study_uid,
            study_value_version=study_value_version,
        )
        for _, selection in enumerate(study_selection.study_objects_selection, start=1):
            result.append(
                self._transform_from_vo_to_response_model(
                    study_uid=study_selection.study_uid,
                    specific_selection=selection,
                    order=selection.activity_order,
                    accepted_version=selection.accepted_version,
                    study_value_version=study_value_version,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                )
            )
        return result

    def _transform_history_to_response_model(
        self, study_selection_history: list[SelectionHistory], study_uid: str
    ) -> list[models.StudySelectionActivityCore]:
        result = []
        for history in study_selection_history:
            result.append(
                models.StudySelectionActivityCore.from_study_selection_history(
                    study_selection_history=history,
                    study_uid=study_uid,
                    get_activity_by_uid_version_callback=self._transform_activity_model,
                    get_ct_term_flowchart_group=self._find_by_uid_or_raise_not_found,
                )
            )
        return result

    def _create_activity_subgroup_selection_value_object(
        self,
        study_uid: str,
        activity_subgroup_uid: str,
    ):
        activity_subgroup_ar = self._validate_activity_subgroup(
            activity_subgroup_uid=activity_subgroup_uid
        )

        # create new VO to add
        new_selection = StudySelectionActivitySubGroupVO.from_input_values(
            study_uid=study_uid,
            user_initials=self.author,
            activity_subgroup_uid=activity_subgroup_uid,
            activity_subgroup_version=activity_subgroup_ar.item_metadata.version,
            generate_uid_callback=self._repos.study_activity_subgroup_repository.generate_uid,
        )
        return new_selection

    @classmethod
    def _validate_activity_subgroup(
        cls, activity_subgroup_uid: str
    ) -> ActivitySubGroupAR:
        activity_subgroup_service = ActivitySubGroupService()
        activity_subgroup_ar = activity_subgroup_service.repository.find_by_uid_2(
            activity_subgroup_uid, for_update=True
        )
        if not activity_subgroup_uid:
            raise exceptions.NotFoundException(
                f"There is no activity subgroup identified by provided uid ({activity_subgroup_uid})"
            )

        if activity_subgroup_ar.item_metadata.status in [
            LibraryItemStatus.DRAFT,
            LibraryItemStatus.RETIRED,
        ]:
            raise exceptions.BusinessLogicException(
                f"There is no approved activity subgroup identified by provided uid ({activity_subgroup_uid})"
            )
        return activity_subgroup_ar

    def _patch_study_activity_subgroup_selection_value_object(
        self,
        study_uid: str,
        current_study_activity: StudySelectionActivityVO,
        selection_create_input: (
            models.StudySelectionActivityInput
            | models.StudySelectionActivityRequestEditInput
            | models.UpdateActivityPlaceholderToSponsorActivity
        ),
    ):
        selection_aggregate = (
            self._repos.study_activity_subgroup_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )
        )
        assert selection_aggregate is not None
        if current_study_activity.study_activity_subgroup_uid is None:
            new_selection = self._create_activity_subgroup_selection_value_object(
                study_uid=study_uid,
                activity_subgroup_uid=selection_create_input.activity_subgroup_uid,
            )
            selection_aggregate.add_object_selection(
                new_selection,
                self._repos.activity_subgroup_repository.check_exists_final_version,
            )
        else:
            new_selection, _ = selection_aggregate.get_specific_object_selection(
                study_selection_uid=current_study_activity.study_activity_subgroup_uid
            )
            is_activity_subgroup_changed = (
                current_study_activity.activity_subgroup_uid
                != selection_create_input.activity_subgroup_uid
            )
            if is_activity_subgroup_changed:
                activity_subgroup_uid = selection_create_input.activity_subgroup_uid
                activity_subgroup_ar = self._validate_activity_subgroup(
                    activity_subgroup_uid=activity_subgroup_uid
                )
                # create new VO to add
                new_selection = StudySelectionActivitySubGroupVO.from_input_values(
                    study_uid=study_uid,
                    user_initials=self.author,
                    activity_subgroup_uid=activity_subgroup_uid,
                    activity_subgroup_version=activity_subgroup_ar.item_metadata.version,
                    generate_uid_callback=lambda: current_study_activity.study_activity_subgroup_uid,
                )
                # let the aggregate update the value object
                selection_aggregate.update_selection(
                    updated_study_object_selection=new_selection,
                    ct_term_level_exist_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                )
        # sync with DB and save the update
        self._repos.study_activity_subgroup_repository.save(
            selection_aggregate, self.author
        )

        return new_selection

    @classmethod
    def _validate_activity_group(cls, activity_group_uid: str) -> ActivityGroupAR:
        activity_group_service = ActivityGroupService()
        activity_group_ar = activity_group_service.repository.find_by_uid_2(
            activity_group_uid, for_update=True
        )
        if not activity_group_uid:
            raise exceptions.NotFoundException(
                f"There is no activity group identified by provided uid ({activity_group_uid})"
            )

        if activity_group_ar.item_metadata.status in [
            LibraryItemStatus.DRAFT,
            LibraryItemStatus.RETIRED,
        ]:
            raise exceptions.BusinessLogicException(
                f"There is no approved activity group identified by provided uid ({activity_group_uid})"
            )
        return activity_group_ar

    def _create_activity_group_selection_value_object(
        self,
        study_uid: str,
        activity_group_uid: str,
    ):
        activity_group_ar = self._validate_activity_group(
            activity_group_uid=activity_group_uid
        )
        # create new VO to add
        new_selection = StudySelectionActivityGroupVO.from_input_values(
            study_uid=study_uid,
            user_initials=self.author,
            activity_group_uid=activity_group_uid,
            activity_group_version=activity_group_ar.item_metadata.version,
            generate_uid_callback=self._repos.study_activity_group_repository.generate_uid,
        )
        return new_selection

    def _patch_study_activity_group_selection_value_object(
        self,
        study_uid: str,
        current_study_activity: StudySelectionActivityVO,
        selection_create_input: (
            models.StudySelectionActivityInput
            | models.StudySelectionActivityRequestEditInput
            | models.UpdateActivityPlaceholderToSponsorActivity
        ),
    ):
        selection_aggregate = self._repos.study_activity_group_repository.find_by_study(
            study_uid=study_uid, for_update=True
        )
        assert selection_aggregate is not None
        if current_study_activity.study_activity_group_uid is None:
            new_selection = self._create_activity_group_selection_value_object(
                study_uid=study_uid,
                activity_group_uid=selection_create_input.activity_group_uid,
            )
            selection_aggregate.add_object_selection(
                new_selection,
                self._repos.activity_group_repository.check_exists_final_version,
            )
        else:
            new_selection, _ = selection_aggregate.get_specific_object_selection(
                study_selection_uid=current_study_activity.study_activity_group_uid
            )
            is_activity_group_changed = (
                current_study_activity.activity_group_uid
                != selection_create_input.activity_group_uid
            )
            if is_activity_group_changed:
                activity_group_uid = selection_create_input.activity_group_uid
                activity_group_ar = self._validate_activity_group(
                    activity_group_uid=activity_group_uid
                )
                # create new VO to add
                new_selection = StudySelectionActivityGroupVO.from_input_values(
                    study_uid=study_uid,
                    user_initials=self.author,
                    activity_group_uid=activity_group_uid,
                    activity_group_version=activity_group_ar.item_metadata.version,
                    generate_uid_callback=lambda: current_study_activity.study_activity_group_uid,
                )
                # let the aggregate update the value object
                selection_aggregate.update_selection(
                    updated_study_object_selection=new_selection,
                    ct_term_level_exist_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                )
        # sync with DB and save the update
        self._repos.study_activity_group_repository.save(
            selection_aggregate, self.author
        )

        return new_selection

    def _patch_selected_activity(
        self,
        current_object: StudySelectionActivityVO,
        request_object: models.StudySelectionActivityRequestEditInput,
    ) -> ActivityAR:
        activity_service = ActivityService()
        activity_ar = activity_service.repository.find_by_uid_2(
            current_object.activity_uid, for_update=True
        )
        if not activity_ar:
            raise exceptions.ValidationException(
                f"The Activity with the following uid ({current_object.activity_uid}) doesn't exist"
            )
        if activity_ar.item_metadata.status not in [
            LibraryItemStatus.FINAL,
            LibraryItemStatus.DRAFT,
        ]:
            raise exceptions.BusinessLogicException(
                f"The underlying Activity ({current_object.activity_uid}) must be in Draft or Final status."
            )
        if activity_ar.item_metadata.status == LibraryItemStatus.FINAL:
            activity_ar.create_new_version(author=self.author)
        if request_object.activity_name:
            activity_name = request_object.activity_name
        else:
            activity_name = current_object.activity_name
        # This method is called only in scope for the ActiivtyRequest edition.
        # It means that we are sure that we have just one grouping linked to the ActivityRequest.
        activity_groupings = []
        if request_object.activity_subgroup_uid or request_object.activity_group_uid:
            activity_subgroup_uid = None
            activity_group_uid = None
            if activity_ar.concept_vo.activity_groupings:
                activity_grouping = activity_ar.concept_vo.activity_groupings[0]
                activity_subgroup_uid = activity_grouping.activity_subgroup_uid
                activity_group_uid = activity_grouping.activity_group_uid
            activity_subgroup_uid = (
                request_object.activity_subgroup_uid
                if request_object.activity_subgroup_uid
                else activity_subgroup_uid
            )
            activity_group_uid = (
                request_object.activity_group_uid
                if request_object.activity_group_uid
                else activity_group_uid
            )
            activity_grouping = ActivityGroupingVO(
                activity_subgroup_uid=activity_subgroup_uid,
                activity_group_uid=activity_group_uid,
            )
            activity_groupings.append(activity_grouping)
        activity_ar.edit_draft(
            author=self.author,
            change_description=None,
            concept_vo=ActivityVO.from_repository_values(
                nci_concept_id=activity_ar.concept_vo.nci_concept_id,
                name=activity_name,
                name_sentence_case=activity_name.lower(),
                definition=activity_ar.concept_vo.definition,
                abbreviation=activity_ar.concept_vo.abbreviation,
                activity_groupings=activity_groupings,
                request_rationale=(
                    request_object.request_rationale
                    if request_object.request_rationale
                    else activity_ar.concept_vo.request_rationale
                ),
                is_request_final=(
                    request_object.is_request_final
                    if request_object.is_request_final
                    else activity_ar.concept_vo.is_request_final
                ),
                is_data_collected=(
                    request_object.is_data_collected
                    if request_object.is_data_collected
                    else activity_ar.concept_vo.is_data_collected
                ),
                is_multiple_selection_allowed=activity_ar.concept_vo.is_multiple_selection_allowed,
            ),
            concept_exists_by_library_and_name_callback=self._repos.activity_repository.latest_concept_in_library_exists_by_name,
            activity_subgroup_exists=self._repos.activity_subgroup_repository.final_concept_exists,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
        )
        activity_ar.approve(
            author=self.author,
            change_description="Created new version from the StudyActivityRequest Edit",
        )
        self._repos.activity_repository.save(activity_ar)
        return activity_ar

    def _patch_soa_group_selection_value_object(
        self,
        study_uid: str,
        current_study_activity: StudySelectionActivityVO,
        selection_create_input: models.StudySelectionActivityInput,
    ):
        selection_aggregate = self._repos.study_soa_group_repository.find_by_study(
            study_uid=study_uid, for_update=True
        )
        assert selection_aggregate is not None
        new_selection, _ = selection_aggregate.get_specific_object_selection(
            study_selection_uid=current_study_activity.study_soa_group_uid
        )
        is_soa_group_changed = (
            current_study_activity.soa_group_term_uid
            != selection_create_input.soa_group_term_uid
        )
        if is_soa_group_changed:
            soa_group_term_uid = selection_create_input.soa_group_term_uid
            ct_term_ar = self._repos.ct_term_name_repository.find_by_uid(
                soa_group_term_uid
            )
            if not ct_term_ar:
                raise exceptions.NotFoundException(
                    f"There is no SoAGroup CTTerm identified by provided uid ({soa_group_term_uid})"
                )

            if ct_term_ar.item_metadata.status in [
                LibraryItemStatus.DRAFT,
                LibraryItemStatus.RETIRED,
            ]:
                raise exceptions.BusinessLogicException(
                    f"There is no approved SoAGroup CTTerm identified by provided uid ({soa_group_term_uid})"
                )
            # create new VO to add
            new_selection = StudySoAGroupVO.from_input_values(
                study_uid=study_uid,
                user_initials=self.author,
                soa_group_term_uid=soa_group_term_uid,
                generate_uid_callback=lambda: current_study_activity.study_soa_group_uid,
            )
            # let the aggregate update the value object
            selection_aggregate.update_selection(
                updated_study_object_selection=new_selection,
                ct_term_level_exist_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
            )
            # sync with DB and save the update
            self._repos.study_soa_group_repository.save(
                selection_aggregate, self.author
            )

        return new_selection

    def _create_soa_group_selection_value_object(
        self,
        study_uid: str,
        selection_create_input: (
            models.StudySelectionActivityCreateInput
            | models.StudySelectionActivityInput
        ),
    ):
        soa_group_term_uid = selection_create_input.soa_group_term_uid
        ct_term_ar = self._repos.ct_term_name_repository.find_by_uid(soa_group_term_uid)
        if not ct_term_ar:
            raise exceptions.NotFoundException(
                f"There is no SoAGroup CTTerm identified by provided uid ({soa_group_term_uid})"
            )

        if ct_term_ar.item_metadata.status in [
            LibraryItemStatus.DRAFT,
            LibraryItemStatus.RETIRED,
        ]:
            raise exceptions.BusinessLogicException(
                f"There is no approved SoAGroup CTTerm identified by provided uid ({soa_group_term_uid})"
            )

        # create new VO to add
        new_selection = StudySoAGroupVO.from_input_values(
            study_uid=study_uid,
            user_initials=self.author,
            soa_group_term_uid=soa_group_term_uid,
            generate_uid_callback=self._repos.study_soa_group_repository.generate_uid,
        )
        return new_selection

    def make_selection(
        self,
        study_uid: str,
        selection_create_input: models.StudySelectionActivityCreateInput,
    ) -> models.StudySelectionActivity:
        repos = self._repos
        try:
            with db.transaction:
                # StudySoAGroup selection
                study_soa_group_selection = self._repos.study_soa_group_repository.find_study_soa_group_in_a_study(
                    study_uid=study_uid,
                    soa_group_term_uid=selection_create_input.soa_group_term_uid,
                )
                if study_soa_group_selection:
                    study_soa_group_selection_uid = study_soa_group_selection.uid
                else:
                    study_soa_group_selection = (
                        self._create_soa_group_selection_value_object(
                            study_uid=study_uid,
                            selection_create_input=selection_create_input,
                        )
                    )
                    # add VO to aggregate
                    study_soa_group_aggregate = (
                        self._repos.study_soa_group_repository.find_by_study(
                            study_uid=study_uid, for_update=True
                        )
                    )
                    assert study_soa_group_aggregate is not None
                    study_soa_group_aggregate.add_object_selection(
                        study_soa_group_selection,
                    )
                    # sync with DB and save the update
                    self._repos.study_soa_group_repository.save(
                        study_soa_group_aggregate, self.author
                    )
                    study_soa_group_selection_uid = (
                        study_soa_group_selection.study_selection_uid
                    )

                study_activity_subgroup_selection_uid: str | None = None
                # StudyActivitySubGroup selection
                if selection_create_input.activity_subgroup_uid:
                    study_activity_subgroup_sel = self._repos.study_activity_subgroup_repository.find_study_activity_subgroup_with_same_groupings(
                        study_uid=study_uid,
                        activity_subgroup_uid=selection_create_input.activity_subgroup_uid,
                        activity_group_uid=selection_create_input.activity_group_uid,
                        soa_group_term_uid=selection_create_input.soa_group_term_uid,
                    )
                    if study_activity_subgroup_sel:
                        study_activity_subgroup_selection_uid = (
                            study_activity_subgroup_sel.uid
                        )
                    else:
                        # create new VO to add
                        study_activity_subgroup_sel = self._create_activity_subgroup_selection_value_object(
                            study_uid=study_uid,
                            activity_subgroup_uid=selection_create_input.activity_subgroup_uid,
                        )
                        # add VO to aggregate
                        study_activity_subgroup_aggregate = self._repos.study_activity_subgroup_repository.find_by_study(
                            study_uid=study_uid, for_update=True
                        )
                        assert study_activity_subgroup_aggregate is not None
                        study_activity_subgroup_aggregate.add_object_selection(
                            study_activity_subgroup_sel,
                            self._repos.activity_subgroup_repository.check_exists_final_version,
                        )
                        # sync with DB and save the update
                        self._repos.study_activity_subgroup_repository.save(
                            study_activity_subgroup_aggregate, self.author
                        )
                        study_activity_subgroup_selection_uid = (
                            study_activity_subgroup_sel.study_selection_uid
                        )

                study_activity_group_selection_uid: str | None = None
                # StudyActivityGroup selection
                if (
                    selection_create_input.activity_subgroup_uid
                    and selection_create_input.activity_group_uid
                ):
                    study_activity_group_selection = self._repos.study_activity_group_repository.find_study_activity_group_with_same_groupings(
                        study_uid=study_uid,
                        activity_group_uid=selection_create_input.activity_group_uid,
                        soa_group_term_uid=selection_create_input.soa_group_term_uid,
                    )
                    if study_activity_group_selection:
                        study_activity_group_selection_uid = (
                            study_activity_group_selection.uid
                        )
                    else:
                        # create new VO to add
                        study_activity_group_selection = self._create_activity_group_selection_value_object(
                            study_uid=study_uid,
                            activity_group_uid=selection_create_input.activity_group_uid,
                        )
                        # add VO to aggregate
                        study_activity_group_aggregate = (
                            self._repos.study_activity_group_repository.find_by_study(
                                study_uid=study_uid, for_update=True
                            )
                        )
                        assert study_activity_group_aggregate is not None
                        study_activity_group_aggregate.add_object_selection(
                            study_activity_group_selection,
                            self._repos.activity_group_repository.check_exists_final_version,
                        )
                        # sync with DB and save the update
                        self._repos.study_activity_group_repository.save(
                            study_activity_group_aggregate, self.author
                        )
                        study_activity_group_selection_uid = (
                            study_activity_group_selection.study_selection_uid
                        )

                # StudyActivitySelection
                # create new VO to add
                study_activity_selection = self._create_value_object(
                    study_uid=study_uid,
                    selection_create_input=selection_create_input,
                    study_soa_group_selection_uid=study_soa_group_selection_uid,
                    study_activity_subgroup_selection_uid=study_activity_subgroup_selection_uid,
                    study_activity_group_selection_uid=study_activity_group_selection_uid,
                )
                # add VO to aggregate
                study_activity_aggregate = self.repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
                assert study_activity_aggregate is not None
                study_activity_aggregate.add_object_selection(
                    study_activity_selection,
                    self.selected_object_repository.check_exists_final_version,
                    self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                )
                study_activity_aggregate.validate()
                # sync with DB and save the update
                self.repository.save(study_activity_aggregate, self.author)

                # create StudyActivityInstance selection
                if (
                    # We are not creating a StudyActivityInstance selection for Activity placeholders
                    study_activity_selection.activity_library_name
                    != REQUESTED_LIBRARY_NAME
                ):
                    related_activity_instances = self._repos.activity_instance_repository.get_all_activity_instances_for_activity_grouping(
                        activity_uid=study_activity_selection.activity_uid,
                        activity_subgroup_uid=study_activity_selection.activity_subgroup_uid,
                        activity_group_uid=study_activity_selection.activity_group_uid,
                        filter_by_boolean_flags=True,
                    )
                    linked_activity_instances = []
                    for activity_instance in related_activity_instances:
                        if activity_instance.uid not in linked_activity_instances:
                            linked_activity_instances.append(activity_instance.uid)

                    # If there is no ActivityInstances linked to selected Activity
                    # we create a 'placeholder' StudyActivityInstance that can link to ActivityInstance later
                    if len(linked_activity_instances) == 0:
                        linked_activity_instances.append(None)
                    for activity_instance_uid in linked_activity_instances:
                        activity_instance_selection = StudySelectionActivityInstanceVO.from_input_values(
                            study_uid=study_uid,
                            user_initials=self.author,
                            activity_instance_uid=activity_instance_uid,
                            activity_uid=study_activity_selection.activity_uid,
                            activity_subgroup_uid=study_activity_selection.activity_subgroup_uid,
                            activity_group_uid=study_activity_selection.activity_group_uid,
                            study_activity_uid=study_activity_selection.study_selection_uid,
                            generate_uid_callback=self._repos.study_activity_instance_repository.generate_uid,
                        )  # add VO to aggregate
                        study_activity_instance_aggregate = self._repos.study_activity_instance_repository.find_by_study(
                            study_uid=study_uid, for_update=True
                        )
                        assert study_activity_instance_aggregate is not None
                        study_activity_instance_aggregate.add_object_selection(
                            activity_instance_selection,
                            self._repos.activity_instance_repository.check_exists_final_version,
                        )
                        study_activity_instance_aggregate.validate()
                        # sync with DB and save the update
                        self._repos.study_activity_instance_repository.save(
                            study_activity_instance_aggregate, self.author
                        )

                study_activity_aggregate = self.repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
                # Fetch the new selection which was just added
                (
                    new_selection,
                    order,
                ) = study_activity_aggregate.get_specific_object_selection(
                    study_activity_selection.study_selection_uid
                )
                terms_at_specific_datetime = (
                    self._extract_study_standards_effective_date(study_uid=study_uid)
                )
                # add the activity and return
                return self._transform_from_vo_to_response_model(
                    study_uid=study_activity_aggregate.study_uid,
                    specific_selection=new_selection,
                    order=order,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                )
        finally:
            repos.close()

    @db.transaction
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        # StudyActivitySchedule and StudyActivityInstruction Services for cascade delete if any
        study_activity_schedules_service = StudyActivityScheduleService()
        study_activity_instructions_service = StudyActivityInstructionService()

        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = repos.study_activity_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            (
                study_activity_selection,
                _,
            ) = selection_aggregate.get_specific_object_selection(study_selection_uid)
            activity_ar = repos.activity_repository.find_by_uid_2(
                study_activity_selection.activity_uid, for_update=True
            )
            # We should retire ActivityRequest if it's not finalized
            if (
                activity_ar.library.name == REQUESTED_LIBRARY_NAME
                and not activity_ar.concept_vo.is_finalized
                and activity_ar.concept_vo.is_request_final
            ):
                if not activity_ar:
                    raise exceptions.ValidationException(
                        f"The Activity with the following uid ({study_activity_selection.activity_uid}) doesn't exist"
                    )
                if activity_ar.item_metadata.status == LibraryItemStatus.DRAFT:
                    activity_ar.approve(author=self.author)
                    activity_ar.inactivate(author=self.author)
                if activity_ar.item_metadata.status == LibraryItemStatus.FINAL:
                    activity_ar.inactivate(author=self.author)
                repos.activity_repository.save(activity_ar)

            # Remove related Study activity schedules
            study_activity_schedules = study_activity_schedules_service.get_all_schedules_for_specific_activity(
                study_uid=study_uid, study_activity_uid=study_selection_uid
            )
            for study_activity_schedule in study_activity_schedules:
                self._repos.study_activity_schedule_repository.delete(
                    study_uid,
                    study_activity_schedule.study_activity_schedule_uid,
                    self.author,
                )

            # Remove related Study activity instructions
            study_activity_instructions = study_activity_instructions_service.get_all_study_instructions_for_specific_study_activity(
                study_uid=study_uid, study_activity_uid=study_selection_uid
            )
            for study_activity_instruction in study_activity_instructions:
                self._repos.study_activity_instruction_repository.delete(
                    study_uid,
                    study_activity_instruction.study_activity_instruction_uid,
                    self.author,
                )

            # Remove related Study activity subgroups
            study_activity_subgroups = repos.study_activity_subgroup_repository.get_all_study_activity_subgroups_for_study_activity(
                study_uid=study_uid, study_activity_uid=study_selection_uid
            )
            for study_activity_subgroup in study_activity_subgroups:
                # delete study activity subgroup
                (
                    study_activity_subgroup_ar,
                    _,
                    _,
                ) = self._get_specific_activity_subgroup_selection_by_uids(
                    study_uid=study_uid,
                    study_selection_uid=study_activity_subgroup.uid,
                    for_update=True,
                )

                study_activity_subgroup_ar.remove_object_selection(
                    study_activity_subgroup.uid
                )
                repos.study_activity_subgroup_repository.save(
                    study_activity_subgroup_ar, self.author
                )

            # Remove related Study activity groups
            study_activity_groups = repos.study_activity_group_repository.get_all_study_activity_groups_for_study_activity(
                study_uid=study_uid, study_activity_uid=study_selection_uid
            )
            for study_activity_group in study_activity_groups:
                # delete study activity group
                (
                    study_activity_group_ar,
                    _,
                    _,
                ) = self._get_specific_activity_group_selection_by_uids(
                    study_uid=study_uid,
                    study_selection_uid=study_activity_group.uid,
                    for_update=True,
                )
                study_activity_group_ar.remove_object_selection(
                    study_activity_group.uid
                )
                repos.study_activity_group_repository.save(
                    study_activity_group_ar, self.author
                )

            # Remove related Study soa groups
            study_soa_groups = repos.study_soa_group_repository.get_all_study_soa_groups_for_study_activity(
                study_uid=study_uid, study_activity_uid=study_selection_uid
            )
            for study_soa_group in study_soa_groups:
                # delete study soa group
                (
                    study_soa_group_ar,
                    _,
                    _,
                ) = self._get_specific_soa_group_selection_by_uids(
                    study_uid=study_uid,
                    study_selection_uid=study_soa_group.uid,
                    for_update=True,
                )
                study_soa_group_ar.remove_object_selection(study_soa_group.uid)
                repos.study_soa_group_repository.save(study_soa_group_ar, self.author)

            # Remove related Study activity instances
            study_activity_instances = repos.study_activity_instance_repository.get_all_study_activity_instances_for_study_activity(
                study_uid=study_uid, study_activity_uid=study_selection_uid
            )
            for study_activity_instance in study_activity_instances:
                # delete study activity instance
                (
                    study_activity_instance_ar,
                    _,
                    _,
                ) = self._get_specific_activity_instance_selection_by_uids(
                    study_uid=study_uid,
                    study_selection_uid=study_activity_instance.uid,
                    for_update=True,
                )
                study_activity_instance_ar.remove_object_selection(
                    study_activity_instance.uid
                )
                repos.study_activity_instance_repository.save(
                    study_activity_instance_ar, self.author
                )

            # remove the connection
            assert selection_aggregate is not None
            selection_aggregate.remove_object_selection(study_selection_uid)

            # sync with DB and save the update
            repos.study_activity_repository.save(selection_aggregate, self.author)
        finally:
            repos.close()

    def _patch_prepare_new_value_object(
        self,
        request_object: (
            models.StudySelectionActivityInput
            | models.StudySelectionActivityRequestEditInput
            | models.UpdateActivityPlaceholderToSponsorActivity
        ),
        current_object: StudySelectionActivityVO,
    ) -> StudySelectionActivityVO:
        # transform current to input model
        transformed_current = models.StudySelectionActivityInput(
            show_activity_group_in_protocol_flowchart=current_object.show_activity_group_in_protocol_flowchart,
            show_activity_subgroup_in_protocol_flowchart=current_object.show_activity_subgroup_in_protocol_flowchart,
            show_activity_in_protocol_flowchart=current_object.show_activity_in_protocol_flowchart,
            show_soa_group_in_protocol_flowchart=current_object.show_soa_group_in_protocol_flowchart,
            soa_group_term_uid=current_object.soa_group_term_uid,
        )

        # fill the missing from the inputs
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_object,
            reference_base_model=transformed_current,
        )
        # update StudySoAGroup selection
        updated_soa_selection = self._patch_soa_group_selection_value_object(
            study_uid=current_object.study_uid,
            current_study_activity=current_object,
            selection_create_input=request_object,
        )
        # update StudyActivitySubGroup
        if (
            isinstance(
                request_object,
                (
                    models.StudySelectionActivityRequestEditInput,
                    models.UpdateActivityPlaceholderToSponsorActivity,
                ),
            )
            and request_object.activity_subgroup_uid
        ):
            activity_subgroup_uid = request_object.activity_subgroup_uid
            activity_subgroup_name = None  # This gets filled in later
            study_activity_subgroup = (
                self._patch_study_activity_subgroup_selection_value_object(
                    study_uid=current_object.study_uid,
                    current_study_activity=current_object,
                    selection_create_input=request_object,
                )
            )
            study_activity_subgroup_uid = study_activity_subgroup.study_selection_uid
        else:
            activity_subgroup_uid = current_object.activity_subgroup_uid
            activity_subgroup_name = current_object.activity_subgroup_name
            study_activity_subgroup_uid = current_object.study_activity_subgroup_uid

        # update StudyActivityGroup
        if (
            isinstance(
                request_object,
                (
                    models.StudySelectionActivityRequestEditInput,
                    models.UpdateActivityPlaceholderToSponsorActivity,
                ),
            )
            and request_object.activity_group_uid
        ):
            activity_group_uid = request_object.activity_group_uid
            activity_group_name = None  # This gets filled in later
            study_activity_group = (
                self._patch_study_activity_group_selection_value_object(
                    study_uid=current_object.study_uid,
                    current_study_activity=current_object,
                    selection_create_input=request_object,
                )
            )
            study_activity_group_uid = study_activity_group.study_selection_uid
        else:
            activity_group_uid = current_object.activity_group_uid
            activity_group_name = current_object.activity_group_name
            study_activity_group_uid = current_object.study_activity_group_uid

        # update underlying Activity
        activity_ver = current_object.activity_version
        activity_name = current_object.activity_name
        if isinstance(
            request_object, models.StudySelectionActivityRequestEditInput
        ) and any(
            [
                request_object.request_rationale,
                request_object.is_request_final,
                request_object.is_data_collected,
                request_object.activity_name,
                request_object.activity_subgroup_uid,
                request_object.activity_group_uid,
            ]
        ):
            activity_ar = self._patch_selected_activity(
                current_object=current_object,
                request_object=request_object,
            )
            activity_name = activity_ar.name
            activity_ver = activity_ar.item_metadata.version
        elif (
            isinstance(
                request_object, models.UpdateActivityPlaceholderToSponsorActivity
            )
            and request_object.activity_uid
        ):
            activity_service = ActivityService()
            activity_ar = activity_service.repository.find_by_uid_2(
                request_object.activity_uid, for_update=True
            )
            if not activity_ar:
                raise exceptions.ValidationException(
                    f"The Activity with the following uid ({current_object.activity_uid}) doesn't exist"
                )
            activity_name = activity_ar.name
            activity_ver = activity_ar.item_metadata.version

        return StudySelectionActivityVO.from_input_values(
            study_uid=current_object.study_uid,
            activity_uid=(
                request_object.activity_uid
                if isinstance(
                    request_object, models.UpdateActivityPlaceholderToSponsorActivity
                )
                and request_object.activity_uid
                else current_object.activity_uid
            ),
            activity_version=activity_ver,
            activity_order=current_object.activity_order,
            activity_name=activity_name,
            soa_group_term_uid=updated_soa_selection.soa_group_term_uid,
            study_soa_group_uid=updated_soa_selection.study_selection_uid,
            study_selection_uid=current_object.study_selection_uid,
            study_activity_subgroup_uid=study_activity_subgroup_uid,
            activity_subgroup_uid=activity_subgroup_uid,
            activity_subgroup_name=activity_subgroup_name,
            study_activity_group_uid=study_activity_group_uid,
            activity_group_uid=activity_group_uid,
            activity_group_name=activity_group_name,
            show_activity_in_protocol_flowchart=request_object.show_activity_in_protocol_flowchart,
            user_initials=self.author,
        )

    def handle_batch_operations(
        self,
        study_uid: str,
        operations: list[models.StudySelectionActivityBatchInput],
    ) -> list[models.StudySelectionActivityBatchOutput]:
        results = []
        for operation in operations:
            result = {}
            item = None
            try:
                if operation.method == "PATCH":
                    item = self.patch_selection(
                        study_uid,
                        operation.content.study_activity_uid,
                        operation.content.content,
                    )
                    response_code = status.HTTP_200_OK
                elif operation.method == "DELETE":
                    self.delete_selection(
                        study_uid, operation.content.study_activity_uid
                    )
                    response_code = status.HTTP_204_NO_CONTENT
                else:
                    item = self.make_selection(study_uid, operation.content)
                    response_code = status.HTTP_201_CREATED
            except exceptions.MDRApiBaseException as error:
                result["response_code"] = error.status_code
                result["content"] = BatchErrorResponse(message=str(error))
            else:
                result["response_code"] = response_code
                result["content"] = item
            finally:
                results.append(models.StudySelectionActivityBatchOutput(**result))
        return results

    @db.transaction
    def update_activity_request_with_sponsor_activity(
        self,
        study_uid: str,
        study_selection_uid: str,
    ) -> models.StudySelectionActivity:
        repos = self._repos
        # Load aggregate
        selection_aggregate = repos.study_activity_repository.find_by_study(
            study_uid=study_uid, for_update=True
        )

        assert selection_aggregate is not None
        # Load the current VO for updates
        current_vo, _ = selection_aggregate.get_specific_object_selection(
            study_selection_uid=study_selection_uid
        )
        activity_ar = self._repos.activity_repository.find_by_uid_2(
            current_vo.activity_uid
        )
        replaced_activity_ar = self._repos.activity_repository.find_by_uid_2(
            activity_ar.concept_vo.replaced_by_activity
        )
        updated_study_activity = self.patch_selection_non_transactional(
            study_uid=study_uid,
            study_selection_uid=study_selection_uid,
            selection_update_input=models.UpdateActivityPlaceholderToSponsorActivity(
                activity_uid=replaced_activity_ar.uid,
                # It is safe to access activity_groupings by [0] as it's a required to pass just exactly one
                # set of groupings when creating a Sponsor activity out of Activity Request
                activity_subgroup_uid=replaced_activity_ar.concept_vo.activity_groupings[
                    0
                ].activity_subgroup_uid,
                activity_group_uid=replaced_activity_ar.concept_vo.activity_groupings[
                    0
                ].activity_group_uid,
            ),
        )
        related_activity_instances = self._repos.activity_instance_repository.get_all_activity_instances_for_activity_grouping(
            activity_uid=current_vo.activity_uid,
            activity_subgroup_uid=current_vo.activity_subgroup_uid,
            activity_group_uid=current_vo.activity_group_uid,
            filter_by_boolean_flags=True,
        )
        linked_activity_instances = []
        for activity_instance in related_activity_instances:
            if activity_instance.uid not in linked_activity_instances:
                linked_activity_instances.append(activity_instance.uid)

        # If there is no ActivityInstances linked to selected Activity
        # we create a 'placeholder' StudyActivityInstance that can link to ActivityInstance later
        if len(linked_activity_instances) == 0:
            linked_activity_instances.append(None)
        for activity_instance_uid in linked_activity_instances:
            activity_instance_selection = StudySelectionActivityInstanceVO.from_input_values(
                study_uid=study_uid,
                user_initials=self.author,
                activity_instance_uid=activity_instance_uid,
                activity_uid=current_vo.activity_uid,
                activity_subgroup_uid=current_vo.activity_subgroup_uid,
                activity_group_uid=current_vo.activity_group_uid,
                study_activity_uid=current_vo.study_selection_uid,
                generate_uid_callback=self._repos.study_activity_instance_repository.generate_uid,
            )  # add VO to aggregate
            study_activity_instance_aggregate = (
                self._repos.study_activity_instance_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )
            assert study_activity_instance_aggregate is not None
            study_activity_instance_aggregate.add_object_selection(
                activity_instance_selection,
                self._repos.activity_instance_repository.check_exists_final_version,
            )
            study_activity_instance_aggregate.validate()
            # sync with DB and save the update
            self._repos.study_activity_instance_repository.save(
                study_activity_instance_aggregate, self.author
            )
        return updated_study_activity

    def get_detailed_soa_history(
        self, study_uid: str, page_number: int, page_size: int, total_count: bool
    ) -> GenericFilteringReturn[DetailedSoAHistory]:
        if not self._repos.study_definition_repository.study_exists_by_uid(
            study_uid=study_uid
        ):
            raise exceptions.NotFoundException(
                f"Study with specified uid '{study_uid}' was not found."
            )
        (
            detailed_soa_history,
            amount_of_history_items,
        ) = self.repository.get_detailed_soa_history(
            study_uid=study_uid,
            page_size=page_size,
            page_number=page_number,
            total_count=total_count,
        )
        all_detailed_history = GenericFilteringReturn.create(
            items=detailed_soa_history, total=amount_of_history_items
        )
        all_detailed_history.items = [
            DetailedSoAHistory.from_history(detailed_soa_history_item=item)
            for item in all_detailed_history.items
        ]
        return all_detailed_history
