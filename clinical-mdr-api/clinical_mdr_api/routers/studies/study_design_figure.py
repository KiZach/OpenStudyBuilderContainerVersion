"""Study chart router."""

from fastapi import Path, Query
from fastapi.responses import Response

from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.routers import studies_router as router
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_design_figure import (
    StudyDesignFigureService,
)

StudyUID = Path(None, description="The unique id of the study.")

time_unit = Query(
    "days",
    regex="^(weeks|days)$",
    description="The preferred time unit, either days or weeks.",
)


class SVGResponse(Response):
    media_type = "image/svg+xml"


@router.get(
    "/{uid}/design.svg",
    dependencies=[rbac.STUDY_READ],
    summary="Builds and returns a Study Design visualization image in SVG format",
    status_code=200,
    responses={
        200: {"content": {"image/svg+xml": {"schema": {"type": "string"}}}},
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_study_flowchart_html(
    response: Response,
    uid: str = StudyUID,
) -> SVGResponse:
    StudyService().check_if_study_exists(uid)
    response.headers["Content-Disposition"] = f'inline; filename="{uid} design.svg"'
    return SVGResponse(StudyDesignFigureService().get_svg_document(uid))
