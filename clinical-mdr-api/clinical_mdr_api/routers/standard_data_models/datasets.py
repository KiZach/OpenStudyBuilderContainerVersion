"""datasets router."""
from typing import Any

from fastapi import APIRouter, Path, Query
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api import config
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.standard_data_models.dataset import Dataset
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.standard_data_models.dataset import DatasetService

# Prefixed with "/standards"
router = APIRouter()

DatasetUID = Path(None, description="The unique id of the Dataset")


@router.get(
    "/datasets",
    dependencies=[rbac.LIBRARY_READ],
    summary="List all datasets",
    description=f"""
State before:

Business logic:
 - List all datasets in their latest version.

State after:
 - No change

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=CustomPage[Dataset],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
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
def get_datasets(
    request: Request,  # request is actually required by the allow_exports decorator
    data_model_ig_name: str = Query(
        ...,
        description="The name of the selected Data model implementation guide, for instance 'CDASHIG'",
    ),
    data_model_ig_version: str = Query(
        ...,
        description="The version of the selected Data model implementation guide, for instance '2.2'",
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
):
    dataset_service = DatasetService()
    results = dataset_service.get_all_items(
        data_model_ig_name=data_model_ig_name,
        data_model_ig_version=data_model_ig_version,
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
    "/datasets/headers",
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
    data_model_ig_name: str = Query(
        ...,
        description="The name of the selected Data model implementation guide, for instance 'CDASHIG'",
    ),
    data_model_ig_version: str = Query(
        ...,
        description="The version of the selected Data model implementation guide, for instance '2.2'",
    ),
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
    dataset_service = DatasetService()
    return dataset_service.get_distinct_values_for_header(
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
        data_model_ig_name=data_model_ig_name,
        data_model_ig_version=data_model_ig_version,
    )


@router.get(
    "/datasets/{uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get details on a specific dataset",
    description="""
State before:
 - a dataset with uid must exist.

Business logic:

State after:
 - No change

Possible errors:
 - Invalid uid.
 """,
    response_model=Dataset,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_dataset(
    data_model_ig_name: str = Query(
        ...,
        description="The name of the selected Data model implementation guide, for instance 'CDASHIG'",
    ),
    data_model_ig_version: str = Query(
        ...,
        description="The version of the selected Data model implementation guide, for instance '2.2'",
    ),
    uid: str = DatasetUID,
):
    dataset_service = DatasetService()
    return dataset_service.get_by_uid(
        uid=uid,
        data_model_ig_version=data_model_ig_version,
        data_model_ig_name=data_model_ig_name,
    )
