"""
Tests for /concepts/compounds endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments
import json
import logging
from functools import reduce

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api import models
from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import CT_CODELIST_NAMES, TestUtils

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
rand: str
compounds_all: list[models.Compound]
compound_aliases_all: list[models.CompoundAlias]
ct_term_dosage: models.CTTerm
ct_term_delivery_device: models.CTTerm
ct_term_dose_frequency: models.CTTerm
ct_term_dispenser: models.CTTerm
ct_term_roa: models.CTTerm
strength_value: models.NumericValueWithUnit
dose_value: models.NumericValueWithUnit
brands: list[models.Brand]
lag_time: models.LagTime
half_life: models.NumericValueWithUnit


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "compounds.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global rand
    global compounds_all
    global compound_aliases_all
    global ct_term_dosage
    global ct_term_delivery_device
    global ct_term_dose_frequency
    global ct_term_dispenser
    global ct_term_roa
    global strength_value
    global dose_value
    global brands
    global lag_time
    global half_life

    rand = TestUtils.random_str(10)

    # Get codelist UIDs
    relevant_codelists = [
        CT_CODELIST_NAMES.delivery_device,
        CT_CODELIST_NAMES.dosage_form,
        CT_CODELIST_NAMES.frequency,
        CT_CODELIST_NAMES.roa,
        CT_CODELIST_NAMES.dispenser,
        CT_CODELIST_NAMES.adverse_events,
    ]
    codelists = TestUtils.get_codelists_by_names(relevant_codelists)

    # Create CT Terms
    ct_term_dosage = TestUtils.create_ct_term(
        sponsor_preferred_name="dosage_form_1",
        codelist_uid=TestUtils.get_codelist_uid_by_name(
            codelists, CT_CODELIST_NAMES.dosage_form
        ),
    )
    ct_term_delivery_device = TestUtils.create_ct_term(
        sponsor_preferred_name="delivery_device_1",
        codelist_uid=TestUtils.get_codelist_uid_by_name(
            codelists, CT_CODELIST_NAMES.delivery_device
        ),
    )
    ct_term_dose_frequency = TestUtils.create_ct_term(
        sponsor_preferred_name="dose_frequency_1",
        codelist_uid=TestUtils.get_codelist_uid_by_name(
            codelists, CT_CODELIST_NAMES.frequency
        ),
    )
    ct_term_dispenser = TestUtils.create_ct_term(
        sponsor_preferred_name="dispenser_1",
        codelist_uid=TestUtils.get_codelist_uid_by_name(
            codelists, CT_CODELIST_NAMES.dispenser
        ),
    )
    ct_term_roa = TestUtils.create_ct_term(
        sponsor_preferred_name="route_of_administration_1",
        codelist_uid=TestUtils.get_codelist_uid_by_name(
            codelists, CT_CODELIST_NAMES.roa
        ),
    )

    # Create Numeric values with unit
    strength_value = TestUtils.create_numeric_value_with_unit(value=5, unit="mg/mL")
    dose_value = TestUtils.create_numeric_value_with_unit(value=10, unit="mg")
    half_life = TestUtils.create_numeric_value_with_unit(value=8, unit="hours")

    # Create Lag-times
    lag_time = TestUtils.create_lag_time(value=7, unit="days")

    # Create Brands
    brands = [
        TestUtils.create_brand(name=name) for name in ["Brand A", "Brand B", "Brand C"]
    ]

    for _x in range(30):
        TestUtils.create_ct_term()

    # Create some compounds
    compounds_all = []
    compound_aliases_all = []
    compounds_all.append(
        TestUtils.create_compound(
            name=f"Compound A {rand}",
            dosage_form_uids=[ct_term_dosage.term_uid],
            delivery_devices_uids=[ct_term_delivery_device.term_uid],
            dispensers_uids=[ct_term_dispenser.term_uid],
            route_of_administration_uids=[ct_term_roa.term_uid],
            strength_values_uids=[strength_value.uid],
            dose_frequency_uids=[ct_term_dose_frequency.term_uid],
            dose_values_uids=[dose_value.uid],
            lag_times_uids=[lag_time.uid],
            half_life_uid=half_life.uid,
            substance_terms_uids=[],
            brands_uids=[brands[0].uid, brands[1].uid],
        )
    )

    compounds_all.append(TestUtils.create_compound(name=f"name-AAA-{rand}"))
    compounds_all.append(TestUtils.create_compound(name=f"name-BBB-{rand}"))
    compounds_all.append(TestUtils.create_compound(definition=f"def-XXX-{rand}"))
    compounds_all.append(TestUtils.create_compound(definition=f"def-YYY-{rand}"))

    for index in range(5):
        compound_a = TestUtils.create_compound(name=f"name-AAA-{rand}-{index}")
        compounds_all.append(compound_a)
        compound_aliases_all.append(
            TestUtils.create_compound_alias(
                name=f"compAlias-AAA-{rand}-{index}", compound_uid=compound_a.uid
            )
        )

        compound_b = TestUtils.create_compound(name=f"name-BBB-{rand}-{index}")
        compounds_all.append(compound_b)
        compound_aliases_all.append(
            TestUtils.create_compound_alias(
                name=f"compAlias-BBB-{rand}-{index}", compound_uid=compound_b.uid
            )
        )

        compound_c = TestUtils.create_compound(definition=f"def-XXX-{rand}-{index}")
        compounds_all.append(compound_c)
        compound_aliases_all.append(
            TestUtils.create_compound_alias(
                definition=f"def-XXX-{rand}-{index}", compound_uid=compound_c.uid
            )
        )

        compound_d = TestUtils.create_compound(definition=f"def-YYY-{rand}-{index}")
        compounds_all.append(compound_d)
        compound_aliases_all.append(
            TestUtils.create_compound_alias(
                definition=f"def-YYY-{rand}-{index}", compound_uid=compound_d.uid
            )
        )


COMPOUND_FIELDS_ALL = [
    "uid",
    "name",
    "name_sentence_case",
    "definition",
    "abbreviation",
    "library_name",
    "start_date",
    "end_date",
    "status",
    "version",
    "change_description",
    "user_initials",
    "possible_actions",
    "analyte_number",
    "nnc_short_number",
    "nnc_long_number",
    "is_sponsor_compound",
    "is_name_inn",
    "substances",
    "dose_values",
    "strength_values",
    "lag_times",
    "delivery_devices",
    "dispensers",
    "projects",
    "brands",
    "half_life",
    "dose_frequencies",
    "dosage_forms",
    "routes_of_administration",
]

COMPOUND_FIELDS_NOT_NULL = ["uid", "name", "start_date"]


def test_get_compound(api_client):
    response = api_client.get(f"/concepts/compounds/{compounds_all[0].uid}")
    res = response.json()

    assert response.status_code == 200

    # Check fields included in the response
    assert set(list(res.keys())) == set(COMPOUND_FIELDS_ALL)
    for key in COMPOUND_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == compounds_all[0].uid
    assert res["name"] == f"Compound A {rand}"
    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]
    assert res["dose_values"][0]["uid"] == dose_value.uid
    assert res["dose_values"][0]["value"] == dose_value.value
    assert (
        res["dose_values"][0]["unit_definition_uid"] == dose_value.unit_definition_uid
    )
    assert res["dose_values"][0]["unit_label"] == "mg"
    assert res["strength_values"][0]["uid"] == strength_value.uid
    assert res["strength_values"][0]["value"] == strength_value.value
    assert (
        res["strength_values"][0]["unit_definition_uid"]
        == strength_value.unit_definition_uid
    )
    assert res["strength_values"][0]["unit_label"] == "mg/mL"
    assert res["delivery_devices"][0]["term_uid"] == ct_term_delivery_device.term_uid
    assert (
        res["delivery_devices"][0]["name"]
        == ct_term_delivery_device.sponsor_preferred_name
    )
    assert res["dose_frequencies"][0]["term_uid"] == ct_term_dose_frequency.term_uid
    assert (
        res["dose_frequencies"][0]["name"]
        == ct_term_dose_frequency.sponsor_preferred_name
    )
    assert res["dosage_forms"][0]["term_uid"] == ct_term_dosage.term_uid
    assert res["dosage_forms"][0]["name"] == ct_term_dosage.sponsor_preferred_name
    assert res["dispensers"][0]["term_uid"] == ct_term_dispenser.term_uid
    assert res["dispensers"][0]["name"] == ct_term_dispenser.sponsor_preferred_name
    assert res["routes_of_administration"][0]["term_uid"] == ct_term_roa.term_uid
    assert (
        res["routes_of_administration"][0]["name"] == ct_term_roa.sponsor_preferred_name
    )
    assert res["brands"][0]["uid"] == "Brand_000001"
    assert res["brands"][0]["name"] == "Brand A"
    assert res["brands"][1]["uid"] == "Brand_000002"
    assert res["brands"][1]["name"] == "Brand B"
    assert res["lag_times"][0]["unit_definition_uid"] is not None
    assert res["lag_times"][0]["sdtm_domain_uid"] is not None
    assert res["lag_times"][0]["value"] == 7
    assert res["lag_times"][0]["unit_label"] == "days"
    assert res["lag_times"][0]["sdtm_domain_label"] == "Adverse Event Domain"
    assert res["half_life"]["value"] == 8
    assert res["half_life"]["unit_label"] == "hours"
    assert res["half_life"]["uid"] is not None
    TestUtils.assert_timestamp_is_in_utc_zone(res["start_date"])
    TestUtils.assert_timestamp_is_newer_than(res["start_date"], 60)


def test_update_compound(api_client):
    payload = {
        "name": f"{compounds_all[0].name}-updated",
        "change_description": "name updated",
    }
    response = api_client.patch(
        f"/concepts/compounds/{compounds_all[0].uid}",
        data=json.dumps(payload),
        headers={"content-type": "application/json"},
    )
    res = response.json()

    assert response.status_code == 200

    TestUtils.assert_timestamp_is_in_utc_zone(res["start_date"])
    TestUtils.assert_timestamp_is_newer_than(res["start_date"], 60)


def test_get_compounds_pagination(api_client):
    results_paginated: dict = {}
    sort_by = '{"name": true}'
    for page_number in range(1, 4):
        url = f"/concepts/compounds?page_number={page_number}&page_size=10&sort_by={sort_by}"
        response = api_client.get(url)
        res = response.json()
        res_names = list(map(lambda x: x["name"], res["items"]))
        results_paginated[page_number] = res_names
        log.info("Page %s: %s", page_number, res_names)

    log.info("All pages: %s", results_paginated)

    results_paginated_merged = list(
        set(list(reduce(lambda a, b: a + b, list(results_paginated.values()))))
    )
    log.info("All unique rows returned by pagination: %s", results_paginated_merged)

    res_all = api_client.get(
        f"/concepts/compounds?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    results_all_in_one_page = list(map(lambda x: x["name"], res_all["items"]))
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)
    assert len(compounds_all) == len(results_paginated_merged)


@pytest.mark.parametrize(
    "page_size, page_number, total_count, sort_by, expected_result_len",
    [
        pytest.param(None, None, None, None, 10),
        pytest.param(3, 1, True, None, 3),
        pytest.param(3, 2, True, None, 3),
        pytest.param(10, 2, True, None, 10),
        pytest.param(10, 3, True, None, 5),  # Total numer of compounds is 25
        pytest.param(10, 1, True, '{"name": false}', 10),
        pytest.param(10, 2, True, '{"name": true}', 10),
    ],
)
def test_get_compounds(
    api_client, page_size, page_number, total_count, sort_by, expected_result_len
):
    url = "/concepts/compounds"
    query_params = []
    if page_size:
        query_params.append(f"page_size={page_size}")
    if page_number:
        query_params.append(f"page_number={page_number}")
    if total_count:
        query_params.append(f"total_count={total_count}")
    if sort_by:
        query_params.append(f"sort_by={sort_by}")

    if query_params:
        url = f"{url}?{'&'.join(query_params)}"

    log.info("GET %s", url)
    response = api_client.get(url)
    res = response.json()

    assert response.status_code == 200

    # Check fields included in the response
    assert list(res.keys()) == ["items", "total", "page", "size"]
    assert len(res["items"]) == expected_result_len
    assert res["total"] == (len(compounds_all) if total_count else 0)
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(list(item.keys())) == set(COMPOUND_FIELDS_ALL)
        for key in COMPOUND_FIELDS_NOT_NULL:
            assert item[key] is not None
        TestUtils.assert_timestamp_is_in_utc_zone(item["start_date"])
        TestUtils.assert_timestamp_is_newer_than(item["start_date"], 60)

    if sort_by:
        # sort_by is JSON string in the form: {"sort_field_name": is_ascending_order}
        sort_by_dict = json.loads(sort_by)
        sort_field: str = list(sort_by_dict.keys())[0]
        sort_order_ascending: bool = list(sort_by_dict.values())[0]

        # extract list of values of 'sort_field_name' field from the returned result
        result_vals = list(map(lambda x: x[sort_field], res["items"]))
        result_vals_sorted_locally = result_vals.copy()
        result_vals_sorted_locally.sort(reverse=not sort_order_ascending)
        assert result_vals == result_vals_sorted_locally


@pytest.mark.parametrize(
    "export_format",
    [
        pytest.param("text/csv"),
        pytest.param("text/xml"),
        pytest.param(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    ],
)
def test_get_compounds_csv_xml_excel(api_client, export_format):
    url = "/concepts/compounds"
    TestUtils.verify_exported_data_format(api_client, export_format, url)


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param('{"*": {"v": ["aaa"]}}', "name", "name-AAA"),
        pytest.param('{"*": {"v": ["bBb"]}}', "name", "name-BBB"),
        pytest.param(
            '{"*": {"v": ["wn-us"], "op": "co"}}', "user_initials", "unknown-user"
        ),
        pytest.param('{"*": {"v": ["Draft"]}}', "status", "Draft"),
        pytest.param('{"*": {"v": ["0.1"]}}', "version", "0.1"),
        pytest.param('{"*": {"v": ["ccc"]}}', None, None),
    ],
)
def test_filtering_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    url = f"/concepts/compounds?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert response.status_code == 200
    if expected_result_prefix:
        assert len(res["items"]) > 0
        # Each returned row has a field that starts with the specified filter value
        for row in res["items"]:
            assert row[expected_matched_field].startswith(expected_result_prefix)
    else:
        assert len(res["items"]) == 0


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result",
    [
        pytest.param('{"name": {"v": ["name-AAA-{rand}"]}}', "name", "name-AAA-{rand}"),
        pytest.param('{"name": {"v": ["name-BBB-{rand}"]}}', "name", "name-BBB-{rand}"),
        pytest.param('{"name": {"v": ["cc"]}}', None, None),
        pytest.param(
            '{"definition": {"v": ["def-XXX-{rand}"]}}', "definition", "def-XXX-{rand}"
        ),
        pytest.param(
            '{"definition": {"v": ["def-YYY-{rand}"]}}', "definition", "def-YYY-{rand}"
        ),
        pytest.param('{"definition": {"v": ["cc"]}}', None, None),
    ],
)
def test_filtering_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    filter_by = filter_by.replace("{rand}", rand)
    url = f"/concepts/compounds?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert response.status_code == 200
    if expected_result:
        assert len(res["items"]) > 0
        # Each returned row has a field whose value is equal to the specified filter value
        for row in res["items"]:
            assert row[expected_matched_field] == expected_result.replace(
                "{rand}", rand
            )
    else:
        assert len(res["items"]) == 0


# Compound Aliases


def test_get_compound_aliases_pagination(api_client):
    results_paginated: dict = {}
    sort_by = '{"name": true}'
    for page_number in range(1, 4):
        url = f"/concepts/compound-aliases?page_number={page_number}&page_size=10&sort_by={sort_by}"
        response = api_client.get(url)
        res = response.json()
        res_names = list(map(lambda x: x["name"], res["items"]))
        results_paginated[page_number] = res_names
        log.info("Page %s: %s", page_number, res_names)

    log.info("All pages: %s", results_paginated)

    results_paginated_merged = list(
        set(list(reduce(lambda a, b: a + b, list(results_paginated.values()))))
    )
    log.info("All unique rows returned by pagination: %s", results_paginated_merged)

    res_all = api_client.get(
        f"/concepts/compound-aliases?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    results_all_in_one_page = list(map(lambda x: x["name"], res_all["items"]))
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)
    assert len(compound_aliases_all) == len(results_paginated_merged)


@pytest.mark.parametrize(
    "page_size, page_number, total_count, sort_by, expected_result_len",
    [
        pytest.param(None, None, None, None, 10),
        pytest.param(3, 1, True, None, 3),
        pytest.param(3, 2, True, None, 3),
        pytest.param(10, 2, True, None, 10),
        pytest.param(10, 1, True, '{"name": false}', 10),
        pytest.param(10, 2, True, '{"name": true}', 10),
    ],
)
def test_get_compound_aliases(
    api_client, page_size, page_number, total_count, sort_by, expected_result_len
):
    url = "/concepts/compound-aliases"
    query_params = []
    if page_size:
        query_params.append(f"page_size={page_size}")
    if page_number:
        query_params.append(f"page_number={page_number}")
    if total_count:
        query_params.append(f"total_count={total_count}")
    if sort_by:
        query_params.append(f"sort_by={sort_by}")

    if query_params:
        url = f"{url}?{'&'.join(query_params)}"

    log.info("GET %s", url)
    response = api_client.get(url)
    res = response.json()

    assert response.status_code == 200

    # Check fields included in the response
    assert list(res.keys()) == ["items", "total", "page", "size"]
    assert len(res["items"]) == expected_result_len
    assert res["total"] == (len(compound_aliases_all) if total_count else 0)
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    if sort_by:
        # sort_by is JSON string in the form: {"sort_field_name": is_ascending_order}
        sort_by_dict = json.loads(sort_by)
        sort_field: str = list(sort_by_dict.keys())[0]
        sort_order_ascending: bool = list(sort_by_dict.values())[0]

        # extract list of values of 'sort_field_name' field from the returned result
        result_vals = list(map(lambda x: x[sort_field], res["items"]))
        result_vals_sorted_locally = result_vals.copy()
        result_vals_sorted_locally.sort(reverse=not sort_order_ascending)
        assert result_vals == result_vals_sorted_locally


@pytest.mark.parametrize(
    "export_format",
    [
        pytest.param("text/csv"),
        pytest.param("text/xml"),
        pytest.param(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    ],
)
def test_get_compound_aliases_csv_xml_excel(api_client, export_format):
    url = "/concepts/compound-aliases"
    TestUtils.verify_exported_data_format(api_client, export_format, url)


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param('{"*": {"v": ["aaa"]}}', "name", "compAlias-AAA"),
        pytest.param('{"*": {"v": ["bBb"]}}', "name", "compAlias-BBB"),
        pytest.param(
            '{"*": {"v": ["wn-us"], "op": "co"}}', "user_initials", "unknown-user"
        ),
        pytest.param('{"*": {"v": ["Draft"]}}', "status", "Draft"),
        pytest.param('{"*": {"v": ["0.1"]}}', "version", "0.1"),
        pytest.param('{"*": {"v": ["ccc"]}}', None, None),
    ],
)
def test_compound_aliases_filtering_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    url = f"/concepts/compound-aliases?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert response.status_code == 200
    if expected_result_prefix:
        assert len(res["items"]) > 0
        # Each returned row has a field that starts with the specified filter value
        for row in res["items"]:
            assert row[expected_matched_field].startswith(expected_result_prefix)
    else:
        assert len(res["items"]) == 0


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result",
    [
        pytest.param(
            '{"name": {"v": ["compAlias-AAA-{rand}-1"]}}',
            "name",
            "compAlias-AAA-{rand}-1",
        ),
        pytest.param(
            '{"name": {"v": ["compAlias-BBB-{rand}-1"]}}',
            "name",
            "compAlias-BBB-{rand}-1",
        ),
        pytest.param('{"name": {"v": ["cc"]}}', None, None),
        pytest.param(
            '{"definition": {"v": ["def-XXX-{rand}-1"]}}',
            "definition",
            "def-XXX-{rand}-1",
        ),
        pytest.param(
            '{"definition": {"v": ["def-YYY-{rand}-1"]}}',
            "definition",
            "def-YYY-{rand}-1",
        ),
        pytest.param('{"definition": {"v": ["cc"]}}', None, None),
    ],
)
def test_compound_aliases_filtering_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    filter_by = filter_by.replace("{rand}", rand)
    url = f"/concepts/compound-aliases?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert response.status_code == 200
    if expected_result:
        assert len(res["items"]) > 0
        # Each returned row has a field whose value is equal to the specified filter value
        for row in res["items"]:
            assert row[expected_matched_field] == expected_result.replace(
                "{rand}", rand
            )
    else:
        assert len(res["items"]) == 0
