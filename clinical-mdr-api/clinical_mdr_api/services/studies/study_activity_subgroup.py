from copy import copy
from datetime import datetime
from typing import Any

from clinical_mdr_api.domain_repositories.concepts.activities.activity_sub_group_repository import (
    ActivitySubGroupRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_subgroup_repository import (
    StudySelectionActivitySubGroupRepository,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity_subgroup import (
    StudySelectionActivitySubGroupVO,
)
from clinical_mdr_api.exceptions import ValidationException
from clinical_mdr_api.models.study_selections.study_selection import (
    StudyActivitySubGroup,
    StudyActivitySubGroupEditInput,
)
from clinical_mdr_api.models.utils import BaseModel
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.studies.study_activity_selection_base import (
    StudyActivitySelectionBaseService,
    _AggregateRootType,
    _VOType,
)


class StudyActivitySubGroupService(StudyActivitySelectionBaseService):
    _repos: MetaRepository
    repository_interface = StudySelectionActivitySubGroupRepository
    selected_object_repository_interface = ActivitySubGroupRepository

    def _create_value_object(
        self,
        study_uid: str,
        selection_create_input: BaseModel,
        **kwargs,
    ):
        pass

    def _transform_all_to_response_model(
        self, study_selection: _AggregateRootType
    ) -> list[BaseModel]:
        pass

    def _transform_from_vo_to_response_model(
        self,
        study_uid: str,
        specific_selection: _VOType,
        order: int,
        terms_at_specific_datetime: datetime | None,
        accepted_version: bool | None = None,
    ) -> BaseModel:
        return StudyActivitySubGroup.from_study_selection_activity_vo(
            study_uid=study_uid, specific_selection=specific_selection
        )

    def _transform_history_to_response_model(
        self, study_selection_history: list[Any], study_uid: str
    ) -> list[BaseModel]:
        pass

    def update_study_activities(self, study_uid: str, study_selection_uid: str):
        study_activities = self._repos.study_activity_repository.get_all_study_activities_for_study_activity_subgroup(
            study_activity_subgroup_uid=study_selection_uid
        )
        study_activity_aggregate = self._repos.study_activity_repository.find_by_study(
            study_uid,
            for_update=True,
        )
        assert study_activity_aggregate is not None

        for study_activity in study_activities:
            selection, _ = study_activity_aggregate.get_specific_object_selection(
                study_activity.uid
            )
            updated_selection = copy(selection)
            study_activity_aggregate.update_selection(
                updated_study_object_selection=updated_selection,
                object_exist_callback=self._repos.activity_repository.final_or_replaced_retired_activity_exists,
                ct_term_level_exist_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
            )
        # sync with DB and save the update
        self._repos.study_activity_repository.save(
            study_activity_aggregate, self.author
        )

    def _patch_prepare_new_value_object(
        self,
        request_object: StudyActivitySubGroupEditInput,
        current_object: StudySelectionActivitySubGroupVO,
    ) -> StudySelectionActivitySubGroupVO:
        if (
            request_object.show_activity_subgroup_in_protocol_flowchart
            == current_object.show_activity_subgroup_in_protocol_flowchart
        ):
            raise ValidationException(
                f"The StudyActivitySubGroup is already set to be "
                f"{'visible' if request_object.show_activity_subgroup_in_protocol_flowchart else 'not visible'}' in the protocol flowchart"
            )

        return StudySelectionActivitySubGroupVO.from_input_values(
            study_uid=current_object.study_uid,
            activity_subgroup_uid=current_object.activity_subgroup_uid,
            activity_subgroup_version=current_object.activity_subgroup_version,
            study_selection_uid=current_object.study_selection_uid,
            show_activity_subgroup_in_protocol_flowchart=request_object.show_activity_subgroup_in_protocol_flowchart,
            user_initials=self.author,
        )
