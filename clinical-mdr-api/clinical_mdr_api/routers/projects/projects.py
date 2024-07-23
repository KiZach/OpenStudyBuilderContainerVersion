from typing import Any

from fastapi import APIRouter, Body, Query
from pydantic.types import Json

from clinical_mdr_api import config, models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.projects.project import ProjectService

# Prefixed with "/projects"
router = APIRouter()


# Argument definitions
# ProjectUID = Path(
#     None, description="The unique id of the project.")


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all projects.",
    response_model=GenericFilteringReturn[models.Project],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_projects(
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
) -> GenericFilteringReturn[models.Project]:
    service = ProjectService()
    return service.get_all_projects(
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        total_count=total_count,
    )


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates a new project.",
    response_model=models.Project,
    status_code=201,
    responses={
        201: {"description": "Created - The project was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Some application/business rules forbid to process the request. Expect more detailed"
            " information in response body.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def create(
    project_create_input: models.ProjectCreateInput = Body(
        description="Related parameters of the project that shall be created."
    ),
) -> models.Project:
    service = ProjectService()
    return service.create(project_create_input)


@router.get(
    "/headers",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=list[Any],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_distinct_adam_listing_values_for_header(
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
    service = ProjectService()
    return service.get_project_headers(
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )
