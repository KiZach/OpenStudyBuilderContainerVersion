"""New Activities router."""
from typing import Any

from fastapi import APIRouter, Body, Path, Query, Response, status
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api import config
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstance,
    ActivityInstanceCreateInput,
    ActivityInstanceEditInput,
    ActivityInstanceOverview,
)
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers.responses import YAMLResponse
from clinical_mdr_api.services.concepts.activities.activity_instance_service import (
    ActivityInstanceService,
)

# Prefixed with "/concepts/activities/activity-instances"
router = APIRouter()

ActivityInstanceUID = Path(None, description="The unique id of the ActivityInstance")


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="List all activity instances (for a given library)",
    description=f"""
State before:
 - The library must exist (if specified)
 
Business logic:
 - List all activity instances in their latest version, including properties derived from linked control terminology.
 
State after:
 - No change
 
Possible errors:
 - Invalid library name specified.

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=CustomPage[ActivityInstance],
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
            "activity_instance_class=activity_instance_class.name",
            "activity=activity_groupings.activity.name",
            "activity_instance=name",
            "definition",
            "nci_concept_id",
            "topic_code",
            "adam_param_code",
            "is_required_for_activity",
            "is_default_selected_for_activity",
            "is_data_sharing",
            "is_legacy_usage",
            "start_date",
            "user_initials",
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
def get_activities(
    request: Request,  # request is actually required by the allow_exports decorator
    library: str | None = Query(None, description=""),
    activity_names: list[str]
    | None = Query(
        None,
        description="A list of activity names to use as a specific filter",
        alias="activity_names[]",
    ),
    activity_subgroup_names: list[str]
    | None = Query(
        None,
        description="A list of activity subgroup names to use as a specific filter",
        alias="activity_subgroup_names[]",
    ),
    activity_group_names: list[str]
    | None = Query(
        None,
        description="A list of activity group names to use as a specific filter",
        alias="activity_group_names[]",
    ),
    activity_instance_class_names: list[str]
    | None = Query(
        None,
        description="A list of activity_instance_class names to use as a specific filter",
        alias="activity_instance_class_names[]",
    ),
    sort_by: Json = Query({}, description=_generic_descriptions.SORT_BY),
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
    activity_instance_service = ActivityInstanceService()
    results = activity_instance_service.get_all_concepts(
        library=library,
        activity_names=activity_names,
        activity_subgroup_names=activity_subgroup_names,
        activity_group_names=activity_group_names,
        activity_instance_class_names=activity_instance_class_names,
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
    "/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="List all versions of all activity instances (for a given library)",
    description=f"""
State before:
 - The library must exist (if specified)
 
Business logic:
 - List version history of all activity instances
 - The returned versions are ordered by version start_date descending (newest entries first).

State after:
 - No change
 
Possible errors:
 - Invalid library name specified.

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=CustomPage[ActivityInstance],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "library_name",
            "activity=activities.name",
            "name",
            "definition",
            "topic_code",
            "adam_param_code",
            "is_required_for_activity",
            "is_default_selected_for_activity",
            "is_data_sharing",
            "is_legacy_usage",
            "sdtm_domain=sdtm_domain.name",
            "start_date",
            "user_initials",
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
def get_activity_instances_versions(
    request: Request,  # request is actually required by the allow_exports decorator
    library: str | None = Query(None, description=""),
    activity_names: list[str]
    | None = Query(
        None,
        description="A list of activity names to use as a specific filter",
        alias="activity_names[]",
    ),
    activity_instance_class_names: list[str]
    | None = Query(
        None,
        description="A list of activity_instance_class names to use as a specific filter",
        alias="activity_instance_class_names[]",
    ),
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
    activity_instance_service = ActivityInstanceService()
    results = activity_instance_service.get_all_concept_versions(
        library=library,
        activity_names=activity_names,
        activity_instance_class_names=activity_instance_class_names,
        sort_by={"start_date": False},
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
    "/headers",
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
    library: str | None = Query(None, description=""),
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
    activity_instance_service = ActivityInstanceService()
    return activity_instance_service.get_distinct_values_for_header(
        library=library,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.get(
    "/{uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get details on a specific activity instance (in a specific version)",
    description="""
State before:
 - a activity instance with uid must exist.

Business logic:
 - If parameter at_specified_date_time is specified then the latest/newest representation of the concept at this point in time is returned. The point in time needs to be specified in ISO 8601 format including the timezone, e.g.: '2020-10-31T16:00:00+02:00' for October 31, 2020 at 4pm in UTC+2 timezone. If the timezone is ommitted, UTC�0 is assumed.
 - If parameter status is specified then the representation of the concept in that status is returned (if existent). This is useful if the concept has a status 'Draft' and a status 'Final'.
 - If parameter version is specified then the latest/newest representation of the concept in that version is returned. Only exact matches are considered. The version is specified in the following format: <major>.<minor> where <major> and <minor> are digits. E.g. '0.1', '0.2', '1.0', ...

State after:
 - No change

Possible errors:
 - Invalid uid, at_specified_date_time, status or version.
 """,
    response_model=ActivityInstance,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_activity(uid: str = ActivityInstanceUID):
    activity_instance_service = ActivityInstanceService()
    return activity_instance_service.get_by_uid(uid=uid)


@router.get(
    "/{uid}/overview",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get detailed overview a specific activity instance",
    description="""
Returns detailed description about activity instance, including information about:
 - Activity
 - Activity subgroups
 - Activity groups
 - Activity instance class
 - Activity items
 - Activity item class

State before:
 - an activity instance with uid must exist.

State after:
 - No change

Possible errors:
 - Invalid uid.
 """,
    response_model=ActivityInstanceOverview,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "activity",
            "activity_subgroups",
            "activity_groups",
            "activity_instance",
            "activity_items",
        ],
        "formats": [
            "application/x-yaml",
        ],
    }
)
# pylint: disable=unused-argument
def get_activity_instance_overview(
    request: Request,  # request is actually required by the allow_exports decorator
    uid: str = ActivityInstanceUID,
    version: str
    | None = Query(
        None, description="Select specific version, omit to view latest version"
    ),
):
    activity_instance_service = ActivityInstanceService()
    return activity_instance_service.get_activity_instance_overview(
        activity_instance_uid=uid, version=version
    )


@router.get(
    "/{uid}/overview.cosmos",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get a COSMoS compatible representation of a specific activity instance",
    description="""
Returns detailed description about activity instance, including information about:
 - Activity subgroups
 - Activity groups
 - Activity instance
 - Activity instance class

State before:
 - an activity instance with uid must exist.

State after:
 - No change

Possible errors:
 - Invalid uid.
 """,
    responses={
        200: {"content": {"application/x-yaml": {}}},
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
# pylint: disable=unused-argument
def get_cosmos_activity_instance_overview(
    request: Request,  # request is actually required by the allow_exports decorator
    uid: str = ActivityInstanceUID,
):
    activity_instance_service = ActivityInstanceService()
    return YAMLResponse(
        activity_instance_service.get_cosmos_activity_instance_overview(
            activity_instance_uid=uid
        )
    )


@router.get(
    "/{uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="List version history for activity instance",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for activity instance.
 - The returned versions are ordered by start_date descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model=list[ActivityInstance],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity isntance with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_versions(uid: str = ActivityInstanceUID):
    activity_instance_service = ActivityInstanceService()
    return activity_instance_service.get_version_history(uid=uid)


@router.post(
    "",
    summary="Creates new activity instance.",
    dependencies=[rbac.LIBRARY_WRITE],
    description="""
State before:
 - The specified library allows creation of concepts (the 'is_editable' property of the library needs to be true).

Business logic:
 - New node is created for the activity instance with the set properties.
 - relationships to specified activity parent are created (as in the model)
 - relationships to specified activity instance class is created (as in the model)
 - The status of the new created version will be automatically set to 'Draft'.
 - The 'version' property of the new version will be automatically set to 0.1.
 - The 'change_description' property will be set automatically to 'Initial version'.

State after:
 - activity instance is created in status Draft and assigned an initial minor version number as 0.1.
 - Audit trail entry must be made with action of creating new Draft version.

Possible errors:
 - Invalid library or control terminology uid's specified.
""",
    response_model=ActivityInstance,
    status_code=201,
    responses={
        201: {
            "description": "Created - The activity instance was successfully created."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not exist.\n"
            "- The library does not allow to add new items.\n",
        },
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def create(
    activity_instance_create_input: ActivityInstanceCreateInput = Body(description=""),
):
    activity_instance_service = ActivityInstanceService()
    return activity_instance_service.create(
        concept_input=activity_instance_create_input
    )


@router.patch(
    "/{uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Update activity instance",
    description="""
State before:
 - uid must exist and activity instance must exist in status draft.
 - The activity instance must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).

Business logic:
 - If activity instance exist in status draft then attributes are updated.
- If the linked activity instance is updated, the relationships are updated to point to the activity instance value node.

State after:
 - attributes are updated for the activity instance.
 - Audit trail entry must be made with update of attributes.

Possible errors:
 - Invalid uid.

""",
    response_model=ActivityInstance,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity instance is not in draft status.\n"
            "- The activity instance had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity instance with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def edit(
    uid: str = ActivityInstanceUID,
    activity_instance_edit_input: ActivityInstanceEditInput = Body(description=""),
):
    activity_instance_service = ActivityInstanceService()
    return activity_instance_service.edit_draft(
        uid=uid, concept_edit_input=activity_instance_edit_input
    )


@router.post(
    "/{uid}/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Create a new version of an activity instance",
    description="""
State before:
 - uid must exist and the activity instance must be in status Final.
 
Business logic:
- The activity instance is changed to a draft state.

State after:
 - Activity instance changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.
 
Possible errors:
 - Invalid uid or status not Final.
""",
    response_model=ActivityInstance,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not allow to create activity instances.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The activity instance is not in final status.\n"
            "- The activity instance with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def create_new_version(
    uid: str = ActivityInstanceUID,
):
    activity_instance_service = ActivityInstanceService()
    return activity_instance_service.create_new_version(uid=uid)


@router.post(
    "/{uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approve draft version of an activity instance",
    description="""
State before:
 - uid must exist and activity instance must be in status Draft.
 
Business logic:
 - The latest 'Draft' version will remain the same as before.
 - The status of the new approved version will be automatically set to 'Final'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' version increased by +1.0.
 - The 'change_description' property will be set automatically 'Approved version'.
 
State after:
 - Activity instance changed status to Final and assigned a new major version number.
 - Audit trail entry must be made with action of approving to new Final version.
 
Possible errors:
 - Invalid uid or status not Draft.
    """,
    response_model=ActivityInstance,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity instance is not in draft status.\n"
            "- The library does not allow to approve activity instance.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity instance with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def approve(
    uid: str = ActivityInstanceUID,
):
    activity_instance_service = ActivityInstanceService()
    return activity_instance_service.approve(uid=uid)


@router.delete(
    "/{uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of an activity instance",
    description="""
State before:
 - uid must exist and activity instance must be in status Final.
 
Business logic:
 - The latest 'Final' version will remain the same as before.
 - The status will be automatically set to 'Retired'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.
 
State after:
 - Activity instance changed status to Retired.
 - Audit trail entry must be made with action of inactivating to retired version.
 
Possible errors:
 - Invalid uid or status not Final.
    """,
    response_model=ActivityInstance,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity instance is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity instance with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def inactivate(
    uid: str = ActivityInstanceUID,
):
    activity_instance_service = ActivityInstanceService()
    return activity_instance_service.inactivate_final(uid=uid)


@router.post(
    "/{uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of an activity instance",
    description="""
State before:
 - uid must exist and activity instance must be in status Retired.
 
Business logic:
 - The latest 'Retired' version will remain the same as before.
 - The status will be automatically set to 'Final'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - Activity instance changed status to Final.
 - An audit trail entry must be made with action of reactivating to final version.
 
Possible errors:
 - Invalid uid or status not Retired.
    """,
    response_model=ActivityInstance,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity instance is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity instance with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def reactivate(
    uid: str = ActivityInstanceUID,
):
    activity_instance_service = ActivityInstanceService()
    return activity_instance_service.reactivate_retired(uid=uid)


@router.delete(
    "/{uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Delete draft version of an activity instance",
    description="""
State before:
 - uid must exist
 - The concept must be in status Draft in a version less then 1.0 (never been approved).
 - The concept must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).
 
Business logic:
 - The draft concept is deleted.
 
State after:
 - Activity instance is successfully deleted.
 
Possible errors:
 - Invalid uid or status not Draft or exist in version 1.0 or above (previously been approved) or not in an editable library.
    """,
    response_model=None,
    status_code=204,
    responses={
        204: {
            "description": "No Content - The activity instance was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity instance is not in draft status.\n"
            "- The activity instance was already in final state or is in use.\n"
            "- The library does not allow to delete activity instance.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An activity instance with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def delete_activity_instance(
    uid: str = ActivityInstanceUID,
):
    activity_instance_service = ActivityInstanceService()
    activity_instance_service.soft_delete(uid=uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
