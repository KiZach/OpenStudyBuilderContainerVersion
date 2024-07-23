"""
Tests for /studies/{uid}/study-endpoints endpoints
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
    EndpointRoot,
    EndpointTemplateRoot,
    ObjectiveRoot,
    ObjectiveTemplateRoot,
    TimeframeRoot,
    TimeframeTemplateRoot,
)
from clinical_mdr_api.main import app
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.tests.integration.utils.api import (
    drop_db,
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
    STARTUP_CT_TERM_NAME_CYPHER,
    STARTUP_STUDY_ENDPOINT_CYPHER,
    STARTUP_STUDY_OBJECTIVE_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

log = logging.getLogger(__name__)
study: Study
endpoint_uid: str
study_objective_uid1: str


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studyendpointapi"
    inject_and_clear_db(db_name)
    inject_base_data()
    global study
    study = TestUtils.create_study()

    db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
    db.cypher_query(STARTUP_STUDY_OBJECTIVE_CYPHER)
    db.cypher_query(STARTUP_STUDY_ENDPOINT_CYPHER)
    ObjectiveTemplateRoot.generate_node_uids_if_not_present()
    ObjectiveRoot.generate_node_uids_if_not_present()
    EndpointTemplateRoot.generate_node_uids_if_not_present()
    EndpointRoot.generate_node_uids_if_not_present()
    TimeframeTemplateRoot.generate_node_uids_if_not_present()
    TimeframeRoot.generate_node_uids_if_not_present()

    yield
    drop_db(db_name)


def test_study_endpoint_modify_actions_on_locked_study(api_client):
    global endpoint_uid
    global study_objective_uid1

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
    study_objective_uid1 = res["study_objective_uid"]

    response = api_client.post(
        f"/studies/{study.uid}/study-endpoints",
        json={
            "endpoint_uid": "Endpoint_000001",
            "study_objective_uid": study_objective_uid1,
            "endpoint_level_uid": "term_root_final",
        },
    )
    res = response.json()
    assert res["endpoint_level"]["term_uid"] == "term_root_final"
    assert response.status_code == 201

    # get all endpoints
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/audit-trail/",
    )
    res = response.json()
    assert response.status_code == 200
    old_res = res
    endpoint_uid = res[0]["study_endpoint_uid"]

    # get specific endpoint of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}",
    )
    res = response.json()
    assert response.status_code == 200
    assert res["endpoint_level"]["term_uid"] == "term_root_final"

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
        f"/studies/{study.uid}/study-endpoints",
        json={
            "timeframe_uid": "Timeframe_000001",
            "study_objective_uid": study_objective_uid1,
        },
    )
    res = response.json()
    assert response.status_code == 400
    assert res["message"] == f"Study with specified uid '{study.uid}' is locked."

    # edit endpoint
    response = api_client.patch(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}",
        json={"new_order": 2},
    )
    res = response.json()
    assert response.status_code == 400
    assert res["message"] == f"Study with specified uid '{study.uid}' is locked."

    # get all history when was locked
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/audit-trail/",
    )
    res = response.json()
    assert response.status_code == 200
    for i, _ in enumerate(old_res):
        old_res[i]["study_objective"]["study_version"] = mock.ANY
    assert old_res == res

    # test cannot delete
    response = api_client.delete(f"/studies/{study.uid}/study-endpoints/{endpoint_uid}")
    assert response.status_code == 400
    assert (
        response.json()["message"]
        == f"Study with specified uid '{study.uid}' is locked."
    )


def test_study_endpoint_with_study_objective_relationship(api_client):
    # get specific study endpoint
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}",
    )
    res = response.json()
    assert response.status_code == 200
    assert res["endpoint_level"]["term_uid"] == "term_root_final"
    assert res["study_objective"]["study_objective_uid"] == study_objective_uid1
    before_unlock = res
    before_unlock_objectives = api_client.get(
        f"/studies/{study.uid}/study-objectives"
    ).json()

    # get study endpoint headers
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/headers?field_name=endpoint_level.term_uid",
    )
    res = response.json()
    assert response.status_code == 200
    assert res == ["term_root_final"]

    # Unlock
    response = api_client.delete(f"/studies/{study.uid}/locks")
    assert response.status_code == 200

    # edit study endpoint
    response = api_client.patch(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}",
        json={
            "endpoint_uid": "Endpoint_000001",
            "endpoint_level_uid": "term_root_final5",
        },
    )
    res = response.json()
    assert response.status_code == 200
    assert res["endpoint_level"]["term_uid"] == "term_root_final5"

    # edit study objective
    response = api_client.patch(
        f"/studies/{study.uid}/study-objectives/{study_objective_uid1}",
        json={
            "objective_uid": "Objective_000002",
            "objective_level_uid": "term_root_final5",
        },
    )
    res = response.json()
    assert res["objective_level"]["term_uid"] == "term_root_final5"
    assert response.status_code == 200

    # get all study endpoints of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints?study_value_version=1",
    )
    res = response.json()
    assert response.status_code == 200
    before_unlock["study_version"] = mock.ANY
    before_unlock["study_objective"]["study_version"] = mock.ANY
    assert res["items"][0] == before_unlock

    # get all
    for i, _ in enumerate(before_unlock_objectives["items"]):
        before_unlock_objectives["items"][i]["study_version"] = mock.ANY
    assert (
        before_unlock_objectives
        == api_client.get(
            f"/studies/{study.uid}/study-objectives?study_value_version=1"
        ).json()
    )

    # get specific study endpoint of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}?study_value_version=1",
    )
    res = response.json()
    assert response.status_code == 200
    assert res == before_unlock

    # get study endpoint headers of specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/headers?field_name=endpoint_level.term_uid&study_value_version=1",
    )
    res = response.json()
    assert response.status_code == 200
    assert res == ["term_root_final"]

    # get all study endpoints
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints",
    )
    res = response.json()
    assert response.status_code == 200
    assert res["items"][0]["endpoint_level"]["term_uid"] == "term_root_final5"

    # get specific study endpoint
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}",
    )
    res = response.json()
    assert response.status_code == 200
    assert res["endpoint_level"]["term_uid"] == "term_root_final5"


def test_study_value_version_validation(api_client):
    # get all study endpoints of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints?study_value_version=a",
    )
    assert response.status_code == 422

    # get study study endpoint headers
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/headers?field_name=endpoint_level.term_uid",
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
def test_get_study_endpoints_csv_xml_excel(api_client, export_format):
    url = f"/studies/{study.uid}/study-endpoints"
    exported_data = TestUtils.verify_exported_data_format(
        api_client, export_format, url
    )
    if export_format == "text/csv":
        assert "study_version" in str(exported_data.read())
        assert "LATEST" in str(exported_data.read())


def test_update_endpoint_library_items_of_relationship_to_value_nodes(api_client):
    """
    Test that the StudyEndpoint selection remains connected to the specific Value node even if the Value node is not latest anymore.

    StudyEndpoint is connected to value nodes:
    - EndpointTemplate
    """
    # get specific study endpoint
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}",
    )
    res = response.json()
    assert response.status_code == 200
    library_template_endpoint_uid = res["endpoint"]["endpoint_template"]["uid"]
    initial_endpoint_name = res["endpoint"]["name"]

    text_value_2_name = "2ndname"
    # change endpoint name and approve the version
    response = api_client.post(
        f"/endpoint-templates/{library_template_endpoint_uid}/versions",
        json={
            "change_description": "test change",
            "name": text_value_2_name,
            "guidance_text": "don't know",
        },
    )
    response = api_client.post(
        f"/endpoint-templates/{library_template_endpoint_uid}/approvals?cascade=true"
    )

    # check that the Library item has been changed
    response = api_client.get(f"/endpoint-templates/{library_template_endpoint_uid}")
    res = response.json()
    assert response.status_code == 200
    assert res["name"] == text_value_2_name

    # check that the StudySelection StudyEndpoint hasn't been updated
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}",
    )
    res = response.json()
    assert response.status_code == 200
    assert res["endpoint"]["name"] == initial_endpoint_name

    # check that the StudySelection can approve the current version
    response = api_client.post(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}/accept-version",
    )
    res = response.json()
    assert response.status_code == 200
    assert res["accepted_version"] is True
    assert res["endpoint"]["endpoint_template"]["name"] == initial_endpoint_name

    # get all objectives
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/audit-trail/",
    )
    res = response.json()
    assert response.status_code == 200
    counting_before_sync = len(res)

    # check that the StudySelection's objective can be updated to the LATEST
    response = api_client.post(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}/sync-latest-endpoint-version",
    )
    res = response.json()
    assert response.status_code == 200
    assert res["endpoint"]["endpoint_template"]["name"] == text_value_2_name

    # get all objectives
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/audit-trail/",
    )
    res = response.json()
    assert response.status_code == 200
    assert len(res) == counting_before_sync + 1


def test_update_timeframe_library_items_of_relationship_to_value_nodes(api_client):
    """
    Test that the StudyEndpoint selection remains connected to the specific Value node even if the Value node is not latest anymore.

    StudyEndpoint is connected to value nodes:
    - TimeframeTemplate
    """

    # timeframes
    response = api_client.patch(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}",
        json={
            "timeframe_uid": "Timeframe_000001",
            "study_objective_uid": study_objective_uid1,
        },
    )
    res = response.json()
    assert response.status_code == 200
    library_template_timeframe_uid = res["timeframe"]["timeframe_template"]["uid"]
    initial_timeframe_name = res["timeframe"]["timeframe_template"]["name"]

    text_value_2_name = "2ndname"
    # change endpoint name and approve the version
    response = api_client.post(
        f"/timeframe-templates/{library_template_timeframe_uid}/versions",
        json={"change_description": "test change", "name": text_value_2_name},
    )
    # change endpoint name and approve the version
    response = api_client.patch(
        f"/timeframe-templates/{library_template_timeframe_uid}",
        json={
            "name": text_value_2_name,
            "library": {"name": "Sponsor", "is_editable": True},
            "change_description": "Work in Progress",
        },
    )
    response = api_client.post(
        f"/timeframe-templates/{library_template_timeframe_uid}/approvals?cascade=true"
    )
    # check that the Library item has been changed
    response = api_client.get(f"/timeframe-templates/{library_template_timeframe_uid}")
    res = response.json()
    assert response.status_code == 200
    assert res["name"] == text_value_2_name

    # check that the StudySelection StudyEndpoint hasn't been updated
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}",
    )
    res = response.json()
    assert response.status_code == 200
    assert res["timeframe"]["name"] == initial_timeframe_name

    # check that the StudySelection can approve the current version
    response = api_client.post(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}/accept-version",
    )
    res = response.json()
    assert response.status_code == 200
    assert res["accepted_version"] is True
    assert res["timeframe"]["timeframe_template"]["name"] == initial_timeframe_name

    # get all objectives
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/audit-trail/",
    )
    res = response.json()
    assert response.status_code == 200
    counting_before_sync = len(res)

    # check that the StudySelection's objective can be updated to the LATEST
    response = api_client.post(
        f"/studies/{study.uid}/study-endpoints/{endpoint_uid}/sync-latest-timeframe-version",
    )
    res = response.json()
    assert response.status_code == 200
    assert res["timeframe"]["timeframe_template"]["name"] == text_value_2_name

    # get all objectives
    response = api_client.get(
        f"/studies/{study.uid}/study-endpoints/audit-trail/",
    )
    res = response.json()
    assert response.status_code == 200
    assert len(res) == counting_before_sync + 1
