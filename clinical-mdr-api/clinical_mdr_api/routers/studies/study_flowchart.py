"""Study chart router."""

import os

from fastapi import Path, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from starlette.requests import Request

from clinical_mdr_api import config
from clinical_mdr_api.models import DetailedSoAHistory
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers import studies_router as router
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_activity_selection import (
    StudyActivitySelectionService,
)
from clinical_mdr_api.services.studies.study_flowchart import (
    DOCX_STYLES,
    StudyFlowchartService,
)
from clinical_mdr_api.services.utils.table_f import (
    TableWithFootnotes,
    table_to_docx,
    table_to_html,
)

DETAILED_QUERY_DESCRIPTION = "Return detailed SoA, including all rows that are otherwise hidden from protocol SoA"

DETAILED_QUERY = Query(
    default=False,
    description=DETAILED_QUERY_DESCRIPTION,
)

OPERATIONAL_QUERY = Query(
    default=False,
    description="Returns operational SoA if True else Protocol SoA if False (default)",
)

STUDY_UID_PATH = Path(None, description="The unique id of the study.")


TIME_UNIT_QUERY = Query(
    None,
    regex="^(week|day)$",
    description="The preferred time unit, either day or week.",
)


@router.get(
    "/{study_uid}/flowchart/coordinates",
    dependencies=[rbac.STUDY_READ],
    summary="Returns uid to [row,column] coordinates mapping of items included in SoA Protocol Flowchart table",
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
    response_model=dict[str, tuple[int, int]],
)
def get_study_flowchart_coordinates(
    study_uid: str = STUDY_UID_PATH,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> dict[str, tuple[int, int]]:
    coordinates = StudyFlowchartService().get_flowchart_item_uid_coordinates(
        study_uid=study_uid, study_value_version=study_value_version
    )
    return coordinates


@router.get(
    "/{study_uid}/flowchart",
    dependencies=[rbac.STUDY_READ],
    summary="Protocol, Detailed or Operational SoA table with footnotes as JSON",
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
    response_model=TableWithFootnotes,
    response_model_exclude_none=True,
)
def get_study_flowchart(
    study_uid: str = STUDY_UID_PATH,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
    time_unit: str | None = TIME_UNIT_QUERY,
    detailed: bool | None = Query(default=True, description=DETAILED_QUERY_DESCRIPTION),
    operational: bool | None = OPERATIONAL_QUERY,
) -> TableWithFootnotes:
    # build internal representation of flowchart
    table = StudyFlowchartService().get_flowchart_table(
        study_uid=study_uid,
        time_unit=time_unit,
        study_value_version=study_value_version,
        operational=operational,
        hide_soa_groups=not (detailed or operational),
    )

    return table


@router.get(
    "/{study_uid}/flowchart.html",
    dependencies=[rbac.STUDY_READ],
    summary="Builds and returns an HTML document with Protocol, Detailed or Operational SoA table with footnotes",
    responses={
        200: {"content": {"text/html": {"schema": {"type": "string"}}}},
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_study_flowchart_html(
    study_uid: str = STUDY_UID_PATH,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
    time_unit: str | None = TIME_UNIT_QUERY,
    detailed: bool | None = DETAILED_QUERY,
    debug_uids: bool
    | None = Query(default=False, description="Show uids on column superscript"),
    debug_coordinates: bool
    | None = Query(default=False, description="Debug coordinates as superscripts"),
    debug_propagation: bool
    | None = Query(default=False, description="Debug propagations without hiding rows"),
    operational: bool | None = OPERATIONAL_QUERY,
) -> HTMLResponse:
    # build internal representation of flowchart
    service = StudyFlowchartService()
    table = service.get_flowchart_table(
        study_uid=study_uid,
        time_unit=time_unit,
        study_value_version=study_value_version,
        operational=operational,
        hide_soa_groups=not (detailed or operational),
    )

    if detailed or operational:
        StudyFlowchartService.show_hidden_rows(table)
    else:
        StudyFlowchartService.propagate_hidden_rows(table)

    if debug_propagation:
        StudyFlowchartService.propagate_hidden_rows(table)
        StudyFlowchartService.show_hidden_rows(table)

    if debug_coordinates:
        coordinates = service.get_flowchart_item_uid_coordinates(
            study_uid=study_uid, study_value_version=study_value_version
        )
        StudyFlowchartService.add_coordinates(table, coordinates)

    if debug_uids:
        StudyFlowchartService.add_uid_debug(table)

    # convert flowchart to HTML document
    html = table_to_html(table)

    return HTMLResponse(html)


@router.get(
    "/{study_uid}/flowchart.docx",
    dependencies=[rbac.STUDY_READ],
    summary="Builds and returns an DOCX document with Protocol, Detailed or Operational SoA table with footnotes",
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
def get_study_flowchart_docx(
    study_uid: str = STUDY_UID_PATH,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
    time_unit: str | None = TIME_UNIT_QUERY,
    detailed: bool | None = DETAILED_QUERY,
    operational: bool | None = OPERATIONAL_QUERY,
) -> StreamingResponse:
    # get study_id for constructing download filename
    study = StudyService().get_by_uid(
        study_uid, study_value_version=study_value_version
    )

    # build internal representation of flowchart
    table = StudyFlowchartService().get_flowchart_table(
        study_uid=study_uid,
        time_unit=time_unit,
        study_value_version=study_value_version,
        operational=operational,
        hide_soa_groups=not (detailed or operational),
    )

    if detailed or operational:
        StudyFlowchartService.show_hidden_rows(table)
    else:
        StudyFlowchartService.propagate_hidden_rows(table)

    # Add Protocol Section column
    if not operational:
        StudyFlowchartService.add_protocol_section_column(table)

    # convert flowchart to DOCX document applying styles
    docx = table_to_docx(table, styles=DOCX_STYLES)
    stream = docx.get_document_stream()

    # determine the size of the binary DOCX document for HTTP header
    size = stream.seek(0, os.SEEK_END)
    stream.seek(0)

    # construct download filename
    filename = [study.current_metadata.identification_metadata.study_id]
    if detailed:
        filename.append("detailed")
    filename.append("flowchart.docx")
    filename = " ".join(filename)

    # send response along with document info in HTTP header
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": f"{size:d}",
        },
    )


@router.get(
    "/{study_uid}/detailed-soa-history",
    dependencies=[rbac.STUDY_READ],
    summary="Returns the history of changes performed to a specific detailed SoA",
    response_model=CustomPage[DetailedSoAHistory],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_detailed_soa_history(
    study_uid: str = STUDY_UID_PATH,
    page_number: int
    | None = Query(1, ge=1, description=_generic_descriptions.PAGE_NUMBER),
    page_size: int
    | None = Query(
        config.DEFAULT_PAGE_SIZE,
        ge=0,
        le=config.MAX_PAGE_SIZE,
        description=_generic_descriptions.PAGE_SIZE,
    ),
    total_count: bool
    | None = Query(False, description=_generic_descriptions.TOTAL_COUNT),
) -> list[DetailedSoAHistory]:
    detailed_soa_history = StudyActivitySelectionService().get_detailed_soa_history(
        study_uid=study_uid,
        page_size=page_size,
        page_number=page_number,
        total_count=total_count,
    )
    return CustomPage.create(
        items=detailed_soa_history.items,
        total=detailed_soa_history.total,
        page=page_number,
        size=page_size,
    )


@router.get(
    "/{study_uid}/detailed-soa-exports",
    dependencies=[rbac.STUDY_READ],
    summary="Exports the Detailed SoA content",
    response_model=list[dict],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "study_number",
            "study_version",
            "soa_group",
            "activity_group",
            "activity_subgroup",
            "epoch",
            "visit",
            "activity",
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
def export_detailed_soa_content(
    request: Request,  # request is actually required by the allow_exports decorator
    study_uid: str = STUDY_UID_PATH,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> list[dict]:
    soa_content = StudyFlowchartService().download_detailed_soa_content(
        study_uid=study_uid,
        study_value_version=study_value_version,
    )
    return soa_content


@router.get(
    "/{study_uid}/operational-soa-exports",
    dependencies=[rbac.STUDY_READ],
    summary="Exports the Operational SoA content",
    response_model=list[dict],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "study_number",
            "study_version",
            "soa_group",
            "activity_group",
            "activity_subgroup",
            "epoch",
            "visit",
            "activity",
            "activity_instance",
            "topic_code",
            "param_code",
        ],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
            "Study number=study_number",
            "Study version=study_version",
            "SoA group=soa_group",
            "Activity group=activity_group",
            "Activity subgroup=activity_subgroup",
            "Epoch=epoch",
            "Visit=visit",
            "Activity=activity",
            "Activity instance=activity_instance",
            "Topic code=topic_code",
            "Param code=param_code",
        ],
    }
)
# pylint: disable=unused-argument
def export_operational_soa_content(
    request: Request,  # request is actually required by the allow_exports decorator
    study_uid: str = STUDY_UID_PATH,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> list[dict]:
    soa_content = StudyFlowchartService().download_operational_soa_content(
        study_uid=study_uid,
        study_value_version=study_value_version,
    )
    return soa_content


@router.get(
    "/{study_uid}/protocol-soa-exports",
    dependencies=[rbac.STUDY_READ],
    summary="Exports the Protocol SoA content",
    response_model=list[dict],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "study_number",
            "study_version",
            "soa_group",
            "activity_group",
            "activity_subgroup",
            "epoch",
            "visit",
            "activity",
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
def export_protocol_soa_content(
    request: Request,  # request is actually required by the allow_exports decorator
    study_uid: str = STUDY_UID_PATH,
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> list[dict]:
    soa_content = StudyFlowchartService().download_detailed_soa_content(
        study_uid=study_uid,
        study_value_version=study_value_version,
        protocol_flowchart=True,
    )
    return soa_content
