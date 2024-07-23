import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_ODM_ALIASES,
    STARTUP_ODM_DESCRIPTIONS,
    STARTUP_ODM_FORMAL_EXPRESSIONS,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class OdmConditionTest(api.APITest):
    TEST_DB_NAME = "odmconditions"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ODM_FORMAL_EXPRESSIONS)
        db.cypher_query(STARTUP_ODM_DESCRIPTIONS)
        db.cypher_query(STARTUP_ODM_ALIASES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "odm_conditions.json")]

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "user_initials",
        ]


class OdmConditionNegativeTest(api.APITest):
    TEST_DB_NAME = "odmconditions"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ODM_FORMAL_EXPRESSIONS)
        db.cypher_query(STARTUP_ODM_DESCRIPTIONS)
        db.cypher_query(STARTUP_ODM_ALIASES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "odm_conditions_negative.json")]

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "user_initials",
            "time",
        ]
