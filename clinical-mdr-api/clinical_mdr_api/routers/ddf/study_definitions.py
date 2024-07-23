from fastapi import APIRouter, Path
from usdm_model import Study as USDMStudy

from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import PrettyJSONResponse
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.ddf.usdm_service import USDMService

router = APIRouter(prefix="/studyDefinitions")


@router.get(
    path="/{study_uid}",
    dependencies=[rbac.STUDY_READ],
    response_class=PrettyJSONResponse,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
    summary="""Return an entire study in DDF USDM format""",
    description="""
State before:
- Study must exist.

State after:
- no change.

Possible errors:
- Invalid study-uid.
""",
)
def get_study(
    study_uid: str = Path(..., description="The unique uid of the study."),
) -> USDMStudy:
    usdm_service = USDMService(study_uid=study_uid)
    ddf_study = usdm_service.get_by_uid(study_uid)
    return ddf_study
