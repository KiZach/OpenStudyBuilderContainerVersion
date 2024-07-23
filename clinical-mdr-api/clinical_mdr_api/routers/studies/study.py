import os
from typing import Any

from fastapi import APIRouter, Body, Path, Query, Request, Response, status
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic.types import Json

from clinical_mdr_api import config, models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage, GenericFilteringReturn
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_activity_group import (
    StudyActivityGroupService,
)
from clinical_mdr_api.services.studies.study_activity_instance_selection import (
    StudyActivityInstanceSelectionService,
)
from clinical_mdr_api.services.studies.study_activity_selection import (
    StudyActivitySelectionService,
)
from clinical_mdr_api.services.studies.study_activity_subgroup import (
    StudyActivitySubGroupService,
)
from clinical_mdr_api.services.studies.study_arm_selection import (
    StudyArmSelectionService,
)
from clinical_mdr_api.services.studies.study_branch_arm_selection import (
    StudyBranchArmSelectionService,
)
from clinical_mdr_api.services.studies.study_cohort_selection import (
    StudyCohortSelectionService,
)
from clinical_mdr_api.services.studies.study_compound_selection import (
    StudyCompoundSelectionService,
)
from clinical_mdr_api.services.studies.study_criteria_selection import (
    StudyCriteriaSelectionService,
)
from clinical_mdr_api.services.studies.study_element_selection import (
    StudyElementSelectionService,
)
from clinical_mdr_api.services.studies.study_endpoint_selection import (
    StudyEndpointSelectionService,
)
from clinical_mdr_api.services.studies.study_objective_selection import (
    StudyObjectiveSelectionService,
)
from clinical_mdr_api.services.studies.study_objectives import StudyObjectivesService
from clinical_mdr_api.services.studies.study_soa_group import StudySoAGroupService

# Mounted without a path-prefix
router = APIRouter()

studyUID = Path(None, description="The unique id of the study.")
study_selection_uid = Path(None, description="The unique id of the study selection.")
PROJECT_NAME = Query(
    None,
    description="Optionally, the name of the project for which to return study selections.",
)
PROJECT_NUMBER = Query(
    None,
    description="Optionally, the number of the project for which to return study selections.",
)


"""
    API endpoints to study objectives
"""


@router.get(
    "/study-objectives",
    dependencies=[rbac.STUDY_READ],
    summary="Returns all study objectives currently selected",
    response_model=CustomPage[models.StudySelectionObjective],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_selected_objectives_for_all_studies(
    no_brackets: bool = Query(
        False,
        description="Indicates whether brackets around Template Parameters in the Objective"
        "should be returned",
    ),
    project_name: str | None = PROJECT_NAME,
    project_number: str | None = PROJECT_NUMBER,
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
) -> CustomPage[models.StudySelectionObjective]:
    service = StudyObjectiveSelectionService()
    all_selections = service.get_all_selections_for_all_studies(
        no_brackets=no_brackets,
        project_name=project_name,
        project_number=project_number,
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
    "/study-objectives/headers",
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
def get_distinct_objective_values_for_header(
    project_name: str | None = PROJECT_NAME,
    project_number: str | None = PROJECT_NUMBER,
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
    service = StudyObjectiveSelectionService()
    return service.get_distinct_values_for_header(
        project_name=project_name,
        project_number=project_number,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.get(
    "/studies/{uid}/study-objectives",
    dependencies=[rbac.STUDY_READ],
    summary="Returns all study objectives currently selected for study with provided uid",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    response_model=GenericFilteringReturn[models.StudySelectionObjective],
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
            "study_objective_uid",
            "order",
            "objective_level=objective_level.sponsor_preferred_name",
            "name_plain=objective.name_plain",
            "name=objective.name",
            "guidance_text=objective_template.guidance_text",
            "endpoint_count",
            "start_date",
            "user_initials",
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
def get_all_selected_objectives(
    request: Request,  # request is actually required by the allow_exports decorator
    uid: str = studyUID,
    no_brackets: bool = Query(
        False,
        description="Indicates whether brackets around Template Parameters in the Objective"
        "should be returned",
    ),
    filters: Json
    | None = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    page_number: int
    | None = Query(1, ge=1, description=_generic_descriptions.PAGE_NUMBER),
    page_size: int
    | None = Query(
        config.DEFAULT_PAGE_SIZE,
        ge=0,
        le=config.MAX_PAGE_SIZE,
        description=_generic_descriptions.PAGE_SIZE,
    ),
    operator: str | None = Query("and", description=_generic_descriptions.OPERATOR),
    total_count: bool
    | None = Query(False, description=_generic_descriptions.TOTAL_COUNT),
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> GenericFilteringReturn[models.StudySelectionObjective]:
    service = StudyObjectiveSelectionService()
    return service.get_all_selection(
        study_uid=uid,
        no_brackets=no_brackets,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        study_value_version=study_value_version,
    )


@router.get(
    "/studies/{uid}/study-objectives/headers",
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
def get_distinct_values_for_header(
    uid: str = studyUID,
    project_name: str | None = PROJECT_NAME,
    project_number: str | None = PROJECT_NUMBER,
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
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
):
    service = StudyObjectiveSelectionService()
    return service.get_distinct_values_for_header(
        study_uid=uid,
        project_name=project_name,
        project_number=project_number,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
        study_value_version=study_value_version,
    )


@router.get(
    "/studies/{uid}/study-objectives/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List full audit trail related to definition of all study objectives.",
    description="""
The following values should be return for all study objectives.
- date_time
- user_initials
- action
- objective_template
- objective
- objective_level
- order
    """,
    response_model=list[models.StudySelectionObjectiveCore],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_objectives_audit_trail(
    uid: str = studyUID,
) -> list[models.StudySelectionObjectiveCore]:
    service = StudyObjectiveSelectionService()
    return service.get_all_selection_audit_trail(study_uid=uid)


@router.get(
    "/studies/{uid}/study-objectives/{study_objective_uid}",
    dependencies=[rbac.STUDY_READ],
    summary="Returns specific study objective",
    response_model=models.StudySelectionObjective,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the objective for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_selected_objective(
    uid: str = studyUID,
    study_objective_uid: str = study_selection_uid,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> models.StudySelectionObjective:
    service = StudyObjectiveSelectionService()
    return service.get_specific_selection(
        study_uid=uid,
        study_selection_uid=study_objective_uid,
        study_value_version=study_value_version,
    )


@router.get(
    "/studies/{uid}/study-objectives/{study_objective_uid}/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List audit trail related to definition of a specific study objective.",
    description="""
The following values should be return for selected study objective:
- date_time
- user_initials
- action
- objective_template
- objective
- objective_level
- order
    """,
    response_model=list[models.StudySelectionObjectiveCore],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the objective for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_selected_objective_audit_trail(
    uid: str = studyUID,
    study_objective_uid: str = study_selection_uid,
) -> models.StudySelectionObjectiveCore:
    service = StudyObjectiveSelectionService()
    return service.get_specific_selection_audit_trail(
        study_uid=uid, study_selection_uid=study_objective_uid
    )


@router.post(
    "/studies/{uid}/study-objectives",
    dependencies=[rbac.STUDY_WRITE],
    summary="Creating a study objective selection based on the input data, including optionally creating a library objective",
    response_model=models.StudySelectionObjective,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the objective",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or objective is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def post_new_objective_selection_create(
    uid: str = studyUID,
    selection: models.study_selections.study_selection.StudySelectionObjectiveCreateInput
    | models.study_selections.study_selection.StudySelectionObjectiveInput = Body(
        description="Parameters of the selection that shall be created."
    ),
    create_objective: bool = Query(
        False,
        description="Indicates whether the specified objective should be created in the library.\n"
        "- If this parameter is set to `true`, a `StudySelectionObjectiveCreateInput` payload needs to be sent.\n"
        "- Otherwise, `StudySelectionObjectiveInput` payload should be sent, referencing an existing library objective by uid.",
    ),
) -> models.StudySelectionObjective:
    service = StudyObjectiveSelectionService()

    if create_objective:
        return service.make_selection_create_objective(
            study_uid=uid, selection_create_input=selection
        )
    return service.make_selection(study_uid=uid, selection_create_input=selection)


@router.post(
    "/studies/{uid}/study-objectives/batch-select",
    dependencies=[rbac.STUDY_WRITE],
    summary="Select multiple objective templates as a batch. If the template has no parameters, will also create the instance.",
    description="""
    State before:
    - Study must exist and study status must be in draft.

    Business logic:
    - Select objective template without instantiating them.
    - This must be done as a batch

    State after:
    - Study objectives are created.
    - Objective templates are all selected by the study objective.
    - If a given template has no parameters, the instance will be created and selected.
    - Added new entry in the audit trail for the creation of the study-objective.

    Possible errors:
    - Invalid study-uid.
    - Invalid study-objective-template-uid.

    Returned data:
    List selected objective templates/instances with the following information:
    - study_uid
    - study_objective_template_uid / study_objective_uid
    - order (Derived Integer)
    - latest version of the selected objective template/instance
    """,
    response_model=list[models.StudySelectionObjective],
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the objective",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or objective is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def post_batch_select_objective_template(
    uid: str = studyUID,
    selection: list[
        models.study_selections.study_selection.StudySelectionObjectiveTemplateSelectInput
    ] = Body(
        description="List of objects with properties needed to identify the templates to select",
    ),
) -> models.StudySelectionObjective:
    service = StudyObjectiveSelectionService()
    return service.batch_select_objective_template(
        study_uid=uid, selection_create_input=selection
    )


@router.post(
    "/studies/{uid}/study-objectives/preview",
    dependencies=[rbac.STUDY_WRITE],
    summary="Preview creating a study objective selection based on the input data",
    response_model=models.StudySelectionObjective,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the objective",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or objective is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def preview_new_objective_selection_create(
    uid: str = studyUID,
    selection: models.study_selections.study_selection.StudySelectionObjectiveCreateInput = Body(
        description="Related parameters of the selection that shall be previewed."
    ),
) -> models.StudySelectionObjective:
    service = StudyObjectiveSelectionService()
    return service.make_selection_preview_objective(
        study_uid=uid, selection_create_input=selection
    )


@router.delete(
    "/studies/{uid}/study-objectives/{study_objective_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Deletes a study objective",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the objective and the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def delete_selected_objective(
    uid: str = studyUID,
    study_objective_uid: str = study_selection_uid,
):
    service = StudyObjectiveSelectionService()
    service.delete_selection(study_uid=uid, study_selection_uid=study_objective_uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/studies/{uid}/study-objectives/{study_objective_uid}/order",
    dependencies=[rbac.STUDY_WRITE],
    summary="Change a order of a study objective",
    response_model=models.StudySelectionObjective,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and objective to reorder.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_new_objective_selection_order(
    uid: str = studyUID,
    study_objective_uid: str = study_selection_uid,
    new_order_input: models.StudySelectionObjectiveNewOrder = Body(
        description="Related parameters of the selection that shall be created."
    ),
) -> models.StudySelectionObjective:
    service = StudyObjectiveSelectionService()
    return service.set_new_order(
        study_uid=uid,
        study_selection_uid=study_objective_uid,
        new_order=new_order_input.new_order,
    )


@router.patch(
    "/studies/{uid}/study-objectives/{study_objective_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="update the objective level of a study objective",
    response_model=models.StudySelectionObjective,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and objective.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_update_objective_selection(
    uid: str = studyUID,
    study_objective_uid: str = study_selection_uid,
    selection: models.StudySelectionObjectiveInput = Body(
        description="Related parameters of the selection that shall be created."
    ),
) -> models.StudySelectionObjective:
    service = StudyObjectiveSelectionService()
    return service.patch_selection(
        study_uid=uid,
        study_selection_uid=study_objective_uid,
        selection_update_input=selection,
    )


@router.post(
    "/studies/{uid}/study-objectives/{study_objective_uid}/sync-latest-version",
    dependencies=[rbac.STUDY_WRITE],
    summary="update to latest objective version study selection",
    response_model=models.StudySelectionObjective,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and objective.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def sync_latest_version(
    uid: str = studyUID,
    study_objective_uid: str = study_selection_uid,
) -> models.StudySelectionObjective:
    service = StudyObjectiveSelectionService()
    return service.update_selection_to_latest_version(
        study_uid=uid, study_selection_uid=study_objective_uid
    )


# API endpoints to study endpoints


@router.get(
    "/study-endpoints",
    dependencies=[rbac.STUDY_READ],
    summary="Returns all study endpoints currently selected",
    response_model=CustomPage[models.StudySelectionEndpoint],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_selected_endpoints_for_all_studies(
    no_brackets: bool = Query(
        False,
        description="Indicates whether brackets around Template Parameters in the Endpoint"
        "should be returned",
    ),
    project_name: str | None = PROJECT_NAME,
    project_number: str | None = PROJECT_NUMBER,
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
) -> CustomPage[models.StudySelectionEndpoint]:
    service = StudyEndpointSelectionService()
    all_selections = service.get_all_selections_for_all_studies(
        no_brackets=no_brackets,
        project_name=project_name,
        project_number=project_number,
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
    "/study-endpoints/headers",
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
def get_distinct_endpoint_values_for_header(
    project_name: str | None = PROJECT_NAME,
    project_number: str | None = PROJECT_NUMBER,
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
    service = StudyEndpointSelectionService()
    return service.get_distinct_values_for_header(
        project_name=project_name,
        project_number=project_number,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.get(
    "/studies/{uid}/study-endpoints",
    dependencies=[rbac.STUDY_READ],
    summary="""List all study endpoints currently selected for study with provided uid""",
    description=f"""
State before:
- Study must exist.

Business logic:
 - By default (no study status is provided) list all study endpoints for the study uid in status draft. If the study not exist in status draft then return the study endpoints for the study in status released. If the study uid only exist as deleted then this is returned.
- If a specific study status parameter is provided then return study endpoints for this study status.
- If the locked study status parameter is requested then a study version should also be provided, and then the study endpoints for the specific locked study version is returned.
- Indicate by an boolean variable if the study endpoint can be updated (if the selected study is in status draft).
- Indicate by an boolean variable if all expected selections have been made for each study endpoint, or some are missing.
   - e.g. endpoint level, minimum one timeframe and one unit is expected.
 - Indicate by an boolean variable if the selected endpoint is available in a newer version.
 - Indicate by an boolean variable if a study endpoint can be re-ordered.

State after:
- no change.

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=GenericFilteringReturn[models.StudySelectionEndpoint],
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
            "study_endpoint_uid",
            "order",
            "name_plain=endpoint.name_plain",
            "name=endpoint.name",
            "guidance_text=endpoint_template.guidance_text",
            "units=endpoint_units.units",
            "timeframe=timeframe.name",
            "objective=study_objective",
            "start_date",
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
def get_all_selected_endpoints(
    request: Request,  # request is actually required by the allow_exports decorator
    uid: str = studyUID,
    no_brackets: bool = Query(
        False,
        description="Indicates whether brackets around Template Parameters in the Objective"
        "and Endpoint should be returned",
    ),
    filters: Json
    | None = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    page_number: int
    | None = Query(1, ge=1, description=_generic_descriptions.PAGE_NUMBER),
    page_size: int
    | None = Query(
        config.DEFAULT_PAGE_SIZE,
        ge=0,
        le=config.MAX_PAGE_SIZE,
        description=_generic_descriptions.PAGE_SIZE,
    ),
    operator: str | None = Query("and", description=_generic_descriptions.OPERATOR),
    total_count: bool
    | None = Query(False, description=_generic_descriptions.TOTAL_COUNT),
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> GenericFilteringReturn[models.StudySelectionEndpoint]:
    service = StudyEndpointSelectionService()
    return service.get_all_selection(
        study_uid=uid,
        no_brackets=no_brackets,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        study_value_version=study_value_version,
    )


@router.get(
    "/studies/{uid}/study-endpoints/headers",
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
def get_distinct_study_endpoint_values_for_header(
    uid: str = studyUID,
    project_name: str | None = PROJECT_NAME,
    project_number: str | None = PROJECT_NUMBER,
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
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
):
    service = StudyEndpointSelectionService()
    return service.get_distinct_values_for_header(
        study_uid=uid,
        project_name=project_name,
        project_number=project_number,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
        study_value_version=study_value_version,
    )


@router.get(
    "/studies/{uid}/study-endpoints/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List full audit trail related to definition of all study endpoints.",
    description="""
Parameters:
 - uid as study-uid (required)
 - [NOT YET IMPLEMENTED] study status (optional)
 - [NOT YET IMPLEMENTED] study version (required when study status is locked)

State before:
 - Study must exist.

Business logic:
 - List all entries in the audit trail related to study endpoints for specified study-uid.
 - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.

State after:
 - no change.
 
Possible errors:
 - Invalid study-uid.

Returned data:
 - List of actions and changes related to study endpoints.
    """,
    response_model=list[models.StudySelectionEndpoint],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_endpoints_audit_trail(
    uid: str = studyUID,
) -> list[models.StudySelectionEndpoint]:
    service = StudyEndpointSelectionService()
    return service.get_all_selection_audit_trail(study_uid=uid)


@router.get(
    "/studies/{uid}/study-endpoints/{study_endpoint_uid}",
    dependencies=[rbac.STUDY_READ],
    summary="Returns specific study endpoint",
    description="""
State before:
 - Study and study endpoint must exist

Business logic:
 - By default (no study status is provided) list all details for specified study endpoint for the study uid in status draft. If the study not exist in status draft then return the study endpoints for the study in status released. If the study uid only exist as deleted then this is returned.
 - If a specific study status parameter is provided then return study endpoints for this study status.
 - If the locked study status parameter is requested then a study version should also be provided, and then the specified study endpoint for the specific locked study version is returned.
 - Indicate by an boolean variable if the study endpoint can be updated (if the selected study is in status draft).
 - Indicate by an boolean variable if all expected selections have been made for each study endpoint, or some are missing.
 - e.g. endpoint level, minimum one timeframe and one unit is expected.
 - Indicate by an boolean variable if the selected endpoint is available in a newer version.
 - Indicate by an boolean variable if a study endpoint can be re-ordered.

State after:
 - no change
""",
    response_model=models.StudySelectionEndpoint,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - When there exist no study endpoint with the study endpoint uid.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_selected_endpoint(
    uid: str = studyUID,
    study_endpoint_uid: str = study_selection_uid,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> models.StudySelectionEndpoint:
    service = StudyEndpointSelectionService()
    return service.get_specific_selection(
        study_uid=uid,
        study_selection_uid=study_endpoint_uid,
        study_value_version=study_value_version,
    )


@router.get(
    "/studies/{uid}/study-endpoints/{study_endpoint_uid}/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List audit trail related to definition of a specific study coendpointsmpound.",
    description="""
Parameters:
 - uid as study-uid (required)
 - study-compound-uid (required)
 - [NOT YET IMPLEMENTED] study status (optional)
 - [NOT YET IMPLEMENTED] study version (required when study status is locked)

State before:
 - Study and study compounds must exist.

Business logic:
 - List a specific entry in the audit trail related to the specified study endpoints for the specified study-uid.
 - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.

State after:
 - no change.
 
Possible errors:
 - Invalid study-uid.

Returned data:
 - List of actions and changes related to the specified study endpoints.
    """,
    response_model=list[models.StudySelectionEndpoint],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the objective for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_selected_endpoint_audit_trail(
    uid: str = studyUID,
    study_endpoint_uid: str = study_selection_uid,
) -> models.StudySelectionEndpoint:
    service = StudyEndpointSelectionService()
    return service.get_specific_selection_audit_trail(
        study_uid=uid, study_selection_uid=study_endpoint_uid
    )


@router.post(
    "/studies/{uid}/study-endpoints",
    dependencies=[rbac.STUDY_WRITE],
    summary="Creates a study endpoint selection based on the input data, including optionally creating library endpoint",
    response_model=models.StudySelectionEndpoint,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the endpoint",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or endpoint is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def post_new_endpoint_selection_create(
    uid: str = studyUID,
    selection: models.study_selections.study_selection.StudySelectionEndpointCreateInput
    | models.study_selections.study_selection.StudySelectionEndpointInput = Body(
        description="Parameters of the selection that shall be created."
    ),
    create_endpoint: bool = Query(
        False,
        description="Indicates whether the specified endpoint should be created in the library.\n"
        "- If this parameter is set to `true`, a `StudySelectionEndpointCreateInput` payload needs to be sent.\n"
        "- Otherwise, `StudySelectionEndpointInput` payload should be sent, referencing an existing library endpoint by uid.",
    ),
) -> models.StudySelectionEndpoint:
    service = StudyEndpointSelectionService()
    if create_endpoint:
        return service.make_selection_create_endpoint(
            study_uid=uid, selection_create_input=selection
        )
    return service.make_selection(study_uid=uid, selection_create_input=selection)


@router.post(
    "/studies/{uid}/study-endpoints/batch-select",
    dependencies=[rbac.STUDY_WRITE],
    summary="Select multiple endpoint templates as a batch. If the template has no parameters, will also create the instance.",
    description="""
    State before:
    - Study must exist and study status must be in draft.

    Business logic:
    - Select endpoint template without instantiating them.
    - This must be done as a batch

    State after:
    - Study endpoints are created.
    - Endpoint templates are all selected by the study endpoint.
    - If a given template has no parameters, the instance will be created and selected.
    - Added new entry in the audit trail for the creation of the study-endpoint.

    Possible errors:
    - Invalid study-uid.
    - Invalid study-endpoint-template-uid.

    Returned data:
    List selected endpoint templates/instances with the following information:
    - study_uid
    - study_endpoint_template_uid / study_endpoint_uid
    - order (Derived Integer)
    - latest version of the selected endpoint template/instance
    """,
    response_model=list[models.StudySelectionEndpoint],
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the endpoint",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or endpoint is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def post_batch_select_endpoint_template(
    uid: str = studyUID,
    selection: list[
        models.study_selections.study_selection.StudySelectionEndpointTemplateSelectInput
    ] = Body(
        description="List of objects with properties needed to identify the templates to select",
    ),
) -> models.StudySelectionEndpoint:
    service = StudyEndpointSelectionService()
    return service.batch_select_endpoint_template(
        study_uid=uid, selection_create_input=selection
    )


@router.post(
    "/studies/{uid}/study-endpoints/preview",
    dependencies=[rbac.STUDY_WRITE],
    summary="Preview creating a study endpoint selection based on the input data",
    response_model=models.StudySelectionEndpoint,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the endpoint",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or endpoint is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def post_new_endpoint_selection_preview(
    uid: str = studyUID,
    selection: models.study_selections.study_selection.StudySelectionEndpointCreateInput = Body(
        description="Related parameters of the selection that shall be previewed."
    ),
) -> models.StudySelectionEndpoint:
    service = StudyEndpointSelectionService()
    return service.make_selection_preview_endpoint(
        study_uid=uid, selection_create_input=selection
    )


@router.delete(
    "/studies/{uid}/study-endpoints/{study_endpoint_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Deletes a objective selection",
    description="""
State before:
 - Study must exist and study status must be in draft.
 - study-endpoint-uid must exist.

Business logic:
 - Remove specified study-endpoint from the study.
 - Reference to the study-endpoint should still exist in the audit trail.
 - If a subsequent study endpoint exist in the list of study endpoints then the order number for following study endpoint must be decreased with 1.

State after:
- Study endpoint is deleted from the study, but still exist as a node in the database with a reference from the audit trail.
- Added new entry in the audit trail for the deletion of the study-endpoint.
""",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - When there exist no study endpoint with the study endpoint uid.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def delete_selected_endpoint(
    uid: str = studyUID,
    study_endpoint_uid: str = study_selection_uid,
):
    service = StudyEndpointSelectionService()
    service.delete_selection(study_uid=uid, study_selection_uid=study_endpoint_uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/studies/{uid}/study-endpoints/{study_endpoint_uid}/order",
    dependencies=[rbac.STUDY_WRITE],
    summary="Change a order of a selection",
    description="""
State before:
 - Study must exist and study status must be in draft.
 - study_endpoint_uid must exist.

Business logic:
 - moves the study selection to the order which is send in the new_order property

State after:
 - Order number for specified study-endpoint is updated to new order number.
 - Note this will change order on either the preceding or following study-endpoints as well.
 - Added new entry in the audit trail for the re-ordering of the study-endpoints.
""",
    response_model=models.StudySelectionEndpoint,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Order is larger than the number of selections",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - When there exist no study endpoint with the study endpoint uid.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_new_endpoint_selection_order(
    uid: str = studyUID,
    study_endpoint_uid: str = study_selection_uid,
    new_order_input: models.StudySelectionEndpointNewOrder = Body(
        description="Related parameters of the selection that shall be created."
    ),
) -> models.StudySelectionEndpoint:
    service = StudyEndpointSelectionService()
    return service.set_new_order(
        study_uid=uid,
        study_selection_uid=study_endpoint_uid,
        new_order=new_order_input.new_order,
    )


@router.patch(
    "/studies/{uid}/study-endpoints/{study_endpoint_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="update the study endpoint",
    description="""
State before:
 - Study must exist and study status must be in draft.
 - Selected endpoint-uid, endpoint-template-uid, endpoint-level, timeframe-uid and unit-definition-uid must exist.

Business logic:
 - Same logic applies as for selecting or creating an study endpoint (see two POST statements for /study-endpoints)

State after:
- Endpoint is added as study endpoint to the study.
 - This PATCH method can cover cover two parts:
    - Change the endpoint level for the currently selected study endpoint
    - Replace the currently selected study endpoint based on the same functionality as POST `/studies/{uid}/study-endpoints`
 - Added new entry in the audit trail for the update of the study-endpoint.
""",
    response_model=models.StudySelectionEndpoint,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - When there exist no study endpoint with the study endpoint uid.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_update_endpoint_selection(
    uid: str = studyUID,
    study_endpoint_uid: str = study_selection_uid,
    selection: models.StudySelectionEndpointInput = Body(
        description="Related parameters of the selection that shall be created."
    ),
) -> models.StudySelectionEndpoint:
    service = StudyEndpointSelectionService()
    return service.patch_selection(
        study_uid=uid,
        study_selection_uid=study_endpoint_uid,
        selection_update_input=selection,
    )


@router.get(
    "/studies/{uid}/study-objectives.docx",
    dependencies=[rbac.STUDY_READ],
    summary="""Returns Study Objectives and Endpoints table in standard layout DOCX document""",
    responses={
        200: {
            "content": {
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {}
            }
        },
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_selected_objectives_and_endpoints_standard_docx(
    uid: str = studyUID,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> StreamingResponse:
    StudyService().check_if_study_exists(uid)
    docx = StudyObjectivesService().get_standard_docx(
        study_uid=uid, study_value_version=study_value_version
    )
    stream = docx.get_document_stream()
    size = stream.seek(0, os.SEEK_END)
    stream.seek(0)
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{uid} study-objectives.docx"',
            "Content-Length": f"{size:d}",
        },
    )


@router.get(
    "/studies/{uid}/study-objectives.html",
    dependencies=[rbac.STUDY_READ],
    summary="""Returns Study Objectives and Endpoints table in standard layout HTML document""",
    responses={
        200: {"content": {"text/html": {"schema": {"type": "string"}}}},
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_selected_objectives_and_endpoints_standard_html(
    uid: str = studyUID,
) -> HTMLResponse:
    StudyService().check_if_study_exists(uid)
    return HTMLResponse(
        content=StudyObjectivesService().get_standard_html(study_uid=uid)
    )


# API endpoints to study compounds


@router.get(
    "/study-compounds",
    dependencies=[rbac.STUDY_READ],
    summary="Returns all study compounds currently selected",
    response_model=CustomPage[models.StudySelectionCompound],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_selected_compounds_for_all_studies(
    project_name: str | None = PROJECT_NAME,
    project_number: str | None = PROJECT_NUMBER,
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
) -> CustomPage[models.StudySelectionCompound]:
    service = StudyCompoundSelectionService()
    all_selections = service.get_all_selections_for_all_studies(
        project_name=project_name,
        project_number=project_number,
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
    "/study-compounds/headers",
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
def get_distinct_compound_values_for_header(
    project_name: str | None = PROJECT_NAME,
    project_number: str | None = PROJECT_NUMBER,
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
    service = StudyCompoundSelectionService()
    return service.get_distinct_values_for_header(
        project_name=project_name,
        project_number=project_number,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.get(
    "/studies/{uid}/study-compounds",
    dependencies=[rbac.STUDY_READ],
    summary="List all study compounds currently selected for study with provided uid",
    description=f"""
State before:
 - Study-uid must exist.

Business logic:
 - By default (no study status is provided) list all study compounds for the study uid in status draft. If the study not exist in status draft then return the study compounds for the study in status released. If the study uid only exist as deleted then this is returned.
 - If a specific study status parameter is provided then return study compounds for this study status.
 - If the locked study status parameter is requested then a study version should also be provided, and then the study compounds for the specific locked study version is returned.
 - Indicate by an boolean variable if the study compound can be updated (if the selected study is in status draft).
 - Indicate by an boolean variable if all expected selections have been made for each study compound, or some are missing.
   - e.g. Compound and TypeOfTreatment are expected.
 - Indicate by an boolean variable if the selected compound is available in a newer version.
 - Indicate by an boolean variable if a study compound can be re-ordered.
 
State after:
- no change.

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=GenericFilteringReturn[models.StudySelectionCompound],
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
            "uid=study_compound_uid",
            "compound=compound.name",
            "pharma_class=compound.p_class_concept",
            "substance_names=compound.unii_substance_name",
            "unii_codes=compound.unii_substance_cd",
            "type_of_treatment=type_of_treatment.name",
            "route_of_admin=route_of_administration.name",
            "dosage_form=dosage_form.name",
            "dispensed_in=dispensed_in",
            "device=device",
            "formulation=formulation",
            "other=other_info",
            "reason_for_missing=reason_for_missing_null_value_code",
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
def get_all_selected_compounds(
    request: Request,  # request is actually required by the allow_exports decorator
    uid: str = studyUID,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
    filters: Json
    | None = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    page_number: int
    | None = Query(1, ge=1, description=_generic_descriptions.PAGE_NUMBER),
    page_size: int
    | None = Query(
        config.DEFAULT_PAGE_SIZE,
        ge=0,
        le=config.MAX_PAGE_SIZE,
        description=_generic_descriptions.PAGE_SIZE,
    ),
    operator: str | None = Query("and", description=_generic_descriptions.OPERATOR),
    total_count: bool
    | None = Query(False, description=_generic_descriptions.TOTAL_COUNT),
) -> GenericFilteringReturn[models.StudySelectionCompound]:
    service = StudyCompoundSelectionService()
    return service.get_all_selection(
        study_uid=uid,
        study_value_version=study_value_version,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
    )


@router.get(
    "/studies/{uid}/study-compounds/headers",
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
def get_distinct_compounds_values_for_header(
    uid: str = studyUID,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
    project_name: str | None = PROJECT_NAME,
    project_number: str | None = PROJECT_NUMBER,
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
    service = StudyCompoundSelectionService()
    return service.get_distinct_values_for_header(
        study_uid=uid,
        study_value_version=study_value_version,
        project_name=project_name,
        project_number=project_number,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.get(
    "/studies/{uid}/study-compounds/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List full audit trail related to definition of all study compounds.",
    description="""
Parameters:
 - uid as study-uid (required)
 - [NOT YET IMPLEMENTED] study status (optional)
 - [NOT YET IMPLEMENTED] study version (required when study status is locked)

State before:
 - Study must exist.

Business logic:
 - List all entries in the audit trail related to study compounds for specified study-uid.
 - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.

State after:
 - no change.
 
Possible errors:
 - Invalid study-uid.

Returned data:
 - List of actions and changes related to study compounds.
    """,
    response_model=list[models.StudySelectionCompound],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_compounds_audit_trail(
    uid: str = studyUID,
) -> list[models.StudySelectionCompound]:
    service = StudyCompoundSelectionService()
    return service.get_all_selection_audit_trail(study_uid=uid)


@router.get(
    "/studies/{uid}/study-compounds/{study_compound_uid}/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List audit trail related to definition of a specific study compound.",
    description="""
Parameters:
 - uid as study-uid (required)
 - study-compound-uid (required)
 - [NOT YET IMPLEMENTED] study status (optional)
 - [NOT YET IMPLEMENTED] study version (required when study status is locked)

State before:
 - Study and study compounds must exist.

Business logic:
 - List a specific entry in the audit trail related to the specified study compound for the specified study-uid.
 - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.

State after:
 - no change.
 
Possible errors:
 - Invalid study-uid.

Returned data:
 - List of actions and changes related to the specified study compound.
    """,
    response_model=list[models.StudySelectionCompound],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the objective for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_selected_compound_audit_trail(
    uid: str = studyUID,
    study_compound_uid: str = study_selection_uid,
) -> models.StudySelectionCompound:
    service = StudyCompoundSelectionService()
    return service.get_specific_selection_audit_trail(
        study_uid=uid, study_selection_uid=study_compound_uid
    )


@router.get(
    "/studies/{uid}/study-compounds/{study_compound_uid}",
    dependencies=[rbac.STUDY_READ],
    summary="Returns specific study compound",
    description="""
State before:
 - Study-uid and study-compound-uid must exist

Business logic:
 - By default (no study status is provided) list all details for specified study compound for the study uid in status draft. If the study not exist in status draft then return the study compounds for the study in status released. If the study uid only exist as deleted then this is returned.
 - If a specific study status parameter is provided then return study compounds for this study status.
 - If the locked study status parameter is requested then a study version should also be provided, and then the specified study compound for the specific locked study version is returned.  - Indicate by an boolean variable if the study compound can be updated (if the selected study is in status draft).
 - Indicate by an boolean variable if all expected selections have been made for each study compound, or some are missing.
   - e.g. Compound and TypeOfTreatment are expected.
 - Indicate by an boolean variable if the selected compound is available in a newer version.
 - Indicate by an boolean variable if a study compound can be re-ordered.

State after:
 - no change
""",
    response_model=models.StudySelectionCompound,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the objective for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_selected_compound(
    uid: str = studyUID,
    study_compound_uid: str = study_selection_uid,
) -> models.StudySelectionCompound:
    service = StudyCompoundSelectionService()
    return service.get_specific_selection(
        study_uid=uid, study_selection_uid=study_compound_uid
    )


@router.post(
    "/studies/{uid}/study-compounds",
    dependencies=[rbac.STUDY_WRITE],
    summary="Add a study compound to a study based on selection of a compound concept in library, or a 'Reason for missing'.",
    description="""
State before:
 - Study must exist and be in status draft
 - Compound-uid must exist and be in status Final.
 
Business logic:
 - Add a study-compound to the study based on selection of an existing compound concept in the library.
 - If the selected compound-uid is retired then an error message must be provided.
 - A single relationships can be defined for a study compound to each of the following code list terms:
   - Type of treatment
   - Route of administration
   - Dosages form
   - Dispensed in
   - Device
   - Formulation
 - It is also possible to save a free test string describing other information for the study-compound.
 - Order for the study compound must be assigged as the next incremental order number or as 1 if this is the initial study objective for the study.
 - It should be possible to define a 'Reason for missing' value for a specific value of 'Type of treatment'. In this case the following rule apply:
   - Only the parameter for 'Type of treatment' can be defined - the parameter value for compound or any other related parameters must be null.
   - No other study compound must exist for the study with the same value for 'Type of Treatment'.
   - No other 'Reason for missing' value must exist for the study with the same value for 'Type of Treatment' (ReasonForMissing can only be defined once for a TypeOfTreatment).
   - Thereby either the parameter compound-uid or type-of-treatment-uid must be provided, but not both of them 8they are mytually exclusive).

State after:
 - compound is added as study compound to the study.
 - Added new entry in the audit trail for the creation of the study-compound.
 """,
    response_model=models.StudySelectionCompound,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the objective",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or objective is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def post_new_compound_selection(
    uid: str = studyUID,
    selection: models.StudySelectionCompoundInput = Body(
        description="Related parameters of the selection that shall be created."
    ),
) -> models.StudySelectionCompound:
    service = StudyCompoundSelectionService()
    return service.make_selection(study_uid=uid, selection_create_input=selection)


@router.delete(
    "/studies/{uid}/study-compounds/{study_compound_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Delete a study compound.",
    description="""
State before:
- Study and study-compound-uid must exist and study must be in status draft.

Business logic:
 - Remove specified study-compound from the study.
 - Reference to the study-compound should still exist in the audit trail.
 - If a subsequent study compound exist in the list of study compounds then the order number for following study compound must be decreased with 1.

State after:
- Study compound is deleted from the study, but still exist as a node in the database with a reference from the audit trail.
- Added new entry in the audit trail for the deletion of the study-compound.
""",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the objective and the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def delete_selected_compound(
    uid: str = studyUID,
    study_compound_uid: str = study_selection_uid,
):
    service = StudyCompoundSelectionService()
    service.delete_selection(study_uid=uid, study_selection_uid=study_compound_uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/studies/{uid}/study-compounds/{study_compound_uid}/order",
    dependencies=[rbac.STUDY_WRITE],
    summary="Change display order of study compound",
    description="""
State before:
- Study and study-compound-uid must exist and study must be in status draft.
- Old order number must match current order number in database for study compound.

Business logic:
 - moves the study selection to the order which is send in the new_order property
 
State after:
 - Order number for specified study-compound is updated to new order number.
 - Note this will change order on either the preceding or following study-compounds as well.
 - Added new entry in the audit trail for the re-ordering of the study-compounds.
""",
    response_model=models.StudySelectionCompound,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and objective to reorder.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_new_compound_selection_order(
    uid: str = studyUID,
    study_compound_uid: str = study_selection_uid,
    new_order_input: models.StudySelectionCompoundNewOrder = Body(
        description="Related parameters of the selection that shall be created."
    ),
) -> models.StudySelectionCompound:
    service = StudyCompoundSelectionService()
    return service.set_new_order(
        study_uid=uid,
        study_selection_uid=study_compound_uid,
        new_order=new_order_input.new_order,
    )


@router.patch(
    "/studies/{uid}/study-compounds/{study_compound_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Edit or replace a study compound",
    description="""
State before:
 - Study must exist and be in status draft
 - Compound-uid must exist and be in status Final.

Business logic:
 - Update specified study-compound with selection of an existing compound concept in the library.
 - If the selected compound-uid is retired then an error message must be provided.
 - A single relationships can be defined for a study compound to each of the following code list terms:
   - Type of treatment
   - Route of administration
   - Dosages form
   - Dispensed in
   - Device
   - Formulation
 - It is also possible to save a free text string describing other information for the study-compound.
 - Order number for the study compound cannot be changed by this API endpoint.
 - It should be possible to define a 'Reason for missing' value for a specific value of 'Type of treatment'. In this case the following rule apply:
   - Only the parameter for 'Type of treatment' can be defined - the parameter value for compound or any other related parameters must be null.
   - No other study compound must exist for the study with the same value for 'Type of Treatment'.
   - No other 'Reason for missing' value must exist for the study with the same value for 'Type of Treatment' (ReasonForMissing can only be defined once for a TypeOfTreatment).
   - Thereby either the parameter compound-uid or type-of-treatment-uid must be provided, but not both of them 8they are mutually exclusive).

State after:
 - compound or related parameters is updated for the study compound.
 - Added new entry in the audit trail for the update of the study-compound.""",
    response_model=models.StudySelectionCompound,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and objective.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_update_compound_selection(
    uid: str = studyUID,
    study_compound_uid: str = study_selection_uid,
    selection: models.StudySelectionCompoundInput = Body(
        description="Related parameters of the selection that shall be created."
    ),
) -> models.StudySelectionCompound:
    service = StudyCompoundSelectionService()
    return service.patch_selection(
        study_uid=uid,
        study_selection_uid=study_compound_uid,
        selection_update_input=selection,
    )


@router.post(
    "/studies/{uid}/study-endpoints/{study_endpoint_uid}/sync-latest-endpoint-version",
    dependencies=[rbac.STUDY_WRITE],
    summary="update to latest endpoint version study selection",
    description="""
State before:
 - Study must exist
 - Study endpoint selection must exist
 - Endpoint version selected for study endpoint selection is not the latest available final version of endpoint.

Business logic:
 - Update specified endpoint study-selection with the latest final version of previously selected endpoint.

State after:
 - Study exists
 - Study endpoint selection exists
 - Endpoint version selected for study endpoint selection is the latest available final version.
 - Added new entry in the audit trail for the update of the study-endpoint.""",
    response_model=models.StudySelectionEndpoint,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and endpoint",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def sync_latest_endpoint_version(
    uid: str = studyUID,
    study_endpoint_uid: str = study_selection_uid,
) -> models.StudySelectionObjective:
    service = StudyEndpointSelectionService()
    return service.update_selection_to_latest_version_of_endpoint(
        study_uid=uid, study_selection_uid=study_endpoint_uid
    )


@router.post(
    "/studies/{uid}/study-endpoints/{study_endpoint_uid}/sync-latest-timeframe-version",
    dependencies=[rbac.STUDY_WRITE],
    summary="update to latest timeframe version study selection",
    description="""
    State before:
     - Study must exist
     - Study endpoint selection must exist
     - Timeframe version selected for study endpoint selection is not the latest available final version of the timeframe.

    Business logic:
     - Update specified endpoint study-selection with the latest final version of previously selected timeframe.

    State after:
     - Study exists
     - Study endpoint selection exists
     - Timeframe version selected for study endpoint selection is the latest available final version.
     - Added new entry in the audit trail for the update of the study-endpoint.""",
    response_model=models.StudySelectionEndpoint,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and timeframe",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def sync_latest_timeframe_version(
    uid: str = studyUID,
    study_endpoint_uid: str = study_selection_uid,
) -> models.StudySelectionObjective:
    service = StudyEndpointSelectionService()
    return service.update_selection_to_latest_version_of_timeframe(
        study_uid=uid, study_selection_uid=study_endpoint_uid
    )


@router.post(
    "/studies/{uid}/study-endpoints/{study_endpoint_uid}/accept-version",
    dependencies=[rbac.STUDY_WRITE],
    summary="update to latest timeframe version study selection",
    description="""
    State before:
     - Study must exist
     - Study endpoint selection must exist
     - Timeframe and/or endpoint version selected for study endpoint selection is not the latest available final version of the timeframe.

    Business logic:
     - Update specified endpoint study-selection, setting accepted version to show that update was refused by user.

    State after:
     - Study exists
     - Study endpoint selection exists
     - Timeframe and endpoint version selected for study endpoint selection is not changed.
     - Added new entry in the audit trail for the update of the study-endpoint.""",
    response_model=models.StudySelectionEndpoint,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and timeframe",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_endpoint_accept_version(
    uid: str = studyUID,
    study_endpoint_uid: str = study_selection_uid,
) -> models.StudySelectionObjective:
    service = StudyEndpointSelectionService()
    return service.update_selection_accept_versions(
        study_uid=uid, study_selection_uid=study_endpoint_uid
    )


@router.post(
    "/studies/{uid}/study-objectives/{study_objective_uid}/accept-version",
    dependencies=[rbac.STUDY_WRITE],
    summary="update to latest timeframe version study selection",
    description="""
    State before:
     - Study must exist
     - Study endpoint selection must exist
     - Objective version selected for study endpoint selection is not the latest available final version of the timeframe.

    Business logic:
     - Update specified endpoint study-selection, setting accepted version to show that update was refused by user.

    State after:
     - Study exists
     - Study endpoint selection exists
     - Objective version selected for study endpoint selection is not changed.
     - Added new entry in the audit trail for the update of the study-endpoint.""",
    response_model=models.StudySelectionObjective,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and timeframe",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_objective_accept_version(
    uid: str = studyUID,
    study_objective_uid: str = study_selection_uid,
) -> models.StudySelectionObjective:
    service = StudyObjectiveSelectionService()
    return service.update_selection_accept_version(
        study_uid=uid, study_selection_uid=study_objective_uid
    )


# API endpoints to study criteria


@router.get(
    "/study-criteria",
    dependencies=[rbac.STUDY_READ],
    summary="Returns all study criteria currently selected",
    response_model=CustomPage[models.StudySelectionCriteria],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_selected_criteria_for_all_studies(
    no_brackets: bool = Query(
        False,
        description="Indicates whether brackets around Template Parameters in the Criteria"
        "should be returned",
    ),
    project_name: str | None = PROJECT_NAME,
    project_number: str | None = PROJECT_NUMBER,
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
) -> CustomPage[models.StudySelectionCriteria]:
    service = StudyCriteriaSelectionService()
    all_selections = service.get_all_selections_for_all_studies(
        no_brackets=no_brackets,
        project_name=project_name,
        project_number=project_number,
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
    "/study-criteria/headers",
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
def get_distinct_criteria_values_for_header(
    project_name: str | None = PROJECT_NAME,
    project_number: str | None = PROJECT_NUMBER,
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
    service = StudyCriteriaSelectionService()
    return service.get_distinct_values_for_header(
        project_name=project_name,
        project_number=project_number,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.get(
    "/studies/{uid}/study-criteria",
    dependencies=[rbac.STUDY_READ],
    summary="Returns all study criteria currently selected for study with provided uid",
    description=f"""
State before:
- Study must exist.

Business logic:
- By default (no study status is provided) list all study criteria for the study uid in status draft. If the study not exist in status draft then return the study criteria for the study in status released. If the study uid only exist as deleted then this is returned.
- If a specific study status parameter is provided then return study criteria for this study status.
- If the locked study status parameter is requested then a study version should also be provided, and then the study criteria for the specific locked study version is returned.
- Indicate by a boolean variable if the study criteria can be updated (if the selected study is in status draft).  
- Indicate by a boolean variable if all expected selections have been made for each study criteria, or some are missing.
- e.g. a criteria instance is expected.
- Indicate by an boolean variable if a study criteria can be re-ordered.

State after:
- no change.

Possible errors:
- Invalid study-uid.

Returned data:
List selected study with the following information:
- study_uid
- study_criteria_uid
- order (Derived Integer, valid in the scope of a criteria_type)
- criteria_uid (Selected CriteriaRoot  uid)
- criteria_name (String, CriteriaValue name)
- criteria_type (String, derived from the selected criteria instance's template, which has a connection to a type node)
- note (String)
- Modified (as a date of last modification).
- Possible Actions (based on study state, version of selected nodes, metadata consistency checks, etc. - see business rules).
    - Boolean indication if edit is possible.
    - Boolean indication if all expected selections have been made.
    - Boolean indication if the study criteria can be re-ordered.

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=CustomPage[models.StudySelectionCriteria],
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
            "study_criteria_uid",
            "name_plain=criteria.name_plain",
            "name=criteria.name",
            "guidance_text=criteria.criteria_template.guidance_text",
            "key_criteria",
            "start_date",
            "user_initials",
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
def get_all_selected_criteria(
    request: Request,  # request is actually required by the allow_exports decorator
    uid: str = studyUID,
    no_brackets: bool = Query(
        False,
        description="Indicates whether brackets around Template Parameters in the Criteria"
        "should be returned",
    ),
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
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> CustomPage[models.StudySelectionCriteria]:
    service = StudyCriteriaSelectionService()
    all_items = service.get_all_selection(
        study_uid=uid,
        no_brackets=no_brackets,
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
    "/studies/{uid}/study-criteria/headers",
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
def get_distinct_study_criteria_values_for_header(
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
    uid: str = studyUID,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
):
    service = StudyCriteriaSelectionService()
    return service.get_distinct_values_for_header(
        study_uid=uid,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
        study_value_version=study_value_version,
    )


@router.get(
    "/studies/{uid}/study-criteria/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List full audit trail related to definition of all study criteria.",
    description="""
    State before:
    - Study must exist.

    Business logic:
    - List all entries in the audit trail related to study criteria for specified study-uid.
    - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.

    State after:
    - no change.
    
    Possible errors:
    - Invalid study-uid.

    Returned data:
    List selected study with the following information:
    - study_uid
    - study_criteria_uid
    - order (Derived Integer)
    - criteria_uid (Selected CriteriaRoot  uid)
    - criteria_name (String, CriteriaValue name)
    - criteria_type (String, derived from the selected criteria instance's template, which has a connection to a type node)
    - note (String)
    - Modified (as a date of last modification).
    - Possible Actions (based on study state, version of selected nodes, metadata consistency checks, etc. - see business rules).
        - Boolean indication if edit is possible.
        - Boolean indication if all expected selections have been made.
        - Boolean indication if the study criteria can be re-ordered.
    """,
    response_model=list[models.StudySelectionCriteriaCore],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_criteria_audit_trail(
    uid: str = studyUID,
    criteria_type_uid: str
    | None = Query(
        None,
        description="Optionally, the uid of the criteria_type for which to return study criteria audit trial.",
    ),
) -> list[models.StudySelectionCriteriaCore]:
    service = StudyCriteriaSelectionService()
    return service.get_all_selection_audit_trail(
        study_uid=uid, criteria_type_uid=criteria_type_uid
    )


@router.get(
    "/studies/{uid}/study-criteria/{study_criteria_uid}",
    dependencies=[rbac.STUDY_READ],
    summary="Returns specific study criteria",
    description="""
    State before:
    - Study and study criteria must exist
    
    Business logic:
    - By default (no study status is provided) list all details for specified study criteria for the study uid in status draft. If the study not exist in status draft then return the study criteria for the study in status released. If the study uid only exist as deleted then this is returned.
    - If a specific study status parameter is provided then return study criteria for this study status.
    - If the locked study status parameter is requested then a study version should also be provided, and then the specified study criteria for the specific locked study version is returned.
    - Indicate by an boolean variable if the study criteria can be updated (if the selected study is in status draft).
    - Indicate by an boolean variable if all expected selections have been made for each study criteria, or some are missing.
    - Indicate by an boolean variable if the selected criteria is available in a newer version.
    - Indicate by an boolean variable if a study criteria can be re-ordered.
    
    State after:
    - no change
    
    Possible errors:
    - Invalid study-uid or study_criteria_uid.
    
    Returned data:
    List selected study with the following information:
    - study_uid
    - study_criteria_uid
    - order (Derived Integer)
    - criteria_uid (Selected CriteriaRoot  uid)
    - criteria_name (String, CriteriaValue name)
    - criteria_type (String, derived from the selected criteria instance's template, which has a connection to a type node)
    - note (String)
    - Modified (as a date of last modification).
    - Possible Actions (based on study state, version of selected nodes, metadata consistency checks, etc. - see business rules).
        - Boolean indication if edit is possible.
        - Boolean indication if all expected selections have been made.
        - Boolean indication if the study criteria can be re-ordered.
    """,
    response_model=models.StudySelectionCriteria,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exists no selection of the criteria for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_selected_criteria(
    uid: str = studyUID,
    study_criteria_uid: str = study_selection_uid,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> models.StudySelectionCriteria:
    service = StudyCriteriaSelectionService()
    return service.get_specific_selection(
        study_uid=uid,
        study_selection_uid=study_criteria_uid,
        study_value_version=study_value_version,
    )


@router.get(
    "/studies/{uid}/study-criteria/{study_criteria_uid}/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List audit trail related to definition of a specific study criteria.",
    description="""
    State before:
    - Study and study criteria must exist.

    Business logic:
    - List a specific entry in the audit trail related to the specified study criteria for the specified study-uid.
    - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.

    State after:
    - no change.
    
    Possible errors:
    - Invalid study-uid.

    Returned data:
    List selected study with the following information:
    - study_uid
    - study_criteria_uid
    - order (Derived Integer)
    - criteria_uid (Selected CriteriaRoot  uid)
    - criteria_name (String, CriteriaValue name)
    - criteria_type (String, derived from the selected criteria instance's template, which has a connection to a type node)
    - note (String)
    - Modified (as a date of last modification).
    - Possible Actions (based on study state, version of selected nodes, metadata consistency checks, etc. - see business rules).
        - Boolean indication if edit is possible.
        - Boolean indication if all expected selections have been made.
        - Boolean indication if the study criteria can be re-ordered.
    """,
    response_model=list[models.StudySelectionCriteriaCore],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the criteria for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_selected_criteria_audit_trail(
    uid: str = studyUID,
    study_criteria_uid: str = study_selection_uid,
) -> models.StudySelectionCriteriaCore:
    service = StudyCriteriaSelectionService()
    return service.get_specific_selection_audit_trail(
        study_uid=uid, study_selection_uid=study_criteria_uid
    )


@router.post(
    "/studies/{uid}/study-criteria",
    dependencies=[rbac.STUDY_WRITE],
    summary="Creating a study criteria selection based on the input data including creating new criteria",
    description="""
    State before:
    - Study must exist and study status must be in draft.

    Business logic:
    - Create a study criteria and to a study based on valid selections and values.
    
    State after:
    - criteria instance is created
    - criteria is added as study criteria to the study.
    - Added new entry in the audit trail for the creation of the study-criteria.
    
    Possible errors:
    - Invalid study-uid.

    Returned data:
    List selected study with the following information:
    - study_uid
    - study_criteria_uid
    - order (Derived Integer)
    - criteria_uid (Selected CriteriaRoot  uid)
    - criteria_name (String, CriteriaValue name)
    - criteria_type (String, derived from the selected criteria instance's template, which has a connection to a type node)
    - note (String)
    - Modified (as a date of last modification).
    - Possible Actions (based on study state, version of selected nodes, metadata consistency checks, etc. - see business rules).
        - Boolean indication if edit is possible. (study is in Draft status)
        - Boolean indication if all expected selections have been made. (expected !== required)
    """,
    response_model=models.StudySelectionCriteria,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the criteria",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or criteria is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def post_new_criteria_selection_create(
    uid: str = studyUID,
    selection: models.study_selections.study_selection.StudySelectionCriteriaCreateInput
    | models.study_selections.study_selection.StudySelectionCriteriaInput = Body(
        description="Parameters of the selection that shall be created."
    ),
    create_criteria: bool = Query(
        False,
        description="Indicates whether the specified criteria should be created in the library.\n"
        "- If this parameter is set to `true`, a `StudySelectionCriteriaCreateInput` payload needs to be sent.\n"
        "- Otherwise, `StudySelectionCriteriaInput` payload should be sent, referencing an existing library criteria by uid.",
    ),
) -> models.StudySelectionCriteria:
    service = StudyCriteriaSelectionService()

    if create_criteria:
        return service.make_selection_create_criteria(
            study_uid=uid, selection_create_input=selection
        )
    return service.make_selection(study_uid=uid, selection_create_input=selection)


@router.post(
    "/studies/{uid}/study-criteria/preview",
    dependencies=[rbac.STUDY_WRITE],
    summary="Previews creating a study criteria selection based on the input data including creating new criteria",
    response_model=models.StudySelectionCriteria,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the criteria",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or criteria is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def preview_new_criteria_selection_create(
    uid: str = studyUID,
    selection: models.study_selections.study_selection.StudySelectionCriteriaCreateInput = Body(
        description="Related parameters of the selection that shall be previewed."
    ),
) -> models.StudySelectionCriteria:
    service = StudyCriteriaSelectionService()
    return service.make_selection_preview_criteria(
        study_uid=uid, selection_create_input=selection
    )


@router.post(
    "/studies/{uid}/study-criteria/batch-select",
    dependencies=[rbac.STUDY_WRITE],
    summary="Select multiple criteria templates as a batch. If the template has no parameters, will also create the instance.",
    description="""
    State before:
    - Study must exist and study status must be in draft.

    Business logic:
    - Select criteria template without instantiating them.
    - This must be done as a batch

    State after:
    - Study criteria is created.
    - Criteria templates are all selected by the study criteria.
    - If a given template has no parameters, the instance will be created and selected.
    - Added new entry in the audit trail for the creation of the study-criteria.

    Possible errors:
    - Invalid study-uid.
    - Invalid study-criteria-template-uid.

    Returned data:
    List selected criteria templates/instances with the following information:
    - study_uid
    - study_criteria_template_uid / study_criteria_uid
    - order (Derived Integer)
    - latest version of the selected criteria template/instance
    """,
    response_model=list[models.StudySelectionCriteria],
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the criteria",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or criteria is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def post_batch_select_criteria_template(
    uid: str = studyUID,
    selection: list[
        models.study_selections.study_selection.StudySelectionCriteriaTemplateSelectInput
    ] = Body(
        description="List of objects with properties needed to identify the templates to select",
    ),
) -> models.StudySelectionCriteria:
    service = StudyCriteriaSelectionService()
    return service.batch_select_criteria_template(
        study_uid=uid, selection_create_input=selection
    )


@router.patch(
    "/studies/{uid}/study-criteria/{study_criteria_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Update the study criteria template selection",
    description="""
    State before:
    - Study and study selection must exist and the selected object must be a template and not an instance.

    Business logic:
    - Create an instance of the selected template
    - Re-attach the study criteria object to the instance instead of the template
    
    State after:
    - Instance of the template is created
    - Study criteria is detached from the template
    - Study criteria is attached to the instance
    
    Possible errors:
    - Invalid study-uid.
    - Invalid study-criteria-uid.

    Returned data:
    Selected criteria instance with the following information:
    - study_uid
    - study_criteria_uid
    - order
    - latest version of the selected criteria
    """,
    response_model=models.StudySelectionCriteria,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or study criteria is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_update_criteria_selection(
    uid: str = studyUID,
    study_criteria_uid: str = study_selection_uid,
    criteria_data: models.CriteriaUpdateWithCriteriaKeyInput = Body(
        description="Data necessary to create the criteria instance from the template",
    ),
) -> models.StudySelectionCriteria:
    service = StudyCriteriaSelectionService()
    return service.patch_selection(
        study_uid=uid,
        study_criteria_uid=study_criteria_uid,
        criteria_data=criteria_data,
    )


@router.delete(
    "/studies/{uid}/study-criteria/{study_criteria_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Deletes a study criteria",
    description="""
    State before:
    - Study must exist and study status must be in draft.
    - study_criteria_uid must exist. 

    Business logic:
    - Remove specified study-criteria from the study.
    - Reference to the study-criteria should still exist in the audit trail.

    State after:
    - Study criteria deleted from the study, but still exist as a node in the database with a reference from the audit trail.
    - Added new entry in the audit trail for the deletion of the study-criteria .
    
    Possible errors:
    - Invalid study-uid or study_criteria_uid.

    Returned data:
    - none
    """,
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the criteria and the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def delete_selected_criteria(
    uid: str = studyUID,
    study_criteria_uid: str = study_selection_uid,
):
    service = StudyCriteriaSelectionService()
    service.delete_selection(study_uid=uid, study_selection_uid=study_criteria_uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/studies/{uid}/study-criteria/{study_criteria_uid}/order",
    dependencies=[rbac.STUDY_WRITE],
    summary="Change the order of a study criteria",
    response_model=models.StudySelectionCriteria,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exists no selection between the study and criteria to reorder.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_new_criteria_selection_order(
    uid: str = studyUID,
    study_criteria_uid: str = study_selection_uid,
    new_order_input: models.StudySelectionCriteriaNewOrder = Body(
        description="New value to set for the order property of the selection"
    ),
) -> models.StudySelectionCriteria:
    service = StudyCriteriaSelectionService()
    return service.set_new_order(
        study_uid=uid,
        study_selection_uid=study_criteria_uid,
        new_order=new_order_input.new_order,
    )


@router.patch(
    "/studies/{uid}/study-criteria/{study_criteria_uid}/key-criteria",
    dependencies=[rbac.STUDY_WRITE],
    summary="Change the key-criteria property of a study criteria",
    response_model=models.StudySelectionCriteria,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exists no selection between the study and criteria to change.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_criteria_selection_key_criteria_property(
    uid: str = studyUID,
    study_criteria_uid: str = study_selection_uid,
    key_criteria_input: models.StudySelectionCriteriaKeyCriteria = Body(
        description="New value to set for the key-criteria property of the selection",
    ),
) -> models.StudySelectionCriteria:
    service = StudyCriteriaSelectionService()
    return service.set_key_criteria(
        study_uid=uid,
        study_selection_uid=study_criteria_uid,
        key_criteria=key_criteria_input.key_criteria,
    )


@router.post(
    "/studies/{uid}/study-criteria/{study_criteria_uid}/sync-latest-version",
    dependencies=[rbac.STUDY_WRITE],
    summary="update to latest criteria version study selection",
    response_model=models.StudySelectionCriteria,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and criteria.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def sync_criteria_latest_version(
    uid: str = studyUID,
    study_criteria_uid: str = study_selection_uid,
) -> models.StudySelectionCriteria:
    service = StudyCriteriaSelectionService()
    return service.update_selection_to_latest_version(
        study_uid=uid, study_selection_uid=study_criteria_uid
    )


@router.post(
    "/studies/{uid}/study-criteria/{study_criteria_uid}/accept-version",
    dependencies=[rbac.STUDY_WRITE],
    summary="accept current version of study criteria",
    description="""
    Business logic:
     - Update specified criteria study-selection, setting accepted version to show that update was refused by user.
    """,
    response_model=models.StudySelectionCriteria,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and timeframe",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_criteria_accept_version(
    uid: str = studyUID,
    study_criteria_uid: str = study_selection_uid,
) -> models.StudySelectionCriteria:
    service = StudyCriteriaSelectionService()
    return service.update_selection_accept_version(
        study_uid=uid, study_selection_uid=study_criteria_uid
    )


#
# API endpoints to study activity instances


@router.get(
    "/study-activity-instances",
    dependencies=[rbac.STUDY_READ],
    summary="Returns all study activity instances currently selected",
    response_model=CustomPage[models.StudySelectionActivityInstance],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_selected_activity_instances_for_all_studies(
    project_name: str | None = PROJECT_NAME,
    project_number: str | None = PROJECT_NUMBER,
    activity_names: list[str]
    | None = Query(
        None,
        description="A list of activity names to use as a specific filter",
        alias="activity_names[]",
    ),
    activity_subgroup_names: list[str]
    | None = Query(
        None,
        description="A list of activity sub group names to use as a specific filter",
        alias="activity_subgroup_names[]",
    ),
    activity_group_names: list[str]
    | None = Query(
        None,
        description="A list of activity group names to use as a specific filter",
        alias="activity_group_names[]",
    ),
    activity_instance_names: list[str]
    | None = Query(
        None,
        description="A list of activity instance names to use as a specific filter",
        alias="activity_instance_names[]",
    ),
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
) -> CustomPage[models.StudySelectionActivityInstance]:
    service = StudyActivityInstanceSelectionService()
    all_selections = service.get_all_selections_for_all_studies(
        project_name=project_name,
        project_number=project_number,
        activity_names=activity_names,
        activity_subgroup_names=activity_subgroup_names,
        activity_group_names=activity_group_names,
        activity_instance_names=activity_instance_names,
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
    "/studies/{uid}/study-activity-instances",
    dependencies=[rbac.STUDY_READ],
    summary="Returns all study activity instances currently selected",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    response_model=CustomPage[models.StudySelectionActivityInstance],
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
@decorators.allow_exports(
    {
        "defaults": [
            "study_uid",
            "order",
            "soa_group=study_soa_group.soa_group_name",
            "activity_group=study_activity_group.activity_group_name",
            "activity_subgroup=study_activity_subgroup.activity_subgroup_name",
            "activity=activity.name",
            "data_collection=activity.is_data_collected",
            "instance=activity_instance.name",
            "topic_code=activity_instance.topic_code",
            "state",
            "param_code=activity_instance.adam_param_code",
            "activity_concept_id=activity.uid",
            "activity_instance_concept_id=activity_instance.uid",
            "required=activity_instance.is_required_for_activity",
            "default=activity_instance.is_default_selected_for_activity",
            "multiple_selection=activity.is_multiple_selection_allowed",
            "legacy=activity_instance.is_legacy_usage",
            "instance_class=activity_instance.activity_instance_class.name",
            "activity_items=activity_instance.activity_items",
            "modified=start_date",
            "modified_by=user_initials",
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
def get_all_selected_activity_instances(
    request: Request,  # request is actually required by the allow_exports decorator
    activity_names: list[str]
    | None = Query(
        None,
        description="A list of activity names to use as a specific filter",
        alias="activity_names[]",
    ),
    activity_subgroup_names: list[str]
    | None = Query(
        None,
        description="A list of activity sub group names to use as a specific filter",
        alias="activity_subgroup_names[]",
    ),
    activity_group_names: list[str]
    | None = Query(
        None,
        description="A list of activity group names to use as a specific filter",
        alias="activity_group_names[]",
    ),
    activity_instance_names: list[str]
    | None = Query(
        None,
        description="A list of activity instance names to use as a specific filter",
        alias="activity_instance_names[]",
    ),
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
    uid: str = studyUID,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> CustomPage[models.StudySelectionActivityInstance]:
    service = StudyActivityInstanceSelectionService()
    all_items = service.get_all_selection(
        study_uid=uid,
        activity_names=activity_names,
        activity_subgroup_names=activity_subgroup_names,
        activity_group_names=activity_group_names,
        activity_instance_names=activity_instance_names,
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
    "/studies/{uid}/study-activity-instances/headers",
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
def get_distinct_study_activity_instances_values_for_header(
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
    uid: str = studyUID,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
):
    service = StudyActivityInstanceSelectionService()
    return service.get_distinct_values_for_header(
        study_uid=uid,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
        study_value_version=study_value_version,
    )


@router.delete(
    "/studies/{uid}/study-activity-instances/{study_activity_instance_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Delete a study activity instance",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the activity instance and the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def delete_study_activity_instance(
    uid: str = studyUID,
    study_activity_instance_uid: str = study_selection_uid,
):
    service = StudyActivityInstanceSelectionService()
    service.delete_selection(
        study_uid=uid, study_selection_uid=study_activity_instance_uid
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/studies/{uid}/study-activity-instances",
    dependencies=[rbac.STUDY_WRITE],
    summary="Creating a study activity instance selection based on the input data",
    response_model=models.StudySelectionActivityInstance,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the activity",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or activity is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def post_new_activity_instance_selection(
    uid: str = studyUID,
    selection: models.StudySelectionActivityInstanceCreateInput = Body(
        description="Related parameters of the selection that shall be created."
    ),
) -> models.StudySelectionActivityInstance:
    service = StudyActivityInstanceSelectionService()
    return service.make_selection(study_uid=uid, selection_create_input=selection)


@router.patch(
    "/studies/{uid}/study-activity-instances/{study_activity_instance_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Edit a study activity instance",
    description="""
State before:
 - Study must exist and be in status draft
Business logic:
State after:
 - Added new entry in the audit trail for the update of the study-activity-instance.""",
    response_model=models.StudySelectionActivityInstance,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and activity instance.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_update_study_activity_instance(
    uid: str = studyUID,
    study_activity_instance_uid: str = study_selection_uid,
    selection: models.StudySelectionActivityInstanceEditInput = Body(
        description="Related parameters of the selection that shall be updated."
    ),
) -> models.StudySelectionActivity:
    service = StudyActivityInstanceSelectionService()
    return service.patch_selection(
        study_uid=uid,
        study_selection_uid=study_activity_instance_uid,
        selection_update_input=selection,
    )


@router.get(
    "/studies/{uid}/study-activity-instances/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List full audit trail related to all StudyActivityInstances in scope of a single Study.",
    description="""
The following values should be returned for all study activity instances:
- date_time
- user_initials
- action
- activity
- activity instances
- state
- order
    """,
    response_model=list[models.StudySelectionActivityInstance],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_study_activity_instance_audit_trail(
    uid: str = studyUID,
) -> list[models.StudySelectionActivityInstance]:
    service = StudyActivityInstanceSelectionService()
    return service.get_all_selection_audit_trail(study_uid=uid)


@router.get(
    "/studies/{uid}/study-activity-instances/{study_activity_instance_uid}",
    dependencies=[rbac.STUDY_READ],
    summary="Returns specific study activity instance",
    response_model=models.StudySelectionActivityInstance,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exists no selection of the activity instance for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_selected_activity_instance(
    uid: str = studyUID,
    study_activity_instance_uid: str = study_selection_uid,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> models.StudySelectionActivity:
    service = StudyActivityInstanceSelectionService()
    return service.get_specific_selection(
        study_uid=uid,
        study_selection_uid=study_activity_instance_uid,
        study_value_version=study_value_version,
    )


@router.get(
    "/studies/{uid}/study-activity-instances/{study_activity_instance_uid}/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List audit trail related to a specific StudyActivityInstance.",
    response_model=list[models.StudySelectionActivityInstance],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the activity instance for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_specific_study_activity_instance_audit_trail(
    uid: str = studyUID,
    study_activity_instance_uid: str = study_selection_uid,
) -> models.StudySelectionActivityInstance:
    service = StudyActivityInstanceSelectionService()
    return service.get_specific_selection_audit_trail(
        study_uid=uid, study_selection_uid=study_activity_instance_uid
    )


@router.post(
    "/studies/{uid}/study-activity-instances/{study_activity_instance_uid}/sync-latest-version",
    dependencies=[rbac.STUDY_WRITE],
    summary="update to latest activity instance version study selection",
    description="""
    State before:
     - Study must exist
     - StudyActivityInstance selection must exist
     - Activity instance selected for study activity instance selection 
     is not the latest available final version of the activity instance.

    Business logic:
     - Update specified activity instance study-selection to latest activity instance

    State after:
     - Study exists
     - Study activity instance selection exists
     - Activity instance version selected for study activity instance selection is changed.
     - Added new entry in the audit trail for the update of the study-activity-instance.""",
    response_model=models.StudySelectionActivityInstance,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and study activity-instance",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_study_activity_instance_sync_to_latest_activity_instance(
    uid: str = studyUID,
    study_activity_instance_uid: str = study_selection_uid,
) -> models.StudySelectionActivityInstance:
    service = StudyActivityInstanceSelectionService()
    return service.update_selection_to_latest_version(
        study_uid=uid, study_selection_uid=study_activity_instance_uid
    )


#
# API endpoints to study activity


@router.get(
    "/study-activities",
    dependencies=[rbac.STUDY_READ],
    summary="Returns all study activities currently selected",
    response_model=CustomPage[models.StudySelectionActivity],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_selected_activities_for_all_studies(
    project_name: str | None = PROJECT_NAME,
    project_number: str | None = PROJECT_NUMBER,
    activity_names: list[str]
    | None = Query(
        None,
        description="A list of activity names to use as a specific filter",
        alias="activity_names[]",
    ),
    activity_subgroup_names: list[str]
    | None = Query(
        None,
        description="A list of activity sub group names to use as a specific filter",
        alias="activity_subgroup_names[]",
    ),
    activity_group_names: list[str]
    | None = Query(
        None,
        description="A list of activity group names to use as a specific filter",
        alias="activity_group_names[]",
    ),
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
) -> CustomPage[models.StudySelectionEndpoint]:
    service = StudyActivitySelectionService()
    all_selections = service.get_all_selections_for_all_studies(
        project_name=project_name,
        project_number=project_number,
        activity_names=activity_names,
        activity_subgroup_names=activity_subgroup_names,
        activity_group_names=activity_group_names,
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
    "/studies/{uid}/study-activities",
    dependencies=[rbac.STUDY_READ],
    summary="Returns all study activities currently selected",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    response_model=CustomPage[models.StudySelectionActivity],
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
@decorators.allow_exports(
    {
        "defaults": [
            "uid=study_activity_uid",
            "order",
            "soa_group=study_soa_group.soa_group_name",
            "activity_group=study_activity_group.activity_group_name",
            "activity_subgroup=study_activity_subgroup.activity_subgroup_name",
            "name=activity.name",
            "start_date",
            "user_initials",
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
def get_all_selected_activities(
    request: Request,  # request is actually required by the allow_exports decorator
    activity_names: list[str]
    | None = Query(
        None,
        description="A list of activity names to use as a specific filter",
        alias="activity_names[]",
    ),
    activity_subgroup_names: list[str]
    | None = Query(
        None,
        description="A list of activity sub group names to use as a specific filter",
        alias="activity_subgroup_names[]",
    ),
    activity_group_names: list[str]
    | None = Query(
        None,
        description="A list of activity group names to use as a specific filter",
        alias="activity_group_names[]",
    ),
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
    uid: str = studyUID,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> CustomPage[models.StudySelectionActivity]:
    service = StudyActivitySelectionService()
    all_items = service.get_all_selection(
        study_uid=uid,
        activity_names=activity_names,
        activity_subgroup_names=activity_subgroup_names,
        activity_group_names=activity_group_names,
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
    "/studies/{uid}/study-activities/headers",
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
def get_distinct_activity_values_for_header(
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
    uid: str = studyUID,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
):
    service = StudyActivitySelectionService()
    return service.get_distinct_values_for_header(
        study_uid=uid,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
        study_value_version=study_value_version,
    )


@router.get(
    "/studies/{uid}/study-activities/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List full audit trail related to definition of all study activities.",
    description="""
The following values should be returned for all study activities:
- date_time
- user_initials
- action
- activity
- order
    """,
    response_model=list[models.StudySelectionActivityCore],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_activity_audit_trail(
    uid: str = studyUID,
) -> list[models.StudySelectionActivityCore]:
    service = StudyActivitySelectionService()
    return service.get_all_selection_audit_trail(study_uid=uid)


@router.get(
    "/studies/{uid}/study-activities/{study_activity_uid}",
    dependencies=[rbac.STUDY_READ],
    summary="Returns specific study activity",
    response_model=models.StudySelectionActivity,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exists no selection of the activity for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_selected_activity(
    uid: str = studyUID,
    study_activity_uid: str = study_selection_uid,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> models.StudySelectionActivity:
    service = StudyActivitySelectionService()
    return service.get_specific_selection(
        study_uid=uid,
        study_selection_uid=study_activity_uid,
        study_value_version=study_value_version,
    )


@router.get(
    "/studies/{uid}/study-activities/{study_activity_uid}/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List audit trail related to definition of a specific study activity.",
    response_model=list[models.StudySelectionActivityCore],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the activity for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_selected_activity_audit_trail(
    uid: str = studyUID,
    study_activity_uid: str = study_selection_uid,
) -> models.StudySelectionActivityCore:
    service = StudyActivitySelectionService()
    return service.get_specific_selection_audit_trail(
        study_uid=uid, study_selection_uid=study_activity_uid
    )


@router.post(
    "/studies/{uid}/study-activities",
    dependencies=[rbac.STUDY_WRITE],
    summary="Creating a study activity selection based on the input data",
    response_model=models.StudySelectionActivity,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the activity",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or activity is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def post_new_activity_selection_create(
    uid: str = studyUID,
    selection: models.StudySelectionActivityCreateInput = Body(
        description="Related parameters of the selection that shall be created."
    ),
) -> models.StudySelectionActivity:
    service = StudyActivitySelectionService()
    return service.make_selection(study_uid=uid, selection_create_input=selection)


@router.patch(
    "/studies/{uid}/study-activities/{study_activity_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Edit a study activity",
    description="""
State before:
 - Study must exist and be in status draft
Business logic:
State after:
 - Added new entry in the audit trail for the update of the study-activity.""",
    response_model=models.StudySelectionActivity,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and activity.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_update_activity_selection(
    uid: str = studyUID,
    study_activity_uid: str = study_selection_uid,
    selection: models.StudySelectionActivityInput = Body(
        description="Related parameters of the selection that shall be updated."
    ),
) -> models.StudySelectionActivity:
    service = StudyActivitySelectionService()
    return service.patch_selection(
        study_uid=uid,
        study_selection_uid=study_activity_uid,
        selection_update_input=selection,
    )


@router.patch(
    "/studies/{uid}/study-activity-subgroups/{study_activity_subgroup_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Edit a study activity subgroup protocol visibility flag",
    description="""
State before:
 - Study must exist and be in status draft
Business logic:
State after:
 - Added new entry in the audit trail for the update of the study-activity-subgroup.""",
    response_model=models.StudyActivitySubGroup,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study-activity and study-activity-subgroup.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_update_activity_subgroup_selection(
    uid: str = studyUID,
    study_activity_subgroup_uid: str = study_selection_uid,
    selection: models.StudyActivitySubGroupEditInput = Body(
        description="Related parameters of the selection that shall be updated."
    ),
) -> models.StudyActivitySubGroup:
    service = StudyActivitySubGroupService()
    return service.patch_selection(
        study_uid=uid,
        study_selection_uid=study_activity_subgroup_uid,
        selection_update_input=selection,
    )


@router.patch(
    "/studies/{uid}/study-activity-groups/{study_activity_group_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Edit a study activity group protocol visibility flag",
    description="""
State before:
 - Study must exist and be in status draft
Business logic:
State after:
 - Added new entry in the audit trail for the update of the study-activity-group.""",
    response_model=models.StudyActivityGroup,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study-activity and study-activity-group.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_update_activity_group_selection(
    uid: str = studyUID,
    study_activity_group_uid: str = study_selection_uid,
    selection: models.StudyActivityGroupEditInput = Body(
        description="Related parameters of the selection that shall be updated."
    ),
) -> models.StudyActivityGroup:
    service = StudyActivityGroupService()
    return service.patch_selection(
        study_uid=uid,
        study_selection_uid=study_activity_group_uid,
        selection_update_input=selection,
    )


@router.patch(
    "/studies/{uid}/study-soa-groups/{study_soa_group_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Edit a study soa group protocol visibility flag",
    description="""
State before:
 - Study must exist and be in status draft
Business logic:
State after:
 - Added new entry in the audit trail for the update of the study-soa-group.""",
    response_model=models.StudySoAGroup,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study-activity and study-soa-group.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_update_soa_group_selection(
    uid: str = studyUID,
    study_soa_group_uid: str = study_selection_uid,
    selection: models.StudySoAGroupEditInput = Body(
        description="Related parameters of the selection that shall be updated."
    ),
) -> models.StudyActivityGroup:
    service = StudySoAGroupService()
    return service.patch_selection(
        study_uid=uid,
        study_selection_uid=study_soa_group_uid,
        selection_update_input=selection,
    )


@router.patch(
    "/studies/{uid}/study-activity-requests/{study_activity_request_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Edit a study activity request",
    description="""
State before:
 - Study must exist and be in status draft
Business logic:
State after:
 - Added new entry in the audit trail for the update of the study-activity.""",
    response_model=models.StudySelectionActivity,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and activity.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_update_activity_selection_request(
    uid: str = studyUID,
    study_activity_request_uid: str = study_selection_uid,
    selection: models.StudySelectionActivityRequestEditInput = Body(
        description="Related parameters of the selection that shall be updated."
    ),
) -> models.StudySelectionActivity:
    service = StudyActivitySelectionService()
    return service.patch_selection(
        study_uid=uid,
        study_selection_uid=study_activity_request_uid,
        selection_update_input=selection,
    )


@router.patch(
    "/studies/{uid}/study-activities/{study_activity_uid}/activity-requests-approvals",
    dependencies=[rbac.STUDY_WRITE],
    summary="Update Study Activity with the Sponsor Activity that replaced Activity Request",
    description="""
State before:
 - Study must exist and be in status draft
Business logic:
State after:
 - Added new entry in the audit trail for the update of the study-activity.""",
    response_model=models.StudySelectionActivity,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and activity.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def update_activity_request_with_sponsor_activity(
    uid: str = studyUID,
    study_activity_uid: str = study_selection_uid,
) -> models.StudySelectionActivity:
    service = StudyActivitySelectionService()
    return service.update_activity_request_with_sponsor_activity(
        study_uid=uid,
        study_selection_uid=study_activity_uid,
    )


@router.delete(
    "/studies/{uid}/study-activities/{study_activity_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Delete a study activity",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the activity and the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def delete_selected_activity(
    uid: str = studyUID,
    study_activity_uid: str = study_selection_uid,
):
    service = StudyActivitySelectionService()
    service.delete_selection(study_uid=uid, study_selection_uid=study_activity_uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/studies/{uid}/study-activities/batch",
    dependencies=[rbac.STUDY_WRITE],
    summary="Batch create and/or edit of study activities",
    response_model=list[models.StudySelectionActivityBatchOutput],
    status_code=207,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def activity_selection_batch_operations(
    uid: str = studyUID,
    operations: list[models.StudySelectionActivityBatchInput] = Body(description=""),
) -> list[models.StudySelectionActivityBatchOutput]:
    service = StudyActivitySelectionService()
    return service.handle_batch_operations(uid, operations)


@router.patch(
    "/studies/{uid}/study-activities/{study_activity_uid}/order",
    dependencies=[rbac.STUDY_WRITE],
    summary="Change the order of a study activity",
    response_model=models.StudySelectionActivity,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exists no selection between the study and activity to reorder.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_new_activity_selection_order(
    uid: str = studyUID,
    study_activity_uid: str = study_selection_uid,
    new_order_input: models.StudySelectionActivityNewOrder = Body(
        description="New value to set for the order property of the selection"
    ),
) -> models.StudySelectionActivity:
    service = StudyActivitySelectionService()
    return service.set_new_order(
        study_uid=uid,
        study_selection_uid=study_activity_uid,
        new_order=new_order_input.new_order,
    )


# Study Selection Arm endpoints


@router.get(
    "/studies/{uid}/study-arms",
    dependencies=[rbac.STUDY_READ],
    summary="""List all study arms currently selected for study with provided uid""",
    description=f"""
State before:
- Study must exist.
    
Business logic:
    - By default (no study status is provided) list all study arms for the study uid in status draft. If the study not exist in status draft then return the study arms for the study in status released. If the study uid only exist as deleted then this is returned.
    - If a specific study status parameter is provided then return study arm for this study status.
- If the locked study status parameter is requested then a study version should also be provided, and then the study arms for the specific locked study version is returned.
- Indicate by a boolean variable if the study arm can be updated (if the selected study is in status draft).  
- Indicate by a boolean variable if all expected selections have been made for each study arms, or some are missing.

State after:
- no change.
    
Possible errors:
- Invalid study-uid.

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=CustomPage[models.StudySelectionArmWithConnectedBranchArms],
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
            "study_uid",
            "study_version",
            "arm_uid",
            "type=arm_type.sponsor_preferred_name",
            "name",
            "code",
            "randomization_group",
            "number_of_subjects",
            "description",
            "start_date",
            "user_initials",
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
def get_all_selected_arms(
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
    uid: str = studyUID,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> CustomPage[models.StudySelectionArmWithConnectedBranchArms]:
    service = StudyArmSelectionService()
    all_items = service.get_all_selection(
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
    "/studies/{uid}/study-arms/headers",
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
def get_distinct_arm_values_for_header(
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
    uid: str = studyUID,
):
    service = StudyArmSelectionService()
    return service.get_distinct_values_for_header(
        study_uid=uid,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.get(
    "/study-arms",
    dependencies=[rbac.STUDY_READ],
    summary="Returns all study arms currently selected",
    response_model=CustomPage[models.StudySelectionArmWithConnectedBranchArms],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_selected_arms_for_all_studies(
    project_name: str | None = PROJECT_NAME,
    project_number: str | None = PROJECT_NUMBER,
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
) -> CustomPage[models.StudySelectionArmWithConnectedBranchArms]:
    service = StudyArmSelectionService()
    all_selections = service.get_all_selections_for_all_studies(
        project_name=project_name,
        project_number=project_number,
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


@router.patch(
    "/studies/{uid}/study-arms/{study_arm_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Edit a study arm",
    description="""
State before:
 - Study must exist and be in status draft

Business logic:

State after:
 - Added new entry in the audit trail for the update of the study-arm.""",
    response_model=models.StudySelectionArmWithConnectedBranchArms,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and arm.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_update_arm_selection(
    uid: str = studyUID,
    study_arm_uid: str = study_selection_uid,
    selection: models.StudySelectionArmInput = Body(
        description="Related parameters of the selection that shall be updated."
    ),
) -> models.StudySelectionArmWithConnectedBranchArms:
    service = StudyArmSelectionService()
    return service.patch_selection(
        study_uid=uid,
        study_selection_uid=study_arm_uid,
        selection_update_input=selection,
    )


@router.post(
    "/studies/{uid}/study-arms",
    dependencies=[rbac.STUDY_WRITE],
    summary="Creating a study arm selection based on the input data",
    response_model=models.StudySelectionArm,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the arm",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or arm is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def post_new_arm_selection_create(
    uid: str = studyUID,
    selection: models.study_selections.study_selection.StudySelectionArmCreateInput = Body(
        description="Related parameters of the selection that shall be created."
    ),
) -> models.StudySelectionArm:
    service = StudyArmSelectionService()
    return service.make_selection(study_uid=uid, selection_create_input=selection)


@router.get(
    "/studies/{uid}/study-arms/{study_arm_uid}/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List audit trail related to definition of a specific study arm.",
    response_model=list[models.StudySelectionArmVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the activity for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_selected_arm_audit_trail(
    uid: str = studyUID,
    study_arm_uid: str = study_selection_uid,
) -> list[models.StudySelectionArmVersion]:
    service = StudyArmSelectionService()
    return service.get_specific_selection_audit_trail(
        study_uid=uid, study_selection_uid=study_arm_uid
    )


@router.get(
    "/studies/{uid}/study-arms/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List audit trail related to definition of all study arms.",
    response_model=list[models.StudySelectionArmVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_arm_audit_trail(
    uid: str = studyUID,
) -> list[models.StudySelectionArmVersion]:
    service = StudyArmSelectionService()
    return service.get_all_selection_audit_trail(study_uid=uid)


@router.get(
    "/studies/{uid}/study-arms/{study_arm_uid}",
    dependencies=[rbac.STUDY_READ],
    summary="Returns specific study arm",
    response_model=models.StudySelectionArmWithConnectedBranchArms,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exists no selection of the arm for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_selected_arm(
    uid: str = studyUID,
    study_arm_uid: str = study_selection_uid,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> models.StudySelectionArmWithConnectedBranchArms:
    service = StudyArmSelectionService()
    return service.get_specific_selection(
        study_uid=uid,
        study_selection_uid=study_arm_uid,
        study_value_version=study_value_version,
    )


@router.patch(
    "/studies/{uid}/study-arms/{study_arm_uid}/order",
    dependencies=[rbac.STUDY_WRITE],
    summary="Change the order of a study arm",
    response_model=models.StudySelectionArmWithConnectedBranchArms,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exists no selection between the study and arm to reorder.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_new_arm_selection_order(
    uid: str = studyUID,
    study_arm_uid: str = study_selection_uid,
    new_order_input: models.StudySelectionArmNewOrder = Body(
        description="New value to set for the order property of the selection"
    ),
) -> models.StudySelectionArmWithConnectedBranchArms:
    service = StudyArmSelectionService()
    return service.set_new_order(
        study_uid=uid,
        study_selection_uid=study_arm_uid,
        new_order=new_order_input.new_order,
    )


@router.delete(
    "/studies/{uid}/study-arms/{study_arm_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Delete a study arm",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the arm and the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def delete_selected_arm(
    uid: str = studyUID,
    study_arm_uid: str = study_selection_uid,
):
    service = StudyArmSelectionService()
    service.delete_selection(study_uid=uid, study_selection_uid=study_arm_uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# API endpoints to study elements


@router.post(
    "/studies/{uid}/study-elements",
    dependencies=[rbac.STUDY_WRITE],
    summary="Creating a study element selection based on the input data",
    response_model=models.StudySelectionElement,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the element",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or element is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def post_new_element_selection_create(
    uid: str = studyUID,
    selection: models.study_selections.study_selection.StudySelectionElementCreateInput = Body(
        description="Related parameters of the selection that shall be created."
    ),
) -> models.StudySelectionElement:
    service = StudyElementSelectionService()
    return service.make_selection(study_uid=uid, selection_create_input=selection)


@router.get(
    "/studies/{uid}/study-elements",
    dependencies=[rbac.STUDY_READ],
    summary="""List all study elements currently selected for study with provided uid""",
    description=f"""
State before:
- Study must exist.

State after:
- no change.
    
Possible errors:
- Invalid study-uid.

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=CustomPage[models.StudySelectionElement],
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
            "element_subtype_name=element_subtype.sponsor_preferred_name",
            "element_name=name",
            "element_short_name=short_name",
            "start_rule",
            "end_rule",
            "description",
            "planned_duration",
            "start_date",
            "user_initials",
            "element_uid",
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
def get_all_selected_elements(
    request: Request,  # request is actually required by the allow_exports decorator
    uid: str = studyUID,
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
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> CustomPage[models.StudySelectionElement]:
    service = StudyElementSelectionService()
    all_items = service.get_all_selection(
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
    "/studies/{uid}/study-elements/headers",
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
def get_distinct_element_values_for_header(
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
    uid: str = studyUID,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
):
    service = StudyElementSelectionService()
    return service.get_distinct_values_for_header(
        study_uid=uid,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
        study_value_version=study_value_version,
    )


@router.get(
    "/studies/{uid}/study-elements/{study_element_uid}",
    dependencies=[rbac.STUDY_READ],
    summary="Returns specific study element",
    response_model=models.StudySelectionElement,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exists no selection of the element for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_selected_element(
    uid: str = studyUID,
    study_element_uid: str = study_selection_uid,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> models.StudySelectionElement:
    service = StudyElementSelectionService()
    return service.get_specific_selection(
        study_uid=uid,
        study_selection_uid=study_element_uid,
        study_value_version=study_value_version,
    )


@router.patch(
    "/studies/{uid}/study-elements/{study_element_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Edit a study element",
    description="""
        State before:
        - Study must exist and be in status draft
        Business logic:
        State after:
        - Added new entry in the audit trail for the update of the study-element.""",
    response_model=models.StudySelectionElement,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and element.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_update_element_selection(
    uid: str = studyUID,
    study_element_uid: str = study_selection_uid,
    selection: models.StudySelectionElementInput = Body(
        description="Related parameters of the selection that shall be updated."
    ),
) -> models.StudySelectionElement:
    service = StudyElementSelectionService()
    return service.patch_selection(
        study_uid=uid,
        study_selection_uid=study_element_uid,
        selection_update_input=selection,
    )


@router.get(
    "/studies/{uid}/study-elements/{study_element_uid}/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List audit trail related to definition of a specific study element.",
    response_model=list[models.StudySelectionElementVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the activity for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_selected_element_audit_trail(
    uid: str = studyUID,
    study_element_uid: str = study_selection_uid,
) -> list[models.StudySelectionElementVersion]:
    service = StudyElementSelectionService()
    return service.get_specific_selection_audit_trail(
        study_uid=uid, study_selection_uid=study_element_uid
    )


@router.get(
    "/studies/{uid}/study-element/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List audit trail related to definition of all study element.",
    response_model=list[models.StudySelectionElementVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_element_audit_trail(
    uid: str = studyUID,
) -> list[models.StudySelectionElementVersion]:
    service = StudyElementSelectionService()
    return service.get_all_selection_audit_trail(study_uid=uid)


@router.delete(
    "/studies/{uid}/study-elements/{study_element_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Delete a study element",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the element and the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def delete_selected_element(
    uid: str = studyUID,
    study_element_uid: str = study_selection_uid,
):
    service = StudyElementSelectionService()
    service.delete_selection(study_uid=uid, study_selection_uid=study_element_uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/study-elements/allowed-element-configs",
    dependencies=[rbac.STUDY_READ],
    summary="Returns all allowed config sets for element type and subtype",
    response_model=list[models.StudyElementTypes],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_configs() -> list[models.StudyElementTypes]:
    service = StudyElementSelectionService()
    return service.get_allowed_configs()


@router.patch(
    "/studies/{uid}/study-elements/{study_element_uid}/order",
    dependencies=[rbac.STUDY_WRITE],
    summary="Change the order of a study element",
    response_model=models.StudySelectionElement,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exists no selection between the study and element to reorder.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_new_element_selection_order(
    uid: str = studyUID,
    study_element_uid: str = study_selection_uid,
    new_order_input: models.StudySelectionElementNewOrder = Body(
        description="New value to set for the order property of the selection"
    ),
) -> models.StudySelectionElement:
    service = StudyElementSelectionService()
    return service.set_new_order(
        study_uid=uid,
        study_selection_uid=study_element_uid,
        new_order=new_order_input.new_order,
    )


# API Study-Branch-Arms endpoints


@router.post(
    "/studies/{uid}/study-branch-arms",
    dependencies=[rbac.STUDY_WRITE],
    summary="Creating a study branch arm selection based on the input data",
    response_model=models.StudySelectionBranchArm,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the branch arm",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or branch arm is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def post_new_branch_arm_selection_create(
    uid: str = studyUID,
    selection: models.study_selections.study_selection.StudySelectionBranchArmCreateInput = Body(
        description="Related parameters of the selection that shall be created."
    ),
) -> models.StudySelectionBranchArm:
    service = StudyBranchArmSelectionService()
    return service.make_selection(study_uid=uid, selection_create_input=selection)


@router.get(
    "/studies/{uid}/study-branch-arms",
    dependencies=[rbac.STUDY_READ],
    summary="""List all study branch arms currently selected for study with provided uid""",
    description=f"""
State before:
- Study must exist.
    
Business logic:
    - By default (no study status is provided) list all study branch arms for the study uid in status draft. If the study not exist in status draft then return the study branch arms for the study in status released. If the study uid only exist as deleted then this is returned.
    - If a specific study status parameter is provided then return study branch arm for this study status.
- If the locked study status parameter is requested then a study version should also be provided, and then the study branch arms for the specific locked study version is returned.
- Indicate by a boolean variable if the study branch arm can be updated (if the selected study is in status draft).  
- Indicate by a boolean variable if all expected selections have been made for each study branch arms, or some are missing.

State after:
- no change.
    
Possible errors:
- Invalid study-uid.

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=list[models.StudySelectionBranchArm],
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
            "branch_arm_uid",
            "arm_name=arm_root.name",
            "branch_arm_name=name",
            "branch_arm_short_name=short_name",
            "code",
            "randomization_group",
            "number_of_subjects",
            "description",
            "start_date",
            "user_initials",
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
def get_all_selected_branch_arms(
    request: Request,  # request is actually required by the allow_exports decorator
    uid: str = studyUID,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> list[models.StudySelectionBranchArm]:
    service = StudyBranchArmSelectionService()
    return service.get_all_selection(
        study_uid=uid, study_value_version=study_value_version
    )


@router.get(
    "/studies/{uid}/study-branch-arms/{study_branch_arm_uid}",
    dependencies=[rbac.STUDY_READ],
    summary="Returns specific study branch arm",
    response_model=models.StudySelectionBranchArm,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exists no selection of the branch arm for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_selected_branch_arm(
    uid: str = studyUID,
    study_branch_arm_uid: str = study_selection_uid,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> models.StudySelectionBranchArm:
    service = StudyBranchArmSelectionService()
    return service.get_specific_selection(
        study_uid=uid,
        study_selection_uid=study_branch_arm_uid,
        study_value_version=study_value_version,
    )


@router.patch(
    "/studies/{uid}/study-branch-arms/{study_branch_arm_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Edit a study branch arm",
    description="""
            State before:
            - Study must exist and be in status draft
            Business logic:
            State after:
            - Added new entry in the audit trail for the update of the study-branch-arm.""",
    response_model=models.StudySelectionBranchArm,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and branch arm.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_update_branch_arm_selection(
    uid: str = studyUID,
    study_branch_arm_uid: str = study_selection_uid,
    selection: models.StudySelectionBranchArmEditInput = Body(
        description="Related parameters of the selection that shall be updated."
    ),
) -> models.StudySelectionBranchArm:
    service = StudyBranchArmSelectionService()
    selection.branch_arm_uid = study_branch_arm_uid
    return service.patch_selection(
        study_uid=uid,
        selection_update_input=selection,
    )


@router.get(
    "/studies/{uid}/study-branch-arms/{study_branch_arm_uid}/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List audit trail related to definition of a specific study branch-arm.",
    response_model=list[models.StudySelectionBranchArmVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the activity for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_selected_branch_arm_audit_trail(
    uid: str = studyUID,
    study_branch_arm_uid: str = study_selection_uid,
) -> list[models.StudySelectionBranchArmVersion]:
    service = StudyBranchArmSelectionService()
    return service.get_specific_selection_audit_trail(
        study_uid=uid, study_selection_uid=study_branch_arm_uid
    )


@router.get(
    "/studies/{uid}/study-branch-arm/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List audit trail related to definition of all study branch-arm.",
    response_model=list[models.StudySelectionBranchArmVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_branch_arm_audit_trail(
    uid: str = studyUID,
) -> list[models.StudySelectionBranchArmVersion]:
    service = StudyBranchArmSelectionService()
    return service.get_all_selection_audit_trail(study_uid=uid)


@router.delete(
    "/studies/{uid}/study-branch-arms/{study_branch_arm_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Delete a study branch arm",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the branch arm and the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def delete_selected_branch_arm(
    uid: str = studyUID,
    study_branch_arm_uid: str = study_selection_uid,
):
    service = StudyBranchArmSelectionService()
    service.delete_selection(study_uid=uid, study_selection_uid=study_branch_arm_uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/studies/{uid}/study-branch-arms/{study_branch_arm_uid}/order",
    dependencies=[rbac.STUDY_WRITE],
    summary="Change the order of a study branch arm",
    response_model=models.StudySelectionBranchArm,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exists no selection between the study and branch arm to reorder.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_new_branch_arm_selection_order(
    uid: str = studyUID,
    study_branch_arm_uid: str = study_selection_uid,
    new_order_input: models.StudySelectionBranchArmNewOrder = Body(
        description="New value to set for the order property of the selection"
    ),
) -> models.StudySelectionBranchArm:
    service = StudyBranchArmSelectionService()
    return service.set_new_order(
        study_uid=uid,
        study_selection_uid=study_branch_arm_uid,
        new_order=new_order_input.new_order,
    )


@router.get(
    "/studies/{uid}/study-branch-arms/arm/{arm_uid}",
    dependencies=[rbac.STUDY_READ],
    summary="""List all study branch arms currently selected for study with provided uid""",
    description="""
    State before:
    - Study must exist.
     
    Business logic:
     - By default (no study status is provided) list all study branch arms for the study uid in status draft. If the study not exist in status draft then return the study branch arms for the study in status released. If the study uid only exist as deleted then this is returned.
     - If a specific study status parameter is provided then return study branch arm for this study status.
    - If the locked study status parameter is requested then a study version should also be provided, and then the study branch arms for the specific locked study version is returned.
    - Indicate by a boolean variable if the study branch arm can be updated (if the selected study is in status draft).  
    - Indicate by a boolean variable if all expected selections have been made for each study branch arms, or some are missing.

    State after:
    - no change.
     
    Possible errors:
    - Invalid study-uid.
""",
    response_model=list[models.StudySelectionBranchArm],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_selected_branch_arms_within_arm(
    uid: str,
    arm_uid: str,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> list[models.StudySelectionBranchArm]:
    service = StudyBranchArmSelectionService()
    return service.get_all_selection_within_arm(
        study_uid=uid, study_arm_uid=arm_uid, study_value_version=study_value_version
    )


# API Study-Cohorts endpoints


@router.post(
    "/studies/{uid}/study-cohorts",
    dependencies=[rbac.STUDY_WRITE],
    summary="Creating a study cohort selection based on the input data",
    response_model=models.StudySelectionCohort,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the cohort",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or cohort is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def post_new_cohort_selection_create(
    uid: str = studyUID,
    selection: models.StudySelectionCohortCreateInput = Body(
        description="Related parameters of the selection that shall be created."
    ),
) -> models.StudySelectionCohort:
    service = StudyCohortSelectionService()
    return service.make_selection(study_uid=uid, selection_create_input=selection)


@router.get(
    "/studies/{uid}/study-cohorts",
    dependencies=[rbac.STUDY_READ],
    summary="""List all study cohorts currently selected for study with provided uid""",
    description=f"""
State before:
- Study must exist.
    
Business logic:
    - By default (no study status is provided) list all study cohorts for the study uid in status draft. If the study not exist in status draft then return the study cohorts for the study in status released. If the study uid only exist as deleted then this is returned.
    - If a specific study status parameter is provided then return study cohort for this study status.
- If the locked study status parameter is requested then a study version should also be provided, and then the study cohorts for the specific locked study version is returned.
- Indicate by a boolean variable if the study cohort can be updated (if the selected study is in status draft).  
- Indicate by a boolean variable if all expected selections have been made for each study cohorts, or some are missing.

State after:
- no change.
    
Possible errors:
- Invalid study-uid.

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=CustomPage[models.StudySelectionCohort],
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
            "uid=cohort_uid",
            "arm_name=arm_roots.name",
            "branch_arm_name=branch_arm_roots.name",
            "branch_arm_short_name=branch_arm_roots.short_name",
            "cohort_name=name",
            "cohort_short_name=short_name",
            "code",
            "number_of_subjects",
            "description",
            "start_date",
            "user_initials",
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
def get_all_selected_cohorts(
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
    arm_uid: str
    | None = Query(
        None,
        description="The unique id of the study arm for which specified study cohorts should be returned",
    ),
    uid: str = studyUID,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> CustomPage[models.StudySelectionCohort]:
    service = StudyCohortSelectionService()

    all_selections = service.get_all_selection(
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
        study_uid=uid,
        arm_uid=arm_uid,
        study_value_version=study_value_version,
    )
    return CustomPage.create(
        items=all_selections.items,
        total=all_selections.total,
        page=page_number,
        size=page_size,
    )


@router.get(
    "/studies/{uid}/study-cohorts/{study_cohort_uid}",
    dependencies=[rbac.STUDY_READ],
    summary="Returns specific study cohort",
    response_model=models.StudySelectionCohort,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exists no selection of the cohort for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_selected_cohort(
    uid: str = studyUID,
    study_cohort_uid: str = study_selection_uid,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> models.StudySelectionCohort:
    service = StudyCohortSelectionService()
    return service.get_specific_selection(
        study_uid=uid,
        study_selection_uid=study_cohort_uid,
        study_value_version=study_value_version,
    )


@router.patch(
    "/studies/{uid}/study-cohorts/{study_cohort_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Edit a study cohort",
    description="""
            State before:
            - Study must exist and be in status draft
            Business logic:
            State after:
            - Added new entry in the audit trail for the update of the study-cohort.""",
    response_model=models.StudySelectionCohort,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and cohort.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_update_cohort_selection(
    uid: str = studyUID,
    study_cohort_uid: str = study_selection_uid,
    selection: models.StudySelectionCohortEditInput = Body(
        description="Related parameters of the selection that shall be updated."
    ),
) -> models.StudySelectionCohort:
    service = StudyCohortSelectionService()
    return service.patch_selection(
        study_uid=uid,
        study_selection_uid=study_cohort_uid,
        selection_update_input=selection,
    )


@router.get(
    "/studies/{uid}/study-cohorts/{study_cohort_uid}/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List audit trail related to definition of a specific study study-cohorts.",
    response_model=list[models.StudySelectionCohortVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the activity for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_selected_cohort_audit_trail(
    uid: str = studyUID,
    study_cohort_uid: str = study_selection_uid,
) -> list[models.StudySelectionCohortVersion]:
    service = StudyCohortSelectionService()
    return service.get_specific_selection_audit_trail(
        study_uid=uid, study_selection_uid=study_cohort_uid
    )


@router.get(
    "/studies/{uid}/study-cohort/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List audit trail related to definition of all study study-cohort.",
    response_model=list[models.StudySelectionCohortVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_cohort_audit_trail(
    uid: str = studyUID,
) -> list[models.StudySelectionCohortVersion]:
    service = StudyCohortSelectionService()
    return service.get_all_selection_audit_trail(study_uid=uid)


@router.delete(
    "/studies/{uid}/study-cohorts/{study_cohort_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Delete a study cohort",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the cohort and the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def delete_selected_cohort(
    uid: str = studyUID,
    study_cohort_uid: str = study_selection_uid,
):
    service = StudyCohortSelectionService()
    service.delete_selection(study_uid=uid, study_selection_uid=study_cohort_uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/studies/{uid}/study-cohorts/{study_cohort_uid}/order",
    dependencies=[rbac.STUDY_WRITE],
    summary="Change the order of a study cohort",
    response_model=models.StudySelectionCohort,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exists no selection between the study and cohort to reorder.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_new_cohort_selection_order(
    uid: str = studyUID,
    study_cohort_uid: str = study_selection_uid,
    new_order_input: models.StudySelectionCohortNewOrder = Body(
        description="New value to set for the order property of the selection"
    ),
) -> models.StudySelectionCohort:
    service = StudyCohortSelectionService()
    return service.set_new_order(
        study_uid=uid,
        study_selection_uid=study_cohort_uid,
        new_order=new_order_input.new_order,
    )
