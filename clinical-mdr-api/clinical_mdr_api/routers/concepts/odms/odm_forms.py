from typing import Any

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api import config
from clinical_mdr_api.models import (
    OdmForm,
    OdmFormActivityGroupPostInput,
    OdmFormItemGroupPostInput,
    OdmFormPatchInput,
    OdmFormPostInput,
)
from clinical_mdr_api.models.concepts.odms.odm_common_models import (
    OdmElementWithParentUid,
    OdmVendorElementRelationPostInput,
    OdmVendorRelationPostInput,
    OdmVendorsPostInput,
)
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.concepts.odms.odm_forms import OdmFormService

# Prefixed with "/concepts/odms/forms"
router = APIRouter()

# Argument definitions
OdmFormUID = Path(None, description="The unique id of the ODM Form.")


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Return every variable related to the selected status and version of the ODM Forms",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    response_model=CustomPage[OdmForm],
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
            "oid",
            "library_name",
            "name",
            "descriptions=descriptions.description",
            "instructions=descriptions.instruction",
            "languages=descriptions.language",
            "instructions=descriptions.instruction",
            "sponsor_instructions=descriptions.sponsor_instruction",
            "forms",
            "start_date",
            "end_date",
            "effective_date",
            "retired_date",
            "end_date",
            "item_groups",
            "aliases",
            "activity_groups",
            "status",
            "version",
            "repeating",
            "scope",
            "sdtm_version",
            "vendor_attributes",
            "vendor_element_attributes",
            "vendor_elements",
        ],
        "text/xml": [
            "uid",
            "oid",
            "library_name",
            "name",
            "descriptions",
            "forms",
            "start_date",
            "end_date",
            "effective_date",
            "retired_date",
            "end_date",
            "item_groups",
            "aliases",
            "activity_groups",
            "status",
            "version",
            "repeating",
            "scope",
            "sdtm_version",
            "vendor_attributes",
            "vendor_element_attributes",
            "vendor_elements",
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
def get_all_odm_forms(
    request: Request,  # request is actually required by the allow_exports decorator
    library: str | None = Query(None),
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
    odm_form_service = OdmFormService()
    results = odm_form_service.get_all_concepts(
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
    odm_form_service = OdmFormService()
    return odm_form_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.get(
    "/study-events",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get all ODM Forms that belongs to an ODM Study Event",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    response_model=list[OdmElementWithParentUid],
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
            "oid",
            "library_name",
            "name",
            "description",
            "forms",
            "start_date",
            "end_date",
            "effective_date",
            "retired_date",
            "end_date",
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
def get_odm_form_that_belongs_to_study_event(
    request: Request,  # request is actually required by the allow_exports decorator
):
    odm_form_service = OdmFormService()
    return odm_form_service.get_forms_that_belongs_to_study_event()


@router.get(
    "/{uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get details on a specific ODM Form (in a specific version)",
    description="",
    response_model=OdmForm,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_odm_form(uid: str = OdmFormUID):
    odm_form_service = OdmFormService()
    return odm_form_service.get_by_uid(uid=uid)


@router.get(
    "/{uid}/relationships",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get UIDs of a specific ODM Form's relationships",
    description="",
    response_model=dict,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_active_relationships(uid: str = OdmFormUID):
    odm_form_service = OdmFormService()
    return odm_form_service.get_active_relationships(uid=uid)


@router.get(
    "/{uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="List version history for ODM Form",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for ODM Forms.
 - The returned versions are ordered by start_date descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model=list[OdmForm],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Form with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_odm_form_versions(uid: str = OdmFormUID):
    odm_form_service = OdmFormService()
    return odm_form_service.get_version_history(uid=uid)


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates a new Form in 'Draft' status with version 0.1",
    description="",
    response_model=OdmForm,
    status_code=201,
    responses={
        201: {"description": "Created - The ODM Form was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not exist.\n"
            "- The library does not allow to add new items.\n",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def create_odm_form(
    odm_form_create_input: OdmFormPostInput = Body(description=""),
):
    odm_form_service = OdmFormService()

    return odm_form_service.create_with_relations(concept_input=odm_form_create_input)


@router.patch(
    "/{uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Update ODM Form",
    description="",
    response_model=OdmForm,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Form is not in draft status.\n"
            "- The ODM Form had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Form with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def edit_odm_form(
    uid: str = OdmFormUID,
    odm_form_edit_input: OdmFormPatchInput = Body(description=""),
):
    odm_form_service = OdmFormService()
    return odm_form_service.update_with_relations(
        uid=uid, concept_edit_input=odm_form_edit_input
    )


@router.post(
    "/{uid}/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Create a new version of ODM Form",
    description="""
State before:
 - uid must exist and the ODM Form must be in status Final.

Business logic:
- The ODM Form is changed to a draft state.

State after:
 - ODM Form changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.

Possible errors:
 - Invalid uid or status not Final.
""",
    response_model=OdmForm,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not allow to create ODM Forms.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The ODM Form is not in final status.\n"
            "- The ODM Form with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def create_odm_form_version(uid: str = OdmFormUID):
    odm_form_service = OdmFormService()
    return odm_form_service.create_new_version(uid=uid)


@router.post(
    "/{uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approve draft version of ODM Form",
    description="",
    response_model=OdmForm,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Form is not in draft status.\n"
            "- The library does not allow to approve ODM Form.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Form with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def approve_odm_form(uid: str = OdmFormUID):
    odm_form_service = OdmFormService()
    return odm_form_service.approve(uid=uid)


@router.delete(
    "/{uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of ODM Form",
    description="",
    response_model=OdmForm,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Form is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Form with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def inactivate_odm_form(uid: str = OdmFormUID):
    odm_form_service = OdmFormService()
    return odm_form_service.inactivate_final(uid=uid)


@router.post(
    "/{uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of a ODM Form",
    description="",
    response_model=OdmForm,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Form is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Form with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def reactivate_odm_form(uid: str = OdmFormUID):
    odm_form_service = OdmFormService()
    return odm_form_service.reactivate_retired(uid=uid)


@router.post(
    "/{uid}/activity-groups",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Adds activity groups to the ODM Form.",
    description="",
    response_model=OdmForm,
    status_code=201,
    responses={
        201: {
            "description": "Created - The activity groups were successfully added to the ODM Form."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity groups with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def add_activity_groups_to_odm_form(
    uid: str = OdmFormUID,
    override: bool = Query(
        False,
        description="If true, all existing activity group relationships will be replaced with the provided activity group relationships.",
    ),
    odm_form_activity_group_post_input: list[OdmFormActivityGroupPostInput] = Body(
        description=""
    ),
):
    odm_form_service = OdmFormService()
    return odm_form_service.add_activity_groups(
        uid=uid,
        odm_form_activity_group_post_input=odm_form_activity_group_post_input,
        override=override,
    )


@router.post(
    "/{uid}/item-groups",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Adds item groups to the ODM Form.",
    description="",
    response_model=OdmForm,
    status_code=201,
    responses={
        201: {
            "description": "Created - The item groups were successfully added to the ODM Form."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The item groups with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def add_item_groups_to_odm_form(
    uid: str = OdmFormUID,
    override: bool = Query(
        False,
        description="If true, all existing item group relationships will be replaced with the provided item group relationships.",
    ),
    odm_form_item_group_post_input: list[OdmFormItemGroupPostInput] = Body(
        description=""
    ),
):
    odm_form_service = OdmFormService()
    return odm_form_service.add_item_groups(
        uid=uid,
        odm_form_item_group_post_input=odm_form_item_group_post_input,
        override=override,
    )


@router.post(
    "/{uid}/vendor-elements",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Adds ODM Vendor Elements to the ODM Form.",
    description="",
    response_model=OdmForm,
    status_code=201,
    responses={
        201: {
            "description": "Created - The ODM Vendor Elements were successfully added to the ODM Form."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Vendor Elements with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def add_vendor_elements_to_odm_form(
    uid: str = OdmFormUID,
    override: bool = Query(
        False,
        description="If true, all existing ODM Vendor Element relationships will be replaced with the provided ODM Vendor Element relationships.",
    ),
    odm_vendor_relation_post_input: list[OdmVendorElementRelationPostInput] = Body(
        description=""
    ),
):
    odm_form_service = OdmFormService()
    return odm_form_service.add_vendor_elements(
        uid=uid,
        odm_vendor_relation_post_input=odm_vendor_relation_post_input,
        override=override,
    )


@router.post(
    "/{uid}/vendor-attributes",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Adds ODM Vendor Attributes to the ODM Form.",
    description="",
    response_model=OdmForm,
    status_code=201,
    responses={
        201: {
            "description": "Created - The ODM Vendor Attributes were successfully added to the ODM Form."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Vendor Attributes with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def add_vendor_attributes_to_odm_form(
    uid: str = OdmFormUID,
    override: bool = Query(
        False,
        description="""If true, all existing ODM Vendor Attribute relationships will
        be replaced with the provided ODM Vendor Attribute relationships.""",
    ),
    odm_vendor_relation_post_input: list[OdmVendorRelationPostInput] = Body(
        description=""
    ),
):
    odm_form_service = OdmFormService()
    return odm_form_service.add_vendor_attributes(
        uid=uid,
        odm_vendor_relation_post_input=odm_vendor_relation_post_input,
        override=override,
    )


@router.post(
    "/{uid}/vendor-element-attributes",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Adds ODM Vendor Element attributes to the ODM Form.",
    description="",
    response_model=OdmForm,
    status_code=201,
    responses={
        201: {
            "description": "Created - The ODM Vendor Element attributes were successfully added to the ODM Form."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Vendor Element attributes with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def add_vendor_element_attributes_to_odm_form(
    uid: str = OdmFormUID,
    override: bool = Query(
        False,
        description="""If true, all existing ODM Vendor Element attribute relationships
        will be replaced with the provided ODM Vendor Element attribute relationships.""",
    ),
    odm_vendor_relation_post_input: list[OdmVendorRelationPostInput] = Body(
        description=""
    ),
):
    odm_form_service = OdmFormService()
    return odm_form_service.add_vendor_element_attributes(
        uid=uid,
        odm_vendor_relation_post_input=odm_vendor_relation_post_input,
        override=override,
    )


@router.post(
    "/{uid}/vendors",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Manages all ODM Vendors by replacing existing ODM Vendors by provided ODM Vendors.",
    description="",
    response_model=OdmForm,
    status_code=201,
    responses={
        201: {
            "description": "Created - The ODM Vendors were successfully added to the ODM Form."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Vendors with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def manage_vendors_of_odm_form(
    uid: str = OdmFormUID,
    odm_vendors_post_input: OdmVendorsPostInput = Body(description=""),
):
    odm_form_service = OdmFormService()
    return odm_form_service.manage_vendors(
        uid=uid, odm_vendors_post_input=odm_vendors_post_input
    )


@router.delete(
    "/{uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Delete draft version of ODM Form",
    description="",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The ODM Form was successfully deleted."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Form is not in draft status.\n"
            "- The ODM Form was already in final state or is in use.\n"
            "- The library does not allow to delete ODM Form.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An ODM Form with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def delete_odm_form(uid: str = OdmFormUID):
    odm_form_service = OdmFormService()
    odm_form_service.soft_delete(uid=uid)
