"""
Tests for /studies endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import json
import logging
import random
from string import ascii_lowercase

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models import UnitDefinitionModel
from clinical_mdr_api.models.study_selections.study import Study, StudyCreateInput
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
    get_catalogue_name_library_name,
    input_metadata_in_study,
)
from clinical_mdr_api.tests.integration.utils.utils import PROJECT_NUMBER, TestUtils

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
study: Study

day_unit_definition: UnitDefinitionModel
week_unit_definition: UnitDefinitionModel


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studies.api"
    inject_and_clear_db(db_name)
    inject_base_data()
    global day_unit_definition
    day_unit_definition = TestUtils.get_unit_by_uid(
        unit_uid=TestUtils.get_unit_uid_by_name(unit_name="day")
    )
    global week_unit_definition
    week_unit_definition = TestUtils.get_unit_by_uid(
        unit_uid=TestUtils.get_unit_uid_by_name(unit_name="week")
    )

    global study
    study = TestUtils.create_study()


def test_get_study_by_uid(api_client):
    response = api_client.get(
        f"/studies/{study.uid}",
    )
    assert response.status_code == 200
    res = response.json()
    assert res["uid"] == study.uid
    assert res["study_parent_part"] is None
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"]["identification_metadata"] is not None
    assert res["current_metadata"]["version_metadata"] is not None
    assert res["current_metadata"].get("high_level_study_design") is None
    assert res["current_metadata"].get("study_population") is None
    assert res["current_metadata"].get("study_intervention") is None
    assert res["current_metadata"].get("study_description") is not None

    response = api_client.get(
        f"/studies/{study.uid}",
        params={
            "include_sections": ["high_level_study_design", "study_intervention"],
            "exclude_sections": ["identification_metadata"],
        },
    )
    assert response.status_code == 200
    res = response.json()
    assert res["uid"] == study.uid
    assert res["study_parent_part"] is None
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"].get("identification_metadata") is None
    assert res["current_metadata"]["version_metadata"] is not None
    assert res["current_metadata"].get("high_level_study_design") is not None
    assert res["current_metadata"].get("study_population") is None
    assert res["current_metadata"].get("study_intervention") is not None
    assert res["current_metadata"].get("study_description") is not None

    response = api_client.get(
        f"/studies/{study.uid}",
        params={
            "include_sections": ["non-existent section"],
            "exclude_sections": ["non-existent section"],
        },
    )
    assert response.status_code == 422


def test_get_study_fields_audit_trail(api_client):
    created_study = TestUtils.create_study()

    response = api_client.patch(
        f"/studies/{created_study.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert response.status_code == 200

    # Study-fields audit trail for all sections
    response = api_client.get(
        f"/studies/{created_study.uid}/fields-audit-trail",
    )
    assert response.status_code == 200
    res = response.json()
    for audit_trail_item in res:
        actions = audit_trail_item["actions"]
        for action in actions:
            assert action["section"] in [
                "study_description",
                "Unknown",
                "identification_metadata",
            ]

    # Study-fields audit trail for all sections without identification_metadata
    response = api_client.get(
        f"/studies/{created_study.uid}/fields-audit-trail",
        params={"exclude_sections": ["identification_metadata"]},
    )
    assert response.status_code == 200
    res = response.json()
    for audit_trail_item in res:
        actions = audit_trail_item["actions"]
        for action in actions:
            # we have filtered out the identification_metadata entries, so we should only have
            # study_description entry for study_title patch and Unknown section for preferred_time_unit that is not
            # included in any Study sections
            assert action["section"] in ["study_description", "Unknown"]

    # Study-fields audit trail with non-existent section sent
    response = api_client.get(
        f"/studies/{created_study.uid}/fields-audit-trail",
        params={"exclude_sections": ["non-existent section"]},
    )
    assert response.status_code == 422

    response = api_client.patch(
        f"/studies/{created_study.uid}",
        json={"current_metadata": {"study_description": {"study_title": ""}}},
    )
    assert response.status_code == 200

    # Study-fields audit trail for all sections
    response = api_client.get(
        f"/studies/{created_study.uid}/fields-audit-trail",
    )
    assert response.status_code == 200
    res = response.json()
    assert res[0]["actions"][0]["action"] == "Delete"
    assert res[0]["actions"][0]["after_value"]


def test_study_delete_successful(api_client):
    study_to_delete = TestUtils.create_study()
    response = api_client.delete(f"/studies/{study_to_delete.uid}")
    assert response.status_code == 204

    response = api_client.get("/studies", params={"deleted": True})
    assert response.status_code == 200
    res = response.json()
    assert len(res["items"]) == 1
    assert res["items"][0]["uid"] == study_to_delete.uid

    # try to update the deleted study
    response = api_client.patch(
        f"/studies/{study_to_delete.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert response.status_code == 400
    res = response.json()
    assert res["message"] == f"Study {study_to_delete.uid} is deleted."


def test_study_listing(api_client):
    # Create three new studies
    studies = [
        TestUtils.create_study(),
        TestUtils.create_study(),
        TestUtils.create_study(),
    ]

    response = api_client.get("/studies")
    assert response.status_code == 200
    res = response.json()
    assert len(res["items"]) >= 3
    uids = [s["uid"] for s in res["items"]]
    for study in res["items"]:
        assert "current_metadata" in study
        metadata = study["current_metadata"]
        # Check that the expected fields exist
        assert "identification_metadata" in metadata
        assert "version_metadata" in metadata
        # Check that no unwanted field is present
        assert "study_description" in metadata
        assert "high_level_study_design" not in metadata
        assert "study_population" not in metadata
        assert "study_intervention" not in metadata

    for study in studies:
        # Check that each study occurs only once in the list
        assert uids.count(study.uid) == 1

    # Clean up
    for study in studies:
        response = api_client.delete(f"/studies/{study.uid}")
        assert response.status_code == 204


def test_get_snapshot_history(api_client):
    study_with_history = TestUtils.create_study()
    # update study title to be able to lock it
    response = api_client.patch(
        f"/studies/{study_with_history.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert response.status_code == 200

    # snapshot history before lock
    response = api_client.get(f"/studies/{study_with_history.uid}/snapshot-history")
    res = response.json()
    assert response.status_code == 200
    res = res["items"]
    assert len(res) == 1
    assert res[0]["possible_actions"] == ["delete", "lock", "release"]
    assert res[0]["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res[0]["current_metadata"]["version_metadata"]["version_number"] is None

    # Lock
    response = api_client.post(
        f"/studies/{study_with_history.uid}/locks",
        json={"change_description": "Lock 1"},
    )
    assert response.status_code == 201

    # snapshot history after lock
    response = api_client.get(f"/studies/{study_with_history.uid}/snapshot-history")
    res = response.json()
    assert response.status_code == 200
    res = res["items"]
    assert len(res) == 2
    assert res[0]["current_metadata"]["version_metadata"]["study_status"] == "LOCKED"
    assert res[0]["current_metadata"]["version_metadata"]["version_number"] == 1
    assert (
        res[0]["current_metadata"]["version_metadata"]["version_description"]
        == "Lock 1"
    )
    assert res[1]["current_metadata"]["version_metadata"]["study_status"] == "RELEASED"
    assert res[1]["current_metadata"]["version_metadata"]["version_number"] == 1
    assert (
        res[1]["current_metadata"]["version_metadata"]["version_description"]
        == "Lock 1"
    )

    # Unlock
    response = api_client.delete(f"/studies/{study_with_history.uid}/locks")
    assert response.status_code == 200

    # snapshot history after unlock
    response = api_client.get(f"/studies/{study_with_history.uid}/snapshot-history")
    assert response.status_code == 200
    res = response.json()
    res = res["items"]
    assert len(res) == 3
    assert res[0]["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res[1]["current_metadata"]["version_metadata"]["version_number"] == 1
    assert res[2]["current_metadata"]["version_metadata"]["version_number"] == 1

    # Release
    response = api_client.post(
        f"/studies/{study_with_history.uid}/release",
        json={"change_description": "Explicit release"},
    )
    assert response.status_code == 201
    # snapshot history after release
    response = api_client.get(f"/studies/{study_with_history.uid}/snapshot-history")
    assert response.status_code == 200
    res = response.json()
    res = res["items"]

    assert len(res) == 4
    assert res[0]["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res[1]["current_metadata"]["version_metadata"]["study_status"] == "RELEASED"
    assert (
        res[1]["current_metadata"]["version_metadata"]["version_description"]
        == "Explicit release"
    )
    assert res[1]["current_metadata"]["version_metadata"]["version_number"] == 1.1
    assert res[2]["current_metadata"]["version_metadata"]["version_number"] == 1
    assert (
        res[2]["current_metadata"]["version_metadata"]["version_description"]
        == "Lock 1"
    )

    # 2nd Release
    response = api_client.post(
        f"/studies/{study_with_history.uid}/release",
        json={"change_description": "Explicit second release"},
    )
    assert response.status_code == 201
    # snapshot history after second release
    response = api_client.get(f"/studies/{study_with_history.uid}/snapshot-history")
    assert response.status_code == 200
    res = response.json()
    res = res["items"]
    assert len(res) == 5
    assert res[0]["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res[1]["current_metadata"]["version_metadata"]["study_status"] == "RELEASED"
    assert (
        res[1]["current_metadata"]["version_metadata"]["version_description"]
        == "Explicit second release"
    )
    assert res[1]["current_metadata"]["version_metadata"]["version_number"] == 1.2
    assert res[2]["current_metadata"]["version_metadata"]["study_status"] == "RELEASED"
    assert res[2]["current_metadata"]["version_metadata"]["version_number"] == 1.1
    assert (
        res[2]["current_metadata"]["version_metadata"]["version_description"]
        == "Explicit release"
    )

    # Lock
    response = api_client.post(
        f"/studies/{study_with_history.uid}/locks",
        json={"change_description": "Lock 2"},
    )
    assert response.status_code == 201

    # snapshot history after lock
    response = api_client.get(f"/studies/{study_with_history.uid}/snapshot-history")
    assert response.status_code == 200
    res = response.json()
    res = res["items"]
    assert len(res) == 6
    assert res[0]["current_metadata"]["version_metadata"]["study_status"] == "LOCKED"
    assert res[0]["current_metadata"]["version_metadata"]["version_number"] == 2
    assert (
        res[0]["current_metadata"]["version_metadata"]["version_description"]
        == "Lock 2"
    )
    assert res[1]["current_metadata"]["version_metadata"]["study_status"] == "RELEASED"
    assert res[1]["current_metadata"]["version_metadata"]["version_number"] == 2
    assert (
        res[1]["current_metadata"]["version_metadata"]["version_description"]
        == "Lock 2"
    )


def test_get_default_time_unit(api_client):
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={
            "current_metadata": {
                "identification_metadata": {"study_acronym": "new acronym"}
            }
        },
    )
    assert response.status_code == 200
    res = response.json()
    assert (
        res["current_metadata"]["identification_metadata"]["study_acronym"]
        == "new acronym"
    )
    assert (
        res["current_metadata"]["identification_metadata"]["study_subpart_acronym"]
        is None
    )

    response = api_client.get(f"/studies/{study.uid}/time-units")
    assert response.status_code == 200
    res = response.json()
    assert res["study_uid"] == study.uid
    assert res["time_unit_uid"] == day_unit_definition.uid
    assert res["time_unit_name"] == day_unit_definition.name


def test_edit_time_units(api_client):
    response = api_client.patch(
        f"/studies/{study.uid}/time-units",
        json={"unit_definition_uid": day_unit_definition.uid},
    )
    res = response.json()
    assert response.status_code == 400
    assert (
        res["message"]
        == f"The Preferred Time Unit for the following study ({study.uid}) is already ({day_unit_definition.uid})"
    )

    response = api_client.patch(
        f"/studies/{study.uid}/time-units",
        json={"unit_definition_uid": week_unit_definition.uid},
    )
    res = response.json()
    assert response.status_code == 200
    assert res["study_uid"] == study.uid
    assert res["time_unit_uid"] == week_unit_definition.uid
    assert res["time_unit_name"] == week_unit_definition.name


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
def test_get_studies_csv_xml_excel(api_client, export_format):
    TestUtils.verify_exported_data_format(api_client, export_format, "/studies")


def test_get_specific_version(api_client):
    study = TestUtils.create_study()

    title_1 = "new title"
    title_11 = "title after 1st lock."
    title_12 = "title after 1st release."
    title_2 = "title after 2nd release."
    title_draft = "title after 2nd lock."

    # update study title to be able to lock it
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={"current_metadata": {"study_description": {"study_title": title_1}}},
    )
    assert response.status_code == 200

    # Lock
    response = api_client.post(
        f"/studies/{study.uid}/locks", json={"change_description": "Lock 1"}
    )
    assert response.status_code == 201

    # Unlock
    response = api_client.delete(f"/studies/{study.uid}/locks")
    assert response.status_code == 200

    # update study title
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={"current_metadata": {"study_description": {"study_title": title_11}}},
    )
    assert response.status_code == 200

    # Release
    response = api_client.post(
        f"/studies/{study.uid}/release",
        json={"change_description": "Explicit release"},
    )
    assert response.status_code == 201

    # update study title
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={"current_metadata": {"study_description": {"study_title": title_12}}},
    )
    assert response.status_code == 200

    # 2nd Release
    response = api_client.post(
        f"/studies/{study.uid}/release",
        json={"change_description": "Explicit second release"},
    )
    assert response.status_code == 201

    # update study title
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={"current_metadata": {"study_description": {"study_title": title_2}}},
    )
    assert response.status_code == 200

    # Lock
    response = api_client.post(
        f"/studies/{study.uid}/locks", json={"change_description": "Lock 2"}
    )
    assert response.status_code == 201

    # Unlock
    response = api_client.delete(f"/studies/{study.uid}/locks")
    assert response.status_code == 200

    # update study title
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={"current_metadata": {"study_description": {"study_title": title_draft}}},
    )
    assert response.status_code == 200

    # check study title in different versions
    response = api_client.get(
        f"/studies/{study.uid}",
        params={"include_sections": ["study_description"], "study_value_version": "1"},
    )
    res_title = response.json()["current_metadata"]["study_description"]["study_title"]
    assert res_title == title_1
    response = api_client.get(
        f"/studies/{study.uid}",
        params={
            "include_sections": ["study_description"],
            "study_value_version": "1.1",
        },
    )
    res_title = response.json()["current_metadata"]["study_description"]["study_title"]
    assert res_title == title_11
    response = api_client.get(
        f"/studies/{study.uid}",
        params={
            "include_sections": ["study_description"],
            "study_value_version": "1.2",
        },
    )
    res_title = response.json()["current_metadata"]["study_description"]["study_title"]
    assert res_title == title_12
    response = api_client.get(
        f"/studies/{study.uid}",
        params={"include_sections": ["study_description"], "study_value_version": "2"},
    )
    res_title = response.json()["current_metadata"]["study_description"]["study_title"]
    assert res_title == title_2
    response = api_client.get(
        f"/studies/{study.uid}",
        params={"include_sections": ["study_description"]},
    )
    res_title = response.json()["current_metadata"]["study_description"]["study_title"]
    assert res_title == title_draft


def test_get_protocol_title_for_specific_version(api_client):
    study = TestUtils.create_study()
    TestUtils.create_library(name="UCUM", is_editable=True)
    codelist = TestUtils.create_ct_codelist()
    TestUtils.create_study_ct_data_map(codelist_uid=codelist.codelist_uid)
    compound = TestUtils.create_compound(name="name-AAA", approve=True)
    compound_alias = TestUtils.create_compound_alias(
        name="compAlias-AAA", compound_uid=compound.uid, approve=True
    )
    compound2 = TestUtils.create_compound(name="name-BBB", approve=True)
    compound_alias2 = TestUtils.create_compound_alias(
        name="compAlias-BBB", compound_uid=compound2.uid, approve=True
    )
    catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils=True)
    type_of_trt_codelist = create_codelist(
        name="Type of Treatment",
        uid="CTCodelist_00009",
        catalogue=catalogue_name,
        library=library_name,
    )
    type_of_treatment = create_ct_term(
        codelist=type_of_trt_codelist.codelist_uid,
        name="Investigational Product",
        uid="type_of_treatment_00001",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
    )

    # add some metadata to study
    input_metadata_in_study(study.uid)

    # add a study compound
    response = api_client.post(
        f"/studies/{study.uid}/study-compounds",
        json={
            "compound_alias_uid": compound_alias.uid,
            "type_of_treatment_uid": type_of_treatment.uid,
        },
    )
    res = response.json()
    study_compound_uid = res["study_compound_uid"]
    assert response.status_code == 201

    # response before locking
    response = api_client.get(
        f"/studies/{study.uid}/protocol-title",
    )
    assert response.status_code == 200
    res_old = response.json()

    # Lock
    response = api_client.post(
        f"/studies/{study.uid}/locks", json={"change_description": "Lock 1"}
    )
    assert response.status_code == 201

    # Unlock
    response = api_client.delete(f"/studies/{study.uid}/locks")
    assert response.status_code == 200

    # Update
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={
            "current_metadata": {
                "study_description": {
                    "study_title": "some title, updated",
                }
            }
        },
    )
    assert response.status_code == 200
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={
            "current_metadata": {
                "identification_metadata": {
                    "registry_identifiers": {"eudract_id": "eudract_id, updated"}
                },
            }
        },
    )
    assert response.status_code == 200
    response = api_client.patch(
        f"/studies/{study.uid}/study-compounds/{study_compound_uid}",
        json={"compound_alias_uid": compound_alias2.uid},
    )
    assert response.status_code == 200
    # check the study compound dosings for version 1 is same as first locked
    res_new = api_client.get(
        f"/studies/{study.uid}/protocol-title",
    ).json()
    res_v1 = api_client.get(
        f"/studies/{study.uid}/protocol-title?study_value_version=1",
    ).json()
    assert res_v1 == res_old
    assert res_v1 != res_new


def test_create_study_subpart(api_client):
    response = api_client.post(
        "/studies",
        json={
            "study_acronym": "something",
            "study_subpart_acronym": "sub something",
            "description": "desc",
            "study_parent_part_uid": study.uid,
        },
    )
    assert response.status_code == 201
    post_res = response.json()
    assert post_res["uid"]
    assert post_res["study_parent_part"] == {
        "uid": "Study_000002",
        "study_number": study.current_metadata.identification_metadata.study_number,
        "study_acronym": "new acronym",
        "project_number": "123",
        "description": study.current_metadata.identification_metadata.description,
        "study_id": study.current_metadata.identification_metadata.study_id,
        "study_title": None,
        "registry_identifiers": {
            "ct_gov_id": None,
            "ct_gov_id_null_value_code": None,
            "eudract_id": None,
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": None,
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": None,
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": None,
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": None,
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": None,
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": None,
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": None,
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": None,
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": None,
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": None,
            "investigational_device_exemption_ide_number_null_value_code": None,
        },
    }
    assert post_res["study_subpart_uids"] == []
    assert post_res["current_metadata"].get("identification_metadata") == {
        "study_number": study.current_metadata.identification_metadata.study_number,
        "subpart_id": "a",
        "study_acronym": "something",
        "study_subpart_acronym": "sub something",
        "project_number": "123",
        "project_name": "Project ABC",
        "description": "desc",
        "clinical_programme_name": "CP",
        "study_id": f"{study.current_metadata.identification_metadata.study_id}-a",
        "registry_identifiers": {
            "ct_gov_id": None,
            "ct_gov_id_null_value_code": None,
            "eudract_id": None,
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": None,
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": None,
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": None,
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": None,
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": None,
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": None,
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": None,
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": None,
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": None,
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": None,
            "investigational_device_exemption_ide_number_null_value_code": None,
        },
    }
    assert post_res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert post_res["current_metadata"]["version_metadata"]["version_number"] is None
    assert (
        post_res["current_metadata"]["version_metadata"]["version_author"]
        == "unknown-user"
    )
    assert (
        post_res["current_metadata"]["version_metadata"]["version_description"] is None
    )

    # Check get response of study subpart
    response = api_client.get(f"/studies/{post_res['uid']}")
    assert response.status_code == 200
    get_res = response.json()
    assert get_res["uid"] == post_res["uid"]
    assert get_res["study_parent_part"] == {
        "uid": "Study_000002",
        "study_number": study.current_metadata.identification_metadata.study_number,
        "study_acronym": "new acronym",
        "project_number": "123",
        "description": study.current_metadata.identification_metadata.description,
        "study_id": study.current_metadata.identification_metadata.study_id,
        "study_title": None,
        "registry_identifiers": {
            "ct_gov_id": None,
            "ct_gov_id_null_value_code": None,
            "eudract_id": None,
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": None,
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": None,
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": None,
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": None,
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": None,
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": None,
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": None,
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": None,
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": None,
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": None,
            "investigational_device_exemption_ide_number_null_value_code": None,
        },
    }
    assert get_res["study_subpart_uids"] == []
    assert get_res["current_metadata"].get("identification_metadata") == {
        "study_number": study.current_metadata.identification_metadata.study_number,
        "subpart_id": "a",
        "study_acronym": "something",
        "study_subpart_acronym": "sub something",
        "project_number": "123",
        "project_name": "Project ABC",
        "description": "desc",
        "clinical_programme_name": "CP",
        "study_id": f"{study.current_metadata.identification_metadata.study_id}-a",
        "registry_identifiers": {
            "ct_gov_id": None,
            "ct_gov_id_null_value_code": None,
            "eudract_id": None,
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": None,
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": None,
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": None,
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": None,
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": None,
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": None,
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": None,
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": None,
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": None,
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": None,
            "investigational_device_exemption_ide_number_null_value_code": None,
        },
    }
    assert get_res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert get_res["current_metadata"]["version_metadata"]["version_number"] is None
    assert (
        get_res["current_metadata"]["version_metadata"]["version_author"]
        == "unknown-user"
    )
    assert (
        get_res["current_metadata"]["version_metadata"]["version_description"] is None
    )

    # Check get response of study parent part
    response = api_client.get(f"/studies/{study.uid}")
    assert response.status_code == 200
    get_res = response.json()
    assert get_res["uid"] == study.uid
    assert get_res["study_parent_part"] is None
    assert get_res["study_subpart_uids"] == [post_res["uid"]]
    assert get_res["current_metadata"]["identification_metadata"] is not None
    assert get_res["current_metadata"]["version_metadata"] is not None
    assert get_res["current_metadata"].get("high_level_study_design") is None
    assert get_res["current_metadata"].get("study_population") is None
    assert get_res["current_metadata"].get("study_intervention") is None
    assert get_res["current_metadata"].get("study_description") is not None


def test_use_an_already_existing_study_as_a_study_subpart(api_client):
    parent_study = TestUtils.create_study()
    new_study = TestUtils.create_study()
    response = api_client.patch(
        f"/studies/{new_study.uid}",
        json={
            "study_parent_part_uid": parent_study.uid,
            "current_metadata": {
                "identification_metadata": {
                    "study_acronym": "something",
                    "study_subpart_acronym": "sub something",
                }
            },
        },
    )
    assert response.status_code == 200
    post_res = response.json()
    assert post_res["uid"]
    assert post_res["study_parent_part"] == {
        "uid": parent_study.uid,
        "study_number": parent_study.current_metadata.identification_metadata.study_number,
        "study_acronym": parent_study.current_metadata.identification_metadata.study_acronym,
        "project_number": "123",
        "description": parent_study.current_metadata.identification_metadata.description,
        "study_id": parent_study.current_metadata.identification_metadata.study_id,
        "study_title": None,
        "registry_identifiers": {
            "ct_gov_id": None,
            "ct_gov_id_null_value_code": None,
            "eudract_id": None,
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": None,
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": None,
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": None,
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": None,
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": None,
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": None,
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": None,
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": None,
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": None,
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": None,
            "investigational_device_exemption_ide_number_null_value_code": None,
        },
    }
    assert post_res["study_subpart_uids"] == []
    assert post_res["current_metadata"].get("identification_metadata") == {
        "study_number": parent_study.current_metadata.identification_metadata.study_number,
        "subpart_id": "a",
        "project_number": "123",
        "study_acronym": "something",
        "study_subpart_acronym": "sub something",
        "project_name": new_study.current_metadata.identification_metadata.project_name,
        "description": new_study.current_metadata.identification_metadata.description,
        "clinical_programme_name": "CP",
        "study_id": f"{parent_study.current_metadata.identification_metadata.study_id}-a",
        "registry_identifiers": {
            "ct_gov_id": None,
            "ct_gov_id_null_value_code": None,
            "eudract_id": None,
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": None,
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": None,
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": None,
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": None,
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": None,
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": None,
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": None,
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": None,
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": None,
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": None,
            "investigational_device_exemption_ide_number_null_value_code": None,
        },
    }
    assert post_res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert post_res["current_metadata"]["version_metadata"]["version_number"] is None
    assert (
        post_res["current_metadata"]["version_metadata"]["version_author"]
        == "unknown-user"
    )
    assert (
        post_res["current_metadata"]["version_metadata"]["version_description"] is None
    )

    # Check get response of study parent part
    response = api_client.get(f"/studies/{parent_study.uid}")
    assert response.status_code == 200
    get_res = response.json()
    assert get_res["uid"] == parent_study.uid
    assert get_res["study_parent_part"] is None
    assert get_res["study_subpart_uids"] == [post_res["uid"]]
    assert get_res["current_metadata"]["identification_metadata"] is not None
    assert get_res["current_metadata"]["version_metadata"] is not None
    assert get_res["current_metadata"].get("high_level_study_design") is None
    assert get_res["current_metadata"].get("study_population") is None
    assert get_res["current_metadata"].get("study_intervention") is None
    assert get_res["current_metadata"].get("study_description") is not None

    # Check get response of study subpart
    response = api_client.get(f"/studies/{new_study.uid}")
    assert response.status_code == 200
    get_res = response.json()
    assert get_res["study_parent_part"] == {
        "uid": parent_study.uid,
        "study_number": parent_study.current_metadata.identification_metadata.study_number,
        "study_acronym": parent_study.current_metadata.identification_metadata.study_acronym,
        "project_number": "123",
        "description": parent_study.current_metadata.identification_metadata.description,
        "study_id": parent_study.current_metadata.identification_metadata.study_id,
        "study_title": None,
        "registry_identifiers": {
            "ct_gov_id": None,
            "ct_gov_id_null_value_code": None,
            "eudract_id": None,
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": None,
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": None,
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": None,
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": None,
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": None,
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": None,
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": None,
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": None,
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": None,
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": None,
            "investigational_device_exemption_ide_number_null_value_code": None,
        },
    }
    assert get_res["study_subpart_uids"] == []
    assert get_res["current_metadata"].get("identification_metadata") == {
        "study_number": parent_study.current_metadata.identification_metadata.study_number,
        "subpart_id": "a",
        "project_number": "123",
        "study_acronym": "something",
        "study_subpart_acronym": "sub something",
        "project_name": new_study.current_metadata.identification_metadata.project_name,
        "description": new_study.current_metadata.identification_metadata.description,
        "clinical_programme_name": "CP",
        "study_id": f"{parent_study.current_metadata.identification_metadata.study_id}-a",
        "registry_identifiers": {
            "ct_gov_id": None,
            "ct_gov_id_null_value_code": None,
            "eudract_id": None,
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": None,
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": None,
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": None,
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": None,
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": None,
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": None,
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": None,
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": None,
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": None,
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": None,
            "investigational_device_exemption_ide_number_null_value_code": None,
        },
    }
    assert get_res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert get_res["current_metadata"]["version_metadata"]["version_number"] is None
    assert (
        get_res["current_metadata"]["version_metadata"]["version_author"]
        == "unknown-user"
    )
    assert (
        get_res["current_metadata"]["version_metadata"]["version_description"] is None
    )


def test_cascade_of_study_parent_part(api_client):
    def _check_study_subparts_status(status: str):
        response = api_client.get(
            "/studies",
            params={
                "filters": json.dumps(
                    {
                        "study_parent_part.uid": {
                            "v": [f"{parent_study.uid}"],
                            "op": "eq",
                        }
                    }
                ),
                "page_size": 0,
            },
        )
        assert response.status_code == 200
        res = response.json()
        for item in res["items"]:
            assert (
                item["current_metadata"]["version_metadata"]["study_status"] == status
            )

    parent_study = TestUtils.create_study()
    for _ in range(10):
        TestUtils.create_study(study_parent_part_uid=parent_study.uid)

    response = api_client.patch(
        f"/studies/{parent_study.uid}",
        json={
            "current_metadata": {
                "identification_metadata": {
                    "registry_identifiers": {
                        "ct_gov_id": "ct_gov_id",
                        "eudract_id": "eudract_id",
                        "investigational_new_drug_application_number_ind": "investigational_new_drug_application_number_ind",
                        "japanese_trial_registry_id_japic": "japanese_trial_registry_id_japic",
                        "universal_trial_number_utn": "universal_trial_number_utn",
                        "eu_trial_number": "eu_trial_number",
                        "civ_id_sin_number": "civ_id_sin_number",
                        "national_clinical_trial_number": "national_clinical_trial_number",
                        "japanese_trial_registry_number_jrct": "japanese_trial_registry_number_jrct",
                        "national_medical_products_administration_nmpa_number": "national_medical_products_administration_nmpa_number",
                        "eudamed_srn_number": "eudamed_srn_number",
                        "investigational_device_exemption_ide_number": "investigational_device_exemption_ide_number",
                    }
                },
                "study_description": {
                    "study_title": "new title",
                    "study_short_title": "new short title",
                },
            }
        },
    )
    assert response.status_code == 200

    response = api_client.get(
        "/studies",
        params={
            "filters": json.dumps(
                {
                    "study_parent_part.uid": {
                        "v": [f"{parent_study.uid}"],
                        "op": "eq",
                    }
                }
            ),
            "page_size": 0,
        },
    )
    assert response.status_code == 200
    res = response.json()
    for item in res["items"]:
        response = api_client.get(f"/studies/{item['uid']}")
        rs = response.json()
        assert rs["current_metadata"]["study_description"]["study_title"] == "new title"
        assert (
            rs["current_metadata"]["study_description"]["study_short_title"]
            == "new short title"
        )
        assert rs["current_metadata"]["identification_metadata"][
            "registry_identifiers"
        ] == {
            "ct_gov_id": "ct_gov_id",
            "ct_gov_id_null_value_code": None,
            "eudract_id": "eudract_id",
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": "investigational_new_drug_application_number_ind",
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": "japanese_trial_registry_id_japic",
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": "universal_trial_number_utn",
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": "eu_trial_number",
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": "civ_id_sin_number",
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": "national_clinical_trial_number",
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": "japanese_trial_registry_number_jrct",
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": "national_medical_products_administration_nmpa_number",
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": "eudamed_srn_number",
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": "investigational_device_exemption_ide_number",
            "investigational_device_exemption_ide_number_null_value_code": None,
        }

    response = api_client.post(
        f"/studies/{parent_study.uid}/locks",
        json={"change_description": "Locked"},
    )
    assert response.status_code == 201
    res = response.json()
    assert res["current_metadata"]["version_metadata"]["study_status"] == "LOCKED"
    _check_study_subparts_status("LOCKED")

    response = api_client.delete(f"/studies/{parent_study.uid}/locks")
    assert response.status_code == 200
    res = response.json()
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    _check_study_subparts_status("DRAFT")

    response = api_client.post(
        f"/studies/{parent_study.uid}/release",
        json={"change_description": "Released"},
    )
    assert response.status_code == 201
    res = response.json()
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    _check_study_subparts_status("DRAFT")


def test_reordering_study_subparts(api_client):
    parent_study = TestUtils.create_study()
    new_studies = [
        TestUtils.create_study(study_parent_part_uid=parent_study.uid)
        for _ in range(10)
    ]

    response = api_client.patch(
        f"/studies/{parent_study.uid}/order",
        json={
            "uid": new_studies[2].uid,
            "subpart_id": "a",
        },
    )
    assert response.status_code == 200
    res = response.json()
    assert res[0]["current_metadata"]["identification_metadata"]["subpart_id"] == "b"
    assert res[1]["current_metadata"]["identification_metadata"]["subpart_id"] == "c"
    assert res[2]["current_metadata"]["identification_metadata"]["subpart_id"] == "a"
    assert res[3]["current_metadata"]["identification_metadata"]["subpart_id"] == "d"
    assert res[4]["current_metadata"]["identification_metadata"]["subpart_id"] == "e"
    assert res[5]["current_metadata"]["identification_metadata"]["subpart_id"] == "f"
    assert res[6]["current_metadata"]["identification_metadata"]["subpart_id"] == "g"
    assert res[7]["current_metadata"]["identification_metadata"]["subpart_id"] == "h"
    assert res[8]["current_metadata"]["identification_metadata"]["subpart_id"] == "i"
    assert res[9]["current_metadata"]["identification_metadata"]["subpart_id"] == "j"
    new_studies[0].current_metadata.identification_metadata.subpart_id = "b"
    new_studies[1].current_metadata.identification_metadata.subpart_id = "c"
    new_studies[2].current_metadata.identification_metadata.subpart_id = "a"
    new_studies[3].current_metadata.identification_metadata.subpart_id = "d"
    new_studies[4].current_metadata.identification_metadata.subpart_id = "e"
    new_studies[5].current_metadata.identification_metadata.subpart_id = "f"
    new_studies[6].current_metadata.identification_metadata.subpart_id = "g"
    new_studies[7].current_metadata.identification_metadata.subpart_id = "h"
    new_studies[8].current_metadata.identification_metadata.subpart_id = "i"
    new_studies[9].current_metadata.identification_metadata.subpart_id = "j"

    response = api_client.patch(
        f"/studies/{parent_study.uid}/order",
        json={
            "uid": new_studies[5].uid,
            "subpart_id": "d",
        },
    )
    assert response.status_code == 200
    res = response.json()
    assert res[0]["current_metadata"]["identification_metadata"]["subpart_id"] == "b"
    assert res[1]["current_metadata"]["identification_metadata"]["subpart_id"] == "c"
    assert res[2]["current_metadata"]["identification_metadata"]["subpart_id"] == "a"
    assert res[3]["current_metadata"]["identification_metadata"]["subpart_id"] == "e"
    assert res[4]["current_metadata"]["identification_metadata"]["subpart_id"] == "f"
    assert res[5]["current_metadata"]["identification_metadata"]["subpart_id"] == "d"
    assert res[6]["current_metadata"]["identification_metadata"]["subpart_id"] == "g"
    assert res[7]["current_metadata"]["identification_metadata"]["subpart_id"] == "h"
    assert res[8]["current_metadata"]["identification_metadata"]["subpart_id"] == "i"
    assert res[9]["current_metadata"]["identification_metadata"]["subpart_id"] == "j"
    new_studies[0].current_metadata.identification_metadata.subpart_id = "b"
    new_studies[1].current_metadata.identification_metadata.subpart_id = "c"
    new_studies[2].current_metadata.identification_metadata.subpart_id = "a"
    new_studies[3].current_metadata.identification_metadata.subpart_id = "e"
    new_studies[4].current_metadata.identification_metadata.subpart_id = "f"
    new_studies[5].current_metadata.identification_metadata.subpart_id = "d"
    new_studies[6].current_metadata.identification_metadata.subpart_id = "g"
    new_studies[7].current_metadata.identification_metadata.subpart_id = "h"
    new_studies[8].current_metadata.identification_metadata.subpart_id = "i"
    new_studies[9].current_metadata.identification_metadata.subpart_id = "j"

    response = api_client.patch(
        f"/studies/{parent_study.uid}/order",
        json={
            "uid": new_studies[9].uid,
            "subpart_id": "a",
        },
    )
    assert response.status_code == 200
    res = response.json()
    assert res[0]["current_metadata"]["identification_metadata"]["subpart_id"] == "c"
    assert res[1]["current_metadata"]["identification_metadata"]["subpart_id"] == "d"
    assert res[2]["current_metadata"]["identification_metadata"]["subpart_id"] == "b"
    assert res[3]["current_metadata"]["identification_metadata"]["subpart_id"] == "f"
    assert res[4]["current_metadata"]["identification_metadata"]["subpart_id"] == "g"
    assert res[5]["current_metadata"]["identification_metadata"]["subpart_id"] == "e"
    assert res[6]["current_metadata"]["identification_metadata"]["subpart_id"] == "h"
    assert res[7]["current_metadata"]["identification_metadata"]["subpart_id"] == "i"
    assert res[8]["current_metadata"]["identification_metadata"]["subpart_id"] == "j"
    assert res[9]["current_metadata"]["identification_metadata"]["subpart_id"] == "a"
    new_studies[0].current_metadata.identification_metadata.subpart_id = "c"
    new_studies[1].current_metadata.identification_metadata.subpart_id = "d"
    new_studies[2].current_metadata.identification_metadata.subpart_id = "b"
    new_studies[3].current_metadata.identification_metadata.subpart_id = "f"
    new_studies[4].current_metadata.identification_metadata.subpart_id = "g"
    new_studies[5].current_metadata.identification_metadata.subpart_id = "e"
    new_studies[6].current_metadata.identification_metadata.subpart_id = "h"
    new_studies[7].current_metadata.identification_metadata.subpart_id = "i"
    new_studies[8].current_metadata.identification_metadata.subpart_id = "j"
    new_studies[9].current_metadata.identification_metadata.subpart_id = "a"

    response = api_client.patch(
        f"/studies/{parent_study.uid}/order",
        json={
            "uid": new_studies[9].uid,
            "subpart_id": "j",
        },
    )
    assert response.status_code == 200
    res = response.json()
    assert res[0]["current_metadata"]["identification_metadata"]["subpart_id"] == "b"
    assert res[1]["current_metadata"]["identification_metadata"]["subpart_id"] == "c"
    assert res[2]["current_metadata"]["identification_metadata"]["subpart_id"] == "a"
    assert res[3]["current_metadata"]["identification_metadata"]["subpart_id"] == "e"
    assert res[4]["current_metadata"]["identification_metadata"]["subpart_id"] == "f"
    assert res[5]["current_metadata"]["identification_metadata"]["subpart_id"] == "d"
    assert res[6]["current_metadata"]["identification_metadata"]["subpart_id"] == "g"
    assert res[7]["current_metadata"]["identification_metadata"]["subpart_id"] == "h"
    assert res[8]["current_metadata"]["identification_metadata"]["subpart_id"] == "i"
    assert res[9]["current_metadata"]["identification_metadata"]["subpart_id"] == "j"
    new_studies[0].current_metadata.identification_metadata.subpart_id = "b"
    new_studies[1].current_metadata.identification_metadata.subpart_id = "c"
    new_studies[2].current_metadata.identification_metadata.subpart_id = "a"
    new_studies[3].current_metadata.identification_metadata.subpart_id = "e"
    new_studies[4].current_metadata.identification_metadata.subpart_id = "f"
    new_studies[5].current_metadata.identification_metadata.subpart_id = "d"
    new_studies[6].current_metadata.identification_metadata.subpart_id = "g"
    new_studies[7].current_metadata.identification_metadata.subpart_id = "h"
    new_studies[8].current_metadata.identification_metadata.subpart_id = "i"
    new_studies[9].current_metadata.identification_metadata.subpart_id = "j"


def test_auto_reordering_after_deleting_a_study_subpart(api_client):
    parent_study = TestUtils.create_study()
    new_studies = [
        TestUtils.create_study(study_parent_part_uid=parent_study.uid)
        for _ in range(10)
    ]

    uids_of_random_study_subparts_to_delete = {
        random_study.uid
        for random_study in random.choices(new_studies, k=random.randint(0, 7))
    }
    for (
        uid_of_random_study_subpart_to_delete
    ) in uids_of_random_study_subparts_to_delete:
        response = api_client.delete(
            f"/studies/{uid_of_random_study_subpart_to_delete}"
        )
        assert response.status_code == 204

    response = api_client.get(
        "/studies",
        params={
            "filters": json.dumps(
                {
                    "study_parent_part.uid": {
                        "v": [f"{parent_study.uid}"],
                        "op": "eq",
                    }
                }
            ),
            "page_size": 0,
        },
    )
    assert response.status_code == 200
    res = response.json()

    letters = ascii_lowercase[: 10 - len(uids_of_random_study_subparts_to_delete)]
    idx = 0
    for item in res["items"]:
        if item["uid"] not in uids_of_random_study_subparts_to_delete:
            assert (
                item["current_metadata"]["identification_metadata"]["subpart_id"]
                == letters[idx]
            )
            idx += 1

    study_uids = [item["uid"] for item in res["items"]]
    assert all(
        uid_of_random_study_subpart_to_delete not in study_uids
        for uid_of_random_study_subpart_to_delete in uids_of_random_study_subparts_to_delete
    )


def test_remove_study_subpart_from_parent_part(api_client):
    parent_part = TestUtils.create_study()
    new_study = StudyService().create(
        StudyCreateInput(
            study_number="8772",
            study_acronym=None,
            project_number=PROJECT_NUMBER,
            description=None,
        )
    )
    response = api_client.patch(
        f"/studies/{new_study.uid}",
        json={
            "study_parent_part_uid": parent_part.uid,
            "current_metadata": {
                "identification_metadata": {
                    "study_subpart_acronym": "sub something",
                }
            },
        },
    )
    assert response.status_code == 200
    res = response.json()
    assert res["uid"]
    assert res["study_parent_part"] == {
        "uid": parent_part.uid,
        "study_number": parent_part.current_metadata.identification_metadata.study_number,
        "study_acronym": parent_part.current_metadata.identification_metadata.study_acronym,
        "project_number": "123",
        "description": parent_part.current_metadata.identification_metadata.description,
        "study_id": parent_part.current_metadata.identification_metadata.study_id,
        "study_title": None,
        "registry_identifiers": {
            "ct_gov_id": None,
            "ct_gov_id_null_value_code": None,
            "eudract_id": None,
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": None,
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": None,
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": None,
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": None,
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": None,
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": None,
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": None,
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": None,
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": None,
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": None,
            "investigational_device_exemption_ide_number_null_value_code": None,
        },
    }
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"].get("identification_metadata") == {
        "study_number": parent_part.current_metadata.identification_metadata.study_number,
        "subpart_id": "a",
        "project_number": "123",
        "study_acronym": None,
        "study_subpart_acronym": "sub something",
        "project_name": new_study.current_metadata.identification_metadata.project_name,
        "description": None,
        "clinical_programme_name": "CP",
        "study_id": f"{parent_part.current_metadata.identification_metadata.study_id}-a",
        "registry_identifiers": {
            "ct_gov_id": None,
            "ct_gov_id_null_value_code": None,
            "eudract_id": None,
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": None,
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": None,
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": None,
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": None,
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": None,
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": None,
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": None,
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": None,
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": None,
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": None,
            "investigational_device_exemption_ide_number_null_value_code": None,
        },
    }
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res["current_metadata"]["version_metadata"]["version_number"] is None
    assert (
        res["current_metadata"]["version_metadata"]["version_author"] == "unknown-user"
    )
    assert res["current_metadata"]["version_metadata"]["version_description"] is None

    response = api_client.patch(
        f"/studies/{new_study.uid}",
        json={
            "study_parent_part_uid": None,
            "current_metadata": {"identification_metadata": {"study_acronym": None}},
        },
    )
    assert response.status_code == 400
    res = response.json()
    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == "Either study number or study acronym must be given in study metadata."
    )

    response = api_client.patch(
        f"/studies/{new_study.uid}",
        json={
            "study_parent_part_uid": None,
            "current_metadata": {
                "identification_metadata": {"study_acronym": "something"}
            },
        },
    )
    res = response.json()
    assert response.status_code == 200
    assert res["uid"]
    assert res["study_parent_part"] is None
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"].get("identification_metadata") == {
        "study_number": None,
        "subpart_id": None,
        "project_number": "123",
        "study_acronym": "something",
        "study_subpart_acronym": None,
        "project_name": new_study.current_metadata.identification_metadata.project_name,
        "description": None,
        "clinical_programme_name": "CP",
        "study_id": None,
        "registry_identifiers": {
            "ct_gov_id": None,
            "ct_gov_id_null_value_code": None,
            "eudract_id": None,
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": None,
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": None,
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": None,
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": None,
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": None,
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": None,
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": None,
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": None,
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": None,
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": None,
            "investigational_device_exemption_ide_number_null_value_code": None,
        },
    }
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res["current_metadata"]["version_metadata"]["version_number"] is None
    assert (
        res["current_metadata"]["version_metadata"]["version_author"] == "unknown-user"
    )
    assert res["current_metadata"]["version_metadata"]["version_description"] is None


def test_get_audit_trail_of_all_study_subparts_of_study(api_client):
    response = api_client.get("/studies/Study_000025/audit-trail")
    assert response.status_code == 200
    res = response.json()
    for i in [
        "subpart_uid",
        "subpart_id",
        "study_acronym",
        "study_subpart_acronym",
        "start_date",
        "end_date",
        "user_initials",
        "change_type",
        "changes",
    ]:
        assert i in res[0]

    assert len(res) == 36

    assert res[0]["subpart_id"] == "i"
    assert res[0]["subpart_uid"] == "Study_000034"
    assert res[1]["subpart_id"] == "h"
    assert res[1]["subpart_uid"] == "Study_000033"
    assert res[2]["subpart_id"] == "g"
    assert res[2]["subpart_uid"] == "Study_000032"
    assert res[3]["subpart_id"] == "f"
    assert res[3]["subpart_uid"] == "Study_000030"
    assert res[4]["subpart_id"] == "e"
    assert res[4]["subpart_uid"] == "Study_000029"
    assert res[5]["subpart_id"] == "d"
    assert res[5]["subpart_uid"] == "Study_000031"
    assert res[6]["subpart_id"] == "c"
    assert res[6]["subpart_uid"] == "Study_000027"
    assert res[7]["subpart_id"] == "b"
    assert res[7]["subpart_uid"] == "Study_000026"
    assert res[8]["subpart_id"] == "a"
    assert res[8]["subpart_uid"] == "Study_000028"
    assert res[9]["subpart_id"] == "j"
    assert res[9]["subpart_uid"] == "Study_000035"
    assert res[10]["subpart_id"] == "a"
    assert res[10]["subpart_uid"] == "Study_000035"
    assert res[11]["subpart_id"] == "j"
    assert res[11]["subpart_uid"] == "Study_000034"
    assert res[12]["subpart_id"] == "i"
    assert res[12]["subpart_uid"] == "Study_000033"
    assert res[13]["subpart_id"] == "h"
    assert res[13]["subpart_uid"] == "Study_000032"
    assert res[14]["subpart_id"] == "g"
    assert res[14]["subpart_uid"] == "Study_000030"
    assert res[15]["subpart_id"] == "f"
    assert res[15]["subpart_uid"] == "Study_000029"
    assert res[16]["subpart_id"] == "e"
    assert res[16]["subpart_uid"] == "Study_000031"
    assert res[17]["subpart_id"] == "d"
    assert res[17]["subpart_uid"] == "Study_000027"
    assert res[18]["subpart_id"] == "c"
    assert res[18]["subpart_uid"] == "Study_000026"
    assert res[19]["subpart_id"] == "b"
    assert res[19]["subpart_uid"] == "Study_000028"
    assert res[20]["subpart_id"] == "d"
    assert res[20]["subpart_uid"] == "Study_000031"
    assert res[21]["subpart_id"] == "f"
    assert res[21]["subpart_uid"] == "Study_000030"
    assert res[22]["subpart_id"] == "e"
    assert res[22]["subpart_uid"] == "Study_000029"
    assert res[23]["subpart_id"] == "a"
    assert res[23]["subpart_uid"] == "Study_000028"
    assert res[24]["subpart_id"] == "c"
    assert res[24]["subpart_uid"] == "Study_000027"
    assert res[25]["subpart_id"] == "b"
    assert res[25]["subpart_uid"] == "Study_000026"
    assert res[26]["subpart_id"] == "j"
    assert res[26]["subpart_uid"] == "Study_000035"
    assert res[27]["subpart_id"] == "i"
    assert res[27]["subpart_uid"] == "Study_000034"
    assert res[28]["subpart_id"] == "h"
    assert res[28]["subpart_uid"] == "Study_000033"
    assert res[29]["subpart_id"] == "g"
    assert res[29]["subpart_uid"] == "Study_000032"
    assert res[30]["subpart_id"] == "f"
    assert res[30]["subpart_uid"] == "Study_000031"
    assert res[31]["subpart_id"] == "e"
    assert res[31]["subpart_uid"] == "Study_000030"
    assert res[32]["subpart_id"] == "d"
    assert res[32]["subpart_uid"] == "Study_000029"
    assert res[33]["subpart_id"] == "c"
    assert res[33]["subpart_uid"] == "Study_000028"
    assert res[34]["subpart_id"] == "b"
    assert res[34]["subpart_uid"] == "Study_000027"
    assert res[35]["subpart_id"] == "a"
    assert res[35]["subpart_uid"] == "Study_000026"


def test_get_audit_trail_of_study_subpart(api_client):
    response = api_client.get("/studies/Study_000030/audit-trail?is_subpart=true")
    assert response.status_code == 200
    res = response.json()
    for i in [
        "subpart_uid",
        "subpart_id",
        "study_acronym",
        "study_subpart_acronym",
        "start_date",
        "end_date",
        "user_initials",
        "change_type",
        "changes",
    ]:
        assert i in res[0]

    assert len(res) == 4

    assert res[0]["subpart_id"] == "f"
    assert res[0]["subpart_uid"] == "Study_000030"
    assert res[1]["subpart_id"] == "g"
    assert res[1]["subpart_uid"] == "Study_000030"
    assert res[2]["subpart_id"] == "f"
    assert res[2]["subpart_uid"] == "Study_000030"
    assert res[3]["subpart_id"] == "e"
    assert res[3]["subpart_uid"] == "Study_000030"


def test_cannot_use_a_study_parent_part_as_study_subpart(api_client):
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={
            "study_parent_part_uid": "Study_000001",
            "current_metadata": {"identification_metadata": {}},
        },
    )
    assert response.status_code == 400
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == f"Cannot use Study Parent Part with UID ({study.uid}) as a Study Subpart."
    )


def test_cannot_add_a_study_subpart_without_study_subpart_acronym(
    api_client,
):
    subpart = TestUtils.create_study()
    parent_part = TestUtils.create_study()
    response = api_client.patch(
        f"/studies/{subpart.uid}",
        json={
            "study_parent_part_uid": parent_part.uid,
            "current_metadata": {"identification_metadata": {}},
        },
    )
    assert response.status_code == 400
    res = response.json()

    assert res["type"] == "ValidationException"
    assert res["message"] == "Study Subpart Acronym must be provided for Study Subpart."


def test_cannot_use_a_study_subpart_with_different_project_number_than_study_parent_part(
    api_client,
):
    subpart = TestUtils.create_study()
    project = TestUtils.create_project(
        project_number="0000", clinical_programme_uid="ClinicalProgramme_000001"
    )
    parent_part = TestUtils.create_study(project_number=project.project_number)
    response = api_client.patch(
        f"/studies/{subpart.uid}",
        json={
            "study_parent_part_uid": parent_part.uid,
            "current_metadata": {"identification_metadata": {}},
        },
    )
    assert response.status_code == 400
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "Project number of Study Parent Part and Study Subpart must be same."
    )


def test_cannot_use_a_study_subpart_as_study_parent_part(api_client):
    subpart = TestUtils.create_study(study_parent_part_uid=study.uid)
    local_study = TestUtils.create_study()
    response = api_client.patch(
        f"/studies/{local_study.uid}",
        json={
            "study_parent_part_uid": subpart.uid,
            "current_metadata": {"identification_metadata": {}},
        },
    )
    assert response.status_code == 400
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == f"Provided study_parent_part_uid ({subpart.uid}) is a Study Subpart UID."
    )


def test_cannot_make_a_study_a_subpart_of_itself(api_client):
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={
            "study_parent_part_uid": study.uid,
            "current_metadata": {"identification_metadata": {}},
        },
    )
    assert response.status_code == 400
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "A Study cannot be a Study Parent Part for itself."


def test_cannot_reorder_study_subpart_of_another_study_parent_part(api_client):
    response = api_client.patch(
        f"/studies/{study.uid}/order",
        json={
            "uid": "Study_000006",
            "subpart_id": "a",
        },
    )
    assert response.status_code == 400
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == f"Study Subparts identified by (Study_000006) don't belong to the Study Parent Part identified by ({study.uid})."
    )


def test_cannot_delete_study_parent_part(api_client):
    response = api_client.delete(f"/studies/{study.uid}")
    assert response.status_code == 400
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == f"Study {study.uid}: cannot delete a Study having Study Subparts: ['Study_000053', 'Study_000011']."
    )


def test_cannot_change_study_title_of_subpart(api_client):
    subpart = TestUtils.create_study(study_parent_part_uid=study.uid)
    response = api_client.patch(
        f"/studies/{subpart.uid}",
        json={
            "study_parent_part_uid": "Study_000002",
            "current_metadata": {
                "study_description": {
                    "title": "new title",
                }
            },
        },
    )
    assert response.status_code == 400
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Cannot add or edit Study Description of Study Subparts."


def test_cannot_change_registry_identifiers_of_subpart(api_client):
    subpart = TestUtils.create_study(study_parent_part_uid=study.uid)
    response = api_client.patch(
        f"/studies/{subpart.uid}",
        json={
            "study_parent_part_uid": "Study_000002",
            "current_metadata": {
                "identification_metadata": {
                    "registry_identifiers": {"eudract_id": "eudract_id, updated"}
                }
            },
        },
    )
    assert response.status_code == 400
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Cannot edit Registry Identifiers of Study Subparts."


def test_cannot_change_project_of_subpart(api_client):
    new_project = TestUtils.create_project(
        name="New Project",
        project_number="abcd",
        clinical_programme_uid="ClinicalProgramme_000001",
    )
    response = api_client.patch(
        "/studies/Study_000011",
        json={
            "study_parent_part_uid": "Study_000002",
            "current_metadata": {
                "identification_metadata": {
                    "project_number": new_project.project_number,
                }
            },
        },
    )
    assert response.status_code == 400
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "Project of Study Subparts cannot be changed independently from its Study Parent Part."
    )


def test_cannot_lock_study_subpart(api_client):
    response = api_client.post(
        "/studies/Study_000011/locks", json={"change_description": "Lock"}
    )
    assert response.status_code == 400
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "Study Subparts cannot be locked independently from its Study Parent Part with uid (Study_000002)."
    )


def test_cannot_unlock_study_subpart(api_client):
    response = api_client.delete("/studies/Study_000011/locks")
    assert response.status_code == 400
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "Study Subparts cannot be unlocked independently from its Study Parent Part with uid (Study_000002)."
    )


def test_cannot_release_study_subpart(api_client):
    response = api_client.post(
        "/studies/Study_000011/release", json={"change_description": "Lock"}
    )
    assert response.status_code == 400
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "Study Subparts cannot be released independently from its Study Parent Part with uid (Study_000002)."
    )


def test_cannot_add_study_subpart_to_a_locked_study_parent_part(api_client):
    _study = TestUtils.create_study()
    study_subpart = TestUtils.create_study()

    response = api_client.patch(
        f"/studies/{_study.uid}",
        json={"current_metadata": {"study_description": {"study_title": "a title"}}},
    )
    assert response.status_code == 200

    response = api_client.post(
        f"/studies/{_study.uid}/locks", json={"change_description": "Lock"}
    )
    assert response.status_code == 201

    response = api_client.patch(
        f"/studies/{study_subpart.uid}",
        json={
            "study_parent_part_uid": _study.uid,
            "current_metadata": {"identification_metadata": {}},
        },
    )
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == f"Study Parent Part with UID ({_study.uid}) is locked or doesn't exist."
    )


def test_cannot_remove_study_subpart_from_parent_part_and_provide_an_existing_study_number(
    api_client,
):
    parent_part = TestUtils.create_study(number="1111")
    new_study = TestUtils.create_study(number="0101")
    response = api_client.patch(
        f"/studies/{new_study.uid}",
        json={
            "study_parent_part_uid": parent_part.uid,
            "current_metadata": {
                "identification_metadata": {
                    "study_subpart_acronym": "sub something",
                }
            },
        },
    )
    assert response.status_code == 200

    response = api_client.patch(
        f"/studies/{new_study.uid}",
        json={
            "study_parent_part_uid": None,
            "current_metadata": {
                "identification_metadata": {
                    "study_number": "1111",
                }
            },
        },
    )
    assert response.status_code == 400
    res = response.json()
    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "The following study number already exists in the database (1111)"
    )
