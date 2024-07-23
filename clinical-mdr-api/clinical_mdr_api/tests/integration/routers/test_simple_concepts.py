import os

from neomodel import db
from starlette.testclient import TestClient

import clinical_mdr_api.services.libraries.libraries as library_service
from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
    STARTUP_ACTIVITY_INSTANCES_CT_INIT,
    STARTUP_CT_TERM_NAME_CYPHER,
    STARTUP_TIME_POINTS,
    STARTUP_UNIT_DEFINITIONS,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class NumericValueTest(api.APITest):
    TEST_DB_NAME = "concepttests"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        library_service.create(name="Sponsor", is_editable=True)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "numeric_value.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials", "time"]


class NumericValueWithUnitTest(api.APITest):
    TEST_DB_NAME = "concepttests"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        library_service.create(name="Sponsor", is_editable=True)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_UNIT_DEFINITIONS)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "numeric_value_with_unit.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials", "time"]


class TextValueTest(api.APITest):
    TEST_DB_NAME = "concepttests"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        library_service.create(name="Sponsor", is_editable=True)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "text_value.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials", "time"]


class VisitNameTest(api.APITest):
    TEST_DB_NAME = "concepttests"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        library_service.create(name="Sponsor", is_editable=True)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "visit_name.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials", "time"]


class StudyDayTest(api.APITest):
    TEST_DB_NAME = "concepttests"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        library_service.create(name="Sponsor", is_editable=True)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "study_day.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials", "time"]


class StudyWeekTest(api.APITest):
    TEST_DB_NAME = "concepttests"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        library_service.create(name="Sponsor", is_editable=True)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "study_week.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials", "time"]


class StudyDurationDaysTest(api.APITest):
    TEST_DB_NAME = "concepttests"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        library_service.create(name="Sponsor", is_editable=True)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "study_duration_days.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials", "time"]


class StudyDurationWeeksTest(api.APITest):
    TEST_DB_NAME = "concepttests"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        library_service.create(name="Sponsor", is_editable=True)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "study_duration_weeks.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials", "time"]


class TimePointTest(api.APITest):
    TEST_DB_NAME = "concepttests"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        library_service.create(name="Sponsor", is_editable=True)
        db.cypher_query(STARTUP_TIME_POINTS)
        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "time_point.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials", "time"]


class TimePointNegativeTest(api.APITest):
    TEST_DB_NAME = "concepttests"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        library_service.create(name="Sponsor", is_editable=True)
        db.cypher_query(STARTUP_TIME_POINTS)
        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "time_point_negative.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials", "time"]


class LagTimesTest(api.APITest):
    TEST_DB_NAME = "concepttests"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        library_service.create(name="Sponsor", is_editable=True)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_UNIT_DEFINITIONS)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "lag_time.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "user_initials", "time"]
