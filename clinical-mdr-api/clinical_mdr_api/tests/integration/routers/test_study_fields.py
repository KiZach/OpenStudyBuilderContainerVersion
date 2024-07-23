import os

from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class StudyFieldsTest(api.APITest):
    TEST_DB_NAME = "studyfieldstest"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        clinical_programme = TestUtils.create_clinical_programme(name="CP")
        TestUtils.create_project(
            name="Project ABC",
            project_number="123",
            description="Description ABC",
            clinical_programme_uid=clinical_programme.uid,
        )
        TestUtils.create_project(
            name="Project DEF",
            project_number="456",
            description="Description DEF",
            clinical_programme_uid=clinical_programme.uid,
        )
        # create library
        library = TestUtils.create_library(name="Sponsor", is_editable=True)
        TestUtils.create_library(name="UCUM", is_editable=True)
        # create catalogue
        catalogue_name = TestUtils.create_ct_catalogue()
        codelist = TestUtils.create_ct_codelist()
        TestUtils.create_study_ct_data_map(codelist_uid=codelist.codelist_uid)
        TestUtils.create_study_fields_configuration()

        library_name = library["name"]

        codelist = create_codelist(
            name="time",  # "Hours",
            uid="C66781",  # "CTCodelist_00004-HOUR",
            catalogue=catalogue_name,
            library=library_name,
        )
        hour_term = create_ct_term(
            codelist=codelist.codelist_uid,
            name="hours",  # "Hours",
            uid="hours001",  # "Hours_001",
            order=1,
            catalogue_name=catalogue_name,
            library_name=library_name,
        )
        subset_codelist = create_codelist(
            name="Unit Subset",
            uid="UnitSubsetCuid",
            catalogue=catalogue_name,
            library=library_name,
        )
        study_time_subset = create_ct_term(
            codelist=subset_codelist.codelist_uid,
            name="Study Time",
            uid="StudyTimeSuid",
            order=1,
            catalogue_name=catalogue_name,
            library_name=library_name,
        )
        TestUtils.create_unit_definition(
            name="hours",
            library_name="Sponsor",
            ct_units=[hour_term.uid],
            unit_subsets=[study_time_subset.uid],
        )

        # create Unit Definitions
        TestUtils.create_unit_definition(name="day")
        TestUtils.create_unit_definition(name="week")
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "study_fields.json")]

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "time",
            "date",
            "version_timestamp",
            "user_initials",
            "uid",
            "study_uid",
        ]


class StudyFieldsNegativeTest(api.APITest):
    TEST_DB_NAME = "studyfields"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        clinical_programme = TestUtils.create_clinical_programme(name="CP")
        TestUtils.create_project(
            name="Project ABC",
            project_number="123",
            description="Description ABC",
            clinical_programme_uid=clinical_programme.uid,
        )
        TestUtils.create_project(
            name="Project DEF",
            project_number="456",
            description="Description DEF",
            clinical_programme_uid=clinical_programme.uid,
        )
        TestUtils.create_library(name="Sponsor", is_editable=True)
        TestUtils.create_library(name="UCUM", is_editable=True)
        TestUtils.create_ct_catalogue()
        TestUtils.create_unit_definition(name="day")
        TestUtils.create_unit_definition(name="week")
        codelist = TestUtils.create_ct_codelist()
        TestUtils.create_study_ct_data_map(codelist_uid=codelist.codelist_uid)
        TestUtils.create_study_fields_configuration()
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "study_fields_negative.json")]

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "time",
            "date",
            "version_timestamp",
            "user_initials",
            "uid",
            "study_uid",
        ]
