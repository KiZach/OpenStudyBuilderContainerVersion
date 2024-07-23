from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, Path, Query, Request, Response
from fastapi import status as fast_api_status
from pydantic.types import Json

from clinical_mdr_api import config
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionModel,
    UnitDefinitionPatchInput,
    UnitDefinitionPostInput,
)
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.concepts.unit_definitions.unit_definition import (
    UnitDefinitionService,
)

# Prefixed with "/concepts/unit-definitions"
router = APIRouter()

Service = UnitDefinitionService


# Argument definitions
UnitDefinitionUID = Path(None, description="The unique id of unit definition.")


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all unit definitions in their latest/newest version.",
    description=f"""
Allowed parameters include : filter on fields, sort by field name with sort direction, pagination.

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=CustomPage[UnitDefinitionModel],
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
                    <?xml version="1.0" encoding="UTF-8" ?><root><data type="list"><item type="dict"><uid type="str">e9117175-918f-489e-9a6e-65e0025233a6</uid><name type="str">Alamakota</name><start_date type="str">2020-11-19T11:51:43.000Z</start_date><status type="str">Draft</status><version type="str">0.2</version><change_description type="str">Test</change_description><user_initials type="str">TODO Initials</user_initials></item></data></root>
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
            "uid",
            "library_name",
            "name",
            "master_unit",
            "display_unit",
            "unit_subsets",
            "ucum=ucum.name",
            "ct_units",
            "convertible_unit",
            "si_unit",
            "us_conventional_unit",
            "unit_dimension=unit_dimension.name",
            "legacy_code",
            "molecular_weight_conv_expon",
            "conversion_factor_to_master",
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
def get_all(
    request: Request,  # request is actually required by the allow_exports decorator
    library_name: str | None = Query(None),
    dimension: str
    | None = Query(
        None,
        description="The code submission value of the unit dimension to filter, for instance 'Dose Unit'.",
    ),
    subset: str
    | None = Query(
        None,
        description="The name of the unit subset to filter, for instance 'Age Unit'.",
    ),
    service: Service = Depends(),
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
) -> CustomPage[UnitDefinitionModel]:
    results = service.get_all(
        library_name=library_name,
        dimension=dimension,
        subset=subset,
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
    library_name: str | None = Query(None),
    dimension: str
    | None = Query(
        None,
        description="The code submission value of the unit dimension to filter, for instance 'Dose Unit'.",
    ),
    subset: str
    | None = Query(
        None,
        description="The name of the unit subset to filter, for instance 'Age Unit'.",
    ),
    service: Service = Depends(),
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
    return service.get_distinct_values_for_header(
        library_name=library_name,
        dimension=dimension,
        subset=subset,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.get(
    "/{uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the latest/newest version of a specific Unit definition identified by 'uid'.",
    description="""If multiple request query parameters are used, then they need to
    match all at the same time (they are combined with the AND operation).""",
    response_model=UnitDefinitionModel,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": """Not Found - The unit definition with the specified
            'uid' (and the specified date/time, version and/or status) wasn't found.""",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_by_uid(
    uid: str = UnitDefinitionUID,
    at_specified_date_time: datetime
    | None = Query(
        None,
        description="If specified, the latest/newest representation of the unit definition at this point in time is returned.\n"
        "The point in time needs to be specified in ISO 8601 format including the timezone, e.g.: "
        "'2020-10-31T16:00:00+02:00' for October 31, 2020 at 4pm in UTC+2 timezone. ",
    ),
    status: LibraryItemStatus
    | None = Query(
        None,
        description="If specified, the representation of the unit definition in that status is returned (if existent). "
        "This may be particularly useful if the unit definition has "
        "a) a 'Draft' and a 'Final' status or "
        "b) a 'Draft' and a 'Retired' status at the same time "
        "and you are interested in the 'Final' or 'Retired' status.\n"
        "Valid values are: 'Final', 'Draft' or 'Retired'.",
    ),
    version: str
    | None = Query(
        None,
        description=r"If specified, the latest/newest representation of the concept is returned. "
        r"Only exact matches are considered. "
        r"The version is specified in the following format: \<major\>.\<minor\> where \<major\> and \<minor\> are digits. "
        r"E.g. '0.1', '0.2', '1.0', ...",
    ),
    service: Service = Depends(),
) -> UnitDefinitionModel:
    return service.get_by_uid(
        uid,
        version=version,
        status=status,
        at_specified_datetime=at_specified_date_time,
    )


@router.get(
    "/{uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the version history of a specific concept identified by 'uid'.",
    description=f"""
The returned versions are ordered by `start_date` descending (newest entries first)

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=list[UnitDefinitionModel],
    status_code=200,
    responses={
        200: {
            "content": {
                "text/csv": {
                    "example": """
"library";"uid";"name";"start_date";"end_date";"status";"version";"change_description";"user_initials"
"Sponsor";"826d80a7-0b6a-419d-8ef1-80aa241d7ac7";"First  [ComparatorIntervention]";"2020-10-22T10:19:29+00:00";;"Draft";"0.1";"Initial version";"NdSJ"
"""
                },
                "text/xml": {
                    "example": """
                    <?xml version="1.0" encoding="UTF-8" ?><root><data type="list"><item type="dict"><name type="str">Alamakota</name><start_date type="str">2020-11-19 11:51:43+00:00</start_date><end_date type="str">None</end_date><status type="str">Draft</status><version type="str">0.2</version><change_description type="str">Test</change_description><user_initials type="str">TODO Initials</user_initials></item><item type="dict"><name type="str">Alamakota</name><start_date type="str">2020-11-19 11:51:07+00:00</start_date><end_date type="str">2020-11-19 11:51:43+00:00</end_date><status type="str">Draft</status><version type="str">0.1</version><change_description type="str">Initial version</change_description><user_initials type="str">TODO user initials</user_initials></item></data></root>
"""
                },
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {},
            }
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The concept with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "library_name",
            "uid",
            "name",
            "unit_ct",
            "convertible_unit",
            "display_unit",
            "master_unit",
            "si_unit",
            "us_conventional_unit",
            "legacy_code",
            "molecular_weight_conv_expon",
            "conversion_factor_to_master",
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
def get_versions(
    request: Request,  # request is actually required by the allow_exports decorator
    uid: str = UnitDefinitionUID,
    service: Service = Depends(),
) -> list[UnitDefinitionModel]:
    return service.get_versions(uid)


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE],
    response_model=UnitDefinitionModel,
    summary="Creates a new unit definition in 'Draft' status.",
    description="""This request is only valid if the unit definition
* belongs to a library that allows creating (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Draft'.
* The 'change_description' property will be set automatically.
* The 'version' property will be set to '0.1'.
* The unit definition template will be linked to a library.

""",
    status_code=201,
    responses={
        201: {"description": "Created - The concept was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The concept name is not valid.\n"
            "- The library does not allow to create concept.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The library with the specified 'library_name' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def post(
    unit_definition_post_input: UnitDefinitionPostInput = Body(
        description="The concept that shall be created."
    ),
    service: Service = Depends(),
) -> UnitDefinitionModel:
    return service.post(unit_definition_post_input)  # type: ignore


@router.patch(
    "/{uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Updates the unit definition identified by 'uid'.",
    description="""This request is only valid if the unit definition
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.

""",
    response_model=UnitDefinitionModel,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The unit definition is not in draft status.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The concept with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def patch(
    uid: str = UnitDefinitionUID,
    patch_input: UnitDefinitionPatchInput = Body(
        description="The new content of the concept including the change description.",
    ),
    service: Service = Depends(),
) -> UnitDefinitionModel:
    return service.patch(uid, patch_input)


@router.post(
    "/{uid}/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates a new version of the unit definition identified by 'uid'.",
    description="""This request is only valid if the unit definition
* is in 'Final' or 'Retired' status only (so no latest 'Draft' status exists) and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The latest 'Final' or 'Retired' version will remain the same as before.
* The status of the new version will be automatically set to 'Draft'.
* The 'version' property of the new version will be automatically set to the version of the latest 'Final' or 'Retired' version increased by +0.1.

""",
    response_model=UnitDefinitionModel,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The unit definition is not in final or retired status or has a draft status.\n"
            "- The library does not allow to create a new version.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The  concept with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def new_version(
    uid: str = UnitDefinitionUID, service: Service = Depends()
) -> UnitDefinitionModel:
    return service.new_version(uid)


@router.post(
    "/{uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approves the unit definition identified by 'uid'.",
    description="""This request is only valid if the unit definition
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically.
* The 'version' property will be increased automatically to the next major version.
    """,
    response_model=UnitDefinitionModel,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The unit definition is not in draft status.\n"
            "- The library does not allow to approve drafts.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The unit definition with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def approve(
    uid: str = UnitDefinitionUID, service: Service = Depends()
) -> UnitDefinitionModel:
    return service.approve(uid)


@router.delete(
    "/{uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Inactivates/deactivates the unit definition identified by 'uid'.",
    description="""This request is only valid if the unit definition
* is in 'Final' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Retired'.
* The 'change_description' property will be set automatically.
* The 'version' property will remain the same as before.
    """,
    response_model=UnitDefinitionModel,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The unit definition is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The unit definition with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def inactivate(
    uid: str = UnitDefinitionUID, service: Service = Depends()
) -> UnitDefinitionModel:
    return service.inactivate(uid)


@router.post(
    "/{uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivates the unit definition identified by 'uid'.",
    description="""This request is only valid if the unit definition
* is in 'Retired' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically.
* The 'version' property will remain the same as before.
    """,
    response_model=UnitDefinitionModel,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The unit definition is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The concept with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def reactivate(
    uid: str = UnitDefinitionUID, service: Service = Depends()
) -> UnitDefinitionModel:
    return service.reactivate(uid)


@router.delete(
    "/{uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Deletes the unit definition identified by 'uid'.",
    description="""This request is only valid if \n
* the unit definition is in 'Draft' status and
* the unit definition has never been in 'Final' status and
* the unit definition belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).""",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The concept was successfully deleted."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The concept is not in draft status.\n"
            "- The concept was already in final state or is in use.\n"
            "- The library does not allow to delete concept.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An concept with the specified uid could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def delete(uid: str = UnitDefinitionUID, service: Service = Depends()) -> None:
    service.delete(uid)
    return Response(status_code=fast_api_status.HTTP_204_NO_CONTENT)
