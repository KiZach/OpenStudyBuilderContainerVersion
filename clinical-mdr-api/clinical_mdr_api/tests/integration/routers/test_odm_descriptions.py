import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class OdmDescriptionTest(api.APITest):
    TEST_DB_NAME = "odmdescription"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query("MERGE (library:Library {name:'Sponsor', is_editable:true})")

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "odm_descriptions.json")]

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "user_initials",
        ]


class OdmDescriptionNegativeTest(api.APITest):
    TEST_DB_NAME = "odmdescription"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query("MERGE (library:Library {name:'Sponsor', is_editable:true})")

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "odm_descriptions_negative.json")
    ]

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "user_initials",
            "time",
        ]
