from typing import Any

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json

from clinical_mdr_api import config
from clinical_mdr_api.models import (
    OdmFormalExpression,
    OdmFormalExpressionPatchInput,
    OdmFormalExpressionPostInput,
)
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.concepts.odms.odm_formal_expressions import (
    OdmFormalExpressionService,
)

# Prefixed with "/concepts/odms/formal-expressions"
router = APIRouter()

# Argument definitions
OdmFormalExpressionUID = Path(
    None, description="The unique id of the ODM Formal Expression."
)


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Return every variable related to the selected status and version of the ODM Formal Expressions",
    description="",
    response_model=CustomPage[OdmFormalExpression],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_odm_formal_expressions(
    library: str | None = Query(None),
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
    odm_formal_expression_service = OdmFormalExpressionService()
    results = odm_formal_expression_service.get_all_concepts(
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
    "/headers",
    dependencies=[rbac.LIBRARY_READ],
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
    library_name: str | None = Query(None),
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
    odm_formal_expression_service = OdmFormalExpressionService()
    return odm_formal_expression_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.get(
    "/{uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get details on a specific ODM Formal Expression (in a specific version)",
    description="",
    response_model=OdmFormalExpression,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_odm_formal_expression(uid: str = OdmFormalExpressionUID):
    odm_formal_expression_service = OdmFormalExpressionService()
    return odm_formal_expression_service.get_by_uid(uid=uid)


@router.get(
    "/{uid}/relationships",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get UIDs of a specific ODM Formal Expression's relationships",
    description="",
    response_model=dict,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_active_relationships(uid: str = OdmFormalExpressionUID):
    odm_formal_expression_service = OdmFormalExpressionService()
    return odm_formal_expression_service.get_active_relationships(uid=uid)


@router.get(
    "/{uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="List version history for ODM Formal Expression",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for ODM Formal Expressions.
 - The returned versions are ordered by start_date descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model=list[OdmFormalExpression],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Formal Expression with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_odm_formal_expression_versions(uid: str = OdmFormalExpressionUID):
    odm_formal_expression_service = OdmFormalExpressionService()
    return odm_formal_expression_service.get_version_history(uid=uid)


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates a new Form in 'Draft' status with version 0.1",
    description="",
    response_model=OdmFormalExpression,
    status_code=201,
    responses={
        201: {
            "description": "Created - The ODM Formal Expression was successfully created."
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
def create_odm_formal_expression(
    odm_formal_expression_create_input: OdmFormalExpressionPostInput = Body(
        description=""
    ),
):
    odm_formal_expression_service = OdmFormalExpressionService()
    return odm_formal_expression_service.create(
        concept_input=odm_formal_expression_create_input
    )


@router.patch(
    "/{uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Update ODM Formal Expression",
    description="",
    response_model=OdmFormalExpression,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Formal Expression is not in draft status.\n"
            "- The ODM Formal Expression had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Formal Expression with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def edit_odm_formal_expression(
    uid: str = OdmFormalExpressionUID,
    odm_formal_expression_edit_input: OdmFormalExpressionPatchInput = Body(
        description=""
    ),
):
    odm_formal_expression_service = OdmFormalExpressionService()
    return odm_formal_expression_service.edit_draft(
        uid=uid, concept_edit_input=odm_formal_expression_edit_input
    )


@router.post(
    "/{uid}/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Create a new version of ODM Formal Expression",
    description="""
State before:
 - uid must exist and the ODM Formal Expression must be in status Final.

Business logic:
- The ODM Formal Expression is changed to a draft state.

State after:
 - ODM Formal Expression changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.

Possible errors:
 - Invalid uid or status not Final.
""",
    response_model=OdmFormalExpression,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not allow to create ODM Formal Expressions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The ODM Formal Expression is not in final status.\n"
            "- The ODM Formal Expression with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def create_odm_formal_expression_version(uid: str = OdmFormalExpressionUID):
    odm_formal_expression_service = OdmFormalExpressionService()
    return odm_formal_expression_service.create_new_version(uid=uid)


@router.post(
    "/{uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approve draft version of ODM Formal Expression",
    description="",
    response_model=OdmFormalExpression,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Formal Expression is not in draft status.\n"
            "- The library does not allow to approve ODM Formal Expression.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Formal Expression with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def approve_odm_formal_expression(uid: str = OdmFormalExpressionUID):
    odm_formal_expression_service = OdmFormalExpressionService()
    return odm_formal_expression_service.approve(uid=uid)


@router.delete(
    "/{uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of ODM Formal Expression",
    description="",
    response_model=OdmFormalExpression,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Formal Expression is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Formal Expression with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def inactivate_odm_formal_expression(uid: str = OdmFormalExpressionUID):
    odm_formal_expression_service = OdmFormalExpressionService()
    return odm_formal_expression_service.inactivate_final(uid=uid)


@router.post(
    "/{uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of a ODM Formal Expression",
    description="",
    response_model=OdmFormalExpression,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Formal Expression is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Formal Expression with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def reactivate_odm_formal_expression(uid: str = OdmFormalExpressionUID):
    odm_formal_expression_service = OdmFormalExpressionService()
    return odm_formal_expression_service.reactivate_retired(uid=uid)


@router.delete(
    "/{uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Delete draft version of ODM Formal Expression",
    description="",
    response_model=None,
    status_code=204,
    responses={
        204: {
            "description": "No Content - The ODM Formal Expression was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Formal Expression is not in draft status.\n"
            "- The ODM Formal Expression was already in final state or is in use.\n"
            "- The library does not allow to delete ODM Formal Expression.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An ODM Formal Expression with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def delete_odm_formal_expression(uid: str = OdmFormalExpressionUID):
    odm_formal_expression_service = OdmFormalExpressionService()
    odm_formal_expression_service.soft_delete(uid=uid)
