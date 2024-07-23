import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import STARTUP_ODM_FORMS

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class OdmStudyEventTest(api.APITest):
    TEST_DB_NAME = "odmstudyevents"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ODM_FORMS)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "odm_study_events.json")]

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "user_initials",
        ]


class OdmStudyEventNegativeTest(api.APITest):
    TEST_DB_NAME = "odmstudyevents"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ODM_FORMS)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "odm_study_events_negative.json")
    ]

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "user_initials",
            "time",
        ]
