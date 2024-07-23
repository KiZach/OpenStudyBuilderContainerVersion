import os

from neomodel import db

from clinical_mdr_api.tests.integration.utils import api, data_library
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class StudyProtocolTitleTest(api.APITest):
    TEST_DB_NAME = "studyprotocoltitle"
    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "study_protocol_title.json")]

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        super().setUp(include_base_data=True)
        db.cypher_query(
            data_library.get_codelist_with_term_cypher("Investigational Product")
        )
        db.cypher_query(data_library.STARTUP_STUDY_PROTOCOL_TITLE_CYPHER)
