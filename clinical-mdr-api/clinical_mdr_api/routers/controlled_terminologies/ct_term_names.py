"""CTTermNames router."""
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, Path, Query, Response
from fastapi import status as fast_api_status
from pydantic.types import Json

from clinical_mdr_api import config, models
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.controlled_terminologies.ct_term_name import (
    CTTermNameService,
)

# Prefixed with "/ct"
router = APIRouter()

CTTermUID = Path(None, description="The unique id of the CTTermNames")


@router.get(
    "/terms/names",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all terms names.",
    response_model=CustomPage[models.CTTermName | models.CTTermNameSimple],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_terms(
    codelist_uid: str
    | None = Query(
        None, description="If specified, only terms from given codelist are returned."
    ),
    codelist_name: str
    | None = Query(
        None, description="If specified, only terms from given codelist are returned."
    ),
    library: str
    | None = Query(
        None, description="If specified, only terms from given library are returned."
    ),
    package: str
    | None = Query(
        None, description="If specified, only terms from given package are returned."
    ),
    compact_response: bool
    | None = Query(
        False,
        description="If true, only `term_uid` and `sponsor_prefered_name` fields are returned for each item.",
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
    ct_term_name_service = CTTermNameService()
    results = ct_term_name_service.get_all_ct_terms(
        codelist_uid=codelist_uid,
        codelist_name=codelist_name,
        library=library,
        package=package,
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
    )

    if compact_response:
        # TODO: This is a workaround to remove duplicates from the response.
        # Creating the compact model removes some fields that make the items unique,
        # leading to duplicates in the response.
        # To remove these duplicates, go via a set of tuples.
        # The downside is that the number of returned items may be smaller than
        # the requested page size even if there are more items in the database.
        unique_items = set(
            (x.term_uid, x.sponsor_preferred_name) for x in results.items
        )

        results.items = [
            models.CTTermNameSimple(
                term_uid=term_uid,
                sponsor_preferred_name=sponsor_preferred_name,
            )
            for term_uid, sponsor_preferred_name in unique_items
        ]

        page_size = len(results.items)

    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/terms/names/headers",
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
    codelist_uid: str
    | None = Query(
        None, description="If specified, only terms from given codelist are returned."
    ),
    codelist_name: str
    | None = Query(
        None, description="If specified, only terms from given codelist are returned."
    ),
    library: str
    | None = Query(
        None, description="If specified, only terms from given library are returned."
    ),
    package: str
    | None = Query(
        None, description="If specified, only terms from given package are returned."
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
    ct_term_service = CTTermNameService()
    return ct_term_service.get_distinct_values_for_header(
        codelist_uid=codelist_uid,
        codelist_name=codelist_name,
        library=library,
        package=package,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.get(
    "/terms/{term_uid}/names",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the latest/newest version of a specific ct term identified by 'term_uid'",
    response_model=models.CTTermName,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_term_names(
    term_uid: str = CTTermUID,
    at_specified_date_time: datetime
    | None = Query(
        None,
        description="If specified then the latest/newest representation of the "
        "CTTermNameValue at this point in time is returned.\n"
        "The point in time needs to be specified in ISO 8601 format including the timezone, "
        "e.g.: '2020-10-31T16:00:00+02:00' for October 31, 2020 at 4pm in UTC+2 timezone. "
        "If the timezone is omitted, UTC±0 is assumed.",
    ),
    status: LibraryItemStatus
    | None = Query(
        None,
        description="If specified then the representation of the CTTermNameValue "
        "in that status is returned (if existent).\n_this is useful if the"
        " CTTermNameValue has a status 'Draft' and a status 'Final'.",
    ),
    version: str
    | None = Query(
        None,
        description="If specified then the latest/newest representation of the "
        "for CTTermNameValue in that version is returned.\n"
        "Only exact matches are considered. The version is specified in the following format:"
        "<major>.<minor> where <major> and <minor> are digits. E.g. '0.1', '0.2', '1.0',",
    ),
):
    ct_term_name_service = CTTermNameService()
    return ct_term_name_service.get_by_uid(
        term_uid=term_uid,
        at_specific_date=at_specified_date_time,
        status=status,
        version=version,
    )


@router.get(
    "/terms/{term_uid}/names/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the version history of a specific CTTermName identified by 'term_uid'.",
    description="The returned versions are ordered by\n"
    "0. start_date descending (newest entries first)",
    response_model=list[models.CTTermNameVersion],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The codelist with the specified 'codelist_uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_versions(term_uid: str = CTTermUID):
    ct_term_name_service = CTTermNameService()
    return ct_term_name_service.get_version_history(term_uid=term_uid)


@router.patch(
    "/terms/{term_uid}/names",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Updates the term identified by 'term_uid'.",
    description="""This request is only valid if the term
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true). 

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.
""",
    response_model=models.CTTermName,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The term is not in draft status.\n"
            "- The term had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The term with the specified 'term_uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def edit(
    term_uid: str = CTTermUID,
    term_input: models.CTTermNameEditInput = Body(
        description="The new parameter terms for the term including the change description.",
    ),
):
    ct_term_name_service = CTTermNameService()
    return ct_term_name_service.edit_draft(term_uid=term_uid, term_input=term_input)


@router.post(
    "/terms/{term_uid}/names/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates a new term in 'Draft' status.",
    description="""This request is only valid if
* the specified term is in 'Final' status and
* the specified library allows creating term (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Draft'.
* The 'change_description' property will be set automatically to 'new-version'.
* The 'version' property will be increased by '0.1'.
""",
    response_model=models.CTTermName,
    status_code=201,
    responses={
        201: {"description": "Created - The term was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not allow to create tterm.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The term is not in final status.\n"
            "- The term with the specified 'codelist_uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def create(term_uid: str = CTTermUID):
    ct_term_name_service = CTTermNameService()
    return ct_term_name_service.create_new_version(term_uid=term_uid)


@router.post(
    "/terms/{term_uid}/names/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approves the term identified by 'term_uid'.",
    description="""This request is only valid if the term
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically to 'Approved version'.
* The 'version' property will be increased automatically to the next major version.
    """,
    response_model=models.CTTermName,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The term is not in draft status.\n"
            "- The library does not allow to approve term.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The term with the specified 'term_uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def approve(term_uid: str = CTTermUID):
    ct_term_name_service = CTTermNameService()
    return ct_term_name_service.approve(term_uid=term_uid)


@router.delete(
    "/terms/{term_uid}/names/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Inactivates/deactivates the term identified by 'term_uid'.",
    description="""This request is only valid if the term
* is in 'Final' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Retired'.
* The 'change_description' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=models.CTTermName,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The term is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The term with the specified 'term_uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def inactivate(term_uid: str = CTTermUID):
    ct_term_name_service = CTTermNameService()
    return ct_term_name_service.inactivate_final(term_uid=term_uid)


@router.post(
    "/terms/{term_uid}/names/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivates the term identified by 'term_uid'.",
    description="""This request is only valid if the term
* is in 'Retired' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=models.CTTermName,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The term is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The term with the specified 'term_uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def reactivate(term_uid: str = CTTermUID):
    ct_term_name_service = CTTermNameService()
    return ct_term_name_service.reactivate_retired(term_uid=term_uid)


@router.delete(
    "/terms/{term_uid}/names",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Deletes the term identified by 'term_uid'.",
    description="""This request is only valid if \n
* the term is in 'Draft' status and
* the term has never been in 'Final' status and
* the term belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).""",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The term was successfully deleted."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The term is not in draft status.\n"
            "- The term was already in final state or is in use.\n"
            "- The library does not allow to delete term.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An term with the specified 'term_uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def delete_ct_term(term_uid: str = CTTermUID):
    ct_term_name_service = CTTermNameService()
    ct_term_name_service.soft_delete(term_uid=term_uid)
    return Response(status_code=fast_api_status.HTTP_204_NO_CONTENT)
