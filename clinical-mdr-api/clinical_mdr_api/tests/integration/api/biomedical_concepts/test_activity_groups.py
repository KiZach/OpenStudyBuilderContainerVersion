"""
Tests for /concepts/activities/activity-groups endpoints
"""
import logging
from operator import itemgetter

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.concepts.activities.activity_group import ActivityGroup
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments


log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
activity_groups_all: list[ActivityGroup]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "activitiesgroups.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global activity_groups_all
    activity_groups_all = [
        TestUtils.create_activity_group(name="name-AAA"),
        TestUtils.create_activity_group(
            name="name-BBB",
        ),
    ]

    for index in range(5):
        activity_groups_all.append(
            TestUtils.create_activity_group(
                name=f"ActivityGroup-{index}",
            )
        )

    yield


ACTIVITY_GROUP_FIELDS_ALL = [
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
]

ACTIVITY_GROUP_FIELDS_NOT_NULL = ["uid", "name", "start_date"]


def test_get_activity_group(api_client):
    response = api_client.get(
        f"/concepts/activities/activity-groups/{activity_groups_all[0].uid}"
    )
    res = response.json()

    assert response.status_code == 200

    # Check fields included in the response
    assert set(list(res.keys())) == set(ACTIVITY_GROUP_FIELDS_ALL)
    for key in ACTIVITY_GROUP_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == activity_groups_all[0].uid
    assert res["name"] == "name-AAA"
    assert res["name_sentence_case"] == "name-AAA"
    assert res["library_name"] == "Sponsor"
    assert res["definition"] is None
    assert res["version"] == "1.0"
    assert res["status"] == "Final"
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_get_activity_group_version(api_client):
    response = api_client.get(
        f"/concepts/activities/activity-groups/{activity_groups_all[0].uid}/versions"
    )
    res = response.json()

    assert response.status_code == 200

    assert len(res) == 2

    # Check fields included in the response
    for item in res:
        assert set(list(item.keys())) == set(ACTIVITY_GROUP_FIELDS_ALL)
        for key in ACTIVITY_GROUP_FIELDS_NOT_NULL:
            assert item[key] is not None

    assert res[0]["uid"] == activity_groups_all[0].uid
    assert res[0]["name"] == "name-AAA"
    assert res[0]["name_sentence_case"] == "name-AAA"
    assert res[0]["library_name"] == "Sponsor"
    assert res[0]["definition"] is None
    assert res[0]["version"] == "1.0"
    assert res[0]["status"] == "Final"
    assert res[0]["possible_actions"] == ["inactivate", "new_version"]

    assert res[1]["uid"] == activity_groups_all[0].uid
    assert res[1]["name"] == "name-AAA"
    assert res[1]["name_sentence_case"] == "name-AAA"
    assert res[1]["library_name"] == "Sponsor"
    assert res[1]["definition"] is None
    assert res[1]["version"] == "0.1"
    assert res[1]["status"] == "Draft"
    assert res[1]["possible_actions"] == ["approve", "delete", "edit"]


def test_get_activity_groups_versions(api_client):
    # Create a new version of an activity group
    response = api_client.post(
        f"/concepts/activities/activity-groups/{activity_groups_all[0].uid}/versions"
    )
    assert response.status_code == 201

    # Get all versions of all activities
    response = api_client.get(
        "/concepts/activities/activity-groups/versions?page_size=100"
    )
    res = response.json()

    assert response.status_code == 200

    # Check fields included in the response
    assert set(list(res.keys())) == set(["items", "total", "page", "size"])

    assert len(res["items"]) == len(activity_groups_all) * 2 + 1
    for item in res["items"]:
        assert set(list(item.keys())) == set(ACTIVITY_GROUP_FIELDS_ALL)
        for key in ACTIVITY_GROUP_FIELDS_NOT_NULL:
            assert item[key] is not None

    # Check that the items are sorted by start_date descending
    sorted_items = sorted(res["items"], key=itemgetter("start_date"), reverse=True)
    assert sorted_items == res["items"]


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param('{"*": {"v": ["aaa"]}}', "name", "name-AAA"),
        pytest.param('{"*": {"v": ["bBb"]}}', "name", "name-BBB"),
        pytest.param('{"*": {"v": ["ccc"]}}', None, None),
        pytest.param('{"*": {"v": ["Final"]}}', "status", "Final"),
        pytest.param('{"*": {"v": ["1.0"]}}', "version", "1.0"),
    ],
)
def test_filtering_versions_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    url = f"/concepts/activities/activity-groups/versions?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert response.status_code == 200
    if expected_result_prefix:
        assert len(res["items"]) > 0
        nested_path = None

        # if we expect a nested property to be equal to specified value
        if isinstance(expected_matched_field, str) and "." in expected_matched_field:
            nested_path = expected_matched_field.split(".")
            expected_matched_field = nested_path[-1]
            nested_path = nested_path[:-1]

        # Each returned row has a field that starts with the specified filter value
        for row in res["items"]:
            if nested_path:
                for prop in nested_path:
                    row = row[prop]
            if isinstance(row, list):
                any(
                    item[expected_matched_field].startswith(expected_result_prefix)
                    for item in row
                )
            else:
                assert row[expected_matched_field].startswith(expected_result_prefix)
    else:
        assert len(res["items"]) == 0


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result",
    [
        pytest.param('{"name": {"v": ["name-AAA"]}}', "name", "name-AAA"),
        pytest.param('{"name": {"v": ["name-BBB"]}}', "name", "name-BBB"),
        pytest.param('{"name": {"v": ["cc"]}}', None, None),
        pytest.param(
            '{"name_sentence_case": {"v": ["name-AAA"]}}',
            "name_sentence_case",
            "name-AAA",
        ),
        pytest.param(
            '{"name_sentence_case": {"v": ["name-BBB"]}}',
            "name_sentence_case",
            "name-BBB",
        ),
        pytest.param('{"name_sentence_case": {"v": ["cc"]}}', None, None),
    ],
)
def test_filtering_versions_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    url = f"/concepts/activities/activity-groups/versions?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert response.status_code == 200
    if expected_result:
        assert len(res["items"]) > 0

        # if we expect a nested property to be equal to specified value
        nested_path = None
        if isinstance(expected_matched_field, str) and "." in expected_matched_field:
            nested_path = expected_matched_field.split(".")
            expected_matched_field = nested_path[-1]
            nested_path = nested_path[:-1]

        # Each returned row has a field whose value is equal to the specified filter value
        for row in res["items"]:
            if nested_path:
                for prop in nested_path:
                    row = row[prop]
            if isinstance(expected_result, list):
                assert all(
                    item in row[expected_matched_field] for item in expected_result
                )
            else:
                if isinstance(row, list):
                    all(item[expected_matched_field] == expected_result for item in row)
                else:
                    assert row[expected_matched_field] == expected_result
    else:
        assert len(res["items"]) == 0
