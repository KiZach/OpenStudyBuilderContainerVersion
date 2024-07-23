import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_DICTIONARY_CODELISTS_CYPHER,
    STARTUP_DICTIONARY_TERMS_CYPHER,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class DictionaryTermsTest(api.APITest):
    TEST_DB_NAME = "dictionarycodelists.terms"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_DICTIONARY_CODELISTS_CYPHER)
        db.cypher_query(STARTUP_DICTIONARY_TERMS_CYPHER)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "dictionary_terms.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials"]


class DictionaryTermsNegativeTest(api.APITest):
    TEST_DB_NAME = "dictionarycodelists.terms"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_DICTIONARY_CODELISTS_CYPHER)
        db.cypher_query(STARTUP_DICTIONARY_TERMS_CYPHER)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "dictionary_terms_negative.json")
    ]

    def ignored_fields(self):
        return ["start_date", "end_date", "time", "user_initials"]
