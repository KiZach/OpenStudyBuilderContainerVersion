import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_ACTIVITIES,
    STARTUP_ACTIVITY_GROUPS,
    STARTUP_ACTIVITY_SUB_GROUPS,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class ActivityTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "activity.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials"]


class ActivityNegativeTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "activity_negative.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials", "time"]


class ActivitySubGroupTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "activity_sub_group.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials"]


class ActivitySubGroupTestNegativeTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "activity_sub_group_negative.json")
    ]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials", "time"]


class ActivityGroupTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "activity_group.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials"]


class ActivityGroupNegativeTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "activity_group_negative.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials", "time"]
