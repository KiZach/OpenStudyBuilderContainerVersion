from typing import Any

from fastapi import APIRouter, Body, Path, Query, Request, Response
from fastapi import status as fast_api_status
from pydantic.types import Json

from clinical_mdr_api import config, models
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.syntax_pre_instances.footnote_pre_instances import (
    FootnotePreInstanceService,
)

FootnotePreInstanceUID = Path(
    None, description="The unique id of the Footnote Pre-Instance."
)

# Prefixed with /footnote-pre-instances
router = APIRouter()

Service = FootnotePreInstanceService


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all Syntax Pre-Instances in their latest/newest version.",
    description="Allowed parameters include : filter on fields, sort by field name with sort direction, pagination",
    response_model=CustomPage[models.FootnotePreInstance],
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "library=library.name",
            "uid",
            "sequence_id",
            "footnote_template=template_name",
            "name",
            "indications",
            "activities",
            "activity_groups",
            "activity_subgroups",
            "start_date",
            "end_date",
            "status",
            "version",
            "change_description",
            "user_initials",
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
def footnote_pre_instances(
    request: Request,  # request is actually required by the allow_exports decorator
    status: LibraryItemStatus
    | None = Query(
        None,
        description="If specified, only those Syntax Pre-Instances will be returned that are currently in the specified status. "
        "This may be particularly useful if the Footnote Pre-Instance has "
        "a 'Draft' and a 'Final' status or and you are interested in the 'Final' status.\n"
        "Valid values are: 'Final' or 'Draft'.",
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
        description=_generic_descriptions.SYNTAX_FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: str | None = Query("and", description=_generic_descriptions.OPERATOR),
    total_count: bool
    | None = Query(False, description=_generic_descriptions.TOTAL_COUNT),
):
    results = FootnotePreInstanceService().get_all(
        status=status,
        return_study_count=True,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
    )

    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/headers",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
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
    status: LibraryItemStatus
    | None = Query(
        None,
        description="If specified, only those Syntax Pre-Instances will be returned that are currently in the specified status. "
        "This may be particularly useful if the Footnote Pre-Instance has "
        "a 'Draft' and a 'Final' status or and you are interested in the 'Final' status.\n"
        "Valid values are: 'Final' or 'Draft'.",
    ),
    field_name: str = Query(..., description=_generic_descriptions.HEADER_FIELD_NAME),
    search_string: str
    | None = Query("", description=_generic_descriptions.HEADER_SEARCH_STRING),
    filters: Json
    | None = Query(
        None,
        description=_generic_descriptions.SYNTAX_FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: str | None = Query("and", description=_generic_descriptions.OPERATOR),
    result_count: int
    | None = Query(10, description=_generic_descriptions.HEADER_RESULT_COUNT),
):
    return Service().get_distinct_values_for_header(
        status=status,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.get(
    "/audit-trail",
    dependencies=[rbac.LIBRARY_READ],
    summary="",
    description="",
    response_model=CustomPage[models.FootnotePreInstance],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def retrieve_audit_trail(
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
    results = Service().get_all(
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        for_audit_trail=True,
    )

    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/{uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the latest/newest version of a specific footnote pre-instance identified by 'uid'.",
    description="""If multiple request query parameters are used, then they need to
    match all at the same time (they are combined with the AND operation).""",
    response_model=models.FootnotePreInstance | None,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote pre-instance with the specified 'uid' (and the specified date/time and/or status) wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get(
    uid: str = FootnotePreInstanceUID,
):
    return FootnotePreInstanceService().get_by_uid(uid=uid)


@router.patch(
    "/{uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Updates the Footnote Pre-Instance identified by 'uid'.",
    description="""This request is only valid if the Footnote Pre-Instance
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true). 

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.
* The link to the footnote will remain as is.
""",
    response_model=models.FootnotePreInstance,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The Footnote Pre-Instance is not in draft status.\n"
            "- The Footnote Pre-Instance had been in 'Final' status before.\n"
            "- The provided list of parameters is invalid.\n"
            "- The library does not allow to edit draft versions.\n"
            "- The Footnote Pre-Instance does already exist.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The Footnote Pre-Instance with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def edit(
    uid: str = FootnotePreInstanceUID,
    footnote_pre_instance: models.FootnotePreInstanceEditInput = Body(
        None,
        description="The new parameter terms for the Footnote Pre-Instance, its indexings and the change description.",
    ),
):
    return Service().edit_draft(uid=uid, template=footnote_pre_instance)


@router.patch(
    "/{uid}/indexings",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Updates the indexings of the Footnote Pre-Instance identified by 'uid'.",
    description="""This request is only valid if the Pre-Instance
    * belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).
    
    This is version independent : it won't trigger a status or a version change.
    """,
    response_model=models.FootnotePreInstance,
    status_code=200,
    responses={
        200: {
            "description": "No content - The indexings for this Pre-Instance were successfully updated."
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The Pre-Instance with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_indexings(
    uid: str = FootnotePreInstanceUID,
    indexings: models.FootnotePreInstanceIndexingsInput = Body(
        None,
        description="The lists of UIDs for the new indexings to be set, grouped by indexings to be updated.",
    ),
) -> models.FootnotePreInstance:
    return Service().patch_indexings(uid=uid, indexings=indexings)


@router.get(
    "/{uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the version history of a specific Footnote Pre-Instance identified by 'uid'.",
    description=f"""
The returned versions are ordered by `start_date` descending (newest entries first).

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=list[models.FootnotePreInstanceVersion],
    status_code=200,
    responses={
        200: {"description": "OK."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The Footnote Pre-Instance with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
@decorators.allow_exports(
    {
        "text/csv": [
            "library=library.name",
            "footnote_template=footnote_template.uid",
            "uid",
            "name_plain",
            "name",
            "start_date",
            "end_date",
            "status",
            "version",
            "change_description",
            "user_initials",
        ],
        "text/xml": [
            "library=library.name",
            "footnote_template=footnote_template.name",
            "footnote=footnote.name",
            "uid",
            "name_plain",
            "name",
            "start_date",
            "end_date",
            "status",
            "version",
            "change_description",
            "user_initials",
        ],
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
            "library=library.name",
            "footnote_template=footnote_template.uid",
            "uid",
            "name_plain",
            "name",
            "start_date",
            "end_date",
            "status",
            "version",
            "change_description",
            "user_initials",
        ],
    }
)
# pylint: disable=unused-argument
def get_versions(
    request: Request,  # request is actually required by the allow_exports decorator
    uid: str = FootnotePreInstanceUID,
):
    return Service().get_version_history(uid)


@router.post(
    "/{uid}/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates a new version of the Footnote Pre-Instance identified by 'uid'.",
    description="""This request is only valid if the Footnote Pre-Instance
* is in 'Final' or 'Retired' status only (so no latest 'Draft' status exists) and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The latest 'Final' or 'Retired' version will remain the same as before.
* The status of the new version will be automatically set to 'Draft'.
* The 'version' property of the new version will be automatically set to the version of the latest 'Final' or 'Retired' version increased by +0.1.

Parameters in the 'name' property cannot be changed with this request.
Only the surrounding text (excluding the parameters) can be changed.
""",
    response_model=models.FootnotePreInstance,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The Footnote Pre-Instance is not in final or retired status or has a draft status.\n"
            "- The Footnote Pre-Instance name is not valid.\n"
            "- The library does not allow to create a new version.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The Footnote Pre-Instance with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_new_version(
    uid: str = FootnotePreInstanceUID,
):
    return Service().create_new_version(uid=uid)


@router.delete(
    "/{uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Inactivates/deactivates the footnote pre-instance identified by 'uid'.",
    description="""This request is only valid if the footnote pre-instance
* is in 'Final' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Retired'.
* The 'change_description' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=models.FootnotePreInstance,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The footnote pre-instance is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote pre-instance with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def inactivate(
    uid: str = FootnotePreInstanceUID,
):
    return FootnotePreInstanceService().inactivate_final(uid)


@router.post(
    "/{uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivates the footnote pre-instance identified by 'uid'.",
    description="""This request is only valid if the footnote pre-instance
* is in 'Retired' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=models.FootnotePreInstance,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The footnote pre-instance is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote pre-instance with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def reactivate(
    uid: str = FootnotePreInstanceUID,
):
    return FootnotePreInstanceService().reactivate_retired(uid)


@router.delete(
    "/{uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Deletes the Footnote Pre-Instance identified by 'uid'.",
    description="""This request is only valid if \n
* the Footnote Pre-Instance is in 'Draft' status and
* the Footnote Pre-Instance has never been in 'Final' status and
* the Footnote Pre-Instance belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).""",
    response_model=None,
    status_code=204,
    responses={
        204: {
            "description": "No Content - The Footnote Pre-Instance was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The Footnote Pre-Instance is not in draft status.\n"
            "- The Footnote Pre-Instance was already in final state or is in use.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - A Footnote Pre-Instance with the specified uid could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete(
    uid: str = FootnotePreInstanceUID,
):
    Service().soft_delete(uid)
    return Response(status_code=fast_api_status.HTTP_204_NO_CONTENT)


@router.post(
    "/{uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approves the Footnote Pre-Instance identified by 'uid'.",
    description="""This request is only valid if the Footnote Pre-Instance
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically.
* The 'version' property will be increased automatically to the next major version.
    """,
    response_model=models.FootnotePreInstance,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The Footnote Pre-Instance is not in draft status.\n"
            "- The library does not allow to approve Footnote Pre-Instances.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The Footnote Pre-Instance with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def approve(
    uid: str = FootnotePreInstanceUID,
):
    return Service().approve(uid)
