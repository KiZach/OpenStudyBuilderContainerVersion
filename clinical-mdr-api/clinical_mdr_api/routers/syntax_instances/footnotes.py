from typing import Any

from fastapi import APIRouter, Path, Query, Request, Response
from fastapi import status as fast_api_status
from fastapi.param_functions import Body
from pydantic.types import Json

from clinical_mdr_api import config, models
from clinical_mdr_api.domain_repositories.models.syntax import FootnoteValue
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyComponentEnum,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers._generic_descriptions import study_section_description
from clinical_mdr_api.services.syntax_instances.footnotes import FootnoteService

# Prefixed with /footnotes
router = APIRouter()

Service = FootnoteService

# Argument definitions
FootnoteUID = Path(None, description="The unique id of the footnote.")


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all final versions of footnotes referenced by any study.",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    response_model=CustomPage[models.FootnoteWithType],
    status_code=200,
    responses={
        200: {
            "content": {
                "text/csv": {
                    "example": """
"library","uid","objective","criteria_template","footnote","start_date","end_date","status","version","change_description","user_initials"
"Sponsor","826d80a7-0b6a-419d-8ef1-80aa241d7ac7","Objective","First [ComparatorIntervention]","First Intervention","2020-10-22T10:19:29+00:00",,"Draft","0.1","Initial version","NdSJ"
"""
                },
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {},
                "text/xml": {
                    "example": """
<?xml version="1.0" encoding="UTF-8" ?>
<root>
    <data type="list">
        <item type="dict">
            <library type="str">Sponsor</library>
            <uid type="str">682d7003-8dcc-480d-b07b-878e659b8697</uid>
            <objective type="str">Test template new [glucose metabolism] [MACE+] totot</objective>
            <criteria_template type="str">Footnote using [Activity] and [Indication]</criteria_template>
            <footnote type="str">Footnote using [body weight] and [type 2 diabetes]</footnote>
            <start_date type="str">2020-11-26T13:43:23.000Z</start_date>
            <end_date type="str"></end_date>
            <status type="str">Draft</status>
            <version type="str">0.2</version>
            <change_description type="str">Changed indication</change_description>
            <user_initials type="str">TODO Initials</user_initials>
        </item>
    </data>
</root>
"""
                },
            }
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "library=library.name",
            "uid",
            "objective=objective.name",
            "criteria_template=criteria_template.name",
            "footnote=name",
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
def get_all(
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
        description=_generic_descriptions.SYNTAX_FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: str | None = Query("and", description=_generic_descriptions.OPERATOR),
    total_count: bool
    | None = Query(False, description=_generic_descriptions.TOTAL_COUNT),
):
    all_items = FootnoteService().get_all(
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
    )

    return CustomPage.create(
        items=all_items.items,
        total=all_items.total,
        page=page_number,
        size=page_size,
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
        500: _generic_descriptions.ERROR_500,
    },
)
def get_distinct_values_for_header(
    status: LibraryItemStatus
    | None = Query(
        None,
        description="If specified, only those objective templates will be returned that are currently in the specified status. "
        "This may be particularly useful if the objective template has "
        "a) a 'Draft' and a 'Final' status or "
        "b) a 'Draft' and a 'Retired' status at the same time "
        "and you are interested in the 'Final' or 'Retired' status.\n"
        "Valid values are: 'Final', 'Draft' or 'Retired'.",
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
    return FootnoteService().get_distinct_values_for_header(
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
    response_model=CustomPage[models.Footnote],
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
    summary="Returns the latest/newest version of a specific footnote identified by 'uid'.",
    description="""If multiple request query parameters are used, then they need to
    match all at the same time (they are combined with the AND operation).""",
    response_model=models.FootnoteWithType | None,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote with the specified 'uid' (and the specified date/time and/or status) wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get(
    uid: str = FootnoteUID,
):
    return FootnoteService().get_by_uid(uid=uid)


@router.get(
    "/{uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the version history of a specific footnote identified by 'uid'.",
    description="The returned versions are ordered by\n"
    "0. start_date descending (newest entries first)",
    response_model=list[models.FootnoteVersion],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_versions(uid: str = FootnoteUID):
    return Service().get_version_history(uid=uid)


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE_OR_STUDY_WRITE],
    summary="Creates a new footnote in 'Draft' status.",
    description="""This request is only valid if
* the specified footnote template is in 'Final' status and
* the specified objective is in 'Final' status and
* the specified library allows creating footnote (the 'is_editable' property of the library needs to be true) and
* the footnote does not yet exist (no footnote with the same content in 'Final' or 'Draft' status).

If the request succeeds:
* The status will be automatically set to 'Draft'.
* The 'change_description' property will be set automatically.
* The 'version' property will be set to '0.1'.
""",
    response_model=models.Footnote,
    status_code=201,
    responses={
        201: {"description": "Created - The footnote was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The provided list of parameters is invalid.\n"
            "- The objective wasn't found or it is not in 'Final' status.\n"
            "- The library does not allow to create footnote.\n"
            "- The footnote does already exist.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The library with the specified 'library_name' could not be found.\n"
            "- The footnote template with the specified 'criteria_template_uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def create(
    footnote: models.FootnoteCreateInput = Body(
        description="Related parameters of the footnote that shall be created."
    ),
):
    return FootnoteService().create(footnote)


@router.post(
    "/preview",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Previews the creation of a new footnote.",
    description="""This request is only valid if
* the specified footnote template is in 'Final' status and
* the specified library allows creating footnote (the 'is_editable' property of the library needs to be true) and
* the footnote does not yet exist (no footnote with the same content in 'Final' or 'Draft' status).

If the request succeeds:
* No footnote will be created, but the result of the request will show what the footnote will look like.
""",
    response_model=models.Footnote,
    status_code=200,
    responses={
        200: {"description": "Success - The footnote is able to be created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The provided list of parameters is invalid.\n"
            "- The library does not allow to create footnote.\n"
            "- The footnote does already exist.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The library with the specified 'library_name' could not be found.\n"
            "- The footnote template with the specified 'criteria_template_uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def preview(
    footnote: models.FootnoteCreateInput = Body(
        description="Related parameters of the footnote that shall be previewed."
    ),
):
    return FootnoteService().create(footnote, preview=True)


@router.patch(
    "/{uid}",
    dependencies=[rbac.LIBRARY_WRITE_OR_STUDY_WRITE],
    summary="Updates the footnote identified by 'uid'.",
    description="""This request is only valid if the footnote
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true). 

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.
""",
    response_model=models.FootnoteWithType,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The footnote is not in draft status.\n"
            "- The footnote had been in 'Final' status before.\n"
            "- The provided list of parameters is invalid.\n"
            "- The library does not allow to edit draft versions.\n"
            "- The footnote does already exist.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def edit(
    uid: str = FootnoteUID,
    footnote: models.FootnoteEditInput = Body(
        description="The new parameter terms for the footnote including the change description.",
    ),
):
    return Service().edit_draft(uid, footnote)


@router.post(
    "/{uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE_OR_STUDY_WRITE],
    summary="Approves the footnote identified by 'uid'.",
    description="""This request is only valid if the footnote
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically.
* The 'version' property will be increased automatically to the next major version.
    """,
    response_model=models.FootnoteWithType,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The footnote is not in draft status.\n"
            "- The library does not allow to approve footnote.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def approve(uid: str = FootnoteUID):
    return Service().approve(uid)


@router.delete(
    "/{uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Inactivates/deactivates the footnote identified by 'uid'.",
    description="""This request is only valid if the footnote
* is in 'Final' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Retired'.
* The 'change_description' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=models.FootnoteWithType,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The footnote is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def inactivate(uid: str = FootnoteUID):
    return Service().inactivate_final(uid=uid)


@router.post(
    "/{uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivates the footnote identified by 'uid'.",
    description="""This request is only valid if the footnote
* is in 'Retired' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=models.FootnoteWithType,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The footnote is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def reactivate(uid: str = FootnoteUID):
    return Service().reactivate_retired(uid)


@router.delete(
    "/{uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Deletes the footnote identified by 'uid'.",
    description="""This request is only valid if \n
* the footnote is in 'Draft' status and
* the footnote has never been in 'Final' status and
* the footnote belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).""",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The footnote was successfully deleted."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The footnote is not in draft status.\n"
            "- The footnote was already in final state or is in use.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An footnote with the specified uid could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def delete(uid: str = FootnoteUID):
    Service().soft_delete(uid)
    return Response(status_code=fast_api_status.HTTP_204_NO_CONTENT)


@router.get(
    "/{uid}/studies",
    dependencies=[rbac.STUDY_READ],
    summary="",
    description="",
    response_model=list[Study],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_studies(
    uid: str = FootnoteUID,
    include_sections: list[StudyComponentEnum]
    | None = Query(None, description=study_section_description("include")),
    exclude_sections: list[StudyComponentEnum]
    | None = Query(None, description=study_section_description("exclude")),
):
    return Service().get_referencing_studies(
        uid=uid,
        node_type=FootnoteValue,
        include_sections=include_sections,
        exclude_sections=exclude_sections,
    )


@router.get(
    "/{uid}/parameters",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all template parameters available for the footnote identified by 'uid'. Includes the available values per parameter.",
    description="""Returns all template parameters used in the footnote template
that is the basis for the footnote identified by 'uid'. 
Includes the available values per parameter.

The returned parameters are ordered
0. as they occur in the footnote template

Per parameter, the parameter.values are ordered by
0. value.name ascending

Note that parameters may be used multiple times in templates.
In that case, the same parameter (with the same values) is included multiple times in the response.
    """,
    response_model=list[models.TemplateParameter],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_parameters(
    uid: str = Path(None, description="The unique id of the footnote."),
):
    return FootnoteService().get_parameters(uid)
