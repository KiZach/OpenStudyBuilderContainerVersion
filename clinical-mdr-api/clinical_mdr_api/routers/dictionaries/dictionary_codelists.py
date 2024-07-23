"""DictionaryCodelist router."""
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
from clinical_mdr_api.services.dictionaries.dictionary_codelist_generic_service import (
    DictionaryCodelistGenericService,
)

# Prefixed with "/dictionaries"
router = APIRouter()

DictionaryCodelistUID = Path(
    None, description="The unique id of the DictionaryCodelist"
)
DictionaryCodelistLibrary = Query(
    ...,
    description="The Library from which the dictionaries codelists should be retrieved",
)
TermUID = Path(None, description="The unique id of the Codelist Term")


@router.get(
    "/codelists",
    dependencies=[rbac.LIBRARY_READ],
    summary="List all dictionary codelists.",
    description=f"""
State before:
 - The library must exist.
 
Business logic:
 - List all dictionary codelists (in their latest versions).
 
State after:
 - No change

Possible errors:
 - Invalid library name.

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=CustomPage[models.DictionaryCodelist],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "dictionary_id",
            "name",
            "name_sentence_case",
            "abbreviation",
            "definition",
            "start_date",
            "status",
            "version",
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
    library: str = DictionaryCodelistLibrary,
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
    dictionary_codelist_service = DictionaryCodelistGenericService()
    results = dictionary_codelist_service.get_all_dictionary_codelists(
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
    "/codelists/headers",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns possibles values from the database for a given header",
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
    library: str = DictionaryCodelistLibrary,
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
    dictionary_codelist_service = DictionaryCodelistGenericService()
    return dictionary_codelist_service.get_distinct_values_for_header(
        library=library,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.post(
    "/codelists",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates new dictionary codelist.",
    description="""The following nodes are created
  * DictionaryCodelistRoot
  * DictionaryCodelistValue
""",
    response_model=models.DictionaryCodelist,
    status_code=201,
    responses={
        201: {
            "description": "Created - The dictionary codelist was successfully created."
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
    dictionary_codelist_input: models.DictionaryCodelistCreateInput = Body(
        description="Properties to create DictionaryCodelistValue node."
    ),
):
    dictionary_codelist_service = DictionaryCodelistGenericService()
    return dictionary_codelist_service.create(dictionary_codelist_input)


@router.get(
    "/codelists/{uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="List details on the dictionary codelist with {uid}",
    description="""
State before:
 - The selected codelist must exist.
 
Business logic:
 - List details of the selected codelist (in a given version, if specified)

State after:
 - No change""",
    response_model=models.DictionaryCodelist,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_codelist(
    uid: str = DictionaryCodelistUID,
    version: str
    | None = Query(
        None,
        description="If specified then the latest/newest representation of the dictionary codelist "
        "for DictionaryCodelistValue in that version is returned.\n"
        "Only exact matches are considered. The version is specified in the following format:"
        "<major>.<minor> where <major> and <minor> are digits. E.g. '0.1', '0.2', '1.0',",
    ),
):
    dictionary_codelist_service = DictionaryCodelistGenericService()
    return dictionary_codelist_service.get_by_uid(codelist_uid=uid, version=version)


@router.get(
    "/codelists/{uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="List version history for a dictionary codelist",
    description="""
State before:
 - codelist_uid must exist.
 
Business logic:
 - List version history for the representation of the dictionary codelist, including the use as template parameter.
 - The returned versions are ordered by start_date descending (newest entries first).
 
State after:
 - No change
 
Possible errors:
 - Invalid codelist_uid.
    """,
    response_model=list[models.DictionaryCodelistVersion],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The dictionary codelist with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_versions(
    uid: str = DictionaryCodelistUID,
):
    dictionary_codelist_service = DictionaryCodelistGenericService()
    return dictionary_codelist_service.get_version_history(codelist_uid=uid)


@router.patch(
    "/codelists/{uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Update name or template parameter flag for dictionary codelist",
    description="""
State before:
 - codelist_uid must exist and the dictionary codelist must exist in status draft.
 
Business logic:
 - If the dictionary codelist related to codelist_uid exist in status draft then name attribute and Template Parameter node label are updated.
 - If Template Parameter have been set to 'Y' then it cannot be set back to 'N' (i.e. when the Template Parameter node label have been added it cannot be removed).
 
State after:
 - name attribute and Template Parameter node label are updated for the dictionary codelist.
 - Audit trail entry must be made with update of name attribute or Template Parameter flag.
 
Possible errors:
 - Invalid codelist_uid.
""",
    response_model=models.DictionaryCodelist,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The dictionary codelist is not in draft status.\n"
            "- The dictionary codelist had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The codelist with the specified 'codelist_uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def edit(
    uid: str = DictionaryCodelistUID,
    dictionary_codelist_input: models.DictionaryCodelistEditInput = Body(
        description="The new parameter terms for the dictionary codelist including the change description.",
    ),
):
    dictionary_codelist_service = DictionaryCodelistGenericService()
    return dictionary_codelist_service.edit_draft(
        codelist_uid=uid, codelist_input=dictionary_codelist_input
    )


@router.post(
    "/codelists/{uid}/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Create a new version of the dictionary codelist",
    description="""
State before:
 - codelist_uid must exist and the dictionary codelist must be in status Final.
 
Business logic:
 - The latest 'Final' version will remain the same as before.
 - The status of the new created version will be automatically set to 'Draft'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' or 'Retired' version increased by +0.1.
 - The 'change_description' property will be set automatically to 'New version'.
 
State after:
 - Dictionary codelist changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating new Draft version.
 
Possible errors:
 - Invalid codelist_uid or status not Final.
 
""",
    response_model=models.DictionaryCodelist,
    status_code=201,
    responses={
        201: {
            "description": "Created - The dictionary codelist was successfully created."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not allow to create codelists.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The dictionary codelist is not in final status.\n"
            "- The dictionary codelist with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def create_new_version(
    uid: str = DictionaryCodelistUID,
):
    dictionary_codelist_service = DictionaryCodelistGenericService()
    return dictionary_codelist_service.create_new_version(codelist_uid=uid)


@router.post(
    "/codelists/{uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approve draft version of the dictionary codelist",
    description="""
State before:
 - codelist_uid must exist and the dictionary codelist must be in status Draft.
 
Business logic:
 - The latest 'Draft' version will remain the same as before.
 - The status of the new approved version will be automatically set to 'Final'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' version increased by +1.0.
 - The 'change_description' property will be set automatically 'Approved version'.
 
State after:
 - Dictionary codelist changed status to Final and assigned a new major version number.
 - Audit trail entry must be made with action of approving to new Final version.
 
Possible errors:
 - Invalid codelist_uid or status not Draft.
    """,
    response_model=models.DictionaryCodelist,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The codelist is not in draft status.\n"
            "- The library does not allow to approve codelist.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The codelist with the specified 'codelist_uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def approve(
    uid: str = DictionaryCodelistUID,
):
    dictionary_codelist_service = DictionaryCodelistGenericService()
    return dictionary_codelist_service.approve(codelist_uid=uid)


@router.post(
    "/codelists/{uid}/terms",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Attaches a dictionary term to a dictionary codelist",
    description="""
State before:
 - Codelist identified by uid must exist.

Business logic:
 - Create a HAS_TERM relationship between the selected codelist root and the selected term root, with the current date and current user.

Possible errors:
 - Invalid codelist_uid.
-  Invalid term_uid.
-  Codelist with {uid} is not extensible.
- Term is already part of the specified codelist.""",
    response_model=models.DictionaryCodelist,
    status_code=201,
    responses={
        201: {
            "description": "The HAS_TERM relationship was successfully created.\n"
            "The TemplateParameter labels and HAS_PARAMETER_TERM relationship were successfully added "
            "if dictionary codelist identified by 'uid' is a TemplateParameter."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The dictionary codelist does not exist.\n"
            "- The dictionary term does not exist.\n"
            "- The dictionary codelist already has passed term.\n",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def add_term(
    uid: str = DictionaryCodelistUID,
    term_input: models.DictionaryCodelistTermInput = Body(
        description="UID of the DictionaryTermRoot node."
    ),
):
    dictionary_codelist_service = DictionaryCodelistGenericService()
    return dictionary_codelist_service.add_term(
        codelist_uid=uid, term_uid=term_input.term_uid
    )


@router.delete(
    "/codelists/{codelist_uid}/terms/{term_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Removes a dictionary term from a dictionary codelist",
    description="""
State before:
 - Codelist identified by codelist_uid must exist.
 - Term identified by term_uid must exist.
 - Codelist contains the term that is being removed.


Business logic:
 - Create a HAD_TERM relationship between the selected codelist root and the selected term root, with the current date as the end date, and current user.
 - Remove the old HAS_TERM relationship between the codelist and the term.

Possible errors:
 - Invalid codelist_uid.
 - Invalid term_uid.
- Term is not part of the specified codelist. """,
    response_model=models.DictionaryCodelist,
    status_code=201,
    responses={
        201: {
            "description": "The HAS_TERM relationship was successfully deleted and "
            "HAD_TERM relationship was successfully created.\n"
            "The HAS_PARAMETER_TERM relationship was successfully deleted if codelist identified by "
            "uid is a TemplateParameter"
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The codelist does not exist.\n"
            "- The term does not exist.\n"
            "- The codelist doesn't have passed term.\n",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def remove_term(
    codelist_uid: str = DictionaryCodelistUID,
    term_uid: str = TermUID,
):
    dictionary_codelist_service = DictionaryCodelistGenericService()
    return dictionary_codelist_service.remove_term(
        codelist_uid=codelist_uid, term_uid=term_uid
    )
