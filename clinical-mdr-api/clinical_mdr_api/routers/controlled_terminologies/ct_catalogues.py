"""CTCatalogue router."""
from datetime import datetime, timezone

from fastapi import APIRouter, Query

from clinical_mdr_api import models
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.controlled_terminologies.ct_catalogue import (
    CTCatalogueService,
)

# Prefixed with "/ct"
router = APIRouter()


@router.get(
    "/catalogues",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all controlled terminology catalogues.",
    response_model=list[models.CTCatalogue],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
# pylint: disable=unused-argument
def get_catalogues(
    library: str
    | None = Query(
        None,
        description="If specified, only catalogues from given library are returned.",
    ),
):
    ct_catalogue_service = CTCatalogueService()
    return ct_catalogue_service.get_all_ct_catalogues(library_name=library)


@router.get(
    "/catalogues/changes",
    dependencies=[rbac.LIBRARY_READ],
    summary="List changes between codelists and terms in CT Catalogues.",
    response_model=models.CTCatalogueChanges,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_catalogues_changes(
    library_name: str
    | None = Query(
        None,
        description="If specified, only codelists and terms from given library_name are compared.",
    ),
    catalogue_name: str
    | None = Query(
        None,
        description="If specified, only codelists and terms from given catalogue_name are compared.",
    ),
    comparison_type: str = Query(
        ...,
        description="The type of the comparison.\n"
        "Valid types are `attributes` or `sponsor`",
        example="attributes",
    ),
    start_datetime: datetime = Query(
        ...,
        description="The start datetime to perform comparison (ISO 8601 format with UTC offset)",
        example="2023-03-26T00:00:00+00:00",
    ),
    end_datetime: datetime
    | None = Query(
        None,
        description="The end datetime to perform comparison (ISO 8601 format with UTC offset).\n"
        "If it is not passed, then the current datetime is assigned.",
        example="2023-03-27T00:00:00+00:00",
    ),
):
    if end_datetime is None:
        end_datetime = datetime.now(timezone.utc)
    ct_catalogue_service = CTCatalogueService()
    return ct_catalogue_service.get_ct_catalogues_changes(
        library_name=library_name,
        catalogue_name=catalogue_name,
        comparison_type=comparison_type,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
    )
