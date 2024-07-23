from fastapi import Body, Query, Response, status

from clinical_mdr_api import models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.routers import study_router as router
from clinical_mdr_api.routers.studies import utils
from clinical_mdr_api.services.studies.study_activity_schedule import (
    StudyActivityScheduleService,
)


@router.get(
    "/studies/{uid}/study-activity-schedules",
    dependencies=[rbac.STUDY_READ],
    summary="List all study activity schedules currently defined for the study",
    response_model=list[models.StudyActivitySchedule],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there is no study with the given uid.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_selected_activities(
    uid: str = utils.studyUID,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
    operational: bool
    | None = Query(
        False,
        description="List scheduled study activity instances instead of study activities",
    ),
) -> list[models.StudyActivitySchedule]:
    service = StudyActivityScheduleService()
    return service.get_all_schedules(
        study_uid=uid, study_value_version=study_value_version, operational=operational
    )


@router.post(
    "/studies/{uid}/study-activity-schedules",
    dependencies=[rbac.STUDY_WRITE],
    summary="Add a study activity schedule to a study",
    response_model=models.StudyActivitySchedule,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - A study activity schedule already exists for selected study activity and visit",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study, study activity or study visit is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def post_new_activity_schedule_create(
    uid: str = utils.studyUID,
    selection: models.StudyActivityScheduleCreateInput = Body(
        description="Related parameters of the schedule that shall be created."
    ),
) -> models.StudyActivitySchedule:
    service = StudyActivityScheduleService()
    return service.create(study_uid=uid, schedule_input=selection)


@router.delete(
    "/studies/{uid}/study-activity-schedules/{study_activity_schedule_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Delete a study activity schedule",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the activity schedule and the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def delete_activity_schedule(
    uid: str = utils.studyUID,
    study_activity_schedule_uid: str = utils.study_activity_schedule_uid,
):
    service = StudyActivityScheduleService()
    service.delete(study_uid=uid, schedule_uid=study_activity_schedule_uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/studies/{uid}/study-activity-schedules/audit-trail/",
    dependencies=[rbac.STUDY_READ],
    summary="List full audit trail related to definition of all study activity schedules.",
    description="""
The following values should be returned for all study activities:
- date_time
- user_initials
- action
- activity
- order
    """,
    response_model=list[models.StudyActivityScheduleHistory],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_schedules_audit_trail(
    uid: str = utils.studyUID,
) -> list[models.StudyActivityScheduleHistory]:
    service = StudyActivityScheduleService()
    return service.get_all_schedules_audit_trail(study_uid=uid)


@router.post(
    "/studies/{uid}/study-activity-schedules/batch",
    dependencies=[rbac.STUDY_WRITE],
    summary="Batch operations (create, delete) for study activity schedules",
    response_model=list[models.StudyActivityScheduleBatchOutput],
    status_code=207,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def activity_schedule_batch_operations(
    uid: str = utils.studyUID,
    operations: list[models.StudyActivityScheduleBatchInput] = Body(
        description="List of operation to perform"
    ),
) -> list[models.StudyActivityScheduleBatchOutput]:
    service = StudyActivityScheduleService()
    return service.handle_batch_operations(uid, operations)
