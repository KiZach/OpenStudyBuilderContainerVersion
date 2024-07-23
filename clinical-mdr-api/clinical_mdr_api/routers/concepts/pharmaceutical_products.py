"""pharmaceutical_products router"""
from typing import Any

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api import config
from clinical_mdr_api.models.concepts.pharmaceutical_product import (
    PharmaceuticalProduct,
    PharmaceuticalProductCreateInput,
    PharmaceuticalProductEditInput,
)
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.concepts.pharmaceutical_products_service import (
    PharmaceuticalProductService,
)

# Prefixed with "/concepts"
router = APIRouter()

PharmaceuticalProductUID = Path(
    None, description="The unique id of the pharmaceutical product"
)


@router.get(
    "/pharmaceutical-products",
    dependencies=[rbac.LIBRARY_READ],
    summary="List all pharmaceutical products (for a given library)",
    description=f"""
State before:
 - The library must exist (if specified)

Business logic:
 - List all pharmaceutical products in their latest version, including properties derived from linked control terminology.

State after:
 - No change

Possible errors:
 - Invalid library name specified.
 
{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=CustomPage[PharmaceuticalProduct],
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
            "external_id",
            "dosage_forms=dosage_forms.name",
            "routes_of_administration=routes_of_administration.name",
            "formulations",
            "start_date",
            "version",
            "status",
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
def get_pharmaceutical_products(
    request: Request,  # request is actually required by the allow_exports decorator
    library: str | None = Query(None, description=_generic_descriptions.LIBRARY_NAME),
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
    pharmaceutical_product_service = PharmaceuticalProductService()
    results = pharmaceutical_product_service.get_all_concepts(
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
    "/pharmaceutical-products/headers",
    dependencies=[rbac.LIBRARY_READ],
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
    library: str | None = Query(None, description=_generic_descriptions.LIBRARY_NAME),
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
    pharmaceutical_product_service = PharmaceuticalProductService()
    return pharmaceutical_product_service.get_distinct_values_for_header(
        library=library,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.get(
    "/pharmaceutical-products/{uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get details on a specific pharmaceutical product (in a specific version)",
    description="""
Possible errors:
 - Invalid uid, at_specified_date_time, status or version.
 """,
    response_model=PharmaceuticalProduct,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_activity(
    uid: str = PharmaceuticalProductUID,
):
    pharmaceutical_product_service = PharmaceuticalProductService()
    return pharmaceutical_product_service.get_by_uid(uid=uid)


@router.get(
    "/pharmaceutical-products/{uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="List version history for pharmaceutical products",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for pharmaceutical products.
 - The returned versions are ordered by start_date descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model=list[PharmaceuticalProduct],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The pharmaceutical product with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_versions(
    uid: str = PharmaceuticalProductUID,
):
    pharmaceutical_product_service = PharmaceuticalProductService()
    return pharmaceutical_product_service.get_version_history(uid=uid)


@router.post(
    "/pharmaceutical-products",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates new pharmaceutical product.",
    description="""
State before:
 - The specified library allows creation of concepts (the 'is_editable' property of the library needs to be true).
 - The specified CT term uids must exist, and the term names are in a final state.

Business logic:
 - New node is created for the pharmaceutical product with the set properties.
 - relationships to specified control terminology are created (as in the model).
 - relationships to specified activity parent are created (as in the model)
 - The status of the new created version will be automatically set to 'Draft'.
 - The 'version' property of the new version will be automatically set to 0.1.
 - The 'change_description' property will be set automatically to 'Initial version'.

State after:
 - pharmaceutical product is created in status Draft and assigned an initial minor version number as 0.1.
 - Audit trail entry must be made with action of creating new Draft version.

Possible errors:
 - Invalid library or control terminology uid's specified.
""",
    response_model=PharmaceuticalProduct,
    status_code=201,
    responses={
        201: {
            "description": "Created - The pharmaceutical product was successfully created."
        },
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
    pharmaceutical_product_create_input: PharmaceuticalProductCreateInput = Body(
        description=""
    ),
):
    pharmaceutical_product_service = PharmaceuticalProductService()
    return pharmaceutical_product_service.create(
        concept_input=pharmaceutical_product_create_input
    )


@router.patch(
    "/pharmaceutical-products/{uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Update pharmaceutical product",
    description="""
State before:
 - uid must exist and pharmaceutical product must exist in status draft.
 - The pharmaceutical product must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).

Business logic:
 - If pharmaceutical product exist in status draft then attributes are updated.
 - If links to CT are selected or updated then relationships are made to CTTermRoots.
- If the linked pharmaceutical product is updated, the relationships are updated to point to the pharmaceutical product value node.

State after:
 - attributes are updated for the pharmaceutical product.
 - Audit trail entry must be made with update of attributes.

Possible errors:
 - Invalid uid.

""",
    response_model=PharmaceuticalProduct,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The pharmaceutical product is not in draft status.\n"
            "- The pharmaceutical product had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The pharmaceutical product with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def edit(
    uid: str = PharmaceuticalProductUID,
    pharmaceutical_product_edit_input: PharmaceuticalProductEditInput = Body(
        description=""
    ),
):
    pharmaceutical_product_service = PharmaceuticalProductService()
    return pharmaceutical_product_service.edit_draft(
        uid=uid, concept_edit_input=pharmaceutical_product_edit_input
    )


@router.post(
    "/pharmaceutical-products/{uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approve draft version of a pharmaceutical product",
    description="""
State before:
 - uid must exist and pharmaceutical product must be in status Draft.
 
Business logic:
 - The latest 'Draft' version will remain the same as before.
 - The status of the new approved version will be automatically set to 'Final'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' version increased by +1.0.
 - The 'change_description' property will be set automatically to 'Approved version'.
 
State after:
 - PharmaceuticalProduct changed status to Final and assigned a new major version number.
 - Audit trail entry must be made with action of approving to new Final version.
 
Possible errors:
 - Invalid uid or status not Draft.
    """,
    response_model=PharmaceuticalProduct,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The pharmaceutical product is not in draft status.\n"
            "- The library does not allow pharmaceutical product approval.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The pharmaceutical product with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def approve(
    uid: str = PharmaceuticalProductUID,
):
    pharmaceutical_product_service = PharmaceuticalProductService()
    return pharmaceutical_product_service.approve(uid=uid)


@router.post(
    "/pharmaceutical-products/{uid}/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Create a new version of a pharmaceutical product",
    description="""
State before:
 - uid must exist and the pharmaceutical product must be in status Final.
 
Business logic:
- The pharmaceutical product is changed to a draft state.

State after:
 - PharmaceuticalProduct changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.
 
Possible errors:
 - Invalid uid or status not Final.
""",
    response_model=PharmaceuticalProduct,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not allow to create pharmaceutical products.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The pharmaceutical product is not in final status.\n"
            "- The pharmaceutical product with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def create_new_version(
    uid: str = PharmaceuticalProductUID,
):
    pharmaceutical_product_service = PharmaceuticalProductService()
    return pharmaceutical_product_service.create_new_version(uid=uid)


@router.delete(
    "/pharmaceutical-products/{uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of a pharmaceutical product",
    description="""
State before:
 - uid must exist and pharmaceutical product must be in status Final.
 
Business logic:
 - The latest 'Final' version will remain the same as before.
 - The status will be automatically set to 'Retired'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.
 
State after:
 - PharmaceuticalProduct changed status to Retired.
 - Audit trail entry must be made with action of inactivating to retired version.
 
Possible errors:
 - Invalid uid or status not Final.
    """,
    response_model=PharmaceuticalProduct,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The pharmaceutical product is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The pharmaceutical product with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def inactivate(
    uid: str = PharmaceuticalProductUID,
):
    pharmaceutical_product_service = PharmaceuticalProductService()
    return pharmaceutical_product_service.inactivate_final(uid=uid)


@router.post(
    "/pharmaceutical-products/{uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of a pharmaceutical product",
    description="""
State before:
 - uid must exist and pharmaceutical product must be in status Retired.
 
Business logic:
 - The latest 'Retired' version will remain the same as before.
 - The status will be automatically set to 'Final'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - PharmaceuticalProduct changed status to Final.
 - An audit trail entry must be made with action of reactivating to final version.
 
Possible errors:
 - Invalid uid or status not Retired.
    """,
    response_model=PharmaceuticalProduct,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The pharmaceutical product is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The pharmaceutical product with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def reactivate(
    uid: str = PharmaceuticalProductUID,
):
    pharmaceutical_product_service = PharmaceuticalProductService()
    return pharmaceutical_product_service.reactivate_retired(uid=uid)


@router.delete(
    "/pharmaceutical-products/{uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Delete draft version of a pharmaceutical product",
    description="""
State before:
 - uid must exist
 - The concept must be in status Draft in a version less then 1.0 (never been approved).
 - The concept must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).
 
Business logic:
 - The draft concept is deleted.
 
State after:
 - PharmaceuticalProduct is successfully deleted.
 
Possible errors:
 - Invalid uid or status not Draft or exist in version 1.0 or above (previously been approved) or not in an editable library.
    """,
    response_model=None,
    status_code=204,
    responses={
        204: {
            "description": "No Content - The pharmaceutical product was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The pharmaceutical product is not in draft status.\n"
            "- The pharmaceutical product was already in final state or is in use.\n"
            "- The library does not allow to delete pharmaceutical product.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - A pharmaceutical product with the specified 'uid' could not be found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def delete(
    uid: str = PharmaceuticalProductUID,
):
    pharmaceutical_product_service = PharmaceuticalProductService()
    pharmaceutical_product_service.soft_delete(uid=uid)
