from json import loads
from unittest import TestCase

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_TERM,
    STARTUP_ODM_ALIASES,
    STARTUP_ODM_CONDITIONS,
    STARTUP_ODM_FORMAL_EXPRESSIONS,
    STARTUP_ODM_FORMS,
    STARTUP_ODM_ITEM_GROUPS,
    STARTUP_ODM_ITEMS,
    STARTUP_ODM_METHODS,
    STARTUP_ODM_STUDY_EVENTS,
    STARTUP_ODM_VENDOR_ELEMENTS,
    STARTUP_ODM_VENDOR_NAMESPACES,
    STARTUP_ODM_XML_EXPORTER,
    STARTUP_UNIT_DEFINITIONS,
)


class OdmCsvExporterTest(TestCase):
    TEST_DB_NAME = "odmcsvexporter"
    HEADERS = {"content-type": "text/csv"}

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ODM_FORMAL_EXPRESSIONS)
        db.cypher_query(STARTUP_ODM_CONDITIONS)
        db.cypher_query(STARTUP_ODM_METHODS)
        db.cypher_query(STARTUP_ODM_ALIASES)
        db.cypher_query(STARTUP_CT_TERM)
        db.cypher_query(STARTUP_UNIT_DEFINITIONS)
        db.cypher_query(STARTUP_ODM_ITEMS)
        db.cypher_query(STARTUP_ODM_ITEM_GROUPS)
        db.cypher_query(STARTUP_ODM_FORMS)
        db.cypher_query(STARTUP_ODM_STUDY_EVENTS)
        db.cypher_query(STARTUP_ODM_VENDOR_NAMESPACES)
        db.cypher_query(STARTUP_ODM_VENDOR_ELEMENTS)
        db.cypher_query(STARTUP_ODM_XML_EXPORTER)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    def test_get_odm_study_event(self):
        response = self.test_client.post(
            "concepts/odms/metadata/csvs/export?target_uid=odm_study_event1&target_type=study_event",
            headers=self.HEADERS,
        )

        print(response.text)
        assert response.status_code == 200
        assert (
            response.text
            # pylint: disable=line-too-long
            == '"StudyEvent_Name","StudyEvent_Version","Form_Name","Form_Repeating","Form_Version","ItemGroup_Name","ItemGroup_Version","Item_Name","Item_Datatype","Item_Version","Item_Units","Item_Codelist","Item_Terms"\n"name1","1.0","name1","yes","1.0","name1","1.0","name1","datatype1","1.0","name1","name1","code_submission_value1"\n'
        )

    def test_get_odm_form(self):
        response = self.test_client.post(
            "concepts/odms/metadata/csvs/export?target_uid=odm_form1&target_type=form",
            headers=self.HEADERS,
        )

        assert response.status_code == 200
        assert (
            response.text
            # pylint: disable=line-too-long
            == '"Form_Name","Form_Repeating","Form_Version","ItemGroup_Name","ItemGroup_Version","Item_Name","Item_Datatype","Item_Version","Item_Units","Item_Codelist","Item_Terms"\n"name1","yes","1.0","name1","1.0","name1","datatype1","1.0","name1","name1","code_submission_value1"\n'
        )

    def test_get_odm_item_group(self):
        response = self.test_client.post(
            "concepts/odms/metadata/csvs/export?target_uid=odm_item_group1&target_type=item_group",
            headers=self.HEADERS,
        )

        assert response.status_code == 200
        assert (
            response.text
            # pylint: disable=line-too-long
            == '"ItemGroup_Name","ItemGroup_Version","Item_Name","Item_Datatype","Item_Version","Item_Units","Item_Codelist","Item_Terms"\n"name1","1.0","name1","datatype1","1.0","name1","name1","code_submission_value1"\n'
        )

    def test_get_odm_item(self):
        response = self.test_client.post(
            "concepts/odms/metadata/csvs/export?target_uid=odm_item1&target_type=item",
            headers=self.HEADERS,
        )

        assert response.status_code == 200
        assert (
            response.text
            # pylint: disable=line-too-long
            == '"Item_Name","Item_Datatype","Item_Version","Item_Units","Item_Codelist","Item_Terms"\n"name1","datatype1","1.0","name1","name1","code_submission_value1"\n'
        )

    def test_odm_not_supported_target_type(self):
        response = self.test_client.post(
            "concepts/odms/metadata/csvs/export?target_uid=wrong&target_type=study",
            headers=self.HEADERS,
        )

        assert response.status_code == 400
        rs = loads(response.content)
        assert rs["type"] == "BusinessLogicException"
        assert rs["message"] == "Requested target type not supported."

    def test_odm_study_event_not_found(self):
        response = self.test_client.post(
            "concepts/odms/metadata/csvs/export?target_uid=wrong&target_type=study_event",
            headers=self.HEADERS,
        )

        assert response.status_code == 404

    def test_odm_form_not_found(self):
        response = self.test_client.post(
            "concepts/odms/metadata/csvs/export?target_uid=wrong&target_type=form",
            headers=self.HEADERS,
        )

        assert response.status_code == 404

    def test_odm_item_group_not_found(self):
        response = self.test_client.post(
            "concepts/odms/metadata/csvs/export?target_uid=wrong&target_type=item_group",
            headers=self.HEADERS,
        )

        assert response.status_code == 404

    def test_odm_item_not_found(self):
        response = self.test_client.post(
            "concepts/odms/metadata/csvs/export?target_uid=wrong&target_type=item",
            headers=self.HEADERS,
        )

        assert response.status_code == 404
