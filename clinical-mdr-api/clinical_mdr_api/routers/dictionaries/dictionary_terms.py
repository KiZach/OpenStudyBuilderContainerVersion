"""DictionaryTerms router."""
from typing import Any

from fastapi import APIRouter, Body, Path, Query, Response, status
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api import config, models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.dictionaries.dictionary_term_generic_service import (
    DictionaryTermGenericService,
)
from clinical_mdr_api.services.dictionaries.dictionary_term_substance_service import (
    DictionaryTermSubstanceService,
)

# Prefixed with "/dictionaries"
router = APIRouter()

DictionaryTermUID = Path(None, description="The unique id of the DictionaryTerm")


@router.get(
    "/terms",
    dependencies=[rbac.LIBRARY_READ],
    summary="List terms in the dictionary codelist.",
    description=f"""
Business logic:
 - List dictionary terms in the repository for the dictionary codelist (being a subset of terms)
 - The term uid property is the dictionary concept_id.
 
State after:
 - No change
 
Possible errors:
 - Invalid codelist_uid

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=CustomPage[models.DictionaryTerm],
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
            "abbreviation",
            "definition",
            "dictionary_id",
            "end_date",
            "name",
            "name_sentence_case",
            "start_date",
            "status",
            "term_uid",
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
def get_terms(
    request: Request,  # request is actually required by the allow_exports decorator
    codelist_uid: str = Query(
        ..., description="The unique id of the DictionaryCodelist"
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
    dictionary_term_service = DictionaryTermGenericService()
    results = dictionary_term_service.get_all_dictionary_terms(
        codelist_uid=codelist_uid,
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
    "/terms/headers",
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
    codelist_uid: str = Query(
        ..., description="The unique id of the DictionaryCodelist"
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
    dictionary_term_service = DictionaryTermGenericService()
    return dictionary_term_service.get_distinct_values_for_header(
        codelist_uid=codelist_uid,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.post(
    "/terms",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates new dictionary term.",
    description="""The following nodes are created
  * DictionaryTermRoot
  * DictionaryTermValue
""",
    response_model=models.DictionaryTerm,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        201: {"description": "Created - The dictionary term was successfully created."},
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
    dictionary_term_input: models.DictionaryTermCreateInput = Body(
        description="Properties to create DictionaryTermValue node."
    ),
):
    dictionary_term_service = DictionaryTermGenericService()
    return dictionary_term_service.create(dictionary_term_input)


@router.get(
    "/terms/{uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="List details on the specific dictionary term",
    description="""
State before:
 -
 
Business logic:
 - List details on a specific dictionary term.
 
State after:
 - No change
 
Possible errors:
 - Invalid codelist""",
    response_model=models.DictionaryTerm,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_codelists(uid: str = DictionaryTermUID):
    dictionary_term_service = DictionaryTermGenericService()
    return dictionary_term_service.get_by_uid(term_uid=uid)


@router.get(
    "/terms/{uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="List version history for a specific dictionary term",
    description="""
State before:
 - uid must exist.
 
Business logic:
 - List version history for a dictionary term.
 - The returned versions are ordered by start_date descending (newest entries first).
 
State after:
 - No change
 
Possible errors:
 - Invalid uid.
    """,
    response_model=list[models.DictionaryTermVersion],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The dictionary term with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_versions(uid: str = DictionaryTermUID):
    dictionary_term_service = DictionaryTermGenericService()
    return dictionary_term_service.get_version_history(term_uid=uid)


@router.patch(
    "/terms/{uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Update a dictionary term",
    description="""
State before:
 - uid must exist and dictionary term must exist in status draft.
 
Business logic:
 - For SNOMED: Updates can only be imported from the SNOMED files, webservice or from legacy migration.
 - It should not be possible to update from the study builder app, this we can do with access permissions later.
 - The existing dictionary term is updated.
 - The individual values for name and uid must all be unique values within the dictionary codelist.
 - The status of the updated version will continue to be 'Draft'.
 - The 'version' property of the version will automatically be incremented with +0.1.
 - The 'change_description' property is required.
 
State after:
 - Attribute are updated for the dictionary term.
 - Audit trail entry must be made with update of attributes.
 
Possible errors:
 - Invalid uid.
""",
    response_model=models.DictionaryTerm,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The dictionary term is not in draft status.\n"
            "- The dictionary term had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The term with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def edit(
    uid: str = DictionaryTermUID,
    dictionary_term_input: models.DictionaryTermEditInput = Body(
        description="The new parameter terms for the dictionary term including the change description.",
    ),
):
    dictionary_term_service = DictionaryTermGenericService()
    return dictionary_term_service.edit_draft(
        term_uid=uid, term_input=dictionary_term_input
    )


@router.post(
    "/terms/{uid}/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Create a new version of a dictionary term",
    description="""
State before:
 - uid must exist and the dictionary term must be in status Final.
 
Business logic:
 - The latest 'Final' version will remain the same as before.
 - The status of the new created version will be automatically set to 'Draft'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' or 'Retired' version increased by +0.1.
 - The 'change_description' property will be set automatically to 'New version'.
 
State after:
 - Dictionary term changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating new Draft version.
 
Possible errors:
 - Invalid uid or status not Final.
""",
    response_model=models.DictionaryTerm,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not allow to create terms.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The dictionary term is not in final status.\n"
            "- The dictionary term with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def create_new_version(uid: str = DictionaryTermUID):
    dictionary_term_service = DictionaryTermGenericService()
    return dictionary_term_service.create_new_version(term_uid=uid)


@router.post(
    "/terms/{uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approve draft version of the dictionary term",
    description="""
State before:
 - uid must exist and the dictionary term must be in status Draft.
 
Business logic:
 - The latest 'Draft' version will remain the same as before.
 - The status of the new approved version will be automatically set to 'Final'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' version increased by +1.0.
 - The 'change_description' property will be set automatically 'Approved version'.
 
State after:
 - dictionary term changed status to Final and assigned a new major version number.
 - Audit trail entry must be made with action of approving to new Final version.
 
Possible errors:
 - Invalid uid or status not Draft.
    """,
    response_model=models.DictionaryTerm,
    response_model_exclude_unset=True,
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
            "description": "Not Found - The term with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def approve(uid: str = DictionaryTermUID):
    dictionary_term_service = DictionaryTermGenericService()
    return dictionary_term_service.approve(term_uid=uid)


@router.delete(
    "/terms/{uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of a dictionary term",
    description="""
State before:
 - uid must exist and the dictionary term must be in status Final.
 
Business logic:
 - The latest 'Final' version will remain the same as before.
 - The status will be automatically set to 'Retired'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.
 
State after:
 - dictionary term changed status to Retired.
 - Audit trail entry must be made with action of inactivating to retired version.
 
Possible errors:
 - Invalid uid or status not Final.
    """,
    response_model=models.DictionaryTerm,
    response_model_exclude_unset=True,
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
            "description": "Not Found - The term with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def inactivate(uid: str = DictionaryTermUID):
    dictionary_term_service = DictionaryTermGenericService()
    return dictionary_term_service.inactivate_final(term_uid=uid)


@router.post(
    "/terms/{uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of a dictionary term",
    description="""
State before:
 - uid must exist and dictionary term must be in status Retired.
 
Business logic:
 - The latest 'Retired' version will remain the same as before.
 - The status will be automatically set to 'Final'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - Dictionary term changed status to Final.
 - Audit trail entry must be made with action of reactivating to final version.
 
Possible errors:
 - Invalid uid or status not Retired.
    """,
    response_model=models.DictionaryTerm,
    response_model_exclude_unset=True,
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
            "description": "Not Found - The term with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def reactivate(uid: str = DictionaryTermUID):
    dictionary_term_service = DictionaryTermGenericService()
    return dictionary_term_service.reactivate_retired(term_uid=uid)


@router.delete(
    "/terms/{uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Delete draft version of a dictionary term",
    description="""
State before:
 - uid must exist
 - Dictionary term must be in status Draft in a version less then 1.0 (never been approved).
 
Business logic:
 - The draft dictionary term is deleted
 
State after:
 - Dictionary term is successfully deleted.
 
Possible errors:
 - Invalid uid or status not Draft or exist in version 1.0 or above (previoulsy been approved) or not in an editable library.
    """,
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
            "description": "Not Found - An term with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def delete_ct_term(uid: str = DictionaryTermUID):
    dictionary_term_service = DictionaryTermGenericService()
    dictionary_term_service.soft_delete(term_uid=uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/substances",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates new substance dictionary term.",
    description="""The following nodes are created
  * DictionaryTermRoot/UNIITermRoot
  * DictionaryTermValue/UNIITermValue
""",
    response_model=models.DictionaryTermSubstance,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        201: {"description": "Created - The dictionary term was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not exist.\n"
            "- The library does not allow to add new items.\n",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def create_substance(
    dictionary_term_input: models.DictionaryTermSubstanceCreateInput = Body(
        description="Properties to create DictionaryTermValue node."
    ),
):
    dictionary_term_service = DictionaryTermSubstanceService()
    return dictionary_term_service.create(dictionary_term_input)


@router.get(
    "/substances/{uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Details of the specific substance dictionary term",
    description="""
State before:
 -
 
Business logic:
 - Returns details of the specific substance dictionary term.
 
State after:
 - No change
 
Possible errors:
 - Invalid uid""",
    response_model=models.DictionaryTermSubstance,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_substance_by_id(uid: str = DictionaryTermUID):
    dictionary_term_service = DictionaryTermSubstanceService()
    return dictionary_term_service.get_by_uid(term_uid=uid)


@router.get(
    "/substances",
    dependencies=[rbac.LIBRARY_READ],
    summary="List terms in the substances dictionary codelist.",
    description="""
Business logic:
 - List dictionary terms in the repository for the dictionary codelist for substances
 
State after:
 - No change
 
Possible errors:
 - """,
    response_model=CustomPage[models.DictionaryTermSubstance],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_substances(
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
    dictionary_term_service = DictionaryTermSubstanceService()
    results = dictionary_term_service.get_all_dictionary_terms(
        codelist_name=config.LIBRARY_SUBSTANCES_CODELIST_NAME,
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


@router.patch(
    "/substances/{uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Update a substance dictionary term",
    description="""
State before:
 - uid must exist and dictionary term must exist in status draft.
 
Business logic:
 - The existing dictionary term is updated.
 - The individual values for name and uid must all be unique values within the dictionary codelist.
 - The status of the updated version will continue to be 'Draft'.
 - The 'version' property of the version will automatically be incremented with +0.1.
 - The 'change_description' property is required.
 
State after:
 - Attribute are updated for the dictionary term.
 - Audit trail entry must be made with update of attributes.
 
Possible errors:
 - Invalid uid.
""",
    response_model=models.DictionaryTermSubstance,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The dictionary term is not in draft status.\n"
            "- The dictionary term had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The term with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def edit_substance(
    uid: str = DictionaryTermUID,
    dictionary_term_input: models.DictionaryTermSubstanceEditInput = Body(
        description="The new parameter terms for the dictionary term including the change description.",
    ),
):
    dictionary_term_service = DictionaryTermSubstanceService()
    return dictionary_term_service.edit_draft(
        term_uid=uid, term_input=dictionary_term_input
    )
