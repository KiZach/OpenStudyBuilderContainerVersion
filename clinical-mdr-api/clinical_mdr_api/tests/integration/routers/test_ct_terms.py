import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_TERM_ATTRIBUTES_CYPHER,
    STARTUP_CT_TERM_NAME_CYPHER,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class CTTermNameTest(api.APITest):
    TEST_DB_NAME = "cttests.terms"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    def test_filtering(self):
        self.filtering_common_test_scenario(
            test_client=self.test_client,
            path_root="/ct/terms/names",
            filter_field_name="term_uid",
            wildcard_filter_field_name="term",
        )

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "ct_term_name.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials"]


class CTTermNameTestNegativeTest(api.APITest):
    TEST_DB_NAME = "cttests.terms"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "ct_term_name_negative.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "time"]


class CTTermAttributesTest(api.APITest):
    TEST_DB_NAME = "cttests.terms"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_TERM_ATTRIBUTES_CYPHER)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    def test_filtering(self):
        self.filtering_common_test_scenario(
            test_client=self.test_client,
            path_root="/ct/terms/attributes",
            filter_field_name="term_uid",
            wildcard_filter_field_name="term",
        )

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "ct_term_attributes.json")]

    def ignored_fields(self):
        return [
            "codelist_uid",
            "term_uid",
            "concept_id",
            "start_date",
            "end_date",
            "user_initials",
        ]


class CTTermAttributesTestNegativeTest(api.APITest):
    TEST_DB_NAME = "cttests.terms"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_TERM_ATTRIBUTES_CYPHER)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "ct_term_attributes_negative.json")
    ]

    def ignored_fields(self):
        return ["start_date", "end_date", "time"]
