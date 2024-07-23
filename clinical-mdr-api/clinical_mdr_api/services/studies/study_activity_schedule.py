import datetime

from fastapi import status
from neomodel import db

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.domain_repositories.models._utils import to_relation_trees
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyActivitySchedule as StudyActivityScheduleNeoModel,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_schedule_repository import (
    SelectionHistory,
)
from clinical_mdr_api.domains.study_selections.study_activity_schedule import (
    StudyActivityScheduleVO,
)
from clinical_mdr_api.oauth.user import user
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.studies.study_endpoint_selection import (
    StudySelectionMixin,
)
from clinical_mdr_api.telemetry import trace_calls


class StudyActivityScheduleService(StudySelectionMixin):
    _repos: MetaRepository

    def __init__(self):
        self._repos = MetaRepository()
        self.author = user().id()

    @trace_calls
    def get_all_schedules(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        operational: bool = False,
    ) -> list[models.StudyActivitySchedule]:
        study_activity_schedules = (
            self._repos.study_activity_schedule_repository._get_all_schedules_in_study(
                study_uid=study_uid,
                study_value_version=study_value_version,
                operational=operational,
            )
        )
        study_activity_schedules_response_model = [
            models.StudyActivitySchedule.from_vo(
                i_study_activity_schedule_ogm,
                study_value_version=study_value_version,
            )
            for i_study_activity_schedule_ogm in study_activity_schedules
        ]
        return study_activity_schedules_response_model

    def get_all_schedules_for_specific_visit(
        self, study_uid: str, study_visit_uid: str, detailed_soa: bool = True
    ) -> list[models.StudyActivitySchedule]:
        relations_to_fetch = [
            "has_after__audit_trail",
            "study_visit__has_visit_name__has_latest_value",
            "study_activity__has_selected_activity",
        ]
        filters = {
            "study_value__latest_value__uid": study_uid,
            "study_visit__uid": study_visit_uid,
            "study_visit__has_study_visit__latest_value__uid": study_uid,
        }
        if detailed_soa:
            filters.update(
                {"study_activity__has_study_activity__latest_value__uid": study_uid}
            )
        else:
            relations_to_fetch.append(
                "study_activity__study_activity_has_study_activity_instance"
            )
            filters.update(
                {
                    "study_activity__study_activity_has_study_activity_instance__has_study_activity_instance__latest_value__uid": study_uid
                }
            )
        return [
            models.StudyActivitySchedule.from_orm(sas_node)
            for sas_node in to_relation_trees(
                StudyActivityScheduleNeoModel.nodes.fetch_relations(*relations_to_fetch)
                .filter(**filters)
                .order_by("uid")
            ).distinct()
        ]

    def get_all_schedules_for_specific_activity(
        self, study_uid: str, study_activity_uid: str
    ) -> list[models.StudyActivitySchedule]:
        return [
            models.StudyActivitySchedule.from_orm(sas_node)
            for sas_node in to_relation_trees(
                StudyActivityScheduleNeoModel.nodes.fetch_relations(
                    "has_after__audit_trail",
                    "study_visit__has_visit_name__has_latest_value",
                    "study_activity__has_selected_activity",
                    "study_activity__has_study_activity",
                )
                .filter(
                    study_value__latest_value__uid=study_uid,
                    study_activity__uid=study_activity_uid,
                    study_visit__has_study_visit__latest_value__uid=study_uid,
                    study_activity__has_study_activity__latest_value__uid=study_uid,
                )
                .order_by("uid")
            ).distinct()
        ]

    def _from_input_values(
        self, study_uid: str, schedule_input: models.StudyActivityScheduleCreateInput
    ) -> StudyActivityScheduleVO:
        return StudyActivityScheduleVO(
            study_uid=study_uid,
            study_activity_uid=schedule_input.study_activity_uid,
            study_activity_instance_uid=None,
            study_visit_uid=schedule_input.study_visit_uid,
            user_initials=self.author,
            start_date=datetime.datetime.now(datetime.timezone.utc),
        )

    @db.transaction
    def create(
        self, study_uid: str, schedule_input: models.StudyActivityScheduleCreateInput
    ) -> models.StudyActivitySchedule:
        schedule_vo = self._repos.study_activity_schedule_repository.save(
            self._from_input_values(study_uid, schedule_input), self.author
        )
        return models.StudyActivitySchedule.from_vo(schedule_vo)

    @db.transaction
    def delete(self, study_uid: str, schedule_uid: str):
        try:
            self._repos.study_activity_schedule_repository.delete(
                study_uid, schedule_uid, self.author
            )
        finally:
            self._repos.close()

    def _transform_history_to_response_model(
        self, study_selection_history: list[SelectionHistory], study_uid: str
    ) -> list[models.StudyActivitySchedule]:
        result = []
        for history in study_selection_history:
            result.append(
                models.StudyActivityScheduleHistory(
                    study_uid=study_uid,
                    study_activity_schedule_uid=history.study_selection_uid,
                    study_activity_uid=history.study_activity_uid,
                    study_activity_instance_uid=history.study_activity_instance_uid,
                    study_visit_uid=history.study_visit_uid,
                    modified=history.start_date,
                )
            )
        return result

    def _transform_all_to_response_model(
        self,
        study_selection: list[SelectionHistory],
        study_uid: str,
    ) -> list[models.StudyActivitySchedule]:
        result = []
        for history in study_selection:
            result.append(
                models.StudyActivityScheduleHistory(
                    study_uid=study_uid,
                    study_activity_schedule_uid=history.study_selection_uid,
                    study_activity_uid=history.study_activity_uid,
                    study_visit_uid=history.study_visit_uid,
                    modified=history.start_date,
                )
            )
        return result

    @db.transaction
    def get_all_schedules_audit_trail(self, study_uid: str):
        repos = self._repos
        try:
            try:
                selection_history = (
                    repos.study_activity_schedule_repository.find_selection_history(
                        study_uid
                    )
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(value_error.args[0])

            return self._transform_history_to_response_model(
                selection_history, study_uid
            )
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection_audit_trail(
        self, study_uid: str, schedule_uid: str
    ) -> list[models.StudyActivitySchedule]:
        repos = self._repos
        try:
            try:
                selection_history = (
                    repos.study_activity_schedule_repository.find_selection_history(
                        study_uid, schedule_uid
                    )
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(value_error.args[0])

            return self._transform_history_to_response_model(
                selection_history, study_uid
            )
        finally:
            repos.close()

    def handle_batch_operations(
        self,
        study_uid: str,
        operations: list[models.StudyActivityScheduleBatchInput],
    ) -> list[models.StudyActivityScheduleBatchOutput]:
        results = []
        for operation in operations:
            result = {}
            item = None
            try:
                if operation.method == "POST":
                    item = self.create(study_uid, operation.content)
                    response_code = status.HTTP_201_CREATED
                else:
                    self.delete(study_uid, operation.content.uid)
                    response_code = status.HTTP_204_NO_CONTENT
            except exceptions.MDRApiBaseException as error:
                result["response_code"] = error.status_code
                result["content"] = models.error.BatchErrorResponse(message=str(error))
            else:
                result["response_code"] = response_code
                if item:
                    result["content"] = item.dict()
            finally:
                results.append(models.StudyActivityScheduleBatchOutput(**result))
        return results
