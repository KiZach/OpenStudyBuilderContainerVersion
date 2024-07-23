from typing import Any

from fastapi import APIRouter, Path, Query
from pydantic.types import Json

from clinical_mdr_api import config
from clinical_mdr_api.domains.listings.utils import AdamReport
from clinical_mdr_api.models.listings.listings_adam import (
    StudyEndpntAdamListing,
    StudyVisitAdamListing,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.listings.listings_adam import (
    ADAMListingsService as ListingsService,
)

# Prefixed with "/listings"
router = APIRouter()


@router.get(
    "/studies/{study_uid}/adam/{adam_report}",
    dependencies=[rbac.STUDY_READ],
    summary="ADaM report listing, could be MDVISIT or MDENDPT as specified on adam_report",
    response_model=CustomPage[StudyVisitAdamListing]
    | CustomPage[StudyEndpntAdamListing],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_adam_listing(
    adam_report: AdamReport = Path(
        ..., description="specifies the report to be delivered"
    ),
    study_uid: str = Path(
        ...,
        description="Return study data of a given study and for a given ADaM report domain format.",
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
):
    service = ListingsService()
    all_items = service.get_report(
        adam_report=adam_report,
        study_uid=study_uid,
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
    "/studies/{study_uid}/adam/{adam_report}/headers",
    dependencies=[rbac.STUDY_READ],
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
    adam_report: AdamReport = Path(
        ..., description="specifies the report to be delivered"
    ),
    study_uid: str = Path(
        ...,
        description="Return study data of a given study and for a given ADaM report domain format.",
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
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
):
    service = ListingsService()
    return service.get_distinct_adam_listing_values_for_headers(
        study_uid=study_uid,
        adam_report=adam_report,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
        study_value_version=study_value_version,
    )
