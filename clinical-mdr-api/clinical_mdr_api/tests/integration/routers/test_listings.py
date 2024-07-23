import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
    STARTUP_ACTIVITIES,
    STARTUP_ACTIVITY_GROUPS,
    STARTUP_ACTIVITY_INSTANCES_TOPICCDDEF,
    STARTUP_ACTIVITY_SUB_GROUPS,
    STARTUP_CT_PACKAGE_CYPHER_CDISC_CT,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class TopicCddefTest(api.APITest):
    TEST_DB_NAME = "testlisttopiccd"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_TOPICCDDEF)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "listings_topiccddef.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "uid"]


class CdiscCtVerTest(api.APITest):
    TEST_DB_NAME = "testcdiscct"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_PACKAGE_CYPHER_CDISC_CT)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "listing_cdisc_ct_ver.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials", "time"]


class CdiscCtPkgTest(api.APITest):
    TEST_DB_NAME = "testcdiscct"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_PACKAGE_CYPHER_CDISC_CT)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "listing_cdisc_ct_pkg.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials", "time"]


class CdiscCtListTest(api.APITest):
    TEST_DB_NAME = "testcdiscct"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_PACKAGE_CYPHER_CDISC_CT)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "listing_cdisc_ct_list.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials", "time"]


class CdiscCtValTest(api.APITest):
    TEST_DB_NAME = "testcdiscct"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_PACKAGE_CYPHER_CDISC_CT)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "listing_cdisc_ct_val.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials", "time"]
