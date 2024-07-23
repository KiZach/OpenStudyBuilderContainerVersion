"""Study disclosure router"""

from fastapi import Path
from fastapi.responses import Response

from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.routers.studies.study import router
from clinical_mdr_api.services.ctr_xml.ctr_xml_service import CTRXMLService

StudyUID = Path(None, description="The unique id of the study.")


class XMLResponse(Response):
    media_type = "text/xml"


@router.get(
    "/studies/{uid}/ctr/odm.xml",
    dependencies=[rbac.STUDY_READ],
    summary="Returns study disclosure document in CTR ODM XML format",
    status_code=200,
    responses={
        200: {"content": {"text/xml": {"schema": {"type": "string"}}}},
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_odm_xml(
    uid: str = StudyUID,
) -> XMLResponse:
    return XMLResponse(content=CTRXMLService().get_ctr_odm(uid))
