import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api import main
from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
    STARTUP_ACTIVITIES,
    STARTUP_ACTIVITY_GROUPS,
    STARTUP_ACTIVITY_INSTANCES,
    STARTUP_ACTIVITY_INSTANCES_CT_INIT,
    STARTUP_ACTIVITY_SUB_GROUPS,
    STARTUP_NUMERIC_VALUES_WITH_UNITS,
    STARTUP_PROJECTS_CYPHER,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class CompoundTest(api.APITest):
    TEST_DB_NAME = "compounds"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)
        db.cypher_query(STARTUP_NUMERIC_VALUES_WITH_UNITS)
        db.cypher_query(STARTUP_PROJECTS_CYPHER)

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "compound.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials", "change_description"]


class CompoundNegativeTest(api.APITest):
    TEST_DB_NAME = "compounds"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)
        db.cypher_query(STARTUP_NUMERIC_VALUES_WITH_UNITS)
        db.cypher_query(STARTUP_PROJECTS_CYPHER)

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "compound_negative.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "uid", "time", "user_initials"]


class CompoundAliasTest(api.APITest):
    TEST_DB_NAME = "compounds"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)
        db.cypher_query(STARTUP_NUMERIC_VALUES_WITH_UNITS)
        db.cypher_query(STARTUP_PROJECTS_CYPHER)

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "compound_alias.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials"]


class CompoundAliasNegativeTest(api.APITest):
    TEST_DB_NAME = "compounds"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)
        db.cypher_query(STARTUP_NUMERIC_VALUES_WITH_UNITS)
        db.cypher_query(STARTUP_PROJECTS_CYPHER)

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "compound_alias_negative.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "uid", "time", "user_initials"]
