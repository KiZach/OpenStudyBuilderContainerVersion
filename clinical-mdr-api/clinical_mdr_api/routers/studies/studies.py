from typing import Any

from fastapi import APIRouter, Body, Path, Query, Response
from fastapi import status as response_status
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api import config, exceptions
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyCompactComponentEnum,
    StudyComponentEnum,
    StudyCopyComponentEnum,
    StudyStatus,
)
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.study_selections.study import (
    CompactStudy,
    StatusChangeDescription,
    Study,
    StudyCreateInput,
    StudyFieldAuditTrailEntry,
    StudyPatchRequestJsonModel,
    StudyPreferredTimeUnit,
    StudyPreferredTimeUnitInput,
    StudyProtocolTitle,
    StudySoaPreferences,
    StudySoaPreferencesInput,
    StudySubpartAuditTrail,
    StudySubpartCreateInput,
    StudySubpartReorderingInput,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers._generic_descriptions import (
    study_fields_audit_trail_section_description,
    study_section_description,
)
from clinical_mdr_api.services.studies.study import StudyService

# Prefixed with "/studies"
router = APIRouter()

StudyUID = Path(None, description="The unique id of the study.")


@router.get(
    "",
    dependencies=[rbac.STUDY_READ],
    summary="Returns all studies in their latest/newest version.",
    description=f"""
Allowed parameters include : filter on fields, sort by field name with sort direction, pagination

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=CustomPage[CompactStudy],
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
            "uid",
            "current_metadata.identification_metadata.clinical_programme_name",
            "current_metadata.identification_metadata.project_number",
            "current_metadata.identification_metadata.project_name",
            "current_metadata.identification_metadata.study_number",
            "current_metadata.identification_metadata.study_id",
            "current_metadata.identification_metadata.study_acronym",
            "current_metadata.identification_metadata.study_subpart_acronym",
            "current_metadata.study_description.study_title",
            "current_metadata.version_metadata.study_status",
            "current_metadata.version_metadata.version_timestamp",
            "current_metadata.version_metadata.version_author",
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
    include_sections: list[StudyCompactComponentEnum]
    | None = Query(
        None,
        description="""Optionally specify a list of sections to include from the StudyDefinition.

        Valid values are:

        - identification_metadata
        - version_metadata
        - study_description

        If no filters are specified, the default sections are returned.""",
    ),
    exclude_sections: list[StudyCompactComponentEnum]
    | None = Query(
        None,
        description="""Optionally specify a list of sections to exclude from the StudyDefinition.

        Valid values are:

        - identification_metadata
        - version_metadata
        - study_description

        If no filters are specified, the default sections are returned.""",
    ),
    has_study_objective: bool
    | None = Query(
        default=None,
        description="Optionally, filter studies based on the existence of related Study Objectives or not",
    ),
    has_study_footnote: bool
    | None = Query(
        default=None,
        description="Optionally, filter studies based on the existence of related Study SoA Footnotes or not",
    ),
    has_study_endpoint: bool
    | None = Query(
        default=None,
        description="Optionally, filter studies based on the existence of related Study Endpoints or not",
    ),
    has_study_criteria: bool
    | None = Query(
        default=None,
        description="Optionally, filter studies based on the existence of related Study Criteria or not",
    ),
    has_study_activity: bool
    | None = Query(
        default=None,
        description="Optionally, filter studies based on the existence of related Study Activities or not",
    ),
    has_study_activity_instruction: bool
    | None = Query(
        default=None,
        description="Optionally, filter studies based on the existence of related sTudy Activity Instruction or not",
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
    deleted: bool = Query(
        default=False,
        description="Indicates whether to return 'Active' Studies or 'Deleted' ones.",
    ),
) -> CustomPage[CompactStudy]:
    study_service = StudyService()
    results = study_service.get_all(
        include_sections=include_sections,
        exclude_sections=exclude_sections,
        has_study_footnote=has_study_footnote,
        has_study_objective=has_study_objective,
        has_study_endpoint=has_study_endpoint,
        has_study_criteria=has_study_criteria,
        has_study_activity=has_study_activity,
        has_study_activity_instruction=has_study_activity_instruction,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
        deleted=deleted,
    )

    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/headers",
    dependencies=[rbac.STUDY_READ],
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
    study_service = StudyService()
    return study_service.get_distinct_values_for_header(
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.post(
    "/{uid}/locks",
    dependencies=[rbac.STUDY_WRITE],
    summary="Locks a Study with specified uid",
    description="The Study is locked, which means that the LATEST_LOCKED relationship in the database is created."
    "The first locked version obtains number '1' and each next locked version "
    "is incremented number of the last locked version. "
    "The Study exists in the LOCKED state after successful lock",
    response_model=Study,
    status_code=201,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "ValidationException - The business rules were not met",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def lock(
    uid: str = StudyUID,
    lock_description: StatusChangeDescription = Body(
        description="The description of the locked version."
    ),
):
    study_service = StudyService()
    return study_service.lock(
        uid=uid, change_description=lock_description.change_description
    )


@router.delete(
    "/{uid}/locks",
    dependencies=[rbac.STUDY_WRITE],
    summary="Unlocks a Study with specified uid",
    description="The Study is unlocked, which means that the new DRAFT version of a Study is created"
    " and the Study exists in the DRAFT state.",
    response_model=Study,
    status_code=200,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "ValidationException - The business rules were not met",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def unlock(
    uid: str = StudyUID,
):
    study_service = StudyService()
    return study_service.unlock(uid=uid)


@router.post(
    "/{uid}/release",
    dependencies=[rbac.STUDY_WRITE],
    summary="Releases a Study with specified uid",
    description="The Study is released, which means that 'snapshot' of the Study is created in the database"
    "and the LATEST_RELEASED relationship is created that points to the created snapshot."
    "What's more the new LATEST_DRAFT node is created that describes the new Draft Study after releasing.",
    response_model=Study,
    status_code=201,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "ValidationException - The business rules were not met",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def release(
    uid: str = StudyUID,
    release_description: StatusChangeDescription = Body(
        description="The description of the release version."
    ),
):
    study_service = StudyService()
    return study_service.release(
        uid=uid, change_description=release_description.change_description
    )


@router.delete(
    "/{uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Deletes a Study",
    description="""
State before:
 - uid must exist
 - The Study must be in status Draft and it couldn't be locked before.

Business logic:
 - The draft Study is deleted.

State after:
 - Study is successfully deleted.

Possible errors:
 - Invalid uid or status not Draft or Study was previously locked.
    """,
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The Study was successfully deleted."},
        400: {
            "model": ErrorResponse,
            "description": "ValidationException - The business rules were not met",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def delete_activity(uid: str = StudyUID):
    study_service = StudyService()
    study_service.soft_delete(uid=uid)
    return Response(status_code=response_status.HTTP_204_NO_CONTENT)


@router.get(
    "/{uid}",
    dependencies=[rbac.STUDY_READ],
    summary="Returns the current state of a specific study definition identified by 'uid'.",
    description="If multiple request query parameters are used, then they need to match all at the same time"
    " (they are combined with the AND operation).",
    response_model=Study,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'uid'"
            " (and the specified date/time and/or status) wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get(
    uid: str = StudyUID,
    include_sections: list[StudyComponentEnum]
    | None = Query(None, description=study_section_description("include")),
    exclude_sections: list[StudyComponentEnum]
    | None = Query(None, description=study_section_description("exclude")),
    status: StudyStatus
    | None = Query(
        None,
        description="If specified, the last representation of the study in that status is returned (if existent)."
        "Valid values are: 'Released', 'Draft' or 'Locked'.",
    ),
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
):
    study_service = StudyService()
    study_definition = study_service.get_by_uid(
        uid=uid,
        include_sections=include_sections,
        exclude_sections=exclude_sections,
        at_specified_date_time=None,
        status=status,
        study_value_version=study_value_version,
    )
    return study_definition


@router.patch(
    "/{uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Request to change some aspects (parts) of a specific study definition identified by 'uid'.",
    description="The request to change (some aspect) of the state of current aggregate. "
    "There are some special cases and considerations:\n"
    "* patching study_status in current_metadata.version_metadata is considered as the request for"
    "  locking/unlocking/releasing the study definition and should not be combined with any other"
    "  changes\n"
    "* there are many business rules that apply in different patching scenario or state of the"
    "  study definition. If request is not compliant it will fail with 403 and response body"
    "  will (hopefully) explain what is wrong.\n"
    "* the method may be invoked with dry=true query param. if that's the case it wokrs the same"
    "  except that any change made to the resource are not persisted (however all validations are"
    "  performed.\n",
    response_model=Study,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Some application/business rules forbid to process the request. Expect more detailed"
            " information in response body.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def patch(
    uid: str = StudyUID,
    dry: bool = Query(
        False,
        description="If specified the operation does full validation and returns either 200 or 403 but"
        "nothing is persisted.",
    ),
    study_patch_request: StudyPatchRequestJsonModel = Body(
        description="The request with the structure similar to the GET /{uid} response. Carrying only those"
        "fields requested to change.",
    ),
) -> Study:
    study_service = StudyService()
    if study_patch_request is None:
        raise exceptions.ValidationException("No data to patch was provided.")
    response = study_service.patch(uid, dry, study_patch_request)
    return response


@router.get(
    "/{uid}/snapshot-history",
    dependencies=[rbac.STUDY_READ],
    summary="Returns the history of study snapshot definitions",
    description="It returns the history of changes made to the specified Study Definition Snapshot."
    "The returned history should reflect HAS_VERSION relationships in the database between StudyRoot and StudyValue nodes",
    response_model=CustomPage[CompactStudy],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'uid'"
            " (and the specified date/time and/or status) wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_snapshot_history(
    uid: str = StudyUID,  # ,
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
    study_service = StudyService()
    snapshot_history = study_service.get_study_snapshot_history(
        study_uid=uid,
        page_number=page_number,
        page_size=page_size,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
        total_count=total_count,
    )
    return CustomPage.create(
        items=snapshot_history.items,
        total=snapshot_history.total,
        page=page_number,
        size=page_size,
    )


@router.get(
    "/{uid}/fields-audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="Returns the audit trail for the fields of a specific study definition identified by 'uid'.",
    description="Actions on the study are grouped by date of edit."
    "Optionally select which subset of fields should be reflected in the audit trail.",
    response_model=list[StudyFieldAuditTrailEntry],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'uid'"
            " wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_fields_audit_trail(
    uid: str = StudyUID,  # ,
    include_sections: list[StudyComponentEnum]
    | None = Query(
        None, description=study_fields_audit_trail_section_description("include")
    ),
    exclude_sections: list[StudyComponentEnum]
    | None = Query(
        None, description=study_fields_audit_trail_section_description("exclude")
    ),
):
    study_service = StudyService()
    study_fields_audit_trail = study_service.get_fields_audit_trail_by_uid(
        uid=uid, include_sections=include_sections, exclude_sections=exclude_sections
    )
    return study_fields_audit_trail


@router.get(
    "/{uid}/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="Returns the audit trail for the subparts of a specific study definition identified by 'uid'.",
    description="Actions on the study are grouped by date of edit. Optionally select which subset of fields should be reflected in the audit trail.",
    response_model=list[StudySubpartAuditTrail],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'uid'"
            " wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_study_subpart_audit_trail(uid: str = StudyUID, is_subpart: bool = False):
    study_service = StudyService()
    return study_service.get_subpart_audit_trail_by_uid(uid=uid, is_subpart=is_subpart)


@router.post(
    "",
    dependencies=[rbac.STUDY_WRITE],
    summary="Creates a new Study Definition.",
    description="""
If the request succeeds new DRAFT Study Definition will be with initial identification data as provided in 
request body with new unique uid generated and returned in response body.
        """,
    response_model=Study,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        201: {"description": "Created - The study was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Some application/business rules forbid to process the request. Expect more detailed"
            " information in response body.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def create(
    study_create_input: StudySubpartCreateInput
    | StudyCreateInput = Body(
        description="Related parameters of the objective that shall be created."
    ),
) -> Study:
    study_service = StudyService()
    return study_service.create(study_create_input)


@router.get(
    "/{uid}/protocol-title",
    dependencies=[rbac.STUDY_READ],
    summary="Retrieve all information related to Protocol Title",
    description="""
State before:
 - Study-uid must exist

Business logic:
 - Retrieve Study title, Universal Trial Number, EudraCT number, IND number, Study phase fields
 - Retrieve all names of study compounds associated to {uid} and where type of treatment is equal to Investigational Product

State after:
 - No change
""",
    response_model=StudyProtocolTitle,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'uid'"
            " wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_protocol_title(
    uid: str = StudyUID,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
):
    study_service = StudyService()
    return study_service.get_protocol_title(
        uid=uid, study_value_version=study_value_version
    )


@router.patch(
    "/{uid}/copy-component",
    dependencies=[rbac.STUDY_WRITE],
    summary="Copy study form from another study",
    description="""
State before:
 - uid must exist
 - reference_study_uid must exist

Business logic:
 - if overwrite is set to false, then the projection of the copy will be returned
 - if overwrite is set to true, then the component referenced as a component_to_copy will be copied
 from the study referenced by reference_study_uid to the study referenced by uid.

State after:
 - The specific form is copied or projected into a study referenced by uid 'uid'.
""",
    response_model=Study,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'uid'"
            " wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def copy_simple_form_from_another_study(
    uid: str = StudyUID,
    reference_study_uid: str = Query(
        ..., description="The uid of the study to copy component from"
    ),
    component_to_copy: StudyCopyComponentEnum = Query(
        ..., description="The uid of the study to copy component from"
    ),
    overwrite: bool = Query(
        False,
        description="Indicates whether to overwrite the component of the study referenced by the uid"
        "or return a projection",
    ),
):
    study_service = StudyService()
    return study_service.copy_component_from_another_study(
        uid=uid,
        reference_study_uid=reference_study_uid,
        component_to_copy=component_to_copy,
        overwrite=overwrite,
    )


@router.get(
    "/{uid}/time-units",
    dependencies=[rbac.STUDY_READ],
    summary="Gets a study preferred time unit",
    response_model=StudyPreferredTimeUnit,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study or unit definition with the specified 'uid'"
            " wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_preferred_time_unit(
    uid: str = StudyUID,
    for_protocol_soa: bool = Query(
        False,
        description="Whether the preferred time unit is associated with Protocol SoA or not.",
    ),
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
):
    study_service = StudyService()
    return study_service.get_study_preferred_time_unit(
        study_uid=uid,
        for_protocol_soa=for_protocol_soa,
        study_value_version=study_value_version,
    )


@router.patch(
    "/{uid}/time-units",
    dependencies=[rbac.STUDY_WRITE],
    summary="Edits a study preferred time unit",
    response_model=StudyPreferredTimeUnit,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study or unit definition with the specified 'uid'"
            " wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def patch_preferred_time_unit(
    uid: str = StudyUID,
    preferred_time_unit_input: StudyPreferredTimeUnitInput = Body(
        ..., description="Data needed to create a study preferred time unit"
    ),
    for_protocol_soa: bool = Query(
        False,
        description="Whether the preferred time unit is associated with Protocol Soa or not.",
    ),
):
    study_service = StudyService()
    return study_service.patch_study_preferred_time_unit(
        study_uid=uid,
        unit_definition_uid=preferred_time_unit_input.unit_definition_uid,
        for_protocol_soa=for_protocol_soa,
    )


@router.patch(
    "/{uid}/order",
    dependencies=[rbac.STUDY_WRITE],
    summary="Reorder Study Subparts within a Study Parent Part",
    description="",
    response_model=list[Study],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'uid'"
            " wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def reorder_study_subparts(
    uid: str = StudyUID,
    study_subpart_reordering_input: StudySubpartReorderingInput
    | None = Body(
        None,
        description="Specify the Study Subpart to be reordered. "
        "If provided, the specified Study Subpart will be reordered; otherwise, any gaps in the order will be filled.",
    ),
):
    study_service = StudyService()
    return study_service.reorder_study_subparts(
        study_parent_part_uid=uid,
        study_subpart_reordering_input=study_subpart_reordering_input,
    )


@router.get(
    "/{uid}/soa-preferences",
    dependencies=[rbac.STUDY_READ],
    summary="Get study SoA preferences",
    response_model_by_alias=False,
    response_model=StudySoaPreferences,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - study with the specified 'uid' does not exist or has no SoA preferences set",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_soa_preferences(
    uid: str = StudyUID,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> StudySoaPreferences:
    study_service = StudyService()
    return study_service.get_study_soa_preferences(
        study_uid=uid,
        study_value_version=study_value_version,
    )


@router.patch(
    "/{uid}/soa-preferences",
    dependencies=[rbac.STUDY_WRITE],
    summary="Update study SoA preferences",
    response_model=StudySoaPreferences,
    response_model_by_alias=False,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - study with the specified 'uid' does not exist",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def patch_soa_preferences(
    uid: str = StudyUID,
    soa_preferences: StudySoaPreferencesInput = Body(
        ..., description="SoA preferences data"
    ),
):
    study_service = StudyService()
    return study_service.patch_study_soa_preferences(
        study_uid=uid,
        soa_preferences=soa_preferences,
    )
