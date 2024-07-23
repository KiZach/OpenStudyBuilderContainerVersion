"""
Tests for /studies/{uid}/study-epochs endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

from unittest import mock

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api import main
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.tests.integration.utils.api import (
    drop_db,
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_study_epoch_codelists_ret_cat_and_lib,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

# Global variables shared between fixtures and tests
study: Study
study_epoch_uid: str
epoch_subtype_uid: str
epoch_subtype2_uid: str


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(main.app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studyepochapi"
    inject_and_clear_db(db_name)
    inject_base_data()
    global epoch_subtype_uid
    global epoch_subtype2_uid
    global study
    study = TestUtils.create_study()
    db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
    db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
    create_study_epoch_codelists_ret_cat_and_lib()

    epoch_subtype_uid = "EpochSubType_0001"
    epoch_subtype2_uid = "EpochSubType_0002"
    yield
    drop_db(db_name)


def test_epoch_modify_actions_on_locked_study(api_client):
    global study_epoch_uid
    response = api_client.post(
        f"/studies/{study.uid}/study-epochs",
        json={
            "study_uid": study.uid,
            "epoch_subtype": epoch_subtype_uid,
        },
    )
    res = response.json()
    assert response.status_code == 201

    # get all epochs
    response = api_client.get(
        f"/studies/{study.uid}/study-epoch/audit-trail/",
    )
    res = response.json()
    assert response.status_code == 200
    old_res = res
    study_epoch_uid = res[0]["uid"]

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
        f"/studies/{study.uid}/study-epochs",
        json={
            "study_uid": study.uid,
            "epoch_subtype": epoch_subtype2_uid,
        },
    )
    res = response.json()
    assert response.status_code == 400
    assert res["message"] == f"Study with specified uid '{study.uid}' is locked."

    # edit epoch
    response = api_client.patch(
        f"/studies/{study.uid}/study-epochs/{study_epoch_uid}",
        json={
            "study_uid": study.uid,
            "name": "New_epoch_Name_1",
            "change_description": "this is a changing test",
        },
    )
    res = response.json()
    assert response.status_code == 400
    assert res["message"] == f"Study with specified uid '{study.uid}' is locked."

    # get all history when was locked
    response = api_client.get(
        f"/studies/{study.uid}/study-epoch/audit-trail/",
    )
    res = response.json()
    assert response.status_code == 200
    for i, _ in enumerate(old_res):
        old_res[i]["study_version"] = mock.ANY
    assert old_res == res

    # test cannot delete
    response = api_client.delete(f"/studies/{study.uid}/study-epochs/{study_epoch_uid}")
    assert response.status_code == 400
    assert (
        response.json()["message"]
        == f"Study with specified uid '{study.uid}' is locked."
    )


def test_study_epoch_with_study_epoch_subtype_relationship(api_client):
    # get specific study epoch
    response = api_client.get(
        f"/studies/{study.uid}/study-epochs/{study_epoch_uid}",
    )
    res = response.json()
    assert response.status_code == 200
    assert res["epoch_subtype"] == epoch_subtype_uid
    before_unlock = res

    # get study epoch headers
    response = api_client.get(
        f"/studies/{study.uid}/study-epochs/headers?field_name=epoch_subtype",
    )
    res = response.json()
    assert response.status_code == 200
    assert res == [epoch_subtype_uid]

    # Unlock -- Study remain unlocked
    response = api_client.delete(f"/studies/{study.uid}/locks")
    assert response.status_code == 200

    # edit study epoch
    response = api_client.patch(
        f"/studies/{study.uid}/study-epochs/{study_epoch_uid}",
        json={
            "study_uid": study.uid,
            "epoch_subtype": epoch_subtype2_uid,
            "change_description": "new epoch subtype",
        },
    )
    res = response.json()
    assert response.status_code == 200
    assert res["epoch_subtype"] == epoch_subtype2_uid

    # get all study epochs of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-epochs?study_value_version=1",
    )
    res = response.json()
    assert response.status_code == 200
    before_unlock["study_version"] = mock.ANY
    assert res["items"][0] == before_unlock

    # get specific study epoch of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-epochs/{study_epoch_uid}?study_value_version=1",
    )
    res = response.json()
    assert response.status_code == 200
    assert res == before_unlock

    # get study epoch headers of specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-epochs/headers?field_name=epoch_subtype&study_value_version=1",
    )
    res = response.json()
    assert response.status_code == 200
    assert res == [epoch_subtype_uid]

    # get all study epochs
    response = api_client.get(
        f"/studies/{study.uid}/study-epochs",
    )
    res = response.json()
    assert response.status_code == 200
    assert res["items"][0]["epoch_subtype"] == epoch_subtype2_uid

    # get specific study epoch
    response = api_client.get(
        f"/studies/{study.uid}/study-epochs/{study_epoch_uid}",
    )
    res = response.json()
    assert response.status_code == 200
    assert res["epoch_subtype"] == epoch_subtype2_uid

    # get study epochs headers
    response = api_client.get(
        f"/studies/{study.uid}/study-epochs/headers?field_name=epoch_subtype",
    )
    res = response.json()
    assert response.status_code == 200
    assert res == [epoch_subtype2_uid]


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
def test_get_study_epochs_csv_xml_excel(api_client, export_format):
    url = f"/studies/{study.uid}/study-epochs"
    exported_data = TestUtils.verify_exported_data_format(
        api_client, export_format, url
    )
    if export_format == "text/csv":
        assert "study_version" in str(exported_data.read())
        assert "LATEST" in str(exported_data.read())


def test_study_epoch_order_when_epoch_get_deleted_or_modified(api_client):
    study_for_tests = TestUtils.create_study()
    response = api_client.post(
        f"/studies/{study_for_tests.uid}/study-epochs",
        json={
            "study_uid": study_for_tests.uid,
            "epoch_subtype": epoch_subtype_uid,
        },
    )
    epoch_subtype_1 = response.json()
    assert response.status_code == 201
    assert epoch_subtype_1["order"] == 1
    assert epoch_subtype_1["epoch_name"] == "Epoch Subtype"

    response = api_client.post(
        f"/studies/{study_for_tests.uid}/study-epochs",
        json={
            "study_uid": study_for_tests.uid,
            "epoch_subtype": epoch_subtype_uid,
        },
    )
    epoch_subtype_2 = response.json()
    assert response.status_code == 201
    assert epoch_subtype_2["order"] == 2
    assert epoch_subtype_2["epoch_name"] == "Epoch Subtype 2"

    # Deleting an Epoch from the same Subtype
    response = api_client.delete(
        f"/studies/{study_for_tests.uid}/study-epochs/{epoch_subtype_1['uid']}",
    )
    assert response.status_code == 204
    response = api_client.get(
        f"/studies/{study_for_tests.uid}/study-epochs/{epoch_subtype_2['uid']}",
    )
    old_subtype_2_new_subtype_1 = response.json()
    assert response.status_code == 200
    assert old_subtype_2_new_subtype_1["order"] == 1
    assert old_subtype_2_new_subtype_1["epoch_name"] == "Epoch Subtype"

    response = api_client.post(
        f"/studies/{study_for_tests.uid}/study-epochs",
        json={
            "study_uid": study_for_tests.uid,
            "epoch_subtype": epoch_subtype2_uid,
        },
    )
    epoch_subtype_2_1 = response.json()
    assert response.status_code == 201
    assert epoch_subtype_2_1["order"] == 2
    assert epoch_subtype_2_1["epoch_name"] == "Epoch Subtype1"

    response = api_client.delete(
        f"/studies/{study_for_tests.uid}/study-epochs/{old_subtype_2_new_subtype_1['uid']}",
    )
    assert response.status_code == 204

    response = api_client.get(
        f"/studies/{study_for_tests.uid}/study-epochs/{epoch_subtype_2_1['uid']}",
    )
    assert response.status_code == 200
    epoch_subtype_2_1 = response.json()
    assert epoch_subtype_2_1["order"] == 1
    assert epoch_subtype_2_1["epoch_name"] == "Epoch Subtype1"

    response = api_client.get(
        f"/studies/{study_for_tests.uid}/study-epochs",
    )
    assert response.status_code == 200
    all_epochs = response.json()["items"]
    assert len(all_epochs) == 1

    response = api_client.post(
        f"/studies/{study_for_tests.uid}/study-epochs",
        json={
            "study_uid": study_for_tests.uid,
            "epoch_subtype": epoch_subtype2_uid,
        },
    )
    epoch_subtype_2_2 = response.json()
    assert response.status_code == 201
    assert epoch_subtype_2_2["order"] == 2
    assert epoch_subtype_2_2["epoch_name"] == "Epoch Subtype1 2"

    response = api_client.get(
        f"/studies/{study_for_tests.uid}/study-epochs/{epoch_subtype_2_1['uid']}",
    )
    assert response.status_code == 200
    epoch_subtype_2_1 = response.json()
    assert epoch_subtype_2_1["order"] == 1
    assert epoch_subtype_2_1["epoch_name"] == "Epoch Subtype1 1"

    response = api_client.post(
        f"/studies/{study_for_tests.uid}/study-epochs",
        json={
            "study_uid": study_for_tests.uid,
            "epoch_subtype": epoch_subtype2_uid,
        },
    )
    epoch_subtype_2_3 = response.json()
    assert response.status_code == 201
    assert epoch_subtype_2_3["order"] == 3
    assert epoch_subtype_2_3["epoch_name"] == "Epoch Subtype1 3"

    response = api_client.patch(
        f"/studies/{study_for_tests.uid}/study-epochs/{epoch_subtype_2_1['uid']}/order/2"
    )
    assert response.status_code == 200
    res = response.json()
    assert res["order"] == 3

    response = api_client.get(
        f"/studies/{study_for_tests.uid}/study-epochs",
    )
    assert response.status_code == 200
    all_epochs = response.json()["items"]
    assert len(all_epochs) == 3
    assert all_epochs[0]["uid"] == epoch_subtype_2_2["uid"]
    assert all_epochs[0]["order"] == 1
    assert all_epochs[1]["uid"] == epoch_subtype_2_3["uid"]
    assert all_epochs[1]["order"] == 2
    assert all_epochs[2]["uid"] == epoch_subtype_2_1["uid"]
    assert all_epochs[2]["order"] == 3
