"""Time points router."""
from typing import Any

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json

from clinical_mdr_api import config
from clinical_mdr_api.models.concepts.concept import TimePoint, TimePointInput
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.concepts.simple_concepts.time_point import (
    TimePointService,
)

# Prefixed with "/concepts/time-points"
router = APIRouter()

TimePointUID = Path(None, description="The unique id of the time point")


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="List all time points (for a given library)",
    description="""
State before:
 - The library must exist (if specified)

Business logic:
 - List all time points.

State after:
 - No change

Possible errors:
 - Invalid library name specified.""",
    response_model=CustomPage[TimePoint],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_time_points(
    library: str | None = Query(None, description="The library name"),
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
    time_point_service = TimePointService()
    results = time_point_service.get_all_concepts(
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
    library: str | None = Query(None, description="The library name"),
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
    time_point_service = TimePointService()
    return time_point_service.get_distinct_values_for_header(
        library=library,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.get(
    "/{uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get details on a specific time point",
    description="""
State before:
 - a time point with uid must exist.

State after:
 - No change

Possible errors:
 - Invalid uid
 """,
    response_model=TimePoint,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_time_point(uid: str = TimePointUID):
    time_point_service = TimePointService()
    return time_point_service.get_by_uid(uid=uid)


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates new time point.",
    description="""
State before:
 - The specified library allows creation of concepts (the 'is_editable' property of the library needs to be true).

Business logic:
 - New node is created for the time point with the set properties.

Possible errors:
 - Invalid library.
""",
    response_model=TimePoint,
    status_code=201,
    responses={
        201: {"description": "Created - The time point was successfully created."},
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
    time_point_create_input: TimePointInput = Body(description=""),
):
    time_point_service = TimePointService()
    return time_point_service.create(concept_input=time_point_create_input)
