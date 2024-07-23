from fastapi import APIRouter, Body, Query
from pydantic.types import Json

from clinical_mdr_api import config, models
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.clinical_programmes import (
    clinical_programme as clinical_programme_service,
)

# Prefixed with "/clinical-programmes"
router = APIRouter()


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all clinical programmes.",
    response_model=GenericFilteringReturn[models.ClinicalProgramme],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_programmes(
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
) -> GenericFilteringReturn[models.ClinicalProgramme]:
    return clinical_programme_service.get_all_clinical_programmes(
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        total_count=total_count,
    )


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates a new clinical programme.",
    response_model=models.ClinicalProgramme,
    status_code=201,
    responses={
        201: {
            "description": "Created - The clinical programme was successfully created."
        },
        500: _generic_descriptions.ERROR_500,
    },
)
# pylint: disable=unused-argument
def create(
    clinical_programme_create_input: models.ClinicalProgrammeInput = Body(
        description="Related parameters of the clinical programme that shall be created.",
    ),
) -> models.ClinicalProgramme:
    return clinical_programme_service.create(clinical_programme_create_input)
