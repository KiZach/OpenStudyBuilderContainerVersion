from fastapi import Body, Query, Response, status
from pydantic.types import Json

from clinical_mdr_api import config, models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.routers import study_router as router
from clinical_mdr_api.routers.studies import utils
from clinical_mdr_api.services.studies.study_activity_instruction import (
    StudyActivityInstructionService,
)


@router.get(
    "/study-activity-instructions",
    dependencies=[rbac.STUDY_READ],
    summary="Returns all study activity instructions currently selected",
    response_model=CustomPage[models.StudyActivityInstruction],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_activity_instructions_for_all_studies(
    sort_by: Json = Query(None, description=_generic_descriptions.SORT_BY),
    page_number: int
    | None = Query(1, ge=1, description=_generic_descriptions.PAGE_NUMBER),
    page_size: int
    | None = Query(
        config.DEFAULT_PAGE_SIZE,
        ge=0,
        le=config.MAX_PAGE_SIZE,
        description=_generic_descriptions.PAGE_SIZE,
    ),
    filters: Json
    | None = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: str | None = Query("and", description=_generic_descriptions.OPERATOR),
    total_count: bool
    | None = Query(False, description=_generic_descriptions.TOTAL_COUNT),
) -> CustomPage[models.StudyActivityInstruction]:
    service = StudyActivityInstructionService()
    all_selections = service.get_all_instructions_for_all_studies(
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
    )
    return CustomPage.create(
        items=all_selections.items,
        total=all_selections.total,
        page=page_number,
        size=page_size,
    )


@router.get(
    "/studies/{uid}/study-activity-instructions",
    dependencies=[rbac.STUDY_READ],
    summary="List all study activity instructions currently defined for the study",
    response_model=list[models.StudyActivityInstruction],
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
def get_all_selected_instructions(
    uid: str = utils.studyUID,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> list[models.StudyActivityInstruction]:
    service = StudyActivityInstructionService()
    return service.get_all_instructions(
        study_uid=uid, study_value_version=study_value_version
    )


@router.delete(
    "/studies/{uid}/study-activity-instructions/{study_activity_instruction_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Delete a study activity instruction",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the activity instruction and the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def delete_activity_instructon(
    uid: str = utils.studyUID,
    study_activity_instruction_uid: str = utils.study_activity_instruction_uid,
):
    service = StudyActivityInstructionService()
    service.delete(study_uid=uid, instruction_uid=study_activity_instruction_uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/studies/{uid}/study-activity-instructions/batch",
    dependencies=[rbac.STUDY_WRITE],
    summary="Batch operations (create, delete) for study activity instructions",
    response_model=list[models.StudyActivityInstructionBatchOutput],
    status_code=207,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def activity_instruction_batch_operations(
    uid: str = utils.studyUID,
    operations: list[models.StudyActivityInstructionBatchInput] = Body(
        description="List of operation to perform"
    ),
) -> list[models.StudyActivityInstructionBatchOutput]:
    service = StudyActivityInstructionService()
    return service.handle_batch_operations(uid, operations)
