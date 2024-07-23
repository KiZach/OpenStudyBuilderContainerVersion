import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CODELISTS_ATTRIBUTES_CYPHER,
    STARTUP_CT_CODELISTS_NAME_CYPHER,
    STARTUP_CT_PACKAGE_CYPHER,
    STARTUP_CT_TERM_NAME_CYPHER,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class CTStatsTest(api.APITest):
    TEST_DB_NAME = "ctstatstests"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_PACKAGE_CYPHER)
        db.cypher_query(STARTUP_CT_CODELISTS_NAME_CYPHER)
        db.cypher_query(STARTUP_CT_CODELISTS_ATTRIBUTES_CYPHER)
        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "ct_stats.json")]
