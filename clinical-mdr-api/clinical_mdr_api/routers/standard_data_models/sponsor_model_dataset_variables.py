"""Sponsor Model Dataset Variables router"""
from typing import Any

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api import config
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.standard_data_models.sponsor_model_dataset_variable import (
    SponsorModelDatasetVariable,
    SponsorModelDatasetVariableInput,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.standard_data_models.sponsor_model_dataset_variable import (
    SponsorModelDatasetVariableService,
)

# Prefixed with "/standards/sponsor-models/variable-classes"
router = APIRouter()

SponsorModelDatasetVariableUID = Path(
    None, description="The unique id of the SponsorModelDatasetVariable"
)


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="List all sponsor model dataset variables",
    description="""
State before:

Business logic:
 - List all sponsor model dataset variables in their latest version.

State after:
 - No change

Possible errors:
""",
    response_model=CustomPage[SponsorModelDatasetVariable],
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
@decorators.allow_exports(
    {
        "defaults": ["uid", "name", "start_date", "status", "version"],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
# pylint: disable=unused-argument
def get_sponsor_model_dataset_variables(
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
):
    sponsor_model_dataset_variable_service = SponsorModelDatasetVariableService()
    results = sponsor_model_dataset_variable_service.get_all_items(
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
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_distinct_values_for_header(
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
    sponsor_model_dataset_variable_service = SponsorModelDatasetVariableService()
    return sponsor_model_dataset_variable_service.get_distinct_values_for_header(
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Create a new version of the sponsor model dataset variable.",
    description="""
    State before:
    - The specified parent Dataset must exist.

    Business logic :
    - New instance is created for the DatasetVariable.

    State after:
    - SponsorModelDatasetVariableInstance node is created, assigned a version, and linked with the DatasetVariable node.

    Possible errors:
    - Missing Dataset.
    """,
    response_model=SponsorModelDatasetVariable,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        201: {
            "description": "Created - a new version of the sponsor model dataset variable was successfully created."
        },
        400: {
            "model": ErrorResponse,
            "description": "BusinessLogicException - Reasons include e.g.: \n"
            "- The target parent Dataset *dataset_uid* does not exist in the database.\n",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
# pylint: disable=unused-argument
def create(
    sponsor_model: SponsorModelDatasetVariableInput = Body(
        ...,
        description="Parameters of the Sponsor Model Dataset Variable that shall be created.",
    ),
) -> SponsorModelDatasetVariable:
    sponsor_model_dataset_variable_service = SponsorModelDatasetVariableService()
    return sponsor_model_dataset_variable_service.create(item_input=sponsor_model)
