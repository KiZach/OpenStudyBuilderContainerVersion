"""
Tests for /studies/{uid}/study-compounds endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.concepts.compound import Compound
from clinical_mdr_api.models.concepts.compound_alias import CompoundAlias
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.tests.integration.utils.api import (
    drop_db,
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

log = logging.getLogger(__name__)

study: Study
compound: Compound
compound2: Compound
compound_alias: CompoundAlias
compound_alias2: CompoundAlias

initialize_ct_data_map = {
    "TypeOfTreatment": [("CTTerm_000001", "CTTerm_000001")],
    "RouteOfAdministration": [("CTTerm_000002", "CTTerm_000002")],
    "DosageForm": [("CTTerm_000003", "CTTerm_000003")],
    "DispensedIn": [("CTTerm_000004", "CTTerm_000004")],
    "Device": [("CTTerm_000005", "CTTerm_000005")],
    "Formulation": [("CTTerm_000006", "CTTerm_000006")],
    "ReasonForMissingNullValue": [("CTTerm_000007", "CTTerm_000007")],
}


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studycompounds.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global study
    global compound
    global compound2
    global compound_alias
    global compound_alias2

    study = TestUtils.create_study()
    catalogue = "SDTM CT"
    cdisc_package_name = "SDTM CT 2020-03-27"

    standards_ct_package_uid = TestUtils.create_ct_package(
        catalogue=catalogue, name=cdisc_package_name, approve_elements=False
    )
    TestUtils.create_study_standard_version(
        study_uid=study.uid, ct_package_uid=standards_ct_package_uid
    )

    compound = TestUtils.create_compound(name="name-AAA", approve=True)
    compound2 = TestUtils.create_compound(name="name-BBB", approve=True)

    compound_alias = TestUtils.create_compound_alias(
        name="compAlias-AAA", compound_uid=compound.uid, approve=True
    )
    compound_alias2 = TestUtils.create_compound_alias(
        name="compAlias-BBB", compound_uid=compound2.uid, approve=True
    )

    yield
    drop_db(db_name)


def test_compound_modify_actions_on_locked_study(api_client):
    response = api_client.post(
        f"/studies/{study.uid}/study-compounds",
        json={"compound_alias_uid": compound_alias.uid},
    )
    res = response.json()
    assert response.status_code == 201

    # get all compounds
    response = api_client.get(f"/studies/{study.uid}/study-compounds")
    res = response.json()
    assert response.status_code == 200

    # get all compounds
    response = api_client.get(f"/studies/{study.uid}/study-compounds/audit-trail/")
    res = response.json()
    assert response.status_code == 200
    old_res = res
    compound_uid = res[0]["study_compound_uid"]

    # update study title to be able to lock it
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert response.status_code == 200

    # Lock
    response = api_client.post(
        f"/studies/{study.uid}/locks",
        json={"change_description": "Lock 1"},
    )
    assert response.status_code == 201

    response = api_client.post(
        f"/studies/{study.uid}/study-compounds",
        json={"compound_alias_uid": compound_alias.uid},
    )
    res = response.json()
    assert response.status_code == 400
    assert res["message"] == f"Study with specified uid '{study.uid}' is locked."
    # edit compound
    response = api_client.patch(
        f"/studies/{study.uid}/study-compounds/{compound_uid}",
        json={"type_of_treatment_uid": "CTTerm_000001"},
    )
    res = response.json()
    assert response.status_code == 400
    assert res["message"] == f"Study with specified uid '{study.uid}' is locked."

    # get all history when was locked
    response = api_client.get(f"/studies/{study.uid}/study-compounds/audit-trail/")
    res = response.json()
    assert response.status_code == 200
    assert old_res == res

    # test cannot delete
    response = api_client.delete(f"/studies/{study.uid}/study-compounds/{compound_uid}")
    assert response.status_code == 400
    assert (
        response.json()["message"]
        == f"Study with specified uid '{study.uid}' is locked."
    )


def test_get_compounds_data_for_specific_study_version(api_client):
    """
    This test checks the study versioning on study compounds
    """
    # get compound data for first lock
    response = api_client.get(f"/studies/{study.uid}/study-compounds/")
    res = response.json()
    assert response.status_code == 200
    res_old = res

    # Unlock
    response = api_client.delete(f"/studies/{study.uid}/locks")
    assert response.status_code == 200

    response = api_client.post(
        f"/studies/{study.uid}/study-compounds",
        json={"compound_alias_uid": compound_alias2.uid},
    )
    res = response.json()
    assert response.status_code == 201

    # check the study compounds for version 1 is same as first locked
    res_new = api_client.get(
        f"/studies/{study.uid}/study-compounds",
    ).json()
    res_v1 = api_client.get(
        f"/studies/{study.uid}/study-compounds?study_value_version=1",
    ).json()
    for i, _ in enumerate(res_old["items"]):
        res_old["items"][i]["study_version"] = mock.ANY
    assert res_v1 == res_old
    assert res_v1 != res_new


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
def test_get_study_compounds_csv_xml_excel(api_client, export_format):
    url = f"/studies/{study.uid}/study-compounds"
    exported_data = TestUtils.verify_exported_data_format(
        api_client, export_format, url
    )
    if export_format == "text/csv":
        assert "study_version" in str(exported_data.read())
        assert "LATEST" in str(exported_data.read())
