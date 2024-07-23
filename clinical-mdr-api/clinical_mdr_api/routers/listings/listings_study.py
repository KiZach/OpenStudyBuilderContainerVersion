from fastapi import APIRouter, Query

from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.listings.listings_study import StudyMetadataListingModel
from clinical_mdr_api.models.utils import PrettyJSONResponse
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.listings.listings_study import (
    StudyMetadataListingService,
)

# Prefixed with "/listings"
router = APIRouter()


@router.get(
    "/studies/study-metadata",
    dependencies=[rbac.STUDY_READ],
    summary="Retrieve study metadata of a specific study",
    response_model=StudyMetadataListingModel,
    response_class=PrettyJSONResponse,
    status_code=200,
    responses={
        200: {
            "model": StudyMetadataListingModel,
        },
        500: _generic_descriptions.ERROR_500,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - No study with the specified study ID.",
        },
    },
)
def get_study_metadata(
    project_id: str = Query(None, description="Project ID of study requested"),
    study_number: str = Query(None, description="Study number of study requested"),
    subpart_acronym: str = Query(
        None, description="subpart, if exists, of study requested"
    ),
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
    datetime: str
    | None = Query(
        None,
        description=r"If specified, study data with latest released version of specified datetime is returned. "
        r"format in YYYY-MM-DDThh:mm:ssZ. ",
    ),
):
    study_metadata_listing_service = StudyMetadataListingService()
    return study_metadata_listing_service.get_study_metadata(
        project_id, study_number, subpart_acronym, study_value_version, datetime
    )
