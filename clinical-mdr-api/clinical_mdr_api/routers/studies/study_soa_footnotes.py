from typing import Any

from fastapi import Body, Query, Response, status
from pydantic import Json

from clinical_mdr_api import config
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.study_selections.study_soa_footnote import (
    StudySoAFootnote,
    StudySoAFootnoteCreateFootnoteInput,
    StudySoAFootnoteCreateInput,
    StudySoAFootnoteEditInput,
    StudySoAFootnoteVersion,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers import study_router as router
from clinical_mdr_api.routers.studies import utils
from clinical_mdr_api.services.studies.study_soa_footnote import StudySoAFootnoteService


@router.get(
    "/study-soa-footnotes",
    dependencies=[rbac.STUDY_READ],
    summary="List all study soa footnotes defined for all studies",
    response_model=CustomPage[StudySoAFootnote],
    status_code=200,
    responses={
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_study_soa_footnotes_from_all_studies(
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
) -> CustomPage[StudySoAFootnote]:
    service = StudySoAFootnoteService()
    all_footnotes = service.get_all(
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
    )
    return CustomPage.create(
        items=all_footnotes.items,
        total=all_footnotes.total,
        page=page_number,
        size=page_size,
    )


@router.get(
    "/studies/{uid}/study-soa-footnotes",
    dependencies=[rbac.STUDY_READ],
    summary="List all study soa footnotes currently defined for the study",
    response_model=CustomPage[StudySoAFootnote],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there is no study with the given uid.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_study_soa_footnotes(
    uid: str = utils.studyUID,
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
) -> CustomPage[StudySoAFootnote]:
    service = StudySoAFootnoteService()
    all_footnotes = service.get_all_by_study_uid(
        study_uid=uid,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
        study_value_version=study_value_version,
    )
    return CustomPage.create(
        items=all_footnotes.items,
        total=all_footnotes.total,
        page=page_number,
        size=page_size,
    )


@router.get(
    "/studies/{uid}/study-soa-footnotes/headers",
    dependencies=[rbac.STUDY_READ],
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
    uid: str = utils.studyUID,
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
    service = StudySoAFootnoteService()
    return service.get_distinct_values_for_header(
        study_uid=uid,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
        study_value_version=study_value_version,
    )


@router.get(
    "/study-soa-footnotes/headers",
    dependencies=[rbac.STUDY_READ],
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
def get_distinct_values_for_header_top_level(
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
    service = StudySoAFootnoteService()
    return service.get_distinct_values_for_header(
        study_uid=None,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.get(
    "/studies/{uid}/study-soa-footnotes/{study_soa_footnote_uid}",
    dependencies=[rbac.STUDY_READ],
    summary="List a specific study soa footnote defined for a study",
    response_model=StudySoAFootnote,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there is no study with the given uid or the study soa footnote doesn't exist",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_study_soa_footnote(
    # pylint: disable=unused-argument
    uid: str = utils.studyUID,
    study_soa_footnote_uid: str = utils.study_soa_footnote_uid,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> StudySoAFootnote:
    service = StudySoAFootnoteService()
    return service.get_by_uid(
        uid=study_soa_footnote_uid, study_value_version=study_value_version
    )


@router.post(
    "/studies/{uid}/study-soa-footnotes",
    dependencies=[rbac.STUDY_WRITE],
    summary="Add a study soa footnote to a study",
    response_model=StudySoAFootnote,
    status_code=201,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study, footnote or SoA item is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def post_new_soa_footnote(
    uid: str = utils.studyUID,
    soa_footnote_input: StudySoAFootnoteCreateFootnoteInput
    | StudySoAFootnoteCreateInput = Body(
        description="Related parameters of the schedule that shall be created."
    ),
    create_footnote: bool = Query(
        False,
        description="Indicates whether the specified footnote should be created in the library.\n"
        "- If this parameter is set to `true`, a `StudySoAFootnoteCreateFootnoteInput` payload needs to be sent.\n"
        "- Otherwise, `StudySoAFootnoteCreateInput` payload should be sent, referencing an existing library footnote by uid.",
    ),
) -> StudySoAFootnote:
    service = StudySoAFootnoteService()
    return service.create(
        study_uid=uid,
        footnote_input=soa_footnote_input,
        create_footnote=create_footnote,
    )


@router.post(
    "/studies/{uid}/study-soa-footnotes/batch-select",
    dependencies=[rbac.STUDY_WRITE],
    summary="Batch create Study SoA footnotes to a given Study",
    response_model=list[StudySoAFootnote],
    status_code=201,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study, footnote or SoA item is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def post_new_soa_footnotes_batch_select(
    uid: str = utils.studyUID,
    soa_footnote_input: list[StudySoAFootnoteCreateFootnoteInput] = Body(
        description="Related parameters of the footnote that shall be created."
    ),
) -> StudySoAFootnote:
    service = StudySoAFootnoteService()
    return service.batch_create(study_uid=uid, footnote_input=soa_footnote_input)


@router.patch(
    "/studies/{uid}/study-soa-footnotes/{study_soa_footnote_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Edit a study soa footnote",
    response_model=StudySoAFootnote,
    status_code=200,
    responses={
        200: {
            "description": "No Content - The study soa footnote was successfully edited."
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - the study soa footnote doesn't exist.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def edit_study_soa_footnote(
    uid: str = utils.studyUID,
    study_soa_footnote_uid: str = utils.study_soa_footnote_uid,
    soa_footnote_edit_input: StudySoAFootnoteEditInput = Body(
        description="Related parameters of the schedule that shall be edited."
    ),
):
    service = StudySoAFootnoteService()
    return service.edit(
        study_uid=uid,
        study_soa_footnote_uid=study_soa_footnote_uid,
        footnote_edit_input=soa_footnote_edit_input,
    )


@router.delete(
    "/studies/{uid}/study-soa-footnotes/{study_soa_footnote_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Delete a study soa footnote",
    response_model=None,
    status_code=204,
    responses={
        204: {
            "description": "No Content - The study soa footnote was successfully deleted."
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - the study soa footnote doesn't exist.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def delete_study_soa_footnote(
    uid: str = utils.studyUID,
    study_soa_footnote_uid: str = utils.study_soa_footnote_uid,
):
    service = StudySoAFootnoteService()
    service.delete(study_uid=uid, study_soa_footnote_uid=study_soa_footnote_uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/studies/{uid}/study-soa-footnotes/preview",
    dependencies=[rbac.STUDY_WRITE],
    summary="Preview creating a study soa footnote selection based on the input data",
    response_model=StudySoAFootnote,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a study soa footnote",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or soa footnote is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def preview_new_soa_footnote(
    uid: str = utils.studyUID,
    footnote_input: StudySoAFootnoteCreateFootnoteInput = Body(
        description="Related parameters of the selection that shall be previewed."
    ),
) -> StudySoAFootnote:
    service = StudySoAFootnoteService()
    return service.preview_soa_footnote(
        study_uid=uid, footnote_create_input=footnote_input
    )


@router.get(
    "/studies/{uid}/study-soa-footnotes/{study_soa_footnote_uid}/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List full audit trail related to definition of all study soa footnotes.",
    description="""
The following values should be returned for all study soa footnotes:
- date_time
- user_initials
- action
- activity
- order
    """,
    response_model=list[StudySoAFootnoteVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_specific_soa_footnotes_audit_trail(
    uid: str = utils.studyUID,
    study_soa_footnote_uid: str = utils.study_soa_footnote_uid,
) -> list[StudySoAFootnoteVersion]:
    service = StudySoAFootnoteService()
    return service.audit_trail_specific_soa_footnote(
        study_uid=uid, study_soa_footnote_uid=study_soa_footnote_uid
    )


@router.get(
    "/studies/{uid}/study-soa-footnote/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List full audit trail related to definition of all study soa footnotes within a specific study",
    description="""
The following values should be returned for all study soa footnotes:
- date_time
- user_initials
- action
- activity
- order
    """,
    response_model=list[StudySoAFootnoteVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_soa_footnotes_audit_trail(
    uid: str = utils.studyUID,
) -> list[StudySoAFootnoteVersion]:
    service = StudySoAFootnoteService()
    return service.audit_trail_all_soa_footnotes(study_uid=uid)


@router.post(
    "/studies/{uid}/study-soa-footnotes/{study_soa_footnote_uid}/accept-version",
    dependencies=[rbac.STUDY_WRITE],
    summary="accept StudySoAFootnote selection's footnote version",
    description="""
    State before:
     - Study must exist
     - Study SoA Footnote selection must exist
     - Footnote version selected for study footnote selection is not the latest available final version of the footnote.

    Business logic:
     - Update specified footnote study-selection, setting accepted version to show that update was refused by user.

    State after:
     - Study exists
     - Study SoA Footnote selection exists
     - Footnote version selected for study SoA Footnote selection is not changed.
     - Added new entry in the audit trail for the update of the study-soa-footnote.""",
    response_model=StudySoAFootnote,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and study soa footnote",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_footnote_accept_version(
    uid: str = utils.studyUID,
    study_soa_footnote_uid: str = utils.study_soa_footnote_uid,
) -> StudySoAFootnote:
    service = StudySoAFootnoteService()
    return service.edit(
        study_uid=uid,
        study_soa_footnote_uid=study_soa_footnote_uid,
        footnote_edit_input=StudySoAFootnoteEditInput(
            footnote_uid=None, footnote_template_uid=None, referenced_items=None
        ),
        accept_version=True,
    )


@router.post(
    "/studies/{uid}/study-soa-footnotes/{study_soa_footnote_uid}/sync-latest-version",
    dependencies=[rbac.STUDY_WRITE],
    summary="update to latest footnote version study selection",
    description="""
    State before:
     - Study must exist
     - Study SoA Footnote selection must exist
     - Footnote version selected for study footnote selection is not the latest available final version of the footnote.

    Business logic:
     - Update specified footnote study-selection to latest footnote

    State after:
     - Study exists
     - Study SoA Footnote selection exists
     - Footnote version selected for study SoA Footnote selection is not changed.
     - Added new entry in the audit trail for the update of the study-soa-footnote.""",
    response_model=StudySoAFootnote,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and study soa footnote",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_footnote_sync_to_latest_footnote(
    uid: str = utils.studyUID,
    study_soa_footnote_uid: str = utils.study_soa_footnote_uid,
) -> StudySoAFootnote:
    service = StudySoAFootnoteService()
    return service.edit(
        study_uid=uid,
        study_soa_footnote_uid=study_soa_footnote_uid,
        footnote_edit_input=StudySoAFootnoteEditInput(
            footnote_uid=None, footnote_template_uid=None, referenced_items=None
        ),
        sync_latest_version=True,
    )
