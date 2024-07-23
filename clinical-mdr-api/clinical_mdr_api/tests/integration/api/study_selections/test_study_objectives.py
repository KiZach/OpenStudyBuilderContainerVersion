"""
Tests for /studies/{uid}/study-objectives endpoints
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
from neomodel import db

from clinical_mdr_api.domain_repositories.models.syntax import (
    ObjectiveRoot,
    ObjectiveTemplateRoot,
)
from clinical_mdr_api.main import app
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.tests.integration.utils.api import (
    drop_db,
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_TERM_NAME_CYPHER,
    STARTUP_STUDY_OBJECTIVE_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

log = logging.getLogger(__name__)

study: Study
study_objective_uid: str


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studyobjectiveapi"
    inject_and_clear_db(db_name)
    inject_base_data()
    global study
    study = TestUtils.create_study()

    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
    db.cypher_query(STARTUP_STUDY_OBJECTIVE_CYPHER)
    ObjectiveTemplateRoot.generate_node_uids_if_not_present()
    ObjectiveRoot.generate_node_uids_if_not_present()

    yield
    drop_db(db_name)


def test_objective_modify_actions_on_locked_study(api_client):
    global study_objective_uid

    response = api_client.post(
        f"/studies/{study.uid}/study-objectives",
        json={
            "objective_uid": "Objective_000001",
            "objective_level_uid": "term_root_final",
        },
    )
    res = response.json()
    assert response.status_code == 201
    assert res["objective_level"]["term_uid"] == "term_root_final"
    study_objective_uid = res["study_objective_uid"]

    # get all objectives
    response = api_client.get(
        f"/studies/{study.uid}/study-objectives/audit-trail/",
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
        f"/studies/{study.uid}/study-objectives",
        json={"objective_uid": "Objective_000002"},
    )
    res = response.json()
    assert response.status_code == 400
    assert res["message"] == f"Study with specified uid '{study.uid}' is locked."
    # edit objective
    response = api_client.patch(
        f"/studies/{study.uid}/study-objectives/{study_objective_uid}",
        json={"new_order": 2},
    )
    res = response.json()
    assert response.status_code == 400
    assert res["message"] == f"Study with specified uid '{study.uid}' is locked."

    # get all history when was locked
    response = api_client.get(
        f"/studies/{study.uid}/study-objectives/audit-trail/",
    )
    res = response.json()
    assert response.status_code == 200
    assert old_res == res

    # test cannot delete
    response = api_client.delete(
        f"/studies/{study.uid}/study-objectives/{study_objective_uid}"
    )
    assert response.status_code == 400
    assert (
        response.json()["message"]
        == f"Study with specified uid '{study.uid}' is locked."
    )


def test_study_objective_with_objective_level_relationship(api_client):
    # get specific study objective
    response = api_client.get(
        f"/studies/{study.uid}/study-objectives/{study_objective_uid}",
    )
    res = response.json()
    assert response.status_code == 200
    assert res["objective_level"]["term_uid"] == "term_root_final"
    before_unlock = res

    # get study objective headers
    response = api_client.get(
        f"/studies/{study.uid}/study-objectives/headers?field_name=objective_level.term_uid",
    )
    res = response.json()
    assert response.status_code == 200
    assert res == ["term_root_final"]

    # Unlock
    response = api_client.delete(f"/studies/{study.uid}/locks")
    assert response.status_code == 200

    # edit study objective
    response = api_client.patch(
        f"/studies/{study.uid}/study-objectives/{study_objective_uid}",
        json={
            "objective_uid": "Objective_000001",
            "objective_level_uid": "term_root_final5",
        },
    )
    res = response.json()
    assert res["objective_level"]["term_uid"] == "term_root_final5"
    assert response.status_code == 200

    # get all study objectives of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-objectives?study_value_version=1",
    )
    res = response.json()
    assert response.status_code == 200
    before_unlock["study_version"] = mock.ANY
    assert res["items"][0] == before_unlock

    # get specific study objective of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-objectives/{study_objective_uid}?study_value_version=1",
    )
    res = response.json()
    assert response.status_code == 200
    assert res == before_unlock

    # get study objective headers of specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-objectives/headers?field_name=objective_level.term_uid&study_value_version=1",
    )
    res = response.json()
    assert response.status_code == 200
    assert res == ["term_root_final"]

    # get all study objectives
    response = api_client.get(
        f"/studies/{study.uid}/study-objectives",
    )
    res = response.json()
    assert response.status_code == 200
    assert res["items"][0]["objective_level"]["term_uid"] == "term_root_final5"

    # get specific study objective
    response = api_client.get(
        f"/studies/{study.uid}/study-objectives/{study_objective_uid}",
    )
    res = response.json()
    assert response.status_code == 200
    assert res["objective_level"]["term_uid"] == "term_root_final5"

    # get study objective headers
    response = api_client.get(
        f"/studies/{study.uid}/study-objectives/headers?field_name=objective_level.term_uid",
    )
    res = response.json()
    assert response.status_code == 200
    assert res == ["term_root_final5"]


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
def test_get_study_objectives_csv_xml_excel(api_client, export_format):
    url = f"/studies/{study.uid}/study-objectives"
    exported_data = TestUtils.verify_exported_data_format(
        api_client, export_format, url
    )
    if export_format == "text/csv":
        assert "study_version" in str(exported_data.read())
        assert "LATEST" in str(exported_data.read())


def test_update_library_items_of_relationship_to_value_nodes(api_client):
    """
    Test that the StudyObjective selection remains connected to the specific Value node even if the Value node is not latest anymore.

    StudyObjective is connected to value nodes:
    - ObjectiveValue
    """
    # get specific study objective
    response = api_client.get(
        f"/studies/{study.uid}/study-objectives/{study_objective_uid}",
    )
    res = response.json()
    assert response.status_code == 200
    library_template_objective_uid = res["objective"]["objective_template"]["uid"]
    initial_objective_name = res["objective"]["name"]

    text_value_2_name = "2ndname"
    # change objective name and approve the version
    response = api_client.post(
        f"/objective-templates/{library_template_objective_uid}/versions",
        json={
            "change_description": "test change",
            "name": text_value_2_name,
            "guidance_text": "don't know",
        },
    )
    response = api_client.post(
        f"/objective-templates/{library_template_objective_uid}/approvals?cascade=true"
    )

    # check that the Library item has been changed
    response = api_client.get(f"/objective-templates/{library_template_objective_uid}")
    res = response.json()
    assert response.status_code == 200
    assert res["name"] == text_value_2_name

    # check that the StudySelection StudyObjective hasn't been updated
    response = api_client.get(
        f"/studies/{study.uid}/study-objectives/{study_objective_uid}",
    )
    res = response.json()
    assert response.status_code == 200
    assert res["objective"]["name"] == initial_objective_name

    # check that the StudySelection can approve the current version
    response = api_client.post(
        f"/studies/{study.uid}/study-objectives/{study_objective_uid}/accept-version",
    )
    res = response.json()
    assert response.status_code == 200
    assert res["accepted_version"] is True
    assert res["objective"]["name"] == initial_objective_name
    assert res["latest_objective"]["name"] == text_value_2_name

    # get all objectives
    response = api_client.get(
        f"/studies/{study.uid}/study-objectives/audit-trail/",
    )
    res = response.json()
    assert response.status_code == 200
    counting_before_sync = len(res)

    # check that the StudySelection's objective can be updated to the LATEST
    response = api_client.post(
        f"/studies/{study.uid}/study-objectives/{study_objective_uid}/sync-latest-version",
    )
    res = response.json()
    assert response.status_code == 200
    assert res["objective"]["name"] == text_value_2_name

    # get all objectives
    response = api_client.get(
        f"/studies/{study.uid}/study-objectives/audit-trail/",
    )
    res = response.json()
    assert response.status_code == 200
    assert len(res) == counting_before_sync + 1
