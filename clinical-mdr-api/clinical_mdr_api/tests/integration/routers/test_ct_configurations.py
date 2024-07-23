from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_PARAMETERS_CYPHER,
    library_data,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class ConfigurationTest(api.APITest):
    TEST_DB_NAME = "unittestcodelistconfig"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)
        import clinical_mdr_api.services.libraries.libraries as library_service
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        self.library = library_service.create(**library_data)

    SCENARIO_PATHS = ["clinical_mdr_api/tests/data/scenarios/ct_configuration.json"]

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "uid",
            "time",
            "path",
            "message",
        ]
