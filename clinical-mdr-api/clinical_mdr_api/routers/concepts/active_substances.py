"""active_substances router"""
from typing import Any

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api import config
from clinical_mdr_api.models.concepts.active_substance import (
    ActiveSubstance,
    ActiveSubstanceCreateInput,
    ActiveSubstanceEditInput,
)
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.concepts.active_substances_service import (
    ActiveSubstanceService,
)

# Prefixed with "/concepts"
router = APIRouter()

ActiveSubstanceUID = Path(None, description="The unique id of the active substance")


@router.get(
    "/active-substances",
    dependencies=[rbac.LIBRARY_READ],
    summary="List all active substances (for a given library)",
    description=f"""
State before:
 - The library must exist (if specified)

Business logic:
 - List all active substances in their latest version, including properties derived from linked control terminology.

State after:
 - No change

Possible errors:
 - Invalid library name specified.
 
{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=CustomPage[ActiveSubstance],
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
            "analyte_number",
            "short_number",
            "long_number",
            "inn",
            "external_id",
            "start_date",
            "version",
            "status",
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
def get_active_substances(
    request: Request,  # request is actually required by the allow_exports decorator
    library: str | None = Query(None, description=_generic_descriptions.LIBRARY_NAME),
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
):
    active_substance_service = ActiveSubstanceService()
    results = active_substance_service.get_all_concepts(
        library=library,
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
    )
    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/active-substances/headers",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns possible values from the database for a given header",
    description="Allowed parameters include : field name for which to get possible values, "
    "search string to provide filtering for the field name, additional filters to apply on other fields",
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
    library: str | None = Query(None, description=_generic_descriptions.LIBRARY_NAME),
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
    active_substance_service = ActiveSubstanceService()
    return active_substance_service.get_distinct_values_for_header(
        library=library,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.get(
    "/active-substances/{uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get details on a specific active substance (in a specific version)",
    description="""
Possible errors:
 - Invalid uid, at_specified_date_time, status or version.
 """,
    response_model=ActiveSubstance,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_activity(uid: str = ActiveSubstanceUID):
    active_substance_service = ActiveSubstanceService()
    return active_substance_service.get_by_uid(uid=uid)


@router.get(
    "/active-substances/{uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="List version history for active substances",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for active substances.
 - The returned versions are ordered by start_date descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model=list[ActiveSubstance],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The active substance with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_versions(uid: str = ActiveSubstanceUID):
    active_substance_service = ActiveSubstanceService()
    return active_substance_service.get_version_history(uid=uid)


@router.post(
    "/active-substances",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates new active substance.",
    description="""
State before:
 - The specified library allows creation of concepts (the 'is_editable' property of the library needs to be true).
 - The specified CT term uids must exist, and the term names are in a final state.

Business logic:
 - New node is created for the active substance with the set properties.
 - relationships to specified control terminology are created (as in the model).
 - relationships to specified activity parent are created (as in the model)
 - The status of the new created version will be automatically set to 'Draft'.
 - The 'version' property of the new version will be automatically set to 0.1.
 - The 'change_description' property will be set automatically to 'Initial version'.

State after:
 - Active substance is created in status Draft and assigned an initial minor version number as 0.1.
 - Audit trail entry must be made with action of creating new Draft version.

Possible errors:
 - Invalid library or control terminology uid's specified.
""",
    response_model=ActiveSubstance,
    status_code=201,
    responses={
        201: {
            "description": "Created - The active substance was successfully created."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not exist.\n"
            "- The library does not allow to add new items.\n",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def create(
    active_substance_create_input: ActiveSubstanceCreateInput = Body(description=""),
):
    active_substance_service = ActiveSubstanceService()
    return active_substance_service.create(concept_input=active_substance_create_input)


@router.patch(
    "/active-substances/{uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Update active_substance",
    description="""
State before:
 - uid must exist and active substance must exist in status draft.
 - The active substance must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).

Business logic:
 - If active substance exist in status draft then attributes are updated.
 - If links to CT are selected or updated then relationships are made to CTTermRoots.
- If the linked active substance is updated, the relationships are updated to point to the active substance value node.

State after:
 - attributes are updated for the active_substance.
 - Audit trail entry must be made with update of attributes.

Possible errors:
 - Invalid uid.

""",
    response_model=ActiveSubstance,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The active substance is not in draft status.\n"
            "- The active substance had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The active substance with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def edit(
    uid: str = ActiveSubstanceUID,
    active_substance_edit_input: ActiveSubstanceEditInput = Body(description=""),
):
    active_substance_service = ActiveSubstanceService()
    return active_substance_service.edit_draft(
        uid=uid, concept_edit_input=active_substance_edit_input
    )


@router.post(
    "/active-substances/{uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approve draft version of an active substance",
    description="""
State before:
 - uid must exist and active substance must be in status Draft.
 
Business logic:
 - The latest 'Draft' version will remain the same as before.
 - The status of the new approved version will be automatically set to 'Final'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' version increased by +1.0.
 - The 'change_description' property will be set automatically to 'Approved version'.
 
State after:
 - ActiveSubstance changed status to Final and assigned a new major version number.
 - Audit trail entry must be made with action of approving to new Final version.
 
Possible errors:
 - Invalid uid or status not Draft.
    """,
    response_model=ActiveSubstance,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The active substance is not in draft status.\n"
            "- The library does not allow active substance approval.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The active substance with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def approve(uid: str = ActiveSubstanceUID):
    active_substance_service = ActiveSubstanceService()
    return active_substance_service.approve(uid=uid)


@router.post(
    "/active-substances/{uid}/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Create a new version of an active substance",
    description="""
State before:
 - uid must exist and the active substance must be in status Final.
 
Business logic:
- The active substance is changed to a draft state.

State after:
 - ActiveSubstance changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.
 
Possible errors:
 - Invalid uid or status not Final.
""",
    response_model=ActiveSubstance,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not allow to create active_substances.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The active substance is not in final status.\n"
            "- The active substance with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def create_new_version(uid: str = ActiveSubstanceUID):
    active_substance_service = ActiveSubstanceService()
    return active_substance_service.create_new_version(uid=uid)


@router.delete(
    "/active-substances/{uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of an active substance",
    description="""
State before:
 - uid must exist and active substance must be in status Final.
 
Business logic:
 - The latest 'Final' version will remain the same as before.
 - The status will be automatically set to 'Retired'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.
 
State after:
 - ActiveSubstance changed status to Retired.
 - Audit trail entry must be made with action of inactivating to retired version.
 
Possible errors:
 - Invalid uid or status not Final.
    """,
    response_model=ActiveSubstance,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The active substance is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The active substance with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def inactivate(uid: str = ActiveSubstanceUID):
    active_substance_service = ActiveSubstanceService()
    return active_substance_service.inactivate_final(uid=uid)


@router.post(
    "/active-substances/{uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of an active substance",
    description="""
State before:
 - uid must exist and active substance must be in status Retired.
 
Business logic:
 - The latest 'Retired' version will remain the same as before.
 - The status will be automatically set to 'Final'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - ActiveSubstance changed status to Final.
 - An audit trail entry must be made with action of reactivating to final version.
 
Possible errors:
 - Invalid uid or status not Retired.
    """,
    response_model=ActiveSubstance,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The active substance is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The active substance with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def reactivate(uid: str = ActiveSubstanceUID):
    active_substance_service = ActiveSubstanceService()
    return active_substance_service.reactivate_retired(uid=uid)


@router.delete(
    "/active-substances/{uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Delete draft version of an active substance",
    description="""
State before:
 - uid must exist
 - The concept must be in status Draft in a version less then 1.0 (never been approved).
 - The concept must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).
 
Business logic:
 - The draft concept is deleted.
 
State after:
 - ActiveSubstance is successfully deleted.
 
Possible errors:
 - Invalid uid or status not Draft or exist in version 1.0 or above (previously been approved) or not in an editable library.
    """,
    response_model=None,
    status_code=204,
    responses={
        204: {
            "description": "No Content - The active substance was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The active substance is not in draft status.\n"
            "- The active substance was already in final state or is in use.\n"
            "- The library does not allow to delete active_substance.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An active substance with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def delete(uid: str = ActiveSubstanceUID):
    active_substance_service = ActiveSubstanceService()
    active_substance_service.soft_delete(uid=uid)
