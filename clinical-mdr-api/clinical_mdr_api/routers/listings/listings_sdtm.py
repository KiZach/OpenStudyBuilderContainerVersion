from fastapi import APIRouter, Path, Query
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api import config, models
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.listings.listings_sdtm import (
    SDTMListingsService as ListingsService,
)

# Prefixed with "/listings"
router = APIRouter()


@router.get(
    "/studies/{study_uid}/sdtm/tv",
    dependencies=[rbac.STUDY_READ],
    summary="SDTM TV domain listing",
    response_model=CustomPage[models.StudyVisitListing],
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
            "STUDYID",
            "DOMAIN",
            "VISITNUM",
            "VISIT",
            "VISITDY",
            "ARMCD",
            "ARM",
            "TVSTRL",
            "TVENRL",
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
def get_tv(
    request: Request,  # request is actually required by the allow_exports decorator
    study_uid: str = Path(
        None,
        description="Return study visit data of a given study in SDTM TV domain format.",
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
    all_items = service.list_tv(
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
    "/studies/{study_uid}/sdtm/ta",
    dependencies=[rbac.STUDY_READ],
    summary="SDTM TA domain listing",
    response_model=CustomPage[models.StudyArmListing],
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
            "STUDYID",
            "DOMAIN",
            "ARMCD",
            "ARM",
            "TAETORD",
            "ETCD",
            "ELEMENT",
            "TABRANCH",
            "TATRANS",
            "EPOCH",
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
def get_ta(
    request: Request,  # request is actually required by the allow_exports decorator
    study_uid: str = Path(
        None,
        description="Return study arm data of a given study number in SDTM TA domain format.",
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
    all_items = service.list_ta(
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
    "/studies/{study_uid}/sdtm/ti",
    dependencies=[rbac.STUDY_READ],
    summary="SDTM TI domain listing",
    response_model=CustomPage[models.StudyCriterionListing],
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
            "STUDYID",
            "DOMAIN",
            "IETESTCD",
            "IETEST",
            "IECAT",
            "IESCAT",
            "TIRL",
            "TIVERS",
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
def get_ti(
    request: Request,  # request is actually required by the allow_exports decorator
    study_uid: str = Path(
        None,
        description="Return study criterion data of a given study in SDTM TI domain format.",
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
    all_items = service.list_ti(
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
    "/studies/{study_uid}/sdtm/ts",
    dependencies=[rbac.STUDY_READ],
    summary="SDTM TS domain listing",
    response_model=CustomPage[models.StudySummaryListing],
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
            "STUDYID",
            "DOMAIN",
            "TSPARMCD",
            "TSPARM",
            "TSVAL",
            "TSVALNF",
            "TSVALCD",
            "TSVCDREF",
            "TSVCDVER",
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
def get_ts(
    request: Request,  # request is actually required by the allow_exports decorator
    study_uid: str = Path(
        None,
        description="Return study summary data of a given study in SDTM TS domain format.",
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
    all_items = service.list_ts(
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
    "/studies/{study_uid}/sdtm/te",
    dependencies=[rbac.STUDY_READ],
    summary="SDTM TE domain listing",
    response_model=CustomPage[models.StudyElementListing],
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
            "STUDYID",
            "DOMAIN",
            "ETCD",
            "ELEMENT",
            "TESTRL",
            "TEENRL",
            "TEDUR",
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
def get_te(
    request: Request,  # request is actually required by the allow_exports decorator
    study_uid: str = Path(
        None,
        description="Return study element data of a given study number in SDTM TE domain format.",
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
    all_items = service.list_te(
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
    "/studies/{study_uid}/sdtm/tdm",
    dependencies=[rbac.STUDY_READ],
    summary="SDTM TDM domain listing",
    response_model=CustomPage[models.StudyDiseaseMilestoneListing],
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
            "STUDYID",
            "DOMAIN",
            "MIDSTYPE",
            "TMDEF",
            "TMRPT",
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
def get_tdm(
    request: Request,  # request is actually required by the allow_exports decorator
    study_uid: str = Path(
        None,
        description="Return study disease milestone data of a given study number in SDTM TDM domain format.",
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
    all_items = service.list_tdm(
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
