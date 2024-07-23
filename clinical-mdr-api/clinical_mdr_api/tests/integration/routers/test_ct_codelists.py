import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CODELISTS_ATTRIBUTES_CYPHER,
    STARTUP_CT_CODELISTS_NAME_CYPHER,
    STARTUP_CT_TERM_WITHOUT_CATALOGUE,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class CTCodelistNameTest(api.APITest):
    TEST_DB_NAME = "cttests.codelists"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_CODELISTS_NAME_CYPHER)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    def test_filtering(self):
        self.filtering_common_test_scenario(
            test_client=self.test_client,
            filter_field_name="catalogue_name",
            path_root="/ct/codelists/names",
            wildcard_filter_field_name="CT",
        )

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "ct_codelist_name.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials"]


class CTCodelistNameTestNegativeTest(api.APITest):
    TEST_DB_NAME = "cttests.codelists"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_CODELISTS_NAME_CYPHER)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "ct_codelist_name_negative.json")
    ]

    def ignored_fields(self):
        return ["start_date", "end_date", "time", "user_initials"]


class CTCodelistAttributesTest(api.APITest):
    TEST_DB_NAME = "cttests.codelists"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_CODELISTS_ATTRIBUTES_CYPHER)
        db.cypher_query(STARTUP_CT_TERM_WITHOUT_CATALOGUE)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "ct_codelist_attributes.json")]

    def ignored_fields(self):
        return ["codelist_uid", "start_date", "end_date", "user_initials"]


class CTCodelistAttributesTestNegativeTest(api.APITest):
    TEST_DB_NAME = "cttests.codelists"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_CODELISTS_ATTRIBUTES_CYPHER)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "ct_codelist_attributes_negative.json")
    ]

    def ignored_fields(self):
        return ["start_date", "end_date", "time", "user_initials"]
