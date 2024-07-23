# pylint: disable=redefined-outer-name,unused-argument
import csv
from copy import deepcopy
from io import BytesIO

import docx
import docx.enum.section
import docx.enum.text
import docx.section
import docx.table
import docx.text.paragraph
import lxml.etree
import openpyxl
import pytest
from bs4 import BeautifulSoup
from starlette.testclient import TestClient

from clinical_mdr_api.services.studies.study_flowchart import (
    DOCX_STYLES,
    StudyFlowchartService,
)
from clinical_mdr_api.services.utils.table_f import TableWithFootnotes

# pylint: disable=unused-import
from clinical_mdr_api.tests.integration.services.test_study_flowchart import (
    TestData,
    detailed_soa_table__days,
    detailed_soa_table__weeks,
    operational_soa_table__days,
    operational_soa_table__weeks,
    protocol_soa_table__days,
    protocol_soa_table__weeks,
    tst_data,
)
from clinical_mdr_api.tests.unit.models.test_table_f import (
    compare_docx_footnotes,
    compare_docx_table,
    compare_html_footnotes,
    compare_html_table,
)
from clinical_mdr_api.tests.utils.checks import (
    DOCX_CONTENT_TYPE,
    assert_json_response,
    assert_response_content_type,
    assert_response_status_code,
)

SOA_EXPORT_COLUMN_HEADERS = [
    "study_number",
    "study_version",
    "soa_group",
    "activity_group",
    "activity_subgroup",
    "epoch",
    "visit",
    "activity",
]

OPERATIONAL_SOA_EXPORT_COLUMN_HEADERS = [
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
]
OPERATIONAL_SOA_EXPORT_COLUMN_HEADERS_XLSX = [
    "Study number",
    "Study version",
    "SoA group",
    "Activity group",
    "Activity subgroup",
    "Epoch",
    "Visit",
    "Activity",
    "Activity instance",
    "Topic code",
    "Param code",
]


@pytest.mark.parametrize(
    "time_unit, operational, hide_soa_groups",
    [
        (None, None, False),
        (None, False, False),
        (None, True, False),
        ("day", None, False),
        ("day", False, False),
        ("day", True, False),
        ("week", None, False),
        ("week", False, False),
        ("week", True, False),
        (None, False, True),
    ],
)
def test_flowchart(
    tst_data: TestData,
    api_client: TestClient,
    time_unit: str,
    operational: bool,
    hide_soa_groups: bool,
):
    """Test /studies/{study_uid}/flowchart returns a valid TableWithFootnotes object as JSON"""

    params = {}
    if time_unit is not None:
        params["time_unit"] = time_unit
    if operational is not None:
        params["operational"] = operational
    if hide_soa_groups:
        params["detailed"] = False

    response = api_client.get(f"/studies/{tst_data.study.uid}/flowchart", params=params)
    assert_response_status_code(response, 200)
    assert_json_response(response)
    data = response.json()
    assert isinstance(data, dict)
    assert TableWithFootnotes(**data)


def test_flowchart_study_versioning(tst_data: TestData, api_client):
    response = api_client.get(
        f"/studies/{tst_data.study.uid}/flowchart",
        params={
            "study_value_version": "1",
            "operational": True,
        },
    )
    assert_response_status_code(response, 200)
    assert_json_response(response)
    old_data = response.json()

    response = api_client.get(
        f"/studies/{tst_data.study.uid}/flowchart",
        params={
            "operational": True,
        },
    )
    assert_response_status_code(response, 200)
    assert_json_response(response)
    data = response.json()
    assert data != old_data
    assert len(data["rows"]) != len(old_data["rows"])
    assert len(old_data["rows"]) == 4
    assert len(data["rows"]) == 38


def test_flowchart_coordinates(tst_data: TestData, api_client):
    """Tests /studies/{study_uid}/flowchart/coordinates to return a dict of coordinates (array of 2)"""

    response = api_client.get(f"/studies/{tst_data.study.uid}/flowchart/coordinates")
    assert_response_status_code(response, 200)
    assert_json_response(response)
    results: dict[str, list[int, int]] = response.json()
    assert isinstance(results, dict)
    assert len(results), "no coordinates returned"


@pytest.mark.parametrize(
    "soa_table, detailed, operational, time_unit",
    [
        ("protocol_soa_table__days", None, None, "day"),
        ("protocol_soa_table__weeks", None, None, "week"),
        ("protocol_soa_table__days", None, False, "day"),
        ("protocol_soa_table__weeks", False, None, "week"),
        ("protocol_soa_table__weeks", False, False, "week"),
        ("detailed_soa_table__days", True, None, "day"),
        ("detailed_soa_table__weeks", True, False, "week"),
        ("operational_soa_table__days", False, True, "day"),
        ("operational_soa_table__weeks", None, True, "week"),
        ("operational_soa_table__days", True, True, "day"),
    ],
)
def test_flowchart_html(
    request,
    tst_data: TestData,
    api_client: TestClient,
    soa_table: TableWithFootnotes,
    detailed: bool,
    operational: bool,
    time_unit: str,
):
    """
    Tests HTML SoA by comparing it with JSON SoA

    Go fix test_flowchart() first if both tests are failing.
    """

    soa_table: TableWithFootnotes = deepcopy(request.getfixturevalue(soa_table))

    # Query parameters
    params = {}
    if time_unit is not None:
        params["time_unit"] = time_unit
    if detailed is not None:
        params["detailed"] = detailed
    if operational is not None:
        params["operational"] = operational

    # Fetch HTML SoA
    response = api_client.get(
        f"/studies/{tst_data.study.uid}/flowchart.html", params=params
    )
    assert_response_status_code(response, 200)
    # THEN returns HTML content-type HTTP header
    assert_response_content_type(response, "text/html")

    # THEN body is a parseable HTML document
    # html.parser does not supplement the document with additional elements for the sake of well-formedness
    doc = BeautifulSoup(response.text, features="html.parser")
    # THEN document has HTML tag
    assert doc.find("html"), "<HTML> tag not found"

    # THEN the document has HTML > HEAD > TITLE tags
    assert (title := doc.select_one("html > head > title")), "<TITLE> tag not found"
    # THEN document title matches
    assert title.text == soa_table.title, "title mismatch"

    # THEN the document has TABLE
    assert (table := doc.select_one("html > body > table")), "<TABLE> tag not found"

    # Although table_f.table_to_html() has it's unit tests, we also run them on this SoA table
    # to increase the number of cases and to test on real-world scenarios.

    if detailed or operational:
        # Detailed and Operation SoA show all rows
        StudyFlowchartService.show_hidden_rows(soa_table)

    # Compares table rows and cell contents and formatting
    compare_html_table(table, soa_table)

    # Compares the footnote listing
    if soa_table.footnotes:
        compare_html_footnotes(doc, soa_table)


@pytest.mark.parametrize(
    "soa_table, detailed, operational, time_unit",
    [
        ("protocol_soa_table__days", None, None, "day"),
        ("protocol_soa_table__weeks", None, None, "week"),
        ("protocol_soa_table__days", None, False, "day"),
        ("protocol_soa_table__weeks", False, None, "week"),
        ("protocol_soa_table__weeks", False, False, "week"),
        ("detailed_soa_table__days", True, None, "day"),
        ("detailed_soa_table__weeks", True, False, "week"),
        ("operational_soa_table__days", False, True, "day"),
        ("operational_soa_table__weeks", None, True, "week"),
        ("operational_soa_table__days", True, True, "day"),
    ],
)
def test_flowchart_docx(
    request,
    tst_data: TestData,
    api_client: TestClient,
    soa_table: TableWithFootnotes,
    detailed: bool,
    operational: bool,
    time_unit: str,
):
    """
    Tests DOCX SoA by comparing it with JSON SoA

    Go fix test_flowchart() first if both tests are failing.
    """
    soa_table: TableWithFootnotes = deepcopy(request.getfixturevalue(soa_table))
    if not operational:
        StudyFlowchartService.add_protocol_section_column(soa_table)

    # Query parameters
    params = {}
    if time_unit is not None:
        params["time_unit"] = time_unit
    if detailed is not None:
        params["detailed"] = detailed
    if operational is not None:
        params["operational"] = operational

    # Fetch DOCX SoA
    response = api_client.get(
        f"/studies/{tst_data.study.uid}/flowchart.docx", params=params
    )
    assert_response_status_code(response, 200)
    # THEN returns DOCX content type HTTP header
    assert_response_content_type(response, DOCX_CONTENT_TYPE)

    # THEN body is a parseable DOCX document
    docx_doc = docx.Document(BytesIO(response.content))

    # THEN the document contains exactly one table
    assert len(docx_doc.tables) == 1, "expected exactly 1 table in DOCX SoA"

    # Although table_f.table_to_docx() has it's unit test, we also run that on this SoA table
    # to increase the number of cases and to test on real-world scenarios.

    if detailed or operational:
        # Detailed and Operation SoA show all rows
        StudyFlowchartService.show_hidden_rows(soa_table)

    # Compare table rows and column contents and properties
    compare_docx_table(docx_doc.tables[0], soa_table, DOCX_STYLES)

    if not operational:
        # Compares footnote listing
        compare_docx_footnotes(docx_doc, soa_table.footnotes, DOCX_STYLES)


@pytest.mark.parametrize(
    "time_unit, detailed, operational, debug_uids, debug_coordinates, debug_propagation",
    [
        ("day", None, None, True, None, None),
        ("day", None, None, None, True, None),
        ("day", None, None, None, None, True),
        ("week", None, None, True, None, None),
        ("week", None, None, None, True, None),
        ("week", None, None, None, None, True),
        ("day", None, None, True, None, None),
        ("day", True, False, None, True, None),
        ("day", False, None, True, None, True),
        ("week", None, True, True, None, None),
        ("week", False, True, True, True, None),
        ("week", True, True, True, True, True),
    ],
)
def test_flowchart_html_debug(
    tst_data: TestData,
    api_client: TestClient,
    time_unit: str,
    detailed: bool,
    operational: bool,
    debug_uids: bool,
    debug_coordinates: bool,
    debug_propagation: bool,
):
    """
    Tests HTML SoA with debugging parameters return a valid HTML table
    """

    # Query parameters
    params = {
        "time_unit": time_unit,
        "detailed": detailed,
        "operational": operational,
        "debug_uids": debug_uids,
        "debug_coordinates": debug_coordinates,
        "debug_propagation": debug_propagation,
    }
    params = {k: v for k, v in params.items() if v is not None}

    # Fetch HTML SoA
    response = api_client.get(
        f"/studies/{tst_data.study.uid}/flowchart.html", params=params
    )
    assert_response_status_code(response, 200)
    # THEN returns HTML content-type HTTP header
    assert_response_content_type(response, "text/html")

    # THEN body is a parseable HTML document
    # html.parser does not supplement the document with additional elements for the sake of well-formedness
    doc = BeautifulSoup(response.text, features="html.parser")
    # THEN document has HTML tag
    assert doc.find("html"), "<HTML> tag not found"

    # THEN document has TABLE
    assert (table := doc.select_one("html > body > table")), "<TABLE> tag not found"

    # THEN the table rows
    assert table.find_all("tr"), "<TABLE> has no <TR> rows"


@pytest.mark.parametrize(
    "path, time_unit",
    [
        ("/studies/{study_uid}/flowchart", "days"),
        ("/studies/{study_uid}/flowchart", "weeks"),
        ("/studies/{study_uid}/flowchart", "foo"),
        ("/studies/{study_uid}/flowchart.html", "bar"),
        ("/studies/{study_uid}/flowchart.html", "weeks"),
        ("/studies/{study_uid}/flowchart.docx", "days"),
        ("/studies/{study_uid}/flowchart.docx", "weekz"),
    ],
)
def test_endpoints_with_invalid_time_unit(
    api_client: TestClient, tst_data: TestData, path, time_unit: str | None
):
    response = api_client.get(
        path.format_map({"study_uid": tst_data.study.uid}),
        params={"time_unit": time_unit},
    )
    assert_response_status_code(response, 422)
    assert_json_response(response)
    payload = response.json()
    assert (detail := payload["detail"][0])
    assert detail["msg"]
    assert detail["loc"] == ["query", "time_unit"]


@pytest.mark.parametrize(
    "path, data_format, expected_column_headers",
    [
        (
            "/studies/{study_uid}/detailed-soa-exports",
            "text/csv",
            SOA_EXPORT_COLUMN_HEADERS,
        ),
        (
            "/studies/{study_uid}/detailed-soa-exports",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            SOA_EXPORT_COLUMN_HEADERS,
        ),
        (
            "/studies/{study_uid}/detailed-soa-exports",
            "text/xml",
            SOA_EXPORT_COLUMN_HEADERS,
        ),
        (
            "/studies/{study_uid}/detailed-soa-exports",
            "application/json",
            SOA_EXPORT_COLUMN_HEADERS,
        ),
        (
            "/studies/{study_uid}/protocol-soa-exports",
            "text/csv",
            SOA_EXPORT_COLUMN_HEADERS,
        ),
        (
            "/studies/{study_uid}/protocol-soa-exports",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            SOA_EXPORT_COLUMN_HEADERS,
        ),
        (
            "/studies/{study_uid}/protocol-soa-exports",
            "text/xml",
            SOA_EXPORT_COLUMN_HEADERS,
        ),
        (
            "/studies/{study_uid}/protocol-soa-exports",
            "application/json",
            SOA_EXPORT_COLUMN_HEADERS,
        ),
        (
            "/studies/{study_uid}/operational-soa-exports",
            "text/csv",
            OPERATIONAL_SOA_EXPORT_COLUMN_HEADERS,
        ),
        (
            "/studies/{study_uid}/operational-soa-exports",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            OPERATIONAL_SOA_EXPORT_COLUMN_HEADERS_XLSX,
        ),
        (
            "/studies/{study_uid}/operational-soa-exports",
            "text/xml",
            OPERATIONAL_SOA_EXPORT_COLUMN_HEADERS,
        ),
        (
            "/studies/{study_uid}/operational-soa-exports",
            "application/json",
            OPERATIONAL_SOA_EXPORT_COLUMN_HEADERS,
        ),
    ],
)
def test_soa_exports(
    api_client: TestClient,
    tst_data: TestData,
    path: str,
    data_format: str,
    expected_column_headers,
):
    """Test the export endpoints return the expected data format"""

    response = api_client.get(
        path.format_map({"study_uid": tst_data.study.uid}),
        headers={"Accept": data_format},
    )
    assert_response_status_code(response, 200)
    # THEN returns the expected content-type HTTP header
    assert_response_content_type(response, data_format)

    if data_format == "application/json":
        # THEN payload is valid JSON data
        data = response.json()
        assert data, "empty JSON data"
        assert isinstance(data, list), "unexpected JSON data type"
        # THEN JSON list items have expected properties
        expected_column_headers = set(expected_column_headers)
        for i, item in enumerate(data):
            property_keys = set(item.keys())
            assert (
                property_keys == expected_column_headers
            ), f"Item property keys mismatch in record {i}"

    if data_format == "text/csv":
        # THEN payload is valid CSV data
        reader = csv.reader(response.iter_lines(), dialect=csv.excel)
        num_cols = None
        for line in reader:
            assert line
            if num_cols is None:  # first column
                # THEN column headers in first row have expected text and order
                assert line == expected_column_headers, "Column headers mismatch"
                num_cols = len(line)
            else:
                # THEN all rows have the same number of columns
                assert len(line) == num_cols
        # THEN CSV has rows and columns
        assert num_cols, "empty CSV data"

    if data_format == "text/xml":
        # THEN payload is a valid XML document
        assert (tree := lxml.etree.parse(BytesIO(response.content)))
        assert (root := tree.getroot()), "root tag not found"
        # THEN root XML tag is "items"
        assert root.tag == "items", "root tag is not <items>"
        # THEN data contains records
        assert len(root), "root tag <items> has no children"
        # THEN records have expected properties
        expected_column_headers = set(expected_column_headers)
        property_keys = {child.tag for child in root[0]}
        assert property_keys == expected_column_headers, "Item property keys mismatch"

    if (
        data_format
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ):
        # THEN payload is a valid XLSX document
        workbook = openpyxl.load_workbook(BytesIO(response.content))
        # THEN document has a worksheet
        assert len(workbook.worksheets), "XLSX has no worksheets"
        # THEN worksheet has columns
        worksheet = workbook.worksheets[0]
        assert sum(1 for _ in worksheet.columns), "worksheet 0 has no columns"
        # THEN column headers in first row have expected text and order
        column_headers = [column[0].value for column in worksheet.columns]
        assert column_headers == expected_column_headers, "Column headers mismatch"
        # THEN worksheet has more than 1 row
        num_rows = sum(1 for _ in worksheet.rows)
        assert num_rows > 1, f"worksheet 0 has only {num_rows} rows"
