import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_ACTIVITY_SUB_GROUPS,
    STARTUP_CT_TERM,
    STARTUP_ODM_ALIASES,
    STARTUP_ODM_DESCRIPTIONS,
    STARTUP_ODM_ITEMS,
    STARTUP_ODM_VENDOR_ATTRIBUTES,
    STARTUP_ODM_VENDOR_ELEMENTS,
    STARTUP_ODM_VENDOR_NAMESPACES,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class OdmItemGroupTest(api.APITest):
    TEST_DB_NAME = "odmitemgroups"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ODM_DESCRIPTIONS)
        db.cypher_query(STARTUP_ODM_ALIASES)
        db.cypher_query(STARTUP_ODM_ITEMS)
        db.cypher_query(STARTUP_CT_TERM)
        db.cypher_query(STARTUP_ODM_VENDOR_NAMESPACES)
        db.cypher_query(STARTUP_ODM_VENDOR_ELEMENTS)
        db.cypher_query(STARTUP_ODM_VENDOR_ATTRIBUTES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "odm_item_groups.json")]

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "user_initials",
        ]


class OdmItemGroupNegativeTest(api.APITest):
    TEST_DB_NAME = "odmitemgroups"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ODM_DESCRIPTIONS)
        db.cypher_query(STARTUP_ODM_ALIASES)
        db.cypher_query(STARTUP_ODM_ITEMS)
        db.cypher_query(STARTUP_CT_TERM)
        db.cypher_query(STARTUP_ODM_VENDOR_NAMESPACES)
        db.cypher_query(STARTUP_ODM_VENDOR_ELEMENTS)
        db.cypher_query(STARTUP_ODM_VENDOR_ATTRIBUTES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "odm_item_groups_negative.json")]

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "user_initials",
            "time",
        ]
