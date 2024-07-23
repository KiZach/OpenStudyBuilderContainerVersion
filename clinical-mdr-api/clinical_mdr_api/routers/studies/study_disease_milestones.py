from typing import Any

from fastapi import Body, Path, Query, Request, Response, status
from pydantic.types import Json

from clinical_mdr_api import config
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.study_selections import study_disease_milestone
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers import study_router as router
from clinical_mdr_api.services.studies.study_disease_milestone import (
    StudyDiseaseMilestoneService,
)

studyUID = Path(..., description="The unique id of the study.")

study_disease_milestone_uid_description = Path(
    None, description="The unique id of the study disease_milestone."
)


"""
    API endpoints to study disease_milestones
"""


@router.get(
    "/studies/{uid}/study-disease-milestones",
    dependencies=[rbac.STUDY_READ],
    summary="List all study disease_milestones currently selected for the study.",
    description=f"""
State before:
 - Study must exist.
 
Business logic:
 - By default (no study status is provided) list all study disease_milestones for the study uid in status draft. If the study not exist in status draft then return the study disease_milestones for the study in status released. If the study uid only exist as deleted then this is returned.
 - If a specific study status parameter is provided then return study disease_milestone for this study status.
 - If the locked study status parameter is requested then a study version should also be provided, and then the study disease_milestones for the specific locked study version is returned.
 - Indicate by an boolean variable if the study disease_milestone can be updated (if the selected study is in status draft).  
 - Indicate by an boolean variable if all expected selections have been made for each study disease_milestones, or some are missing.
   - e.g. duration time unit must is expected.

State after:
 - no change.
 
Possible errors:
 - Invalid study-uid.

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=CustomPage[study_disease_milestone.StudyDiseaseMilestone],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "order",
            "disease_milestone_type",
            "disease_milestone_type_named",
            "disease_milestone_type_definition",
            "repetition_indicator",
            "study_uid",
            "study_version",
        ],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
# pylint: disable=unused-argument
def get_all(
    request: Request,  # request is actually required by the allow_exports decorator
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
    uid: str = Path(description="the study"),
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> CustomPage[study_disease_milestone.StudyDiseaseMilestone]:
    disease_milestone_service = StudyDiseaseMilestoneService()
    all_items = disease_milestone_service.get_all_disease_milestones(
        study_uid=uid,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
        study_value_version=study_value_version,
    )

    return CustomPage.create(
        items=all_items.items,
        total=all_items.total,
        page=page_number,
        size=page_size,
    )


@router.get(
    "/studies/{uid}/study-disease-milestones/headers",
    dependencies=[rbac.STUDY_READ],
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=list[Any],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
# pylint: disable=unused-argument
def get_distinct_values_for_header(
    uid: str = studyUID,  # TODO: Use this argument!
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
    field_name: str = Query(..., description=_generic_descriptions.HEADER_FIELD_NAME),
    search_string: str
    | None = Query("", description=_generic_descriptions.HEADER_SEARCH_STRING),
    filters: Json
    | None = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: str | None = Query("and", description=_generic_descriptions.OPERATOR),
    result_count: int
    | None = Query(10, description=_generic_descriptions.HEADER_RESULT_COUNT),
):
    service = StudyDiseaseMilestoneService()
    return service.get_distinct_values_for_header(
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.get(
    "/studies/{uid}/study-disease-milestones/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List audit trail related to all study disease_milestones within the specified study-uid",
    description="""
State before:
 - Study and study disease_milestone must exist.

Business logic:
 - List all study disease_milestone audit trail within the specified study-uid.
 - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.

State after:
 - no change.
 
Possible errors:
 - Invalid study-uid.
     """,
    response_model=list[study_disease_milestone.StudyDiseaseMilestoneVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the provided study.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_study_disease_milestones_all_audit_trail(
    uid: str = studyUID,
) -> list[study_disease_milestone.StudyDiseaseMilestoneVersion]:
    service = StudyDiseaseMilestoneService()
    return service.audit_trail_all_disease_milestones(uid)


@router.get(
    "/studies/{uid}/study-disease-milestones/{study_disease_milestone_uid}",
    dependencies=[rbac.STUDY_READ],
    summary="List all definitions for a specific study disease_milestone",
    description="""
State before:
 - Study and study disease_milestone must exist
 
Business logic:
 - By default (no study status is provided) list all details for specified study disease_milestone for the study uid in status draft. If the study not exist in status draft then return the study disease_milestones for the study in status released. If the study uid only exist as deleted then this is returned.
 - If a specific study status parameter is provided then return study disease_milestones for this study status.
 - If the locked study status parameter is requested then a study version should also be provided, and then the specified study disease_milestone  for the specific locked study version is returned.
 - Indicate by an boolean variable if the study disease_milestone can be updated (if the selected study is in status draft).
 - Indicate by an boolean variable if all expected selections have been made for each study disease_milestone , or some are missing.
 - e.g. disease_milestone level, minimum one timeframe and one unit is expected.
 - Indicate by an boolean variable if the selected disease_milestone is available in a newer version.
 
State after:
 - no change
 
Possible errors:
 - Invalid study-uid or study_disease_milestone Uid.
    """,
    response_model=study_disease_milestone.StudyDiseaseMilestone,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no disease_milestone for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
# pylint: disable=unused-argument
def get_study_disease_milestone(
    uid: str = studyUID,
    study_disease_milestone_uid: str = study_disease_milestone_uid_description,
) -> study_disease_milestone.StudyDiseaseMilestone:
    service = StudyDiseaseMilestoneService()
    return service.find_by_uid(study_disease_milestone_uid)


@router.get(
    "/studies/{uid}/study-disease-milestones/{study_disease_milestone_uid}/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List audit trail related to definition of a specific study disease_milestone",
    description="""
State before:
 - Study and study disease_milestones must exist.

Business logic:
 - List a specific entry in the audit trail related to the specified study disease_milestone for the specified study-uid.
 - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.

State after:
 - no change.
 
Possible errors:
 - Invalid study-uid.
     """,
    response_model=list[study_disease_milestone.StudyDiseaseMilestoneVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the disease milestone provided for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_study_disease_milestone_audit_trail(
    uid: str = studyUID,
    study_disease_milestone_uid: str = study_disease_milestone_uid_description,
) -> list[study_disease_milestone.StudyDiseaseMilestoneVersion]:
    service = StudyDiseaseMilestoneService()
    return service.audit_trail(
        study_uid=uid, disease_milestone_uid=study_disease_milestone_uid
    )


@router.post(
    "/studies/{uid}/study-disease-milestones",
    dependencies=[rbac.STUDY_WRITE],
    summary="Add a study disease_milestone to a study",
    description="""
State before:
 - Study must exist and study status must be in draft.

Business logic:
 - Add a study disease_milestone to a study based on selection of an DiseaseMilestone CT Term.
- Update the order value of all other disease_milestones for this study to be consecutive.

State after:
 - DiseaseMilestone is added as study disease_milestone to the study.
 - Added new entry in the audit trail for the creation of the study-disease_milestone.
 
Possible errors:
 - Invalid study-uid or DiseaseMilestone CT Term uid.
    """,
    response_model=study_disease_milestone.StudyDiseaseMilestone,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the disease_milestone",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def post_new_disease_milestone_create(
    uid: str = studyUID,
    selection: study_disease_milestone.StudyDiseaseMilestoneCreateInput = Body(
        description="Related parameters of the selection that shall be created."
    ),
) -> study_disease_milestone.StudyDiseaseMilestone:
    service = StudyDiseaseMilestoneService()
    return service.create(study_uid=uid, study_disease_milestone_input=selection)


@router.delete(
    "/studies/{uid}/study-disease-milestones/{study_disease_milestone_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Delete a study disease_milestone.",
    description="""
State before:
 - Study must exist and study status must be in draft.
 - study-disease_milestone-uid must exist. 

Business logic:
 - Remove specified study-disease_milestone from the study.
 - Reference to the study-disease_milestone should still exist in the audit trail.
- Update the order value of all other disease_milestones for this study to be consecutive.

State after:
- Study disease_milestoneis deleted from the study, but still exist as a node in the database with a reference from the audit trail.
- Added new entry in the audit trail for the deletion of the study-disease_milestone.
 
Possible errors:
- Invalid study-uid or study_disease_milestone_uid.
    """,
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - the study or disease_milestone does not exist.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
# pylint: disable=unused-argument
def delete_study_disease_milestone(
    uid: str = studyUID,  # TODO: Use this argument!
    study_disease_milestone_uid: str = study_disease_milestone_uid_description,
):
    service = StudyDiseaseMilestoneService()

    service.delete(study_disease_milestone_uid=study_disease_milestone_uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/studies/{uid}/study-disease-milestones/{study_disease_milestone_uid}/order",
    dependencies=[rbac.STUDY_WRITE],
    summary="Change display order of study disease_milestone",
    description="""
State before:
 - Study must exist and study status must be in draft.
 - study_disease_milestone_uid must exist. 
 - Old order number must match current order number in database for study disease_milestone.

Business logic:
 - Old order number must match existing order number in the database for specified study disease_milestone.
 - New order number must be increased or decreased with one.
 - If order number is decreased with 1, then the old order number must be > 1 and a preceding study disease_milestone must exist (the specified study disease_milestone cannot be the first on the list).
   - The specified study disease_milestone get the order number set to be the new order number and the preceding study disease_milestone get the order number to be the old order number.
 - If order number is increased with 1, then a following study disease_milestone must exist (the specified study disease_milestone cannot be the last on the list).
   - The specified study disease_milestone get the order number set to be the new order number and the following study disease_milestone  get the order number to be the old order number.

State after:
 - Order number for specified study disease_milestone is updated to new order number.
 - Note this will change order on either the preceding or following study disease_milestone as well.
 - Added new entry in the audit trail for the re-ordering of the study disease_milestone.

Possible errors:
 - Invalid study-uid, study_disease_milestone_uid
 - Old order number do not match current order number in database.
 - New order number not an increase or decrease of 1
 - Decrease order number for the first study disease_milestone on the list
 - Increase order number for the last study disease_milestone on the list
    """,
    response_model=study_disease_milestone.StudyDiseaseMilestone,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and disease_milestone to reorder.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
# pylint: disable=unused-argument
def patch_reorder(
    uid: str = studyUID,  # TODO: Use this argument!
    study_disease_milestone_uid: str = study_disease_milestone_uid_description,
    new_order_input: study_disease_milestone.StudySelectionDiseaseMilestoneNewOrder = Body(
        description="New value to set for the order property of the selection"
    ),
) -> study_disease_milestone.StudyDiseaseMilestone:
    service = StudyDiseaseMilestoneService()
    return service.reorder(
        study_disease_milestone_uid=study_disease_milestone_uid,
        new_order=new_order_input.new_order,
    )


@router.patch(
    "/studies/{uid}/study-disease-milestones/{study_disease_milestone_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Edit a study disease_milestone",
    description="""
State before:
 - Study must exist and study status must be in draft.

Business logic:
 - Same logic applies as for selecting or creating an study disease_milestone (see two POST statements for /study-disease-milestones)
 - Update the order value of all other disease_milestones for this study to be consecutive.

State after:
 - DiseaseMilestone is added as study disease_milestone to the study.
 - This PATCH method can cover cover two parts:

 - Added new entry in the audit trail for the update of the study-disease_milestone.

Possible errors:
 - Invalid study-uid or study_disease_milestone_uid .
    """,
    response_model=study_disease_milestone.StudyDiseaseMilestone,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no study or disease_milestone .",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
# pylint: disable=unused-argument
def patch_update_disease_milestone(
    uid: str = studyUID,
    study_disease_milestone_uid: str = study_disease_milestone_uid_description,
    selection: study_disease_milestone.StudyDiseaseMilestoneEditInput = Body(
        description="Related parameters of the selection that shall be created."
    ),
) -> study_disease_milestone.StudyDiseaseMilestone:
    service = StudyDiseaseMilestoneService()
    return service.edit(
        study_disease_milestone_uid=study_disease_milestone_uid,
        study_disease_milestone_input=selection,
    )
