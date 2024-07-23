"""
Tests for sponsor ct package
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging
import urllib.parse
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import (
    drop_db,
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
catalogue: str
cdisc_package_name: str
sponsor_package_name: str

URL = "/ct/packages"


@pytest.fixture(scope="function")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="function")
def test_data():
    """Initialize test data"""
    db_name = "sponsor-ct-packages.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global catalogue
    global cdisc_package_name
    global sponsor_package_name

    catalogue = "SDTM CT"
    cdisc_package_name = "SDTM CT 2020-03-27"

    TestUtils.create_ct_package(
        catalogue=catalogue,
        name=cdisc_package_name,
        approve_elements=False,
        effective_date=datetime(2020, 3, 27, tzinfo=timezone.utc),
    )
    sponsor_package = TestUtils.create_sponsor_ct_package(
        extends_package=cdisc_package_name,
        effective_date=date.today(),
    )
    sponsor_package_name = sponsor_package.name

    yield

    drop_db(db_name)


SPONSOR_CT_PACKAGES_FIELDS_ALL = [
    "uid",
    "catalogue_name",
    "name",
    "label",
    "description",
    "href",
    "registration_status",
    "source",
    "import_date",
    "effective_date",
    "user_initials",
    "extends_package",
]

SPONSOR_CT_PACKAGES_FIELDS_NOT_NULL = [
    "uid",
    "catalogue_name",
    "name",
    "import_date",
    "effective_date",
    "user_initials",
    "extends_package",
]


def test_get_all_ct_packages(api_client):
    """Test get sponsor ct packages"""
    response = api_client.get(f"{URL}?standards_only=false")
    assert validate_all_packages_list(
        response,
        expected_sponsor_num=1,
        expected_sponsor_package_uid=sponsor_package_name,
    )


def test_get_sponsor_ct_packages(api_client):
    """Test get sponsor ct packages"""
    response = api_client.get(f"{URL}?sponsor_only=true")
    assert validate_sponsor_package_list(
        response, expected_num=1, expected_name=sponsor_package_name
    )


def test_get_standard_ct_packages(api_client):
    """Test get standard ct packages"""
    response = api_client.get(URL)
    res = response.json()
    assert response.status_code == 200
    assert len(res) > 0
    for package in res:
        assert package["extends_package"] is None


def test_post_sponsor_ct_package(api_client):
    db.cypher_query("CREATE CONSTRAINT FOR (p:CTPackage) REQUIRE (p.uid) IS NODE KEY")
    # Create a new sponsor package with a pre-existing date
    # Expect it to fail as this is forbidden
    response = api_client.post(
        f"{URL}/sponsor",
        json={
            "extends_package": cdisc_package_name,
            "effective_date": date.today().strftime("%Y-%m-%d"),
        },
    )
    assert response.status_code == 400

    # Create a sponsor package with a new date
    response = api_client.post(
        f"{URL}/sponsor",
        json={
            "extends_package": cdisc_package_name,
            "effective_date": (date.today() - timedelta(days=1)).strftime("%Y-%m-%d"),
        },
    )
    res = response.json()
    log.info("Created Sponsor CT Package: %s", res)

    expected_package_name = (
        f"Sponsor {catalogue} {(date.today() - timedelta(days=1)).strftime('%Y-%m-%d')}"
    )
    assert response.status_code == 201
    assert res["uid"]
    assert res["uid"] == expected_package_name
    assert res["name"] == res["uid"]
    assert set(list(res.keys())) == set(SPONSOR_CT_PACKAGES_FIELDS_ALL)
    for key in SPONSOR_CT_PACKAGES_FIELDS_NOT_NULL:
        assert res[key] is not None

    # Finally, test the package GET endpoints are returning the new package
    # Sponsor only
    get_sponsor_only_res = api_client.get(f"{URL}?sponsor_only=true")
    assert validate_sponsor_package_list(
        get_sponsor_only_res, expected_name=expected_package_name, expected_num=2
    )

    # Get all
    all_packages_res = api_client.get(f"{URL}?standards_only=false")
    assert validate_all_packages_list(
        all_packages_res,
        expected_sponsor_num=2,
        expected_sponsor_package_uid=expected_package_name,
    )


def test_get_codelists_sponsor_ct_package(api_client):
    package = create_sponsor_package(
        api_client, (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    )

    # Check that codelists have properly been attached to the package
    # First, get list of expected uids
    cdisc_package_codelists_uids, sponsor_codelists_uids = list_expected_codelist_uids(
        api_client, cdisc_package_name
    )
    # Now, list codelists for the sponsor package
    # It should contain both the codelists from parent CDISC package
    # As well as all of the sponsor codelists
    sponsor_package_codelists_response = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(package['name'])}&page_size=0&is_sponsor=true"
    )
    sponsor_package_codelists_res = sponsor_package_codelists_response.json()
    assert sponsor_package_codelists_response.status_code == 200
    assert len(sponsor_package_codelists_res["items"]) > 0
    codelist_uids = [
        codelist["codelist_uid"] for codelist in sponsor_package_codelists_res["items"]
    ]
    assert set(cdisc_package_codelists_uids) <= set(codelist_uids)
    assert set(sponsor_codelists_uids) <= set(codelist_uids)
    assert len(cdisc_package_codelists_uids) + len(sponsor_codelists_uids) == len(
        codelist_uids
    )


def test_get_terms_sponsor_ct_package(api_client):
    package = create_sponsor_package(
        api_client, (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    )

    # Check that terms have properly been attached to the package
    # First, get list of expected uids
    cdisc_package_terms_uids, sponsor_terms_uids = list_expected_term_uids(
        api_client, cdisc_package_name
    )
    sponsor_package_terms_response = api_client.get(
        f"ct/terms?package={urllib.parse.quote_plus(package['name'])}&page_size=0&is_sponsor=true"
    )
    sponsor_package_terms_res = sponsor_package_terms_response.json()
    assert sponsor_package_terms_response.status_code == 200
    assert len(sponsor_package_terms_res["items"]) > 0
    term_uids = [term["term_uid"] for term in sponsor_package_terms_res["items"]]
    assert set(cdisc_package_terms_uids) <= set(term_uids)
    assert set(sponsor_terms_uids) <= set(term_uids)
    assert len(set(cdisc_package_terms_uids + sponsor_terms_uids)) == len(
        set(term_uids)
    )


def test_get_codelists_identical_sponsor_ct_package_nochanges(api_client):
    package = create_sponsor_package(
        api_client, (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    )

    # When the GET API endpoint /ct/codelists?package=<Test Sponsor CT Package>
    # is called to get codelists content of a Sponsor CT Package
    sponsor_package_codelists = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(package['name'])}&page_size=0&is_sponsor=true"
    ).json()["items"]

    # Then the API must return all codelists content related to a Sponsor CT Package
    # identical to the return from GET /ct/codelists
    all_codelists = api_client.get("ct/codelists?page_size=0").json()["items"]

    # Validate that all codelists in sponsor package are contained as is in the full list
    assert all([codelist in all_codelists for codelist in sponsor_package_codelists])


def test_get_terms_identical_sponsor_ct_package_nochanges(api_client):
    package = create_sponsor_package(
        api_client, (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    )

    # When the GET API endpoint /ct/terms?package=<Test Sponsor CT Package>
    # is called to get terms content of a Sponsor CT Package
    sponsor_package_terms = api_client.get(
        f"ct/terms?package={urllib.parse.quote_plus(package['name'])}&page_size=0&is_sponsor=true"
    ).json()["items"]

    # Then the API must return all terms content related to a Sponsor CT Package
    # identical to the return from GET /ct/terms
    all_terms = api_client.get("ct/terms?page_size=0").json()["items"]

    # Validate that all terms in sponsor package are contained as is in the full list
    assert all([codelist in all_terms for codelist in sponsor_package_terms])


def test_sponsor_ct_package_is_persistent_sponsor_codelists(api_client):
    # Given a Sponsor CT Package exist for a CT Catalogue related to a CDISC CT Package
    package = initialize_persistence_tests(api_client)

    initial_codelists = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]

    # When the POST API endpoint /ct/codelists/ is called
    # to create a new Sponsor Codelist not related to the test Sponsor CT Package
    new_codelist = TestUtils.create_ct_codelist(
        name=TestUtils.random_str(max_length=6, prefix="CTCodelist"),
        library_name="Sponsor",
        approve=True,
        effective_date=datetime.now(),
    )

    # Then the call to the GET API endpoint /ct/codelists?package=<Test Sponsor CT Package>
    # with a reference to the test Sponsor CT Package will not return the newly created Sponsor codelist
    updated_codelists = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    assert len(initial_codelists) == len(updated_codelists)
    assert new_codelist.codelist_uid not in [
        codelist["codelist_uid"] for codelist in updated_codelists
    ]


def test_sponsor_ct_package_is_persistent_sponsor_terms(api_client):
    # Given a Sponsor CT Package exist for a CT Catalogue related to a CDISC CT Package
    package = initialize_persistence_tests(api_client)

    # Create a Sponsor codelist
    new_codelist = TestUtils.create_ct_codelist(
        name=TestUtils.random_str(max_length=6, prefix="CTCodelist"),
        library_name="Sponsor",
        approve=True,
        extensible=True,
        effective_date=datetime.now(),
    )

    initial_terms = api_client.get(
        f"ct/terms?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]

    # When the POST API endpoint /ct/terms/ is called
    # to create a new Sponsor Term not related to the test Sponsor CT Package
    new_term = TestUtils.create_ct_term(
        codelist_uid=new_codelist.codelist_uid,
        library_name="Sponsor",
        effective_date=datetime.now(),
    )

    # Then the call to the GET API endpoint /ct/terms?package=<Test Sponsor CT Package>
    # with a reference to the test Sponsor CT Package will not return the newly created Sponsor term
    updated_terms = api_client.get(
        f"ct/terms?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    assert len(initial_terms) == len(updated_terms)
    assert new_term.term_uid not in [term["term_uid"] for term in updated_terms]


def test_sponsor_ct_package_is_persistent_sponsor_name_cdisc_codelists(api_client):
    # Given a Sponsor CT Package exist for a CT Catalogue related to a CDISC CT Package
    package = initialize_persistence_tests(api_client)

    initial_codelists = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    cdisc_codelist = next(
        (
            codelist
            for codelist in initial_codelists
            if codelist["library_name"] == "CDISC"
        ),
        None,
    )
    # When the PATCH API endpoint /ct/codelists/<Test CDISC Codelist uid>/names is called
    # to update sponsor name for a CDISC Codelist related to the test Sponsor CT Package
    new_name = "New CDISC name"
    api_client.patch(
        f"ct/codelists/{cdisc_codelist['codelist_uid']}/names",
        json={"name": new_name, "change_description": new_name},
    )
    # Then the call to the GET API endpoint /ct/codelists?package=<Test Sponsor CT Package>
    # with a reference to the test Sponsor CT Package will return the original sponsor name and name_sentence_case attribute value
    # for the updated CDISC codelist
    updated_codelists = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    assert len(initial_codelists) == len(updated_codelists)
    assert [x for x in updated_codelists if x not in initial_codelists] == []


def test_sponsor_ct_package_is_persistent_sponsor_name_sponsor_codelists(api_client):
    # Given a Sponsor CT Package exist for a CT Catalogue related to a CDISC CT Package
    package = initialize_persistence_tests(api_client)

    initial_codelists = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    sponsor_codelist = next(
        (
            codelist
            for codelist in initial_codelists
            if codelist["library_name"] == "Sponsor"
        ),
        None,
    )
    # When the PATCH API endpoint /ct/codelists/<Test Sponsor Codelist uid>/names is called
    # to update sponsor name for a Sponsor Codelist related to the test Sponsor CT Package
    new_name = "New Sponsor name"
    api_client.patch(
        f"ct/codelists/{sponsor_codelist['codelist_uid']}/names",
        json={"name": new_name, "change_description": new_name},
    )
    # Then the call to the GET API endpoint /ct/codelists?package=<Test Sponsor CT Package>
    # with a reference to the test Sponsor CT Package will return the original sponsor name and name_sentence_case attribute value
    # for the updated Sponsor codelist
    updated_codelists = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    assert len(initial_codelists) == len(updated_codelists)
    assert [x for x in updated_codelists if x not in initial_codelists] == []


def test_sponsor_ct_package_is_persistent_attributes_sponsor_codelists(api_client):
    # Given a Sponsor CT Package exist for a CT Catalogue related to a CDISC CT Package
    package = initialize_persistence_tests(api_client)

    initial_codelists = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    sponsor_codelist = next(
        (
            codelist
            for codelist in initial_codelists
            if codelist["library_name"] == "Sponsor"
        ),
        None,
    )
    # When the PATCH API endpoint /ct/codelists/<Test Sponsor Codelist uid>/attributes is called
    # to update attributes for a Sponsor Codelist related to the test Sponsor CT Package
    new_definition = "New definition"
    api_client.post(
        f"ct/codelists/{sponsor_codelist['codelist_uid']}/attributes/versions",
    )
    api_client.patch(
        f"ct/codelists/{sponsor_codelist['codelist_uid']}/attributes",
        json={"definition": new_definition},
    )
    # Then the call to the GET API endpoint /ct/codelists?package=<Test Sponsor CT Package>
    # with a reference to the test Sponsor CT Package will return the original attribute values
    # for the updated Sponsor codelist
    updated_codelists = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    assert len(initial_codelists) == len(updated_codelists)
    assert [x for x in updated_codelists if x not in initial_codelists] == []


def test_sponsor_ct_package_is_persistent_sponsor_name_cdisc_terms(api_client):
    # Given a Sponsor CT Package exist for a CT Catalogue related to a CDISC CT Package
    package = initialize_persistence_tests(api_client)

    initial_terms = api_client.get(
        f"ct/terms?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    cdisc_term = next(
        (term for term in initial_terms if term["library_name"] == "CDISC"),
        None,
    )
    # When the PATCH API endpoint /ct/terms/<Test CDISC Term uid>/names is called
    # to update sponsor name for a CDISC Term related to the test Sponsor CT Package
    new_name = "New CDISC name"
    api_client.patch(
        f"ct/terms/{cdisc_term['term_uid']}/names",
        json={"name": new_name, "change_description": new_name},
    )
    # Then the call to the GET API endpoint /ct/terms?package=<Test Sponsor CT Package>
    # with a reference to the test Sponsor CT Package will return the original sponsor name and name_sentence_case attribute value
    # for the updated CDISC term
    updated_terms = api_client.get(
        f"ct/terms?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    assert len(initial_terms) == len(updated_terms)
    assert [x for x in updated_terms if x not in initial_terms] == []


def test_sponsor_ct_package_is_persistent_sponsor_name_sponsor_terms(api_client):
    # Given a Sponsor CT Package exist for a CT Catalogue related to a CDISC CT Package
    package = initialize_persistence_tests(api_client)

    initial_terms = api_client.get(
        f"ct/terms?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    sponsor_term = next(
        (term for term in initial_terms if term["library_name"] == "Sponsor"),
        None,
    )
    # When the PATCH API endpoint /ct/terms/<Test Sponsor Term uid>/names is called
    # to update sponsor name for a Sponsor Term related to the test Sponsor CT Package
    new_name = "New Sponsor name"
    api_client.patch(
        f"ct/terms/{sponsor_term['term_uid']}/names",
        json={"name": new_name, "change_description": new_name},
    )
    # Then the call to the GET API endpoint /ct/terms?package=<Test Sponsor CT Package>
    # with a reference to the test Sponsor CT Package will return the original sponsor name and name_sentence_case attribute value
    # for the updated Sponsor term
    updated_terms = api_client.get(
        f"ct/terms?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    assert len(initial_terms) == len(updated_terms)
    assert [x for x in updated_terms if x not in initial_terms] == []


def test_sponsor_ct_package_is_persistent_attributes_sponsor_terms(api_client):
    # Given a Sponsor CT Package exist for a CT Catalogue related to a CDISC CT Package
    package = initialize_persistence_tests(api_client)

    initial_terms = api_client.get(
        f"ct/terms?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    sponsor_term = next(
        (term for term in initial_terms if term["library_name"] == "Sponsor"),
        None,
    )
    # When the PATCH API endpoint /ct/terms/<Test Sponsor Term uid>/attributes is called
    # to update attributes for a Sponsor Term related to the test Sponsor CT Package
    new_definition = "New definition"
    api_client.post(
        f"ct/terms/{sponsor_term['term_uid']}/attributes/versions",
    )
    api_client.patch(
        f"ct/terms/{sponsor_term['term_uid']}/attributes",
        json={"definition": new_definition},
    )
    # Then the call to the GET API endpoint /ct/terms?package=<Test Sponsor CT Package>
    # with a reference to the test Sponsor CT Package will return the original attribute values
    # for the updated Sponsor term
    updated_terms = api_client.get(
        f"ct/terms?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    assert len(initial_terms) == len(updated_terms)
    assert [x for x in updated_terms if x not in initial_terms] == []


def initialize_persistence_tests(api_client):
    # Create some older terms and codelists
    TestUtils.create_ct_package(
        number_of_codelists=2,
        catalogue=catalogue,
        name=cdisc_package_name + "_old",
        approve_elements=False,
        effective_date=datetime.now(timezone.utc) - timedelta(days=7),
    )

    # Create an older sponsor package, but more recent that the CDISC one
    package = create_sponsor_package(
        api_client, (date.today() - timedelta(days=3)).strftime("%Y-%m-%d")
    )

    return package


# Utility methods
def create_sponsor_package(api_client, effective_date):
    response = api_client.post(
        f"{URL}/sponsor",
        json={
            "extends_package": cdisc_package_name,
            "effective_date": effective_date,
        },
    )
    res = response.json()
    log.info("Created Sponsor CT Package: %s", res)
    assert response.status_code == 201

    return res


def validate_all_packages_list(
    response, expected_sponsor_num, expected_sponsor_package_uid
):
    res = response.json()

    assert response.status_code == 200

    # Get package in res where extends_package is set
    sponsor_packages = [el for el in res if el["extends_package"] is not None]
    assert len(res) > len(sponsor_packages)
    assert len(sponsor_packages) == expected_sponsor_num

    # Check the expected uid is in the list and extract the package
    sponsor_package = next(
        (el for el in sponsor_packages if el["uid"] == expected_sponsor_package_uid),
        None,
    )
    assert sponsor_package

    # Check fields included in the response
    fields_all_set = set(SPONSOR_CT_PACKAGES_FIELDS_ALL)
    assert set(list(sponsor_package.keys())) == fields_all_set
    for key in SPONSOR_CT_PACKAGES_FIELDS_NOT_NULL:
        assert sponsor_package[key] is not None

    assert sponsor_package["catalogue_name"] == catalogue
    assert sponsor_package["name"] == expected_sponsor_package_uid
    assert sponsor_package["extends_package"] == cdisc_package_name

    return True


def validate_sponsor_package_list(response, expected_name, expected_num):
    res = response.json()

    assert response.status_code == 200

    # Get package in res where extends_package is set
    sponsor_packages = [el for el in res if el["extends_package"] is not None]
    assert len(res) == len(sponsor_packages)
    assert len(sponsor_packages) == expected_num

    # Check fields included in the response
    fields_all_set = set(SPONSOR_CT_PACKAGES_FIELDS_ALL)
    assert set(list(sponsor_packages[0].keys())) == fields_all_set
    for key in SPONSOR_CT_PACKAGES_FIELDS_NOT_NULL:
        assert sponsor_packages[0][key] is not None

    assert sponsor_packages[0]["uid"] == expected_name
    assert sponsor_packages[0]["catalogue_name"] == catalogue
    assert sponsor_packages[0]["name"] == expected_name
    assert sponsor_packages[0]["extends_package"] == cdisc_package_name

    return True


def list_expected_codelist_uids(api_client, parent_package_uid):
    # Codelists in parent CDISC package
    cdisc_package_codelists_response = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(parent_package_uid)}&page_size=0"
    )
    cdisc_package_codelists_res = cdisc_package_codelists_response.json()
    cdisc_package_codelists_uids = [
        codelist["codelist_uid"] for codelist in cdisc_package_codelists_res["items"]
    ]

    # Sponsor codelists
    sponsor_codelists_response = api_client.get(
        "ct/codelists?library=Sponsor&page_size=0"
    )
    sponsor_codelists_res = sponsor_codelists_response.json()
    sponsor_codelists_uids = [
        codelist["codelist_uid"] for codelist in sponsor_codelists_res["items"]
    ]

    return cdisc_package_codelists_uids, sponsor_codelists_uids


def list_expected_term_uids(api_client, parent_package_uid):
    # Terms in parent CDISC package
    cdisc_package_terms_response = api_client.get(
        f"ct/terms?package={urllib.parse.quote_plus(parent_package_uid)}&page_size=0"
    )
    cdisc_package_terms_res = cdisc_package_terms_response.json()
    cdisc_package_terms_uids = [
        term["term_uid"] for term in cdisc_package_terms_res["items"]
    ]

    # Sponsor terms
    sponsor_terms_response = api_client.get("ct/terms?library=Sponsor&page_size=0")
    sponsor_terms_res = sponsor_terms_response.json()
    sponsor_terms_uids = [term["term_uid"] for term in sponsor_terms_res["items"]]

    return cdisc_package_terms_uids, sponsor_terms_uids
