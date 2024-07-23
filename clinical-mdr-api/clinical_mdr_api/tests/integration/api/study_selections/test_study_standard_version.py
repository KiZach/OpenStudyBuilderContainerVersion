"""
Tests for /studies/{uid}/study-standard-versions endpoints
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
from clinical_mdr_api.models import CTTerm
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.tests.integration.utils.api import (
    drop_db,
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
study: Study
standard_version_uid: str
standard_version_type_term: CTTerm
standard_version_type_term2: CTTerm
ct_package_uid: str
ct_package_uid_2: str


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studystandardversionapi"
    inject_and_clear_db(db_name)
    inject_base_data()
    global study
    study = TestUtils.create_study()

    catalogue = "SDTM CT"
    cdisc_package_name = "SDTM CT 2020-03-27"
    cdisc_package_name_2 = "SDTM CT 2020-03-28"

    TestUtils.create_ct_package(
        catalogue=catalogue, name=cdisc_package_name, approve_elements=False
    )
    TestUtils.create_ct_package(
        catalogue=catalogue, name=cdisc_package_name_2, approve_elements=False
    )
    yield

    drop_db(db_name)


def test_study_standard_version_crud_operations(api_client):
    # get all standard versions
    response = api_client.get(
        "/ct/packages",
    )
    res = response.json()
    assert response.status_code == 200
    global ct_package_uid
    global ct_package_uid_2
    ct_package_uid = res[0]["uid"]
    ct_package_uid_2 = res[1]["uid"]

    global standard_version_uid
    response = api_client.post(
        f"/studies/{study.uid}/study-standard-versions",
        json={
            "ct_package_uid": ct_package_uid,
        },
    )
    res = response.json()
    assert response.status_code == 201
    assert res["ct_package"]["uid"] == ct_package_uid
    standard_version_uid = res["uid"]

    response = api_client.post(
        f"/studies/{study.uid}/study-standard-versions",
        json={
            "ct_package_uid": ct_package_uid_2,
        },
    )
    res = response.json()
    assert response.status_code == 400
    assert (
        res["message"]
        == f"Already exists a Standard Version {standard_version_uid} for the study: {study.uid}"
    )

    # get all standard versions
    response = api_client.get(
        f"/studies/{study.uid}/study-standard-versions/",
    )
    res = response.json()
    assert response.status_code == 200

    # # get specific standard versions audit trail
    response = api_client.get(
        f"/studies/{study.uid}/study-standard-versions/{standard_version_uid}/audit-trail/",
    )
    res = response.json()
    assert response.status_code == 200

    response = api_client.patch(
        f"/studies/{study.uid}/study-standard-versions/{standard_version_uid}",
        json={
            "ct_package_uid": ct_package_uid_2,
        },
    )
    res = response.json()
    assert response.status_code == 200
    assert res["ct_package"]["uid"] == ct_package_uid_2

    # test delete
    response = api_client.delete(
        f"/studies/{study.uid}/study-standard-versions/{standard_version_uid}"
    )
    assert response.status_code == 204

    # get all standard versions
    response = api_client.get(
        f"/studies/{study.uid}/study-standard-versions/{standard_version_uid}",
    )
    res = response.json()
    assert response.status_code == 400
    assert (
        res["message"]
        == f"The StudyStandardVersion with uid='{standard_version_uid}' could not be found."
    )


def test_standard_version_modify_actions_on_locked_study(api_client):
    global standard_version_uid
    response = api_client.post(
        f"/studies/{study.uid}/study-standard-versions",
        json={
            "ct_package_uid": ct_package_uid,
        },
    )
    res = response.json()
    assert response.status_code == 201
    standard_version_uid = res["uid"]

    # get all standard versions
    response = api_client.get(
        f"/studies/{study.uid}/study-standard-versions/",
    )
    res = response.json()
    assert response.status_code == 200
    old_res = res

    # # get all standard versions
    response = api_client.get(
        f"/studies/{study.uid}/study-standard-versions/audit-trail/",
    )
    res = response.json()
    assert response.status_code == 200
    old_res = res

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
        f"/studies/{study.uid}/study-standard-versions",
        json={
            "ct_package_uid": ct_package_uid,
        },
    )
    res = response.json()
    assert response.status_code == 400
    assert res["message"] == f"Study with specified uid '{study.uid}' is locked."

    response = api_client.patch(
        f"/studies/{study.uid}/study-standard-versions/{standard_version_uid}",
        json={
            "ct_package_uid": ct_package_uid_2,
        },
    )
    res = response.json()
    assert response.status_code == 400
    assert res["message"] == f"Study with specified uid '{study.uid}' is locked."

    # get all history when was locked
    response = api_client.get(
        f"/studies/{study.uid}/study-standard-versions/audit-trail/",
    )
    res = response.json()
    assert response.status_code == 200
    for i, _ in enumerate(old_res):
        old_res[i]["study_version"] = mock.ANY
    assert old_res == res

    # test cannot delete
    response = api_client.delete(
        f"/studies/{study.uid}/study-standard-versions/{standard_version_uid}"
    )
    assert response.status_code == 400
    assert (
        response.json()["message"]
        == f"Study with specified uid '{study.uid}' is locked."
    )


def test_get_standard_version_data_for_specific_study_version(api_client):
    # get the study standard_version for 1st locked: version 1, used for compare later
    response = api_client.get(
        f"/studies/{study.uid}/study-standard-versions",
    )
    assert response.status_code == 200
    res_old = response.json()

    # Unlock
    response = api_client.delete(f"/studies/{study.uid}/locks")
    assert response.status_code == 200

    response = api_client.patch(
        f"/studies/{study.uid}/study-standard-versions/{standard_version_uid}",
        json={
            "ct_package_uid": ct_package_uid_2,
        },
    )
    assert response.status_code == 200

    # check the study standard_version for version 1 is same as first locked
    res_new = api_client.get(
        f"/studies/{study.uid}/study-standard-versions",
    ).json()
    res_v1 = api_client.get(
        f"/studies/{study.uid}/study-standard-versions?study_value_version=1",
    ).json()
    for i, _ in enumerate(res_old):
        res_old[i]["study_version"] = mock.ANY
    assert res_v1 == res_old
    assert res_v1 != res_new
    response = api_client.get(
        f"/studies/{study.uid}/study-standard-versions?study_value_version=1",
    )
    res = response.json()
    assert response.status_code == 200
    assert res[0]["ct_package"]["uid"] == res_v1[0]["ct_package"]["uid"]


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
def test_get_standard_versions_csv_xml_excel(api_client, export_format):
    url = f"/studies/{study.uid}/study-standard-versions"
    exported_data = TestUtils.verify_exported_data_format(
        api_client, export_format, url
    )
    if export_format == "text/csv":
        assert "study_version" in str(exported_data.read())
        assert "LATEST" in str(exported_data.read())
