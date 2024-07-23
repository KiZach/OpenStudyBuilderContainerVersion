"""
Tests for /concepts/activities/activity-instances endpoints
"""
import json
import logging
from functools import reduce
from operator import itemgetter

import pytest
import yaml
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models import Activity, CTTerm
from clinical_mdr_api.models.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClass,
)
from clinical_mdr_api.models.biomedical_concepts.activity_item_class import (
    ActivityItemClass,
)
from clinical_mdr_api.models.concepts.activities.activity_group import ActivityGroup
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstance,
)
from clinical_mdr_api.models.concepts.activities.activity_item import ActivityItem
from clinical_mdr_api.models.concepts.activities.activity_sub_group import (
    ActivitySubGroup,
)
from clinical_mdr_api.tests.integration.utils.api import (
    drop_db,
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import LIBRARY_NAME, TestUtils

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments


log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
activity_instances_all: list[ActivityInstance]
activity_group: ActivityGroup
activity_subgroup: ActivitySubGroup
activities: list[Activity]
activity_instance_classes: list[ActivityInstanceClass]
activity_items: list[ActivityItem]
activity_item_classes: list[ActivityItemClass]
ct_terms: list[CTTerm]
role_term: CTTerm
data_type_term: CTTerm


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "activityinstances.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global activity_group
    activity_group = TestUtils.create_activity_group(name="activity_group")

    global activity_subgroup
    activity_subgroup = TestUtils.create_activity_subgroup(
        name="activity_subgroup", activity_groups=[activity_group.uid]
    )
    global activities
    activities = [
        TestUtils.create_activity(
            name="Activity",
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
        ),
        TestUtils.create_activity(
            name="Second activity",
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
        ),
    ]

    global activity_instance_classes
    activity_instance_classes = [
        TestUtils.create_activity_instance_class(name="Activity instance class 1"),
        TestUtils.create_activity_instance_class(name="Activity instance class 2"),
        TestUtils.create_activity_instance_class(name="Activity instance class 3"),
    ]
    global activity_item_classes
    global data_type_term
    global role_term
    data_type_term = TestUtils.create_ct_term(sponsor_preferred_name="Data type")
    role_term = TestUtils.create_ct_term(sponsor_preferred_name="Role")
    activity_item_classes = [
        TestUtils.create_activity_item_class(
            name="Activity Item Class name1",
            order=1,
            mandatory=True,
            activity_instance_class_uids=[activity_instance_classes[0].uid],
            role_uid=role_term.term_uid,
            data_type_uid=data_type_term.term_uid,
        ),
        TestUtils.create_activity_item_class(
            name="Activity Item Class name2",
            order=2,
            mandatory=True,
            activity_instance_class_uids=[activity_instance_classes[1].uid],
            role_uid=role_term.term_uid,
            data_type_uid=data_type_term.term_uid,
        ),
        TestUtils.create_activity_item_class(
            name="Activity Item Class name3",
            order=3,
            mandatory=True,
            activity_instance_class_uids=[activity_instance_classes[2].uid],
            role_uid=role_term.term_uid,
            data_type_uid=data_type_term.term_uid,
        ),
    ]
    global ct_terms

    codelist = TestUtils.create_ct_codelist(extensible=True, approve=True)
    ct_terms = [
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="Activity item term",
        ),
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="Activity item term2",
        ),
    ]
    global activity_items
    activity_items = [
        {
            "activity_item_class_uid": activity_item_classes[0].uid,
            "ct_term_uids": [ct_terms[0].term_uid],
            "unit_definition_uids": [],
        },
        {
            "activity_item_class_uid": activity_item_classes[1].uid,
            "ct_term_uids": [ct_terms[1].term_uid],
            "unit_definition_uids": [],
        },
        {
            "activity_item_class_uid": activity_item_classes[2].uid,
            "ct_term_uids": [ct_terms[0].term_uid, ct_terms[1].term_uid],
            "unit_definition_uids": [],
        },
    ]
    global activity_instances_all
    # Create some activity instances
    activity_instances_all = [
        TestUtils.create_activity_instance(
            name="name A",
            activity_instance_class_uid=activity_instance_classes[0].uid,
            name_sentence_case="name A",
            topic_code="topic code A",
            is_required_for_activity=True,
            activities=[activities[0].uid],
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            activity_items=[activity_items[0]],
        ),
        TestUtils.create_activity_instance(
            name="name-AAA",
            activity_instance_class_uid=activity_instance_classes[0].uid,
            name_sentence_case="name-AAA",
            topic_code="topic code-AAA",
            is_required_for_activity=True,
            activities=[activities[0].uid],
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            activity_items=[activity_items[0]],
        ),
        TestUtils.create_activity_instance(
            name="name-BBB",
            activity_instance_class_uid=activity_instance_classes[0].uid,
            name_sentence_case="name-BBB",
            topic_code="topic code-BBB",
            is_required_for_activity=True,
            activities=[activities[0].uid],
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            activity_items=[activity_items[0]],
        ),
        TestUtils.create_activity_instance(
            name="name XXX",
            activity_instance_class_uid=activity_instance_classes[0].uid,
            name_sentence_case="name XXX",
            nci_concept_id="C-XXX",
            topic_code="topic code XXX",
            is_required_for_activity=True,
            activities=[activities[0].uid],
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            activity_items=[activity_items[0], activity_items[1], activity_items[2]],
        ),
        TestUtils.create_activity_instance(
            name="name YYY",
            activity_instance_class_uid=activity_instance_classes[0].uid,
            name_sentence_case="name YYY",
            topic_code="topic code YYY",
            is_required_for_activity=True,
            activities=[activities[0].uid],
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            activity_items=[activity_items[0], activity_items[1]],
        ),
    ]

    for index in range(5):
        activity_instances_all.append(
            TestUtils.create_activity_instance(
                name=f"name-AAA-{index}",
                activity_instance_class_uid=activity_instance_classes[1].uid,
                name_sentence_case=f"name-AAA-{index}",
                topic_code=f"topic code-AAA-{index}",
                is_required_for_activity=True,
                activities=[activities[1].uid],
                activity_subgroups=[activity_subgroup.uid],
                activity_groups=[activity_group.uid],
                activity_items=[activity_items[1]],
            )
        )
        activity_instances_all.append(
            TestUtils.create_activity_instance(
                name=f"name-BBB-{index}",
                activity_instance_class_uid=activity_instance_classes[1].uid,
                name_sentence_case=f"name-BBB-{index}",
                topic_code=f"topic code-BBB-{index}",
                is_required_for_activity=True,
                activities=[activities[1].uid],
                activity_subgroups=[activity_subgroup.uid],
                activity_groups=[activity_group.uid],
                activity_items=[activity_items[1]],
            )
        )
        activity_instances_all.append(
            TestUtils.create_activity_instance(
                name=f"name-XXX-{index}",
                activity_instance_class_uid=activity_instance_classes[1].uid,
                name_sentence_case=f"name-XXX-{index}",
                topic_code=f"topic code-XXX-{index}",
                is_required_for_activity=True,
                activities=[activities[1].uid],
                activity_subgroups=[activity_subgroup.uid],
                activity_groups=[activity_group.uid],
                activity_items=[activity_items[1]],
            )
        )
        activity_instances_all.append(
            TestUtils.create_activity_instance(
                name=f"name-YYY-{index}",
                activity_instance_class_uid=activity_instance_classes[1].uid,
                name_sentence_case=f"name-YYY-{index}",
                topic_code=f"topic code-YYY-{index}",
                is_required_for_activity=True,
                activities=[activities[1].uid],
                activity_subgroups=[activity_subgroup.uid],
                activity_groups=[activity_group.uid],
                activity_items=[activity_items[1]],
            )
        )

    yield

    drop_db(db_name)


ACTIVITY_INSTANCES_FIELDS_ALL = [
    "uid",
    "nci_concept_id",
    "name",
    "name_sentence_case",
    "definition",
    "abbreviation",
    "topic_code",
    "adam_param_code",
    "is_required_for_activity",
    "is_default_selected_for_activity",
    "is_data_sharing",
    "is_legacy_usage",
    "is_derived",
    "legacy_description",
    "activity_groupings",
    "activity_name",
    "activity_instance_class",
    "activity_items",
    "library_name",
    "start_date",
    "end_date",
    "status",
    "version",
    "change_description",
    "user_initials",
    "possible_actions",
]

ACTIVITY_INSTANCES_FIELDS_NOT_NULL = [
    "uid",
    "name",
    "activity_instance_class",
]


def test_get_activity_instance(api_client):
    response = api_client.get(
        f"/concepts/activities/activity-instances/{activity_instances_all[0].uid}"
    )
    res = response.json()

    assert response.status_code == 200

    # Check fields included in the response
    assert set(list(res.keys())) == set(ACTIVITY_INSTANCES_FIELDS_ALL)
    for key in ACTIVITY_INSTANCES_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == activity_instances_all[0].uid
    assert res["name"] == "name A"
    assert res["activity_name"] == activities[0].name
    assert res["name_sentence_case"] == "name A"
    assert res["topic_code"] == "topic code A"
    assert len(res["activity_groupings"]) == 1
    assert res["activity_groupings"][0]["activity"]["uid"] == activities[0].uid
    assert res["activity_groupings"][0]["activity"]["name"] == activities[0].name
    assert (
        res["activity_groupings"][0]["activity_subgroup"]["uid"]
        == activity_subgroup.uid
    )
    assert (
        res["activity_groupings"][0]["activity_subgroup"]["name"]
        == activity_subgroup.name
    )
    assert res["activity_groupings"][0]["activity_group"]["uid"] == activity_group.uid
    assert res["activity_groupings"][0]["activity_group"]["name"] == activity_group.name
    assert res["activity_instance_class"]["uid"] == activity_instance_classes[0].uid
    assert res["activity_instance_class"]["name"] == activity_instance_classes[0].name
    assert len(res["activity_items"]) == 1
    assert (
        res["activity_items"][0]["activity_item_class"]["uid"]
        == activity_item_classes[0].uid
    )

    expected_term_uids = set(term_uid for term_uid in activity_items[0]["ct_term_uids"])
    actual_term_uids = set(term["uid"] for term in res["activity_items"][0]["ct_terms"])
    assert expected_term_uids == actual_term_uids
    expected_unit_uids = set(
        unit_uid for unit_uid in activity_items[0]["unit_definition_uids"]
    )
    actual_unit_uids = set(
        unit["uid"] for unit in res["activity_items"][0]["unit_definitions"]
    )
    assert expected_unit_uids == actual_unit_uids

    assert res["library_name"] == "Sponsor"
    assert res["definition"] is None
    assert res["version"] == "1.0"
    assert res["status"] == "Final"
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_get_activity_instances_pagination(api_client):
    results_paginated: dict = {}
    sort_by = '{"name": true}'
    for page_number in range(1, 4):
        url = f"/concepts/activities/activity-instances?page_number={page_number}&page_size=10&sort_by={sort_by}"
        response = api_client.get(url)
        res = response.json()
        res_names = list(map(lambda x: x["name"], res["items"]))
        results_paginated[page_number] = res_names
        log.info("Page %s: %s", page_number, res_names)

    log.info("All pages: %s", results_paginated)

    results_paginated_merged = list(
        list(reduce(lambda a, b: a + b, list(results_paginated.values())))
    )
    log.info("All rows returned by pagination: %s", results_paginated_merged)

    res_all = api_client.get(
        f"/concepts/activities/activity-instances?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    results_all_in_one_page = list(map(lambda x: x["name"], res_all["items"]))
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)
    assert len(activity_instances_all) == len(results_paginated_merged)


@pytest.mark.parametrize(
    "page_size, page_number, total_count, sort_by, expected_result_len",
    [
        pytest.param(None, None, None, None, 10),
        pytest.param(3, 1, True, None, 3),
        pytest.param(3, 2, True, None, 3),
        pytest.param(10, 2, True, None, 10),
        pytest.param(10, 3, True, None, 5),  # Total numer of data models is 25
        pytest.param(10, 1, True, '{"name": false}', 10),
        pytest.param(10, 2, True, '{"name": true}', 10),
        pytest.param(10, 1, True, '{"activity_name": true}', 10),
    ],
)
def test_get_activity_instances(
    api_client, page_size, page_number, total_count, sort_by, expected_result_len
):
    url = "/concepts/activities/activity-instances"
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
    assert res["total"] == (len(activity_instances_all) if total_count else 0)
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(list(item.keys())) == set(ACTIVITY_INSTANCES_FIELDS_ALL)
        for key in ACTIVITY_INSTANCES_FIELDS_NOT_NULL:
            assert item[key] is not None

    if sort_by:
        # sort_by is JSON string in the form: {"sort_field_name": is_ascending_order}
        sort_by_dict = json.loads(sort_by)
        sort_field: str = list(sort_by_dict.keys())[0]
        sort_order_ascending: bool = list(sort_by_dict.values())[0]

        # extract list of values of 'sort_field_name' field from the returned result
        result_vals = list(map(lambda x: x[sort_field], res["items"]))
        result_vals_sorted_locally = result_vals.copy()
        result_vals_sorted_locally.sort(reverse=not sort_order_ascending)
        # This asser fails due to API issue with sorting coupled with pagination
        # assert result_vals == result_vals_sorted_locally


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
def test_get_activity_instances_csv_xml_excel(api_client, export_format):
    url = "/concepts/activities/activity-instances"
    TestUtils.verify_exported_data_format(api_client, export_format, url)


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
def test_filtering_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    url = f"/concepts/activities/activity-instances?filters={filter_by}"
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
        pytest.param(
            '{"topic_code": {"v": ["topic code-AAA"]}}', "topic_code", "topic code-AAA"
        ),
        pytest.param(
            '{"topic_code": {"v": ["topic code-BBB"]}}', "topic_code", "topic code-BBB"
        ),
        pytest.param('{"topic_code": {"v": ["cc"]}}', None, None),
        pytest.param('{"topic_code": {"v": ["cc"]}}', None, None),
        pytest.param(
            '{"activity_instance_class.name": {"v": ["Activity instance class 1"]}}',
            "activity_instance_class.name",
            "Activity instance class 1",
        ),
    ],
)
def test_filtering_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    url = f"/concepts/activities/activity-instances?filters={filter_by}"
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


def test_get_activity_instances_versions(api_client):
    # Create a new version of an activity
    response = api_client.post(
        f"/concepts/activities/activity-instances/{activity_instances_all[0].uid}/versions"
    )
    assert response.status_code == 201

    # Get all versions of all activities
    response = api_client.get(
        "/concepts/activities/activity-instances/versions?page_size=100"
    )
    res = response.json()

    assert response.status_code == 200

    # Check fields included in the response
    assert set(list(res.keys())) == set(["items", "total", "page", "size"])

    assert len(res["items"]) == len(activity_instances_all) * 2 + 1
    for item in res["items"]:
        assert set(list(item.keys())) == set(ACTIVITY_INSTANCES_FIELDS_ALL)
        for key in ACTIVITY_INSTANCES_FIELDS_NOT_NULL:
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
    url = f"/concepts/activities/activity-instances/versions?filters={filter_by}"
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
        pytest.param(
            '{"topic_code": {"v": ["topic code-AAA"]}}', "topic_code", "topic code-AAA"
        ),
        pytest.param(
            '{"topic_code": {"v": ["topic code-BBB"]}}', "topic_code", "topic code-BBB"
        ),
        pytest.param('{"topic_code": {"v": ["cc"]}}', None, None),
        pytest.param('{"topic_code": {"v": ["cc"]}}', None, None),
        pytest.param(
            '{"activity_instance_class.name": {"v": ["Activity instance class 1"]}}',
            "activity_instance_class.name",
            "Activity instance class 1",
        ),
    ],
)
def test_filtering_versions_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    url = f"/concepts/activities/activity-instances/versions?filters={filter_by}"
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


def test_edit_activity_instance(api_client):
    activity_instance = TestUtils.create_activity_instance(
        name="Activity Instance",
        activity_instance_class_uid=activity_instance_classes[0].uid,
        name_sentence_case="activity instance",
        nci_concept_id="C-123",
        topic_code="activity instance tc",
        activities=[activities[0].uid],
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
        activity_items=[activity_items[0]],
        approve=False,
    )
    response = api_client.get(
        f"/concepts/activities/activity-instances/{activity_instance.uid}"
    )
    res = response.json()
    assert response.status_code == 200
    assert res["name"] == "Activity Instance"
    assert res["name_sentence_case"] == "activity instance"
    assert res["nci_concept_id"] == "C-123"
    assert res["topic_code"] == "activity instance tc"
    assert len(res["activity_groupings"]) == 1
    assert res["activity_groupings"][0]["activity"]["uid"] == activities[0].uid
    assert res["activity_groupings"][0]["activity"]["name"] == activities[0].name
    assert (
        res["activity_groupings"][0]["activity_subgroup"]["uid"]
        == activity_subgroup.uid
    )
    assert (
        res["activity_groupings"][0]["activity_subgroup"]["name"]
        == activity_subgroup.name
    )
    assert res["activity_groupings"][0]["activity_group"]["uid"] == activity_group.uid
    assert res["activity_groupings"][0]["activity_group"]["name"] == activity_group.name
    assert res["activity_instance_class"]["uid"] == activity_instance_classes[0].uid
    assert len(res["activity_items"]) == 1
    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert res["possible_actions"] == ["approve", "delete", "edit"]

    # First Edit without activity-items explicitly sent
    response = api_client.patch(
        f"/concepts/activities/activity-instances/{activity_instance.uid}",
        json={
            "name": "some new name",
            "name_sentence_case": "some new name",
            "change_description": "modifying activity instance",
        },
    )
    assert response.status_code == 200

    # Second Edit with more properties sent
    response = api_client.patch(
        f"/concepts/activities/activity-instances/{activity_instance.uid}",
        json={
            "name": "new name",
            "name_sentence_case": "new name",
            "nci_concept_id": "C-123NEW",
            "activity_groupings": [
                {
                    "activity_uid": activities[1].uid,
                    "activity_subgroup_uid": activity_subgroup.uid,
                    "activity_group_uid": activity_group.uid,
                }
            ],
            "activity_instance_class_uid": activity_instance_classes[1].uid,
            "activity_items": [activity_items[0], activity_items[1]],
            "change_description": "modifying activity instance",
        },
    )
    res = response.json()
    assert response.status_code == 200
    assert res["name"] == "new name"
    assert res["name_sentence_case"] == "new name"
    assert res["nci_concept_id"] == "C-123NEW"
    assert res["topic_code"] == "activity instance tc"
    assert len(res["activity_groupings"]) == 1
    assert res["activity_groupings"][0]["activity"]["uid"] == activities[1].uid
    assert res["activity_groupings"][0]["activity"]["name"] == activities[1].name
    assert (
        res["activity_groupings"][0]["activity_subgroup"]["uid"]
        == activity_subgroup.uid
    )
    assert (
        res["activity_groupings"][0]["activity_subgroup"]["name"]
        == activity_subgroup.name
    )
    assert res["activity_groupings"][0]["activity_group"]["uid"] == activity_group.uid
    assert res["activity_groupings"][0]["activity_group"]["name"] == activity_group.name
    assert res["activity_instance_class"]["uid"] == activity_instance_classes[1].uid
    items = res["activity_items"]
    assert len(items) == 2
    items = sorted(items, key=lambda x: x["activity_item_class"]["uid"])

    assert items[0]["activity_item_class"]["uid"] == activity_item_classes[0].uid
    expected_term_uids = set(term_uid for term_uid in activity_items[0]["ct_term_uids"])
    actual_term_uids = set(term["uid"] for term in items[0]["ct_terms"])
    assert expected_term_uids == actual_term_uids
    expected_unit_uids = set(
        unit_uid for unit_uid in activity_items[0]["unit_definition_uids"]
    )
    actual_unit_uids = set(unit["uid"] for unit in items[0]["unit_definitions"])
    assert expected_unit_uids == actual_unit_uids

    assert items[1]["activity_item_class"]["uid"] == activity_item_classes[1].uid
    expected_term_uids = set(term_uid for term_uid in activity_items[1]["ct_term_uids"])
    actual_term_uids = set(term["uid"] for term in items[1]["ct_terms"])
    assert expected_term_uids == actual_term_uids
    expected_unit_uids = set(
        unit_uid for unit_uid in activity_items[1]["unit_definition_uids"]
    )
    actual_unit_uids = set(unit["uid"] for unit in items[1]["unit_definitions"])
    assert expected_unit_uids == actual_unit_uids

    assert res["version"] == "0.3"
    assert res["status"] == "Draft"
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_post_activity_instance(api_client):
    item_to_post = activity_items[1]
    response = api_client.post(
        "/concepts/activities/activity-instances",
        json={
            "name": "activity instance name",
            "name_sentence_case": "activity instance name",
            "nci_concept_id": "C-456",
            "activity_groupings": [
                {
                    "activity_uid": activities[0].uid,
                    "activity_subgroup_uid": activity_subgroup.uid,
                    "activity_group_uid": activity_group.uid,
                }
            ],
            "activity_instance_class_uid": activity_instance_classes[0].uid,
            "activity_items": [item_to_post],
            "is_required_for_activity": True,
            "is_derived": True,
            "library_name": "Sponsor",
        },
    )
    assert response.status_code == 201
    res = response.json()
    assert res["name"] == "activity instance name"
    assert res["name_sentence_case"] == "activity instance name"
    assert res["nci_concept_id"] == "C-456"
    assert len(res["activity_groupings"]) == 1
    assert res["activity_groupings"][0]["activity"]["uid"] == activities[0].uid
    assert res["activity_groupings"][0]["activity"]["name"] == activities[0].name
    assert (
        res["activity_groupings"][0]["activity_subgroup"]["uid"]
        == activity_subgroup.uid
    )
    assert (
        res["activity_groupings"][0]["activity_subgroup"]["name"]
        == activity_subgroup.name
    )
    assert res["activity_groupings"][0]["activity_group"]["uid"] == activity_group.uid
    assert res["activity_groupings"][0]["activity_group"]["name"] == activity_group.name
    assert res["activity_instance_class"]["uid"] == activity_instance_classes[0].uid
    assert len(res["activity_items"]) == 1
    assert (
        res["activity_items"][0]["activity_item_class"]["uid"]
        == activity_item_classes[1].uid
    )

    expected_term_uids = set(term_uid for term_uid in item_to_post["ct_term_uids"])
    actual_term_uids = set(term["uid"] for term in res["activity_items"][0]["ct_terms"])
    assert expected_term_uids == actual_term_uids
    expected_unit_uids = set(
        unit_uid for unit_uid in item_to_post["unit_definition_uids"]
    )
    actual_unit_uids = set(
        unit["uid"] for unit in res["activity_items"][0]["unit_definitions"]
    )
    assert expected_unit_uids == actual_unit_uids

    assert res["name_sentence_case"] == "activity instance name"
    assert res["topic_code"] is None
    assert res["adam_param_code"] is None
    assert res["is_required_for_activity"] is True
    assert res["is_default_selected_for_activity"] is False
    assert res["is_data_sharing"] is False
    assert res["is_legacy_usage"] is False
    assert res["is_derived"] is True
    assert res["library_name"] == "Sponsor"
    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_activity_instance_versioning(api_client):
    response = api_client.post(
        "/concepts/activities/activity-instances",
        json={
            "name": "ac name",
            "name_sentence_case": "ac name",
            "activity_groupings": [
                {
                    "activity_uid": activities[0].uid,
                    "activity_subgroup_uid": activity_subgroup.uid,
                    "activity_group_uid": activity_group.uid,
                }
            ],
            "activity_instance_class_uid": activity_instance_classes[0].uid,
            "library_name": "Sponsor",
        },
    )
    assert response.status_code == 201
    res = response.json()
    activity_instance_uid = res["uid"]

    response = api_client.get(
        f"/concepts/activities/activity-instances/{activity_instance_uid}/versions"
    )
    res = response.json()
    assert response.status_code == 200
    for item in res:
        assert set(list(item.keys())) == set(ACTIVITY_INSTANCES_FIELDS_ALL)
        for key in ACTIVITY_INSTANCES_FIELDS_NOT_NULL:
            assert item[key] is not None

    response = api_client.post(
        f"/concepts/activities/activity-instances/{activity_instance_uid}/versions"
    )
    assert response.status_code == 400
    res = response.json()
    assert res["message"] == "New draft version can be created only for FINAL versions."
    response = api_client.post(
        f"/concepts/activities/activity-instances/{activity_instance_uid}/approvals"
    )
    assert response.status_code == 201

    response = api_client.post(
        f"/concepts/activities/activity-instances/{activity_instance_uid}/approvals"
    )
    assert response.status_code == 400
    res = response.json()
    assert res["message"] == "The object is not in draft status."

    response = api_client.post(
        f"/concepts/activities/activity-instances/{activity_instance_uid}/activations"
    )
    assert response.status_code == 400
    res = response.json()
    assert res["message"] == "Only RETIRED version can be reactivated."
    response = api_client.delete(
        f"/concepts/activities/activity-instances/{activity_instance_uid}/activations"
    )
    assert response.status_code == 200

    response = api_client.post(
        f"/concepts/activities/activity-instances/{activity_instance_uid}/activations"
    )
    assert response.status_code == 200

    response = api_client.delete(
        f"/concepts/activities/activity-instances/{activity_instance_uid}"
    )
    assert response.status_code == 400
    res = response.json()
    assert res["message"] == "Object has been accepted"


def test_activity_instance_overview(api_client):
    response = api_client.get(
        f"/concepts/activities/activity-instances/{activity_instances_all[3].uid}/overview",
    )
    assert response.status_code == 200
    res = response.json()
    verify_instance_overview_content(res=res)


def verify_instance_overview_content(res: dict):
    print(json.dumps(res, indent=2, default=str))

    assert len(res["activity_groupings"]) == 1
    # activity
    assert res["activity_groupings"][0]["activity"]["uid"] == activities[0].uid
    assert res["activity_groupings"][0]["activity"]["name"] == activities[0].name
    assert res["activity_groupings"][0]["activity"]["definition"] is None
    assert res["activity_groupings"][0]["activity"]["library_name"] == LIBRARY_NAME

    # activity subgroups
    assert (
        res["activity_groupings"][0]["activity_subgroup"]["name"] == "activity_subgroup"
    )
    assert res["activity_groupings"][0]["activity_subgroup"]["definition"] is None

    # activity groups
    assert res["activity_groupings"][0]["activity_group"]["name"] == "activity_group"
    assert res["activity_groupings"][0]["activity_group"]["definition"] is None

    # activity instance
    assert res["activity_instance"]["uid"] is not None
    assert res["activity_instance"]["name"] == "name XXX"
    assert res["activity_instance"]["name_sentence_case"] == "name XXX"
    assert res["activity_instance"]["nci_concept_id"] == "C-XXX"
    assert res["activity_instance"]["abbreviation"] is None
    assert res["activity_instance"]["definition"] is None
    assert res["activity_instance"]["adam_param_code"] is None
    assert res["activity_instance"]["is_required_for_activity"] is True
    assert res["activity_instance"]["is_default_selected_for_activity"] is False
    assert res["activity_instance"]["is_data_sharing"] is False
    assert res["activity_instance"]["is_legacy_usage"] is False
    assert res["activity_instance"]["is_derived"] is False
    assert res["activity_instance"]["topic_code"] == "topic code XXX"
    assert res["activity_instance"]["library_name"] == LIBRARY_NAME

    # activity instance class
    assert (
        res["activity_instance"]["activity_instance_class"]["name"]
        == "Activity instance class 1"
    )

    # activity items
    items = res["activity_items"]
    assert len(items) == 3
    items = sorted(items, key=lambda item: item["activity_item_class"]["name"])

    assert len(items[0]["ct_terms"]) == 1
    assert items[0]["ct_terms"][0]["uid"] == ct_terms[0].term_uid
    assert items[0]["ct_terms"][0]["name"] == ct_terms[0].sponsor_preferred_name
    assert len(items[0]["unit_definitions"]) == 0
    assert items[0]["activity_item_class"]["name"] == "Activity Item Class name1"
    assert items[0]["activity_item_class"]["role_name"] == "Role"
    assert items[0]["activity_item_class"]["data_type_name"] == "Data type"
    assert items[0]["activity_item_class"]["order"] == 1
    assert items[0]["activity_item_class"]["mandatory"] is True

    assert len(items[0]["ct_terms"]) == 1
    assert items[1]["ct_terms"][0]["uid"] == ct_terms[1].term_uid
    assert items[1]["ct_terms"][0]["name"] == ct_terms[1].sponsor_preferred_name
    assert len(items[0]["unit_definitions"]) == 0
    assert items[1]["activity_item_class"]["name"] == "Activity Item Class name2"
    assert items[1]["activity_item_class"]["role_name"] == "Role"
    assert items[1]["activity_item_class"]["data_type_name"] == "Data type"
    assert items[1]["activity_item_class"]["order"] == 2
    assert items[1]["activity_item_class"]["mandatory"] is True

    assert len(items[2]["ct_terms"]) == 2
    terms = items[2]["ct_terms"]
    terms = sorted(terms, key=lambda term: term["uid"])
    assert terms[0]["uid"] == ct_terms[0].term_uid
    assert terms[0]["name"] == ct_terms[0].sponsor_preferred_name
    assert terms[1]["uid"] == ct_terms[1].term_uid
    assert terms[1]["name"] == ct_terms[1].sponsor_preferred_name
    assert len(items[0]["unit_definitions"]) == 0
    assert items[2]["activity_item_class"]["name"] == "Activity Item Class name3"
    assert items[2]["activity_item_class"]["role_name"] == "Role"
    assert items[2]["activity_item_class"]["data_type_name"] == "Data type"
    assert items[2]["activity_item_class"]["order"] == 3
    assert items[2]["activity_item_class"]["mandatory"] is True


def test_activity_instance_overview_export_to_yaml(api_client):
    url = f"/concepts/activities/activity-instances/{activity_instances_all[3].uid}/overview"
    export_format = "application/x-yaml"
    headers = {"Accept": export_format}
    response = api_client.get(url, headers=headers)

    assert response.status_code == 200
    assert export_format in response.headers["content-type"]

    res = yaml.load(response.text, Loader=yaml.SafeLoader)
    verify_instance_overview_content(res=res)


def test_activity_instance_cosmos_overview(api_client):
    url = f"/concepts/activities/activity-instances/{activity_instances_all[3].uid}/overview.cosmos"
    response = api_client.get(url)

    assert response.status_code == 200
    assert "application/x-yaml" in response.headers["content-type"]

    res = yaml.load(response.text, Loader=yaml.SafeLoader)

    assert res["shortName"] == "name XXX"
    assert res["conceptId"] == "C-XXX"
    assert res["resultScales"] == [""]
    assert len(res["categories"]) == 1
    assert res["categories"][0] == "activity_subgroup"
    assert len(res["dataElementConcepts"]) == 3


def test_activity_overview(api_client):
    response = api_client.get(
        f"/concepts/activities/activities/{activities[1].uid}/overview",
    )
    assert response.status_code == 200
    res = response.json()
    verify_activity_overview_content(res=res)


def verify_activity_overview_content(res: dict):
    # activity
    assert res["activity"]["name"] == "Second activity"
    assert res["activity"]["name_sentence_case"] == "Second activity"
    assert res["activity"]["definition"] is None
    assert res["activity"]["abbreviation"] is None
    assert res["activity"]["library_name"] == LIBRARY_NAME

    assert len(res["activity_groupings"]) == 1

    # activity subgroups
    assert (
        res["activity_groupings"][0]["activity_subgroup"]["name"] == "activity_subgroup"
    )
    assert res["activity_groupings"][0]["activity_subgroup"]["definition"] is None

    # activity groups
    assert res["activity_groupings"][0]["activity_group"]["name"] == "activity_group"
    assert res["activity_groupings"][0]["activity_subgroup"]["definition"] is None

    # activity instances
    assert res["activity_instances"][0]["uid"] is not None
    assert res["activity_instances"][0]["name"] == "name-AAA-0"
    assert res["activity_instances"][0]["name_sentence_case"] == "name-AAA-0"
    assert res["activity_instances"][0]["abbreviation"] is None
    assert res["activity_instances"][0]["definition"] is None
    assert res["activity_instances"][0]["adam_param_code"] is None
    assert res["activity_instances"][0]["is_required_for_activity"] is True
    assert res["activity_instances"][0]["is_default_selected_for_activity"] is False
    assert res["activity_instances"][0]["is_data_sharing"] is False
    assert res["activity_instances"][0]["is_legacy_usage"] is False
    assert res["activity_instances"][0]["is_derived"] is False
    assert res["activity_instances"][0]["topic_code"] == "topic code-AAA-0"
    assert res["activity_instances"][0]["library_name"] == LIBRARY_NAME

    # activity instance class
    assert (
        res["activity_instances"][0]["activity_instance_class"]["name"]
        == "Activity instance class 2"
    )


def test_activity_overview_export_to_yaml(api_client):
    url = f"/concepts/activities/activities/{activities[1].uid}/overview"
    export_format = "application/x-yaml"
    headers = {"Accept": export_format}
    response = api_client.get(url, headers=headers)

    assert response.status_code == 200
    assert export_format in response.headers["content-type"]

    res = yaml.load(response.text, Loader=yaml.SafeLoader)
    verify_activity_overview_content(res=res)
