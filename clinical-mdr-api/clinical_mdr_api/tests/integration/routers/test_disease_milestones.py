from neomodel import db

from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_STUDY_LIST_CYPHER,
)


class StudyDiseaseMilestoneRouterTest(api.APITest):
    def setUp(self):
        super().setUp()
        db.cypher_query(STARTUP_STUDY_LIST_CYPHER)

        # Generate UIDs
        StudyRoot.generate_node_uids_if_not_present()
        self.study = StudyRoot.nodes.all()[0]

    TEST_DB_NAME = "studydiseasemilestonerouter"

    SCENARIO_PATHS = [
        "clinical_mdr_api/tests/data/scenarios/study_disease_milestone_test.json"
    ]
