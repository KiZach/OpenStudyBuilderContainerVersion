import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
    STARTUP_PARAMETERS_CYPHER,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class ParameterTest(api.APITest):
    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    TEST_DB_NAME = "parameters"
    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "parameters_test.json")]


class PrepopulatedParameters(api.APITest):
    TEST_DB_NAME = "parameters"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "parameters_many_test.json")]
