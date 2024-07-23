"""Service for study activity instructions."""

import datetime

from fastapi import status
from neomodel import db

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.domain_repositories.models._utils import to_relation_trees
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyActivityInstruction as StudyActivityInstructionNeoModel,
)
from clinical_mdr_api.domains.study_selections.study_activity_instruction import (
    StudyActivityInstructionVO,
)
from clinical_mdr_api.domains.syntax_instances.activity_instruction import (
    ActivityInstructionAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.oauth.user import user
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import service_level_generic_filtering
from clinical_mdr_api.services.studies.study_selection_base import StudySelectionMixin
from clinical_mdr_api.services.syntax_instances.activity_instructions import (
    ActivityInstructionService,
)


class StudyActivityInstructionService(StudySelectionMixin):
    _repos: MetaRepository

    def __init__(self):
        self._repos = MetaRepository()
        self.author = user().id()

    @db.transaction
    def get_all_instructions_for_all_studies(
        self,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[models.StudyActivityInstruction]:
        query = StudyActivityInstructionNeoModel.nodes.fetch_relations(
            "study_value__latest_value",
            "study_activity",
            "activity_instruction_value__activity_instruction_root",
            "has_after__audit_trail",
        )
        items = [
            models.StudyActivityInstruction.from_orm(sai_node)
            for sai_node in to_relation_trees(query).distinct()
        ]

        # Do filtering, sorting, pagination and count
        filtered_items = service_level_generic_filtering(
            items=items,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )
        return filtered_items

    @db.transaction
    def get_all_instructions(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[models.StudyActivityInstruction]:
        if study_value_version:
            filters = {
                "study_value__has_version|version": study_value_version,
                "study_activity__has_study_activity__has_version|version": study_value_version,
                "study_value__has_version__uid": study_uid,
                "study_activity__has_study_activity__has_version__uid": study_uid,
            }
        else:
            filters = {
                "study_value__latest_value__uid": study_uid,
                "study_activity__has_study_activity__latest_value__uid": study_uid,
            }

        study_activity_instructions_ogm: list[models.StudyActivityInstruction] = [
            models.StudyActivityInstruction.from_orm(sai_node)
            for sai_node in to_relation_trees(
                StudyActivityInstructionNeoModel.nodes.fetch_relations(
                    "study_activity",
                    "study_value__has_version",
                    "activity_instruction_value__activity_instruction_root",
                    "has_after__audit_trail",
                ).filter(**filters)
            ).distinct()
        ]
        study_activity_instruction_response_model = [
            models.StudyActivityInstruction.from_vo(
                StudyActivityInstructionVO(
                    uid=i_study_activity_instruction_ogm.study_activity_instruction_uid,
                    study_uid=study_uid,
                    study_activity_uid=i_study_activity_instruction_ogm.study_activity_uid,
                    activity_instruction_uid=i_study_activity_instruction_ogm.activity_instruction_uid,
                    activity_instruction_name=i_study_activity_instruction_ogm.activity_instruction_name,
                    start_date=i_study_activity_instruction_ogm.start_date,
                    user_initials=i_study_activity_instruction_ogm.user_initials,
                ),
                study_value_version=study_value_version,
            )
            for i_study_activity_instruction_ogm in study_activity_instructions_ogm
        ]

        return study_activity_instruction_response_model

    def get_all_study_instructions_for_specific_study_activity(
        self, study_uid: str, study_activity_uid: str
    ) -> list[models.StudyActivityInstruction]:
        return [
            models.StudyActivityInstruction.from_orm(sas_node)
            for sas_node in to_relation_trees(
                StudyActivityInstructionNeoModel.nodes.fetch_relations(
                    "study_activity",
                    "activity_instruction_value__activity_instruction_root",
                    "has_after__audit_trail",
                ).filter(
                    study_value__latest_value__uid=study_uid,
                    study_activity__uid=study_activity_uid,
                    study_activity__has_study_activity__latest_value__uid=study_uid,
                )
            ).distinct()
        ]

    def _create_activity_instruction(
        self, activity_instruction_data: models.ActivityInstructionCreateInput
    ) -> ActivityInstructionAR:
        service = ActivityInstructionService()
        activity_instruction_ar = service.create_ar_from_input_values(
            activity_instruction_data
        )

        uid = activity_instruction_ar.uid
        if not service.repository.check_exists_by_name(activity_instruction_ar.name):
            service.repository.save(activity_instruction_ar)
        else:
            uid = service.repository.find_uid_by_name(name=activity_instruction_ar.name)
        activity_instruction_ar = service.repository.find_by_uid(uid, for_update=True)

        # if in draft status - approve
        if activity_instruction_ar.item_metadata.status == LibraryItemStatus.DRAFT:
            activity_instruction_ar.approve(self.author)
            service.repository.save(activity_instruction_ar)
        elif activity_instruction_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException(
                f"There is no approved activity instruction identified by provided uid ({uid})"
            )
        return activity_instruction_ar

    def _from_input_values(
        self,
        study_uid: str,
        activity_instruction_uid: str,
        study_activity_instruction_input: models.StudyActivityInstructionCreateInput,
    ) -> StudyActivityInstructionVO:
        return StudyActivityInstructionVO(
            study_uid=study_uid,
            study_activity_uid=study_activity_instruction_input.study_activity_uid,
            activity_instruction_uid=activity_instruction_uid,
            user_initials=self.author,
            start_date=datetime.datetime.now(datetime.timezone.utc),
        )

    @db.transaction
    def create(
        self,
        study_uid: str,
        study_activity_instruction_input: models.StudyActivityInstructionCreateInput,
    ) -> models.StudyActivityInstruction:
        """Create a new study activity instruction."""
        if study_activity_instruction_input.activity_instruction_data:
            # Create a new activity instruction first
            activity_instruction_ar = self._create_activity_instruction(
                study_activity_instruction_input.activity_instruction_data
            )
            activity_instruction_uid = activity_instruction_ar.uid
        else:
            # Link to an existing activity instruction
            activity_instruction_uid = (
                study_activity_instruction_input.activity_instruction_uid
            )
        instruction_vo = self._repos.study_activity_instruction_repository.save(
            self._from_input_values(
                study_uid, activity_instruction_uid, study_activity_instruction_input
            ),
            self.author,
        )
        return models.StudyActivityInstruction.from_vo(instruction_vo)

    @db.transaction
    def delete(self, study_uid: str, instruction_uid: str):
        try:
            self._repos.study_activity_instruction_repository.delete(
                study_uid, instruction_uid, self.author
            )
        finally:
            self._repos.close()

    def handle_batch_operations(
        self,
        study_uid: str,
        operations: list[models.StudyActivityInstructionBatchInput],
    ) -> list[models.StudyActivityInstructionBatchOutput]:
        results = []
        for operation in operations:
            result = {}
            item = None
            try:
                if operation.method == "POST":
                    item = self.create(study_uid, operation.content)
                    response_code = status.HTTP_201_CREATED
                else:
                    self.delete(
                        study_uid, operation.content.study_activity_instruction_uid
                    )
                    response_code = status.HTTP_204_NO_CONTENT
            except exceptions.MDRApiBaseException as error:
                result["response_code"] = error.status_code
                result["content"] = models.error.BatchErrorResponse(error)
            else:
                result["response_code"] = response_code
                if item:
                    result["content"] = item.dict()
            finally:
                results.append(models.StudyActivityInstructionBatchOutput(**result))
        return results
