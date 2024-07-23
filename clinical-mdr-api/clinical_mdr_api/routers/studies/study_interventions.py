"""Study Protocol Interventions router"""

import os

from fastapi import Path
from fastapi.responses import HTMLResponse, StreamingResponse

from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.routers import studies_router as router
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_interventions import (
    StudyInterventionsService,
)
from clinical_mdr_api.services.utils.table_f import TableWithFootnotes

StudyUID = Path(None, description="The unique id of the study.")


@router.get(
    "/{uid}/interventions",
    dependencies=[rbac.STUDY_READ],
    summary="Returns Study Protocol Interventions table",
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
    response_model=TableWithFootnotes,
)
def get_study_interventions(
    uid: str = StudyUID,
) -> TableWithFootnotes:
    StudyService().check_if_study_exists(uid)
    return StudyInterventionsService().get_table(uid)


@router.get(
    "/{uid}/interventions.html",
    dependencies=[rbac.STUDY_READ],
    summary="Builds and returns an HTML document of Study Protocol Interventions table",
    responses={
        200: {"content": {"text/html": {"schema": {"type": "string"}}}},
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_study_interventions_html(
    uid: str = StudyUID,
) -> HTMLResponse:
    StudyService().check_if_study_exists(uid)
    return HTMLResponse(StudyInterventionsService().get_html(uid))


@router.get(
    "/{uid}/interventions.docx",
    dependencies=[rbac.STUDY_READ],
    summary="Builds and returns a DOCX document of Study Protocol Interventions table",
    responses={
        200: {
            "content": {
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {}
            }
        },
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_study_interventions_docx(
    uid: str = StudyUID,
) -> StreamingResponse:
    StudyService().check_if_study_exists(uid)
    docx = StudyInterventionsService().get_docx(uid)
    stream = docx.get_document_stream()
    size = stream.seek(0, os.SEEK_END)
    stream.seek(0)
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{uid} interventions.docx"',
            "Content-Length": f"{size:d}",
        },
    )
