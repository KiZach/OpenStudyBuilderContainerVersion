"""Footnote templates router."""

from typing import Any

from fastapi import APIRouter, Body, Path, Query, Request, Response
from fastapi import status as fast_api_status
from pydantic.types import Json

from clinical_mdr_api import config, models
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.syntax_pre_instances.footnote_pre_instance import (
    FootnotePreInstanceCreateInput,
)
from clinical_mdr_api.models.syntax_templates.footnote_template import (
    FootnoteTemplateWithCount,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.syntax_pre_instances.footnote_pre_instances import (
    FootnotePreInstanceService,
)
from clinical_mdr_api.services.syntax_templates.footnote_templates import (
    FootnoteTemplateService,
)

# Prefixed with /footnote-templates
router = APIRouter()

Service = FootnoteTemplateService

# Argument definitions
FootnoteTemplateUID = Path(None, description="The unique id of the footnote template.")

PARAMETERS_NOTE = """**Parameters in the 'name' property**:

The 'name' of an footnote template may contain parameters, that can - and usually will - be replaced with concrete values once an footnote is created out of the footnote template.

Parameters are referenced by simple strings in square brackets [] that match existing parameters defined in the MDR repository.

The footnote template will be linked to those parameters defined in the 'name' property.

You may use an arbitrary number of parameters and you may use the same parameter multiple times within the same footnote template 'name'.

*Example*:

name='MORE TESTING of the superiority in the efficacy of [Intervention] with [Activity] and [Activity] in [Timeframe].'

'Intervention', 'Activity' and 'Timeframe' are parameters."""


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all footnote templates in their latest/newest version.",
    description=f"""
Allowed parameters include : filter on fields, sort by field name with sort direction, pagination.

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=CustomPage[models.FootnoteTemplate],
    status_code=200,
    responses={
        200: {
            "content": {
                "text/csv": {
                    "example": """
"library","uid","name","start_date","end_date","status","version","change_description","user_initials"
"Sponsor","826d80a7-0b6a-419d-8ef1-80aa241d7ac7","First  [ComparatorIntervention]","2020-10-22T10:19:29+00:00",,"Draft","0.1","Initial version","NdSJ"
"""
                },
                "text/xml": {
                    "example": """
<?xml version="1.0" encoding="UTF-8" ?>
<root>
    <data type="list">
        <item type="dict">
            <uid type="str">e9117175-918f-489e-9a6e-65e0025233a6</uid>
            <name type="str">"First  [ComparatorIntervention]</name>
            <start_date type="str">2020-11-19T11:51:43.000Z</start_date>
            <status type="str">Draft</status>
            <version type="str">0.2</version>
            <change_description type="str">Test</change_description>
            <user_initials type="str">TODO Initials</user_initials>
        </item>
  </data>
</root>
"""
                },
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {},
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
            "sequence_id",
            "name_plain",
            "name",
            "indications=indications.name",
            "categories=categories.name.sponsor_preferred_name",
            "sub_categories=sub_categories.name.sponsor_preferred_name",
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
def get_footnote_templates(
    request: Request,  # request is actually required by the allow_exports decorator
    status: LibraryItemStatus
    | None = Query(
        None,
        description="If specified, only those footnote templates will be returned that are currently in the specified status. "
        "This may be particularly useful if the footnote template has "
        "a) a 'Draft' and a 'Final' status or "
        "b) a 'Draft' and a 'Retired' status at the same time "
        "and you are interested in the 'Final' or 'Retired' status.\n"
        "Valid values are: 'Final', 'Draft' or 'Retired'.",
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
) -> CustomPage[models.FootnoteTemplate]:
    results = Service().get_all(
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
        500: _generic_descriptions.ERROR_500,
    },
)
def get_distinct_values_for_header(
    status: LibraryItemStatus
    | None = Query(
        None,
        description="If specified, only those footnote templates will be returned that are currently in the specified status. "
        "This may be particularly useful if the footnote template has "
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
    response_model=CustomPage[models.FootnoteTemplate],
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
    summary="Returns the latest/newest version of a specific footnote template identified by 'uid'.",
    description="""If multiple request query parameters are used, then they need to
    match all at the same time (they are combined with the AND operation).""",
    response_model=FootnoteTemplateWithCount | None,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote template with the specified 'uid' (and the specified date/time and/or status) wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_footnote_template(
    uid: str = FootnoteTemplateUID,
):
    return Service().get_by_uid(uid=uid)


@router.get(
    "/{uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the version history of a specific footnote template identified by 'uid'.",
    description=f"""
The returned versions are ordered by `start_date` descending (newest entries first)

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=list[models.FootnoteTemplateVersion],
    status_code=200,
    responses={
        200: {
            "content": {
                "text/csv": {
                    "example": """
"library","uid","name","start_date","end_date","status","version","change_description","user_initials"
"Sponsor","826d80a7-0b6a-419d-8ef1-80aa241d7ac7","First  [ComparatorIntervention]","2020-10-22T10:19:29+00:00",,"Draft","0.1","Initial version","NdSJ"
"""
                },
                "text/xml": {
                    "example": """
<?xml version="1.0" encoding="UTF-8" ?>
<root>
    <data type="list">
        <item type="dict">
            <name type="str">First  [ComparatorIntervention]</name>
            <start_date type="str">2020-11-19 11:51:43+00:00</start_date>
            <end_date type="str">None</end_date>
            <status type="str">Draft</status>
            <version type="str">0.2</version>
            <change_description type="str">Test</change_description>
            <user_initials type="str">TODO Initials</user_initials>
        </item>
        <item type="dict">
            <name type="str">First  [ComparatorIntervention]</name>
            <start_date type="str">2020-11-19 11:51:07+00:00</start_date>
            <end_date type="str">2020-11-19 11:51:43+00:00</end_date>
            <status type="str">Draft</status>
            <version type="str">0.1</version>
            <change_description type="str">Initial version</change_description>
            <user_initials type="str">TODO user initials</user_initials>
        </item>
    </data>
</root>
"""
                },
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {},
            }
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote template with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "library=library.name",
            "name",
            "change_description",
            "status",
            "version",
            "start_date",
            "end_date",
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
#  pylint: disable=unused-argument
def get_footnote_template_versions(
    request: Request,  # request is actually required by the allow_exports decorator
    uid: str = FootnoteTemplateUID,
):
    return Service().get_version_history(uid=uid)


@router.get(
    "/{uid}/versions/{version}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns a specific version of a specific footnote template identified by 'uid' and 'version'.",
    description="**Multiple versions**:\n\n"
    "Technically, there can be multiple versions of the footnote template with the same version number. "
    "This is due to the fact, that the version number remains the same when inactivating or reactivating an footnote template "
    "(switching between 'Final' and 'Retired' status). \n\n"
    "In that case the latest/newest representation is returned.",
    response_model=models.FootnoteTemplate,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote template with the specified 'uid' and 'version' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_footnote_template_version(
    uid: str = FootnoteTemplateUID,
    version: str = Path(
        None,
        description="A specific version number of the footnote template. "
        "The version number is specified in the following format: \\<major\\>.\\<minor\\> where \\<major\\> and \\<minor\\> are digits.\n"
        "E.g. '0.1', '0.2', '1.0', ...",
    ),
):
    return Service().get_specific_version(uid=uid, version=version)


@router.get(
    "/{uid}/releases",
    dependencies=[rbac.LIBRARY_READ],
    summary="List all final versions of a template identified by 'uid', including number of studies using a specific version",
    description="",
    response_model=list[models.FootnoteTemplate],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote template with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_footnote_template_releases(uid: str = FootnoteTemplateUID):
    return Service().get_releases(uid=uid, return_study_count=False)


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE_OR_STUDY_WRITE],
    summary="Creates a new footnote template in 'Draft' status or returns the footnote template if it already exists.",
    description="""This request is only valid if the footnote template
* belongs to a library that allows creating (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Draft'.
* The 'change_description' property will be set automatically.
* The 'version' property will be set to '0.1'.
* The footnote template will be linked to a library.

"""
    + PARAMETERS_NOTE,
    response_model=models.FootnoteTemplate,
    status_code=201,
    responses={
        201: {
            "description": "Created - The footnote template was successfully created."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The footnote template name is not valid.\n"
            "- The library does not allow to create footnote templates.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The library with the specified 'library_name' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def create_footnote_template(
    footnote_template: models.FootnoteTemplateCreateInput = Body(
        description="The footnote template that shall be created."
    ),
):
    return Service().create(footnote_template)


@router.patch(
    "/{uid}",
    dependencies=[rbac.LIBRARY_WRITE_OR_STUDY_WRITE],
    summary="Updates the footnote template identified by 'uid'.",
    description="""This request is only valid if the footnote template
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true). 

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.

Parameters in the 'name' property can only be changed if the footnote template has never been approved.
Once the footnote template has been approved, only the surrounding text (excluding the parameters) can be changed.

"""
    + PARAMETERS_NOTE,
    response_model=models.FootnoteTemplate,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The footnote template is not in draft status.\n"
            "- The footnote template name is not valid.\n"
            "- The library does not allow to edit draft versions.\n"
            "- The change of parameters of previously approved footnote templates.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote template with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def edit(
    uid: str = FootnoteTemplateUID,
    footnote_template: models.FootnoteTemplateEditInput = Body(
        description="The new content of the footnote template including the change description.",
    ),
):
    return Service().edit_draft(uid=uid, template=footnote_template)


@router.patch(
    "/{uid}/indexings",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Updates the indexings of the footnote template identified by 'uid'.",
    description="""This request is only valid if the template
    * belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).
    
    This is version independent : it won't trigger a status or a version change.
    """,
    response_model=models.FootnoteTemplate,
    status_code=200,
    responses={
        200: {
            "description": "No content - The indexings for this template were successfully updated."
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The template with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def patch_indexings(
    uid: str = FootnoteTemplateUID,
    indexings: models.FootnoteTemplateEditIndexingsInput = Body(
        description="The lists of UIDs for the new indexings to be set, grouped by indexings to be updated.",
    ),
) -> models.FootnoteTemplate:
    return Service().patch_indexings(uid=uid, indexings=indexings)


@router.post(
    "/{uid}/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates a new version of the footnote template identified by 'uid'.",
    description="""This request is only valid if the footnote template
* is in 'Final' or 'Retired' status only (so no latest 'Draft' status exists) and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The latest 'Final' or 'Retired' version will remain the same as before.
* The status of the new version will be automatically set to 'Draft'.
* The 'version' property of the new version will be automatically set to the version of the latest 'Final' or 'Retired' version increased by +0.1.

Parameters in the 'name' property cannot be changed with this request.
Only the surrounding text (excluding the parameters) can be changed.
""",
    response_model=models.FootnoteTemplate,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The footnote template is not in final or retired status or has a draft status.\n"
            "- The footnote template name is not valid.\n"
            "- The library does not allow to create a new version.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote template with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def create_new_version(
    uid: str = FootnoteTemplateUID,
    footnote_template: models.FootnoteTemplateEditInput = Body(
        description="The content of the footnote template for the new 'Draft' version including the change description.",
    ),
):
    return Service().create_new_version(uid=uid, template=footnote_template)


@router.post(
    "/{uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE_OR_STUDY_WRITE],
    summary="Approves the footnote template identified by 'uid'.",
    description="""This request is only valid if the footnote template
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically.
* The 'version' property will be increased automatically to the next major version.
    """,
    response_model=models.FootnoteTemplate,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The footnote template is not in draft status.\n"
            "- The library does not allow to approve drafts.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote template with the specified 'uid' could not be found.",
        },
        409: {
            "model": ErrorResponse,
            "description": "Conflict - there are footnote created from template and cascade is false",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def approve(
    uid: str = FootnoteTemplateUID,
    cascade: bool = False,
):
    """
    Approves footnote template. Fails with 409 if there is some footnote created
    from this template and cascade is false
    """
    if not cascade:
        return Service().approve(uid=uid)
    return Service().approve_cascade(uid=uid)


@router.delete(
    "/{uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Inactivates/deactivates the footnote template identified by 'uid' and its Pre-Instances.",
    description="""This request is only valid if the footnote template
* is in 'Final' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Retired'.
* The 'change_description' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=models.FootnoteTemplate,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The footnote template is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote template with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def inactivate(uid: str = FootnoteTemplateUID):
    return Service().inactivate_final(uid=uid)


@router.post(
    "/{uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivates the footnote template identified by 'uid' and its Pre-Instances.",
    description="""This request is only valid if the footnote template
* is in 'Retired' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=models.FootnoteTemplate,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The footnote template is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote template with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def reactivate(uid: str = FootnoteTemplateUID):
    return Service().reactivate_retired(uid=uid)


@router.delete(
    "/{uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Deletes the footnote template identified by 'uid'.",
    description="""This request is only valid if \n
* the footnote template is in 'Draft' status and
* the footnote template has never been in 'Final' status and
* the footnote template has no references to any footnote and
* the footnote template belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).""",
    response_model=None,
    status_code=204,
    responses={
        204: {
            "description": "No Content - The footnote template was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The footnote template is not in draft status.\n"
            "- The footnote template was already in final state or is in use.\n"
            "- The library does not allow to delete footnote templates.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An footnote template with the specified uid could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def delete_footnote_template(uid: str = FootnoteTemplateUID):
    Service().soft_delete(uid)
    return Response(status_code=fast_api_status.HTTP_204_NO_CONTENT)


# TODO this endpoint potentially returns duplicated entries (intentionally, currently).
#       however: check if that is ok with regards to the data volume we expect in the future. is paging needed?
@router.get(
    "/{uid}/parameters",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all parameters used in the footnote template identified by 'uid'. Includes the available terms per parameter.",
    description="""The returned parameters are ordered
0. as they occur in the footnote template

Per parameter, the parameter.terms are ordered by
0. term.name ascending

Note that parameters may be used multiple times in templates.
In that case, the same parameter (with the same terms) is included multiple times in the response.
    """,
    response_model=list[models.TemplateParameter],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_parameters(
    uid: str = Path(None, description="The unique id of the footnote template."),
):
    return Service().get_parameters(uid=uid)


@router.post(
    "/pre-validate",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Validates the content of an footnote template without actually processing it.",
    description="""Be aware that - even if this request is accepted - there is no guarantee that
a following request to e.g. *[POST] /footnote-templates* or *[PATCH] /footnote-templates/{uid}*
with the same content will succeed.

"""
    + PARAMETERS_NOTE,
    status_code=202,
    responses={
        202: {
            "description": "Accepted. The content is valid and may be submitted in another request."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden. The content is invalid - Reasons include e.g.: \n"
            "- The syntax of the 'name' is not valid.\n"
            "- One of the parameters wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def pre_validate(
    footnote_template: models.FootnoteTemplateNameInput = Body(
        description="The content of the footnote template that shall be validated.",
    ),
):
    Service().validate_template_syntax(footnote_template.name)


@router.post(
    "/{uid}/pre-instances",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Create a Pre-Instance",
    description="",
    response_model=models.FootnotePreInstance,
    status_code=201,
    responses={
        201: {
            "description": "Created - The footnote pre-instance was successfully created."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The footnote template is not in draft status.\n"
            "- The footnote template name is not valid.\n"
            "- The library does not allow to edit draft versions.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote template with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_pre_instance(
    uid: str = FootnoteTemplateUID,
    pre_instance: FootnotePreInstanceCreateInput = Body(description=""),
) -> models.FootnoteTemplate:
    return FootnotePreInstanceService().create(
        template=pre_instance,
        template_uid=uid,
    )
