from datetime import datetime
from typing import Callable

from neomodel import db

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.domain_repositories.concepts.activities.activity_instance_repository import (
    ActivityInstanceRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_instance_repository import (
    SelectionHistory,
    StudySelectionActivityInstanceRepository,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity import (
    StudySelectionActivityVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity_instance import (
    StudySelectionActivityInstanceAR,
    StudySelectionActivityInstanceVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    fill_missing_values_in_base_model_from_reference_base_model,
)
from clinical_mdr_api.services.concepts.activities.activity_instance_service import (
    ActivityInstanceService,
)
from clinical_mdr_api.services.studies.study_activity_selection_base import (
    StudyActivitySelectionBaseService,
)


class StudyActivityInstanceSelectionService(StudyActivitySelectionBaseService):
    _repos: MetaRepository
    repository_interface = StudySelectionActivityInstanceRepository
    selected_object_repository_interface = ActivityInstanceRepository

    def update_study_activities(self, study_uid: str, study_selection_uid: str):
        pass

    _vo_to_ar_filter_map = {
        "order": "activity_order",
        "start_date": "start_date",
        "user_initials": "user_initials",
        "activity.name": "activity_name",
        "activity_instance.name": "activity_instance_name",
        "study_soa_group.soa_group_name": "soa_group_term_name",
        "study_activity_subgroup.activity_subgroup_name": "activity_subgroup_name",
        "study_activity_group.activity_group_name": "activity_group_name",
    }

    def _get_selected_object_exist_check(self) -> Callable[[str], bool]:
        return self.selected_object_repository.final_concept_exists

    def _transform_from_vo_to_response_model(
        self,
        study_uid: str,
        specific_selection: StudySelectionActivityInstanceVO,
        order: int,
        terms_at_specific_datetime: datetime | None = None,
        accepted_version: bool = False,
    ) -> models.StudySelectionActivityInstance:
        return models.StudySelectionActivityInstance.from_study_selection_activity_instance_vo_and_order(
            study_uid=study_uid,
            specific_selection=specific_selection,
            get_activity_by_uid_callback=self._transform_latest_activity_model,
            get_activity_by_uid_version_callback=self._transform_activity_model,
            get_activity_instance_by_uid_callback=self._transform_latest_activity_instance_model,
            get_activity_instance_by_uid_version_callback=self._transform_activity_instance_model,
        )

    def _transform_all_to_response_model(
        self,
        study_selection: StudySelectionActivityInstanceAR,
        study_value_version: str | None = None,
    ) -> list[models.StudySelectionActivityInstance]:
        result = []
        for order, specific_selection in enumerate(
            study_selection.study_objects_selection, start=1
        ):
            result.append(
                self._transform_from_vo_to_response_model(
                    study_uid=study_selection.study_uid,
                    specific_selection=specific_selection,
                    order=order,
                )
            )
        return result

    def _transform_history_to_response_model(
        self, study_selection_history: list[SelectionHistory], study_uid: str
    ) -> list[models.StudySelectionActivityInstance]:
        result = []
        for history in study_selection_history:
            result.append(
                models.StudySelectionActivityInstance.from_study_selection_history(
                    study_selection_history=history,
                    study_uid=study_uid,
                    get_activity_by_uid_version_callback=self._transform_activity_model,
                    get_activity_instance_by_uid_version_callback=self._transform_activity_instance_model,
                )
            )
        return result

    def activity_instance_validation(
        self,
        activity_instance_uid: str,
        study_activity_selection: StudySelectionActivityVO,
    ):
        activity_instance_service = ActivityInstanceService()
        activity_instance_ar = activity_instance_service.repository.find_by_uid_2(
            activity_instance_uid, for_update=True
        )
        if not activity_instance_uid:
            raise exceptions.NotFoundException(
                f"There is no activity instance identified by provided uid ({activity_instance_uid})"
            )

        if activity_instance_ar.item_metadata.status in [
            LibraryItemStatus.DRAFT,
            LibraryItemStatus.RETIRED,
        ]:
            raise exceptions.BusinessLogicException(
                f"There is no approved activity instance identified by provided uid ({activity_instance_uid})"
            )

        related_activity_instances = self._repos.activity_instance_repository.get_all_activity_instances_for_activity_grouping(
            activity_uid=study_activity_selection.activity_uid,
            activity_subgroup_uid=study_activity_selection.activity_subgroup_uid,
            activity_group_uid=study_activity_selection.activity_group_uid,
        )
        linked_activity_instances = []
        for activity_instance in related_activity_instances:
            if activity_instance.uid not in linked_activity_instances:
                linked_activity_instances.append(activity_instance.uid)
        if activity_instance_uid not in linked_activity_instances:
            raise exceptions.BusinessLogicException(
                f"The following activity instance ({activity_instance_ar.name}) "
                f"is not linked with the ({study_activity_selection.activity_name}) activity"
            )

        return activity_instance_ar

    def _create_value_object(
        self,
        study_uid: str,
        selection_create_input: models.StudySelectionActivityInstanceCreateInput,
        **kwargs,
    ):
        _, study_activity_selection, _ = self._get_specific_activity_selection_by_uids(
            study_uid=study_uid,
            study_selection_uid=selection_create_input.study_activity_uid,
        )
        if selection_create_input.activity_instance_uid:
            activity_instance_ar = self.activity_instance_validation(
                activity_instance_uid=selection_create_input.activity_instance_uid,
                study_activity_selection=study_activity_selection,
            )
        else:
            activity_instance_ar = None

        # create new VO to add
        new_selection = StudySelectionActivityInstanceVO.from_input_values(
            study_uid=study_uid,
            user_initials=self.author,
            activity_instance_uid=activity_instance_ar.uid
            if activity_instance_ar
            else None,
            activity_instance_version=activity_instance_ar.item_metadata.version
            if activity_instance_ar
            else None,
            study_activity_uid=selection_create_input.study_activity_uid,
            activity_uid=study_activity_selection.activity_uid,
            activity_subgroup_uid=study_activity_selection.activity_subgroup_uid,
            activity_group_uid=study_activity_selection.activity_group_uid,
            generate_uid_callback=self.repository.generate_uid,
        )
        return new_selection

    def make_selection(
        self,
        study_uid: str,
        selection_create_input: models.StudySelectionActivityInstanceCreateInput,
    ) -> models.StudySelectionActivityInstance:
        repos = self._repos
        try:
            with db.transaction:
                # create new VO to add
                study_activity_instance_selection = self._create_value_object(
                    study_uid=study_uid,
                    selection_create_input=selection_create_input,
                )
                # add VO to aggregate
                study_activity_instance_aggregate = self.repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
                assert study_activity_instance_aggregate is not None
                study_activity_instance_aggregate.add_object_selection(
                    study_activity_instance_selection,
                    self.selected_object_repository.check_exists_final_version,
                    self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                )
                study_activity_instance_aggregate.validate()
                # sync with DB and save the update
                self.repository.save(study_activity_instance_aggregate, self.author)

                study_activity_instance_aggregate = self.repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
                # Fetch the new selection which was just added
                (
                    specific_selection,
                    order,
                ) = study_activity_instance_aggregate.get_specific_object_selection(
                    study_activity_instance_selection.study_selection_uid
                )

                # add the activity and return
                return self._transform_from_vo_to_response_model(
                    study_uid=study_activity_instance_aggregate.study_uid,
                    specific_selection=specific_selection,
                    order=order,
                )
        finally:
            repos.close()

    @db.transaction
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = (
                repos.study_activity_instance_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            # remove the connection
            assert selection_aggregate is not None
            selection_aggregate.remove_object_selection(study_selection_uid)

            # sync with DB and save the update
            repos.study_activity_instance_repository.save(
                selection_aggregate, self.author
            )
        finally:
            repos.close()

    def _patch_prepare_new_value_object(
        self,
        request_object: models.StudySelectionActivityInstanceEditInput,
        current_object: StudySelectionActivityInstanceVO,
    ) -> StudySelectionActivityInstanceVO:
        # transform current to input model
        transformed_current = models.StudySelectionActivityInstanceEditInput(
            show_activity_instance_in_protocol_flowchart=current_object.show_activity_instance_in_protocol_flowchart,
            activity_instance_uid=current_object.activity_instance_uid,
            study_activity_uid=current_object.study_activity_uid,
        )

        # fill the missing from the inputs
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_object,
            reference_base_model=transformed_current,
        )

        _, study_activity_selection, _ = self._get_specific_activity_selection_by_uids(
            study_uid=current_object.study_uid,
            study_selection_uid=current_object.study_activity_uid,
        )
        if request_object.activity_instance_uid:
            activity_instance_ar = self.activity_instance_validation(
                activity_instance_uid=request_object.activity_instance_uid,
                study_activity_selection=study_activity_selection,
            )
        else:
            activity_instance_ar = None

        return StudySelectionActivityInstanceVO.from_input_values(
            study_uid=current_object.study_uid,
            study_selection_uid=current_object.study_selection_uid,
            user_initials=self.author,
            activity_instance_uid=activity_instance_ar.uid
            if activity_instance_ar
            else None,
            activity_instance_version=activity_instance_ar.item_metadata.version
            if activity_instance_ar
            else None,
            activity_uid=current_object.activity_uid,
            activity_subgroup_uid=current_object.activity_subgroup_uid,
            activity_group_uid=current_object.activity_group_uid,
            activity_version=current_object.activity_version,
            study_activity_uid=current_object.study_activity_uid,
            show_activity_instance_in_protocol_flowchart=request_object.show_activity_instance_in_protocol_flowchart,
        )

    @db.transaction
    def get_specific_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        study_value_version: str | None = None,
    ) -> models.StudySelectionActivityInstance:
        (
            _,
            specific_selection,
            order,
        ) = self._get_specific_activity_instance_selection_by_uids(
            study_uid, study_selection_uid, study_value_version=study_value_version
        )
        return self._transform_from_vo_to_response_model(
            study_uid=study_uid,
            specific_selection=specific_selection,
            order=order,
        )

    @db.transaction
    def update_selection_to_latest_version(
        self, study_uid: str, study_selection_uid: str
    ):
        (
            selection_ar,
            selection,
            order,
        ) = self._get_specific_activity_instance_selection_by_uids(
            study_uid=study_uid,
            study_selection_uid=study_selection_uid,
            for_update=True,
        )
        activity_instance_uid = selection.activity_instance_uid
        activity_instance_ar = self._repos.activity_instance_repository.find_by_uid_2(
            activity_instance_uid, for_update=True
        )
        if activity_instance_ar.item_metadata.status == LibraryItemStatus.DRAFT:
            activity_instance_ar.approve(self.author)
            self._repos.activity_instance_repository.save(activity_instance_ar)
        elif activity_instance_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException(
                "Cannot add retired activity instances as selection. Please reactivate."
            )
        new_selection: StudySelectionActivityInstanceVO = selection.update_version(
            activity_instance_version=activity_instance_ar.item_metadata.version
        )
        selection_ar.update_selection(new_selection)
        self._repos.study_activity_instance_repository.save(selection_ar, self.author)

        return self._transform_from_vo_to_response_model(
            study_uid=study_uid,
            specific_selection=new_selection,
            order=order,
        )
