"""CTCodelist router."""
from typing import Any

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api import config, models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.controlled_terminologies.ct_codelist import (
    CTCodelistService,
)

# Prefixed with "/ct"
router = APIRouter()

CTCodelistUID = Path(None, description="The unique id of the CTCodelistRoot")
TermUID = Path(None, description="The unique id of the Codelist Term")


@router.post(
    "/codelists",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates new codelist.",
    description="""The following nodes are created
* CTCodelistRoot
  * CTCodelistAttributesRoot
  * CTCodelistAttributesValue
  * CTCodelistNameRoot
  * CTCodelistNameValue
""",
    response_model=models.CTCodelist,
    status_code=201,
    responses={
        201: {"description": "Created - The codelist was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The catalogue does not exist.\n"
            "- The library does not exist.\n"
            "- The library does not allow to add new items.\n",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def create(
    codelist_input: models.CTCodelistCreateInput = Body(
        description="Properties to create CTCodelistAttributes and CTCodelistName.",
    ),
):
    ct_codelist_service = CTCodelistService()
    return ct_codelist_service.create(codelist_input)


@router.get(
    "/codelists",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all codelists names and attributes.",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    response_model=CustomPage[models.CTCodelistNameAndAttributes],
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
            "library_name",
            "concept_id=codelist_uid",
            "sponsor_preferred_name=name.name",
            "template_parameter=name.template_parameter",
            "cd_status=name.status",
            "modified_name=name.start_date",
            "cd_name=attributes.name",
            "submission_value=attributes.submission_value",
            "nci_preferred_name=attributes.nci_preferred_name",
            "extensible=attributes.extensible",
            "attributes_status=attributes.status",
            "modified_attributes=attributes.start_date",
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
def get_codelists(
    request: Request,  # request is actually required by the allow_exports decorator
    catalogue_name: str
    | None = Query(
        None,
        description="If specified, only codelists from given catalogue are returned.",
    ),
    library: str
    | None = Query(
        None,
        description="If specified, only codelists from given library are returned.",
    ),
    package: str
    | None = Query(
        None,
        description="If specified, only codelists from given package are returned.",
    ),
    is_sponsor: bool
    | None = Query(
        False,
        description="Boolean value to indicate desired package is a sponsor package. Defaults to False.",
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
    term_filter: Json
    | None = Query(
        None,
        description="""JSON dictionary consisting of `term_uids` key and `operator` key. Default: `{}` (no term filtering).

`term_uids` Specifies a list of of CT Term UIDs to filter on. Only Codelists with terms with provided UIDs will be returned.

`operator` specifies which logical operation - `and` or `or` - should be used in case multiple CT Term UIDs are provided. Default: `and`""",
        example="""{"term_uids": [""], "operator": "and"}""",
    ),
):
    ct_codelist_service = CTCodelistService()
    results = ct_codelist_service.get_all_codelists(
        catalogue_name=catalogue_name,
        library=library,
        package=package,
        is_sponsor=is_sponsor,
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        term_filter=term_filter,
    )
    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/codelists/{codelist_uid}/sub-codelists",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all sub codelists names and attributes that only have the provided terms.",
    response_model=CustomPage[models.CTCodelistNameAndAttributes],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_sub_codelists_that_have_given_terms(
    codelist_uid: str = CTCodelistUID,
    term_uids: list[str] = Query(
        ...,
        description="A list of term uids",
    ),
    library: str
    | None = Query(
        None,
        description="If specified, only codelists from given library are returned.",
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
    total_count: bool
    | None = Query(False, description=_generic_descriptions.TOTAL_COUNT),
):
    ct_codelist_service = CTCodelistService()
    results = ct_codelist_service.get_sub_codelists_that_have_given_terms(
        codelist_uid=codelist_uid,
        term_uids=term_uids,
        library=library,
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
    )
    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/codelists/headers",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns possibles values from the database for a given header",
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
    catalogue_name: str
    | None = Query(
        None,
        description="If specified, only codelists from given catalogue are returned.",
    ),
    library: str
    | None = Query(
        None, description="If specified, only terms from given library are returned."
    ),
    package: str
    | None = Query(
        None, description="If specified, only terms from given package are returned."
    ),
    is_sponsor: bool
    | None = Query(
        False,
        description="Boolean value to indicate desired package is a sponsor package. Defaults to False.",
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
    ct_codelist_service = CTCodelistService()
    return ct_codelist_service.get_distinct_values_for_header(
        catalogue_name=catalogue_name,
        library=library,
        package=package,
        is_sponsor=is_sponsor,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.post(
    "/codelists/{codelist_uid}/terms",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Adds new CTTerm to CTCodelist.",
    response_model=models.CTCodelist,
    status_code=201,
    responses={
        201: {
            "description": "The HAS_TERM relationship was successfully created.\n"
            "The TemplateParameter labels and HAS_PARAMETER_TERM relationship were successfully added "
            "if codelist identified by codelist_uid is a TemplateParameter."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The codelist does not exist.\n"
            "- The term does not exist.\n"
            "- The codelist is not extensible.\n"
            "- The codelist already has passed term.\n",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def add_term(
    codelist_uid: str = CTCodelistUID,
    term_input: models.CTCodelistTermInput = Body(
        description="UID of the CTTermRoot node."
    ),
):
    ct_codelist_service = CTCodelistService()
    return ct_codelist_service.add_term(
        codelist_uid=codelist_uid, term_uid=term_input.term_uid, order=term_input.order
    )


@router.delete(
    "/codelists/{codelist_uid}/terms/{term_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Removes given CTTerm from CTCodelist.",
    response_model=models.CTCodelist,
    status_code=201,
    responses={
        201: {
            "description": "The HAS_TERM relationship was successfully deleted and "
            "HAD_TERM relationship was successfully created.\n"
            "The HAS_PARAMETER_TERM relationship was successfully deleted if codelist identified by "
            "codelist_uid is a TemplateParameter"
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The codelist does not exist.\n"
            "- The term does not exist.\n"
            "- The codelist is not extensible.\n"
            "- The codelist doesn't have passed term.\n",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def remove_term(
    codelist_uid: str = CTCodelistUID,
    term_uid: str = TermUID,
):
    ct_codelist_service = CTCodelistService()
    return ct_codelist_service.remove_term(codelist_uid=codelist_uid, term_uid=term_uid)
