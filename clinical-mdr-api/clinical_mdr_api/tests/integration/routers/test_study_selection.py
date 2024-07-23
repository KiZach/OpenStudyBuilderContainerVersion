import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.domain_repositories.models.syntax import (
    EndpointRoot,
    EndpointTemplateRoot,
    ObjectiveRoot,
    ObjectiveTemplateRoot,
    TimeframeRoot,
    TimeframeTemplateRoot,
)
from clinical_mdr_api.models.study_selections.study_epoch import StudyEpochEditInput
from clinical_mdr_api.services.controlled_terminologies.ct_term import CTTermService
from clinical_mdr_api.services.libraries.libraries import create as create_library
from clinical_mdr_api.services.studies.study_epoch import StudyEpochService
from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
    STARTUP_ACTIVITIES,
    STARTUP_ACTIVITY_GROUPS,
    STARTUP_ACTIVITY_INSTANCES_CT_INIT,
    STARTUP_ACTIVITY_SUB_GROUPS,
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_CT_TERM_NAME_CYPHER,
    STARTUP_NUMERIC_VALUES_WITH_UNITS,
    STARTUP_STUDY_ACTIVITY_CYPHER,
    STARTUP_STUDY_ARM_CYPHER,
    STARTUP_STUDY_BRANCH_ARM_CYPHER,
    STARTUP_STUDY_COMPOUND_CYPHER,
    STARTUP_STUDY_ENDPOINT_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
    STARTUP_STUDY_OBJECTIVE_CYPHER,
    get_codelist_with_term_cypher,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
    create_study_arm,
    create_study_branch_arm,
    create_study_cohort,
    create_study_design_cell,
    create_study_element,
    create_study_epoch,
    create_study_epoch_codelists_ret_cat_and_lib,
    edit_study_arm,
    edit_study_element,
    edit_study_epoch,
    get_catalogue_name_library_name,
    patch_order_study_design_cell,
    patch_study_branch_arm,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"
initialize_ct_data_map = {
    "TypeOfTreatment": [("CTTerm_000001", "CTTerm_000001")],
    "RouteOfAdministration": [("CTTerm_000002", "CTTerm_000002")],
    "DosageForm": [("CTTerm_000003", "CTTerm_000003")],
    "DispensedIn": [("CTTerm_000004", "CTTerm_000004")],
    "Device": [("CTTerm_000005", "CTTerm_000005")],
    "Formulation": [("CTTerm_000006", "CTTerm_000006")],
    "ReasonForMissingNullValue": [("CTTerm_000007", "CTTerm_000007")],
}


class StudyObjectivesTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
        db.cypher_query(STARTUP_STUDY_OBJECTIVE_CYPHER)
        ObjectiveTemplateRoot.generate_node_uids_if_not_present()
        ObjectiveRoot.generate_node_uids_if_not_present()
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "study_selection_objective.json")
    ]

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "time",
            "uid",
            "user_initials",
            "study_version",
        ]

    def preprocess_expected_response(self, resp_item, actual_response, url):
        """
        Preprocessing is needed as the order returned for the full audit trail of the study selection is depending on the uuid generated,
        as these are random we cannot know up front which is supposed to be listed first.
        """
        if "/studies/study_root/study-objectives/audit-trail/" == url:
            actual_responses_items = []
            for item in actual_response:
                actual_responses_items.append(item["study_objective_uid"])
            uids = {}
            for item in set(actual_responses_items):
                uids[item] = actual_responses_items.count(item)
            first_uid = actual_response[0]["study_objective_uid"]
            if uids[first_uid] == 2:
                return resp_item
            resp_item["result"] = resp_item["result"][3:5].extend(
                resp_item["result"][0:3]
            )
            return resp_item
        return resp_item


class StudyObjectivesNegativeTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_STUDY_OBJECTIVE_CYPHER)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "study_selection_objective_negative.json")
    ]

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "user_initials",
            "time",
            "study_endpoint_uid",
            "uid",
        ]


class StudyEndpointsTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
        db.cypher_query(STARTUP_STUDY_ENDPOINT_CYPHER)
        ObjectiveTemplateRoot.generate_node_uids_if_not_present()
        ObjectiveRoot.generate_node_uids_if_not_present()
        EndpointTemplateRoot.generate_node_uids_if_not_present()
        EndpointRoot.generate_node_uids_if_not_present()
        TimeframeTemplateRoot.generate_node_uids_if_not_present()
        TimeframeRoot.generate_node_uids_if_not_present()
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "study_selection_endpoint.json")]

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "modified_date",
            "time",
            "uid",
            "user_initials",
            "codelist_uid",
            "study_version",
        ]


class StudyEndpointsNegativeTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_STUDY_ENDPOINT_CYPHER)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "study_selection_endpoint_negative.json")
    ]

    def ignored_fields(self):
        return ["start_date", "end_date", "time", "uid"]


class StudyCompoundsTest(api.APITest):
    TEST_DB_NAME = "studyselection"
    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "study_selection_compound.json")]

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_NUMERIC_VALUES_WITH_UNITS)
        TestUtils.create_library(name="UCUM", is_editable=True)
        TestUtils.create_ct_catalogue()
        TestUtils.create_study_ct_data_map(
            codelist_uid="CTCodelist_000001", ct_data_map=initialize_ct_data_map
        )
        TestUtils.create_study_fields_configuration()
        db.cypher_query(STARTUP_STUDY_COMPOUND_CYPHER)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "modified_date",
            "time",
            "uid",
            "nnc_id",
            "UNII",
            "PClass",
            "change_description",
            "user_initials",
            "version_timestamp",
            "study_version",
        ]


class StudyCompoundsNegativeTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_NUMERIC_VALUES_WITH_UNITS)
        TestUtils.create_library(name="UCUM", is_editable=True)
        TestUtils.create_ct_catalogue()
        TestUtils.create_study_ct_data_map(
            codelist_uid="CTCodelist_000001", ct_data_map=initialize_ct_data_map
        )
        db.cypher_query(STARTUP_STUDY_COMPOUND_CYPHER)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "study_selection_compound_negative.json")
    ]

    def ignored_fields(self):
        return ["start_date", "end_date", "modified_date", "time", "uid"]


class StudyActivityTest(api.APITest):
    TEST_DB_NAME = "studyselection"
    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "study_selection_activities.json")
    ]

    def setUp(self):
        super().setUp()
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(
            get_codelist_with_term_cypher(
                "EFFICACY", "Flowchart Group", term_uid="term_efficacy_uid"
            )
        )
        db.cypher_query(STARTUP_STUDY_ACTIVITY_CYPHER)

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "time",
            "uid",
            "user_initials",
            "study_version",
        ]


class StudyArmsTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
        db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        # locking and unlocking to create multiple study value relationships on the existent StudySelections
        TestUtils.create_study_fields_configuration()

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "study_selection_arms.json")]

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "modified_date",
            "time",
            "uid",
            "user_initials",
            "codelist_uid",
            "version_timestamp",
            "study_version",
        ]


class StudyElementsTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        # create library
        create_library("Sponsor", True)
        # create catalogue
        db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
        db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

        element_type_term_uid1 = "ElementTypeTermUid_1"
        db.cypher_query(
            get_codelist_with_term_cypher(
                name="No Treatment",
                codelist_name="Element Type",
                codelist_uid="ElementTypeCodelistUid",
                term_uid=element_type_term_uid1,
            )
        )

        element_subtype_term_uid1 = "ElementSubTypeTermUid_1"
        db.cypher_query(
            get_codelist_with_term_cypher(
                name="Screening",
                codelist_name="Element Sub Type",
                codelist_uid="ElementSubTypeCodelistUid",
                term_uid=element_subtype_term_uid1,
            )
        )
        CTTermService().add_parent(
            term_uid=element_subtype_term_uid1,
            parent_uid=element_type_term_uid1,
            relationship_type="type",
        )

        element_subtype_term_uid2 = "ElementSubTypeTermUid_2"
        db.cypher_query(
            get_codelist_with_term_cypher(
                name="Wash-out",
                codelist_name="Element Sub Type",
                codelist_uid="ElementSubTypeCodelistUid",
                term_uid=element_subtype_term_uid2,
            )
        )

        CTTermService().add_parent(
            term_uid=element_subtype_term_uid2,
            parent_uid=element_type_term_uid1,
            relationship_type="type",
        )

        catalogue_name = "catalogue"
        library_name = "Sponsor"
        codelist = create_codelist(
            name="time",
            uid="C66781",
            catalogue=catalogue_name,
            library=library_name,
        )
        hour_term = create_ct_term(
            codelist=codelist.codelist_uid,
            name="hours",
            uid="hours001",
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
        week_term = create_ct_term(
            codelist=codelist.codelist_uid,
            name="weeks",
            uid="weeks001",
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
        TestUtils.create_unit_definition(
            name="weeks",
            library_name="Sponsor",
            ct_units=[week_term.uid],
            unit_subsets=[study_time_subset.uid],
        )
        # locking and unlocking to create multiple study value relationships on the existent StudySelections
        TestUtils.create_study_fields_configuration()

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "study_selection_elements.json")]

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "modified_date",
            "time",
            "uid",
            "user_initials",
            "codelist_uid",
            "version_timestamp",
            "study_version",
        ]


class StudyBranchArmsTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
        db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
        StudyRoot.generate_node_uids_if_not_present()
        self.study = StudyRoot.nodes.all()[0]
        # Create an epoch
        create_study_epoch_codelists_ret_cat_and_lib()
        catalogue_name, library_name = get_catalogue_name_library_name()
        self.study_epoch = create_study_epoch("EpochSubType_0001")
        self.study_epoch2 = create_study_epoch("EpochSubType_0001")
        self.study_epoch = edit_study_epoch(
            epoch_uid=self.study_epoch.uid, study_uid=self.study_epoch.study_uid
        )
        self.study_epoch2 = edit_study_epoch(
            epoch_uid=self.study_epoch2.uid, study_uid=self.study_epoch2.study_uid
        )
        # Create a study element
        element_type_codelist = create_codelist(
            "Element Type", "CTCodelist_ElementType", catalogue_name, library_name
        )
        element_type_term = create_ct_term(
            element_type_codelist.codelist_uid,
            "Element Type",
            "ElementType_0001",
            1,
            catalogue_name,
            library_name,
        )
        element_type_term_2 = create_ct_term(
            element_type_codelist.codelist_uid,
            "Element Type",
            "ElementType_0002",
            2,
            catalogue_name,
            library_name,
        )
        self.study_elements = [
            create_study_element(element_type_term.uid, self.study.uid),
            create_study_element(element_type_term_2.uid, self.study.uid),
        ]
        self.study_elements = [
            edit_study_element(
                element_uid=self.study_elements[0].element_uid,
                study_uid=self.study.uid,
                new_short_name="short_element 1",
            ),
            edit_study_element(
                element_uid=self.study_elements[1].element_uid,
                study_uid=self.study.uid,
                new_short_name="short_element_2",
            ),
        ]
        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
        db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
        db.cypher_query(STARTUP_STUDY_BRANCH_ARM_CYPHER)
        self.design_cell = create_study_design_cell(
            study_element_uid=self.study_elements[0].element_uid,
            study_epoch_uid=self.study_epoch.uid,
            study_arm_uid="StudyArm_000003",
            study_uid=self.study.uid,
        )
        self.design_cell = create_study_design_cell(
            study_element_uid=self.study_elements[0].element_uid,
            study_epoch_uid=self.study_epoch2.uid,
            study_arm_uid="StudyArm_000003",
            study_uid=self.study.uid,
        )
        # all the tests should work with a study design cell that has been edited
        self.design_cell = patch_order_study_design_cell(
            study_design_cell_uid=self.design_cell.design_cell_uid,
            study_uid=self.study.uid,
        )
        # locking and unlocking to create multiple study value relationships on the existent StudySelections
        TestUtils.create_study_fields_configuration()
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "study_selection_branch_arms.json")
    ]

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "modified_date",
            "time",
            "uid",
            "user_initials",
            "codelist_uid",
            "version_timestamp",
            "study_version",
        ]


class StudyBranchArmsNegativeTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
        db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
        db.cypher_query(STARTUP_STUDY_BRANCH_ARM_CYPHER)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "study_selection_branch_arms_negative.json")
    ]

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "modified_date",
            "time",
            "uid",
            "user_initials",
            "codelist_uid",
            "study_version",
        ]


class StudyCohortsTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
        db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
        db.cypher_query(STARTUP_STUDY_BRANCH_ARM_CYPHER)
        self.study_uid = "study_root"
        self.arm_uid1 = "StudyArm_000001"
        self.branch_arm = create_study_branch_arm(
            study_uid=self.study_uid,
            name="Branch_Arm_Name_1",
            short_name="Branch_Arm_Short_Name_1",
            code="Branch_Arm_code_1",
            description="desc...",
            colour_code="colour...",
            randomization_group="Branch_Arm_randomizationGroup",
            number_of_subjects=100,
            arm_uid=self.arm_uid1,
        )
        self.branch_arm = create_study_branch_arm(
            study_uid=self.study_uid,
            name="Branch_Arm_Name_2",
            short_name="Branch_Arm_Short_Name_2",
            code="Branch_Arm_code_2",
            description="desc...",
            colour_code="colour...2",
            randomization_group="Branch_Arm_randomizationGroup2",
            number_of_subjects=20,
            arm_uid=self.arm_uid1,
        )
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "study_selection_cohorts.json")]

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "modified_date",
            "time",
            "uid",
            "user_initials",
            "codelist_uid",
            "study_version",
        ]


class StudyCohortsNegativeTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
        db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
        db.cypher_query(STARTUP_STUDY_BRANCH_ARM_CYPHER)

        self.study_uid = "study_root"
        self.arm_uid1 = "StudyArm_000001"

        self.cohorts = [
            create_study_cohort(
                study_uid=self.study_uid,
                name="Cohort_Name_1",
                short_name="Cohort_Short_Name_1",
                code="Cohort_code_1",
                description="desc...",
                colour_code="desc...",
                number_of_subjects=100,
                arm_uids=[self.arm_uid1],
            ),
            create_study_cohort(
                study_uid=self.study_uid,
                name="Cohort_Name_2",
                short_name="Cohort_Short_Name_2",
                code="Cohort_code_2",
                description="desc...",
                colour_code="desc...",
                number_of_subjects=100,
                arm_uids=[self.arm_uid1],
            ),
        ]
        self.branch_arm = create_study_branch_arm(
            study_uid=self.study_uid,
            name="Branch_Arm_Name_1",
            short_name="Branch_Arm_Short_Name_1",
            code="Branch_Arm_code_1",
            description="desc...",
            colour_code="colour...",
            randomization_group="Branch_Arm_randomizationGroup",
            number_of_subjects=100,
            arm_uid=self.arm_uid1,
        )
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "study_selection_cohorts_negative.json")
    ]

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "modified_date",
            "time",
            "uid",
            "user_initials",
            "codelist_uid",
            "study_version",
        ]


class StudyDesignCellsTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)

        db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
        db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)

        StudyRoot.generate_node_uids_if_not_present()
        self.study = StudyRoot.nodes.all()[0]

        # Create an epoch
        create_study_epoch_codelists_ret_cat_and_lib()
        catalogue_name, library_name = get_catalogue_name_library_name()
        self.study_epoch = create_study_epoch("EpochSubType_0001")

        # Create a study element
        element_type_codelist = create_codelist(
            "Element Type", "CTCodelist_ElementType", catalogue_name, library_name
        )
        element_type_term = create_ct_term(
            element_type_codelist.codelist_uid,
            "Element Type",
            "ElementType_0001",
            1,
            catalogue_name,
            library_name,
        )
        element_type_term_2 = create_ct_term(
            element_type_codelist.codelist_uid,
            "Element Type",
            "ElementType_0002",
            2,
            catalogue_name,
            library_name,
        )
        self.study_elements = [
            create_study_element(element_type_term.uid, self.study.uid),
            create_study_element(element_type_term_2.uid, self.study.uid),
        ]

        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
        db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
        db.cypher_query(STARTUP_STUDY_BRANCH_ARM_CYPHER)
        # locking and unlocking to create multiple study value relationships on the existent StudySelections
        TestUtils.create_study_fields_configuration()

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "study_selection_design_cells.json")
    ]

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "modified_date",
            "modified",
            "time",
            "uid",
            "user_initials",
            "codelist_uid",
            "version_timestamp",
            "study_version",
        ]


class StudyDesignJointTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
        db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
        StudyRoot.generate_node_uids_if_not_present()
        self.study = StudyRoot.nodes.all()[0]
        # Create an epoch
        create_study_epoch_codelists_ret_cat_and_lib()
        catalogue_name, library_name = get_catalogue_name_library_name()
        self.study_epoch = create_study_epoch("EpochSubType_0001")
        self.study_epoch2 = create_study_epoch("EpochSubType_0001")

        # Create a study element
        element_type_codelist = create_codelist(
            "Element Type", "CTCodelist_ElementType", catalogue_name, library_name
        )
        element_type_term = create_ct_term(
            element_type_codelist.codelist_uid,
            "Element Type",
            "ElementType_0001",
            1,
            catalogue_name,
            library_name,
        )
        element_type_term_2 = create_ct_term(
            element_type_codelist.codelist_uid,
            "Element Type",
            "ElementType_0002",
            2,
            catalogue_name,
            library_name,
        )
        self.study_elements = [
            create_study_element(element_type_term.uid, self.study.uid),
            create_study_element(element_type_term_2.uid, self.study.uid),
        ]

        codelist = create_codelist(
            name="Arm Type",
            uid="CTCodelist_00004",
            catalogue=catalogue_name,
            library=library_name,
        )
        arm_type = create_ct_term(
            codelist=codelist.codelist_uid,
            name="Arm Type",
            uid="ArmType_0001",
            order=1,
            catalogue_name=catalogue_name,
            library_name=library_name,
        )

        self.arm1 = create_study_arm(
            study_uid=self.study.uid,
            name="Arm_Name_1",
            short_name="Arm_Short_Name_1",
            code="Arm_code_1",
            description="desc...",
            colour_code="colour...",
            randomization_group="Arm_randomizationGroup",
            number_of_subjects=100,
            arm_type_uid=arm_type.uid,
        )
        self.arm = create_study_arm(
            study_uid=self.study.uid,
            name="Arm_Name_2",
            short_name="Arm_Short_Name_2",
            code="Arm_code_2",
            description="desc...",
            colour_code="colour...",
            randomization_group="Arm_randomizationGroup2",
            number_of_subjects=100,
            arm_type_uid=arm_type.uid,
        )
        self.arm = create_study_arm(
            study_uid=self.study.uid,
            name="Arm_Name_3",
            short_name="Arm_Short_Name_3",
            code="Arm_code_3",
            description="desc...",
            colour_code="colour...",
            randomization_group="Arm_randomizationGroup3",
            number_of_subjects=100,
            arm_type_uid=arm_type.uid,
        )

        self.arm = create_study_arm(
            study_uid=self.study.uid,
            name="Arm_Name_9",
            short_name="Arm_Short_Name_9",
            code="Arm_code_9",
            description="desc...",
            colour_code="colour...",
            randomization_group="Arm_randomizationGroup9",
            number_of_subjects=100,
            arm_type_uid=arm_type.uid,
        )

        self.design_cell = create_study_design_cell(
            study_element_uid=self.study_elements[0].element_uid,
            study_epoch_uid=self.study_epoch.uid,
            study_arm_uid="StudyArm_000003",
            study_uid=self.study.uid,
        )
        self.design_cell2 = create_study_design_cell(
            study_element_uid=self.study_elements[0].element_uid,
            study_epoch_uid=self.study_epoch2.uid,
            study_arm_uid="StudyArm_000003",
            study_uid=self.study.uid,
        )

        self.design_cell2 = create_study_design_cell(
            study_element_uid=self.study_elements[1].element_uid,
            study_epoch_uid=self.study_epoch2.uid,
            study_arm_uid="StudyArm_000001",
            study_uid=self.study.uid,
        )

        self.branch_arm = create_study_branch_arm(
            study_uid=self.study.uid,
            name="Branch_Arm_Name_1",
            short_name="Branch_Arm_Short_Name_1",
            code="Branch_Arm_code_1",
            description="desc...",
            colour_code="colour...",
            randomization_group="Branch_Arm_randomizationGroup",
            number_of_subjects=100,
            arm_uid="StudyArm_000003",
        )
        self.branch_arm = patch_study_branch_arm(
            branch_arm_uid=self.branch_arm.branch_arm_uid, study_uid=self.study.uid
        )

        self.design_cell3 = create_study_design_cell(
            study_element_uid=self.study_elements[0].element_uid,
            study_epoch_uid=self.study_epoch2.uid,
            study_arm_uid="StudyArm_000005",
            study_uid=self.study.uid,
        )

        self.cohort = create_study_cohort(
            study_uid=self.study.uid,
            name="Cohort_Name_1",
            short_name="Cohort_Short_Name_1",
            code="Cohort_code_1",
            description="desc...",
            colour_code="desc...",
            number_of_subjects=100,
            arm_uids=["StudyArm_000001"],
        )
        # edit arm, epoch, elements to track if the relationships keep maintained and the ZeroOrMore cardinality is managed
        self.arm1 = edit_study_arm(
            study_uid=self.study.uid,
            arm_uid=self.arm1.arm_uid,
            name="last_edit_arm_name",  # previous "Arm_Name_1"
            short_name="last_edit_short_name",  # previous "Arm_Short_Name_1"
        )
        self.study_epoch = edit_study_epoch(
            epoch_uid=self.study_epoch.uid, study_uid=self.study_epoch.study_uid
        )
        self.study_epoch2 = edit_study_epoch(
            epoch_uid=self.study_epoch2.uid, study_uid=self.study_epoch2.study_uid
        )
        self.study_elements = [
            edit_study_element(
                element_uid=self.study_elements[0].element_uid,
                study_uid=self.study.uid,
                new_short_name="short_element 1",
            ),
            edit_study_element(
                element_uid=self.study_elements[1].element_uid,
                study_uid=self.study.uid,
                new_short_name="short_element_2",
            ),
        ]
        epoch_service = StudyEpochService()
        epoch = epoch_service.find_by_uid(
            self.study_epoch2.uid, study_uid=self.study_epoch2.study_uid
        )
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            study_uid=epoch.study_uid,
            start_rule=start_rule,
            end_rule=end_rule,
            change_description="rules change",
        )
        self.study_epoch3 = epoch_service.edit(
            study_uid=epoch.study_uid,
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )
        # locking and unlocking to create multiple study value relationships on the existent StudySelections
        TestUtils.create_study_fields_configuration()

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "study_design_joint.json")]

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "modified_date",
            "modified",
            "time",
            "uid",
            "user_initials",
            "codelist_uid",
            "version_timestamp",
            "study_version",
        ]
