import os

from starlette.testclient import TestClient

from clinical_mdr_api import main
from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class BrandTest(api.APITest):
    TEST_DB_NAME = "brands"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "brand.json")]

    def ignored_fields(self):
        return ["time", "user_initials"]
