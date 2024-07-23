from typing import Any

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api import config
from clinical_mdr_api.models import (
    OdmItem,
    OdmItemActivityPostInput,
    OdmItemPatchInput,
    OdmItemPostInput,
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
from clinical_mdr_api.services.concepts.odms.odm_items import OdmItemService

# Prefixed with "/concepts/odms/items"
router = APIRouter()

# Argument definitions
OdmItemUID = Path(None, description="The unique id of the ODM Item.")


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Return every variable related to the selected status and version of the ODM Items",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    response_model=CustomPage[OdmItem],
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
            "aliases",
            "codelist",
            "comment",
            "datatype",
            "length",
            "significant_digits",
            "origin",
            "prompt",
            "descriptions=descriptions.description",
            "instructions=descriptions.instruction",
            "languages=descriptions.language",
            "instructions=descriptions.instruction",
            "sponsor_instructions=descriptions.sponsor_instruction",
            "repeating",
            "start_date",
            "end_date",
            "effective_date",
            "retired_date",
            "end_date",
            "status",
            "version",
            "sas_field_name",
            "sds_var_name",
            "terms",
            "unit_definitions",
            "sas_dataset_name",
            "activity",
            "vendor_attributes",
            "vendor_element_attributes",
            "vendor_elements",
        ],
        "text/xml": [
            "uid",
            "oid",
            "library_name",
            "name",
            "aliases",
            "codelist",
            "comment",
            "datatype",
            "length",
            "significant_digits",
            "origin",
            "prompt",
            "descriptions",
            "repeating",
            "start_date",
            "end_date",
            "effective_date",
            "retired_date",
            "end_date",
            "status",
            "version",
            "sas_field_name",
            "sds_var_name",
            "terms",
            "unit_definitions",
            "sas_dataset_name",
            "activity",
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
def get_all_odm_items(
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
    odm_item_service = OdmItemService()
    results = odm_item_service.get_all_concepts(
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
    odm_item_service = OdmItemService()
    return odm_item_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.get(
    "/item-groups",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get all ODM Items that belongs to an ODM Item Group",
    description="",
    response_model=list[OdmElementWithParentUid],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_odm_items_that_belongs_to_item_group():
    odm_item_service = OdmItemService()
    return odm_item_service.get_items_that_belongs_to_item_groups()


@router.get(
    "/{uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get details on a specific ODM Item (in a specific version)",
    description="",
    response_model=OdmItem,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_odm_item(uid: str = OdmItemUID):
    odm_item_service = OdmItemService()
    return odm_item_service.get_by_uid(uid=uid)


@router.get(
    "/{uid}/relationships",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get UIDs of a specific ODM Item's relationships",
    description="",
    response_model=dict,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_active_relationships(uid: str = OdmItemUID):
    odm_item_service = OdmItemService()
    return odm_item_service.get_active_relationships(uid=uid)


@router.get(
    "/{uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="List version history for ODM Item",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for ODM Items.
 - The returned versions are ordered by start_date descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model=list[OdmItem],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_odm_item_versions(uid: str = OdmItemUID):
    odm_item_service = OdmItemService()
    return odm_item_service.get_version_history(uid=uid)


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates a new Item in 'Draft' status with version 0.1",
    description="",
    response_model=OdmItem,
    status_code=201,
    responses={
        201: {"description": "Created - The ODM Item was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not exist.\n"
            "- The library does not allow to add new items.\n",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def create_odm_item(odm_item_create_input: OdmItemPostInput = Body(description="")):
    odm_item_service = OdmItemService()
    return odm_item_service.create_with_relations(concept_input=odm_item_create_input)


@router.patch(
    "/{uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Update ODM Item",
    description="",
    response_model=OdmItem,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item is not in draft status.\n"
            "- The ODM Item had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def edit_odm_item(
    uid: str = OdmItemUID,
    odm_item_edit_input: OdmItemPatchInput = Body(description=""),
):
    odm_item_service = OdmItemService()
    return odm_item_service.update_with_relations(
        uid=uid, concept_edit_input=odm_item_edit_input
    )


@router.post(
    "/{uid}/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Create a new version of ODM Item",
    description="""
State before:
 - uid must exist and the ODM Item must be in status Final.

Business logic:
- The ODM Item is changed to a draft state.

State after:
 - ODM Item changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.

Possible errors:
 - Invalid uid or status not Final.
""",
    response_model=OdmItem,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not allow to create ODM Items.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The ODM Item is not in final status.\n"
            "- The ODM Item with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def create_odm_item_version(uid: str = OdmItemUID):
    odm_item_service = OdmItemService()
    return odm_item_service.create_new_version(uid=uid)


@router.post(
    "/{uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approve draft version of ODM Item",
    description="",
    response_model=OdmItem,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item is not in draft status.\n"
            "- The library does not allow to approve ODM Item.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def approve_odm_item(uid: str = OdmItemUID):
    odm_item_service = OdmItemService()
    return odm_item_service.approve(uid=uid)


@router.delete(
    "/{uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of ODM Item",
    description="",
    response_model=OdmItem,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def inactivate_odm_item(uid: str = OdmItemUID):
    odm_item_service = OdmItemService()
    return odm_item_service.inactivate_final(uid=uid)


@router.post(
    "/{uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of a ODM Item",
    description="",
    response_model=OdmItem,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def reactivate_odm_item(uid: str = OdmItemUID):
    odm_item_service = OdmItemService()
    return odm_item_service.reactivate_retired(uid=uid)


@router.post(
    "/{uid}/activities",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Add an activity to the ODM Item.",
    description="",
    response_model=OdmItem,
    status_code=201,
    responses={
        201: {
            "description": "Created - The activity was successfully added to the ODM Item."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def add_activity_to_odm_item(
    uid: str = OdmItemUID,
    override: bool = Query(
        False,
        description="If true, the existing activity relationship will be replaced with the provided activity relationship.",
    ),
    odm_item_activity_post_input: OdmItemActivityPostInput = Body(description=""),
):
    odm_item_service = OdmItemService()
    return odm_item_service.add_activity(
        uid=uid,
        odm_item_activity_post_input=odm_item_activity_post_input,
        override=override,
    )


@router.post(
    "/{uid}/vendor-elements",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Adds ODM Vendor Elements to the ODM Item.",
    description="",
    response_model=OdmItem,
    status_code=201,
    responses={
        201: {
            "description": "Created - The ODM Vendor Elements were successfully added to the ODM Item."
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
def add_vendor_elements_to_odm_item(
    uid: str = OdmItemUID,
    override: bool = Query(
        False,
        description="If true, all existing ODM Vendor Element relationships will be replaced with the provided ODM Vendor Element relationships.",
    ),
    odm_vendor_relation_post_input: list[OdmVendorElementRelationPostInput] = Body(
        description=""
    ),
):
    odm_item_service = OdmItemService()
    return odm_item_service.add_vendor_elements(
        uid=uid,
        odm_vendor_relation_post_input=odm_vendor_relation_post_input,
        override=override,
    )


@router.post(
    "/{uid}/vendor-attributes",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Adds ODM Vendor Attributes to the ODM Item.",
    description="",
    response_model=OdmItem,
    status_code=201,
    responses={
        201: {
            "description": "Created - The ODM Vendor Attributes were successfully added to the ODM Item."
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
def add_vendor_attributes_to_odm_item(
    uid: str = OdmItemUID,
    override: bool = Query(
        False,
        description="""If true, all existing ODM Vendor Attribute relationships will
        be replaced with the provided ODM Vendor Attribute relationships.""",
    ),
    odm_vendor_relation_post_input: list[OdmVendorRelationPostInput] = Body(
        description=""
    ),
):
    odm_item_service = OdmItemService()
    return odm_item_service.add_vendor_attributes(
        uid=uid,
        odm_vendor_relation_post_input=odm_vendor_relation_post_input,
        override=override,
    )


@router.post(
    "/{uid}/vendor-element-attributes",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Adds ODM Vendor Element attributes to the ODM Item.",
    description="",
    response_model=OdmItem,
    status_code=201,
    responses={
        201: {
            "description": "Created - The ODM Vendor Element attributes were successfully added to the ODM Item."
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
def add_vendor_element_attributes_to_odm_item(
    uid: str = OdmItemUID,
    override: bool = Query(
        False,
        description="""If true, all existing ODM Vendor Element attribute relationships will
        be replaced with the provided ODM Vendor Element attribute relationships.""",
    ),
    odm_vendor_relation_post_input: list[OdmVendorRelationPostInput] = Body(
        description=""
    ),
):
    odm_item_service = OdmItemService()
    return odm_item_service.add_vendor_element_attributes(
        uid=uid,
        odm_vendor_relation_post_input=odm_vendor_relation_post_input,
        override=override,
    )


@router.post(
    "/{uid}/vendors",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Manages all ODM Vendors by replacing existing ODM Vendors by provided ODM Vendors.",
    description="",
    response_model=OdmItem,
    status_code=201,
    responses={
        201: {
            "description": "Created - The ODM Vendors were successfully added to the ODM Item."
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
def manage_vendors_of_odm_item_group(
    uid: str = OdmItemUID,
    odm_vendors_post_input: OdmVendorsPostInput = Body(description=""),
):
    odm_item_group_service = OdmItemService()
    return odm_item_group_service.manage_vendors(
        uid=uid, odm_vendors_post_input=odm_vendors_post_input
    )


@router.delete(
    "/{uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Delete draft version of ODM Item",
    description="",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The ODM Item was successfully deleted."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item is not in draft status.\n"
            "- The ODM Item was already in final state or is in use.\n"
            "- The library does not allow to delete ODM Item.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An ODM Item with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def delete_odm_item(uid: str = OdmItemUID):
    odm_item_service = OdmItemService()
    odm_item_service.soft_delete(uid=uid)
