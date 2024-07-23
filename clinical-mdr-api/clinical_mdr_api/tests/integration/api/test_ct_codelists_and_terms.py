"""
Tests for /ct/codelists and /ct/terms endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments
import logging
from functools import reduce

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api import models
from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import (
    drop_db,
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
ct_term_dosage: models.CTTerm
ct_term_delivery_device: models.CTTerm
ct_term_dose_frequency: models.CTTerm
ct_term_dispenser: models.CTTerm
ct_term_roa: models.CTTerm


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "ct.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global ct_term_dosage
    global ct_term_delivery_device
    global ct_term_dose_frequency
    global ct_term_dispenser
    global ct_term_roa

    # Create CT Terms
    ct_term_dosage = TestUtils.create_ct_term(sponsor_preferred_name="dosage_form_1")
    ct_term_delivery_device = TestUtils.create_ct_term(
        sponsor_preferred_name="delivery_device_1"
    )
    ct_term_dose_frequency = TestUtils.create_ct_term(
        sponsor_preferred_name="dose_frequency_1"
    )
    ct_term_dispenser = TestUtils.create_ct_term(sponsor_preferred_name="dispenser_1")
    ct_term_roa = TestUtils.create_ct_term(
        sponsor_preferred_name="route_of_administration_1"
    )

    for _x in range(30):
        TestUtils.create_ct_term()

    catalogue_name = TestUtils.create_ct_catalogue()

    for x in range(30):
        TestUtils.create_ct_codelist(
            name=f"My Codelist {x}",
            sponsor_preferred_name=f"My Codelist {x}",
            catalogue_name=catalogue_name,
            extensible=True,
            approve=True,
        )

    yield

    drop_db(db_name)


@pytest.mark.parametrize(
    "base_url, page_size, sort_by",
    [
        pytest.param("/ct/terms", 20, '{"term_uid": true}'),
        pytest.param("/ct/terms/names", 20, '{"term_uid": true}'),
        pytest.param("/ct/terms/attributes", 20, '{"term_uid": true}'),
        pytest.param("/ct/terms", 20, '{"codelist_uid": true}'),  # "term_uid": false
        pytest.param("/ct/terms/names", 20, '{"sponsor_preferred_name": true}'),
        pytest.param("/ct/terms/attributes", 20, '{"code_submission_value": true}'),
        pytest.param("/ct/terms", 20, '{"term_uid": false}'),
        pytest.param("/ct/terms/names", 20, '{"term_uid": false}'),
        pytest.param("/ct/terms/attributes", 20, '{"term_uid": false}'),
    ],
)
def test_get_ct_terms_pagination(api_client, base_url, page_size, sort_by):
    results_paginated: dict = {}
    for page_number in range(1, 4):
        url = f"{base_url}?page_number={page_number}&page_size={page_size}&sort_by={sort_by}"
        response = api_client.get(url)
        res = response.json()
        res_names = list(map(lambda x: x["term_uid"], res["items"]))
        results_paginated[page_number] = res_names
        log.info("Page %s: %s", page_number, res_names)

    results_paginated_merged = list(
        set(list(reduce(lambda a, b: a + b, list(results_paginated.values()))))
    )
    log.info("All unique rows returned by pagination: %s", results_paginated_merged)

    res_all = api_client.get(
        f"{base_url}?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    results_all_in_one_page = list(map(lambda x: x["term_uid"], res_all["items"]))
    log.info("All rows in one page: %s", results_all_in_one_page)
    log.info(
        "Missing in paginated: %s",
        set(results_all_in_one_page) - set(results_paginated_merged),
    )
    log.info(
        "Extra in paginated: %s",
        set(results_paginated_merged) - set(results_all_in_one_page),
    )
    assert len(results_all_in_one_page) == len(results_paginated_merged)


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
def test_get_ct_terms_csv_xml_excel(api_client, export_format):
    url = "/ct/terms"
    TestUtils.verify_exported_data_format(api_client, export_format, url)


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
def test_get_ct_codelists_csv_xml_excel(api_client, export_format):
    url = "/ct/codelists"
    TestUtils.verify_exported_data_format(api_client, export_format, url)


def test_codelist_filtering_on_terms(api_client):
    response = api_client.get(
        """ct/codelists?term_filter={"operator": "and", "term_uids": ["CTTerm_000001", "CTTerm_000002"]}"""
    )
    res = response.json()

    assert response.status_code == 200

    assert len(res["items"]) == 1
    assert res["items"][0]["codelist_uid"] == "C66737"


def test_retire_unused_term(api_client):
    # create a new codelist
    codelist = TestUtils.create_ct_codelist(
        name="RetireCodelist",
        sponsor_preferred_name="RetireCodelist",
        extensible=True,
        approve=True,
    )
    # add two new terms
    term_to_remove_and_retire = TestUtils.create_ct_term(
        sponsor_preferred_name="term_to_remove_and_retire",
        codelist_uid=codelist.codelist_uid,
    )
    term_to_retire = TestUtils.create_ct_term(
        sponsor_preferred_name="term_to_retire", codelist_uid=codelist.codelist_uid
    )

    # fetch the term to be removed, ensure it's part of only the expected codelist
    response = api_client.get(
        f"ct/terms/{term_to_remove_and_retire.term_uid}/attributes"
    )
    res = response.json()
    assert response.status_code == 200
    assert len(res["codelists"]) == 1
    assert res["codelists"][0]["codelist_uid"] == codelist.codelist_uid

    # remove the term from the codelist
    response = api_client.delete(
        f"/ct/codelists/{codelist.codelist_uid}/terms/{term_to_remove_and_retire.term_uid}"
    )
    assert response.status_code == 201

    # fetch the removed term, ensure it's not part of any codelist
    response = api_client.get(
        f"ct/terms/{term_to_remove_and_retire.term_uid}/attributes"
    )
    res = response.json()
    assert response.status_code == 200
    assert len(res["codelists"]) == 0

    # fetch the codelist terms and check that there is only one term
    response = api_client.get("ct/terms?codelist_name=RetireCodelist")
    res = response.json()
    assert response.status_code == 200
    assert len(res["items"]) == 1

    # retire the removed term attributes and names
    response = api_client.delete(
        f"/ct/terms/{term_to_remove_and_retire.term_uid}/attributes/activations"
    )
    assert response.status_code == 200
    response = api_client.delete(
        f"/ct/terms/{term_to_remove_and_retire.term_uid}/names/activations"
    )
    assert response.status_code == 200

    # retire the remaining term attributes and names
    response = api_client.delete(
        f"/ct/terms/{term_to_retire.term_uid}/attributes/activations"
    )
    assert response.status_code == 200
    response = api_client.delete(
        f"/ct/terms/{term_to_retire.term_uid}/names/activations"
    )
    assert response.status_code == 200

    # fetch codelist terms and check that there is still one term
    response = api_client.get("ct/terms?codelist_name=RetireCodelist")
    res = response.json()
    assert response.status_code == 200
    assert len(res["items"]) == 1
