from clinical_mdr_api.tests.integration.utils import api


class LibraryTest(api.APITest):
    TEST_DB_NAME = "libraries"
    SCENARIO_PATHS = ["clinical_mdr_api/tests/data/scenarios/library_test.json"]

    def ignored_fields(self):
        return ["time"]
