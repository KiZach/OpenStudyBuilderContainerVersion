from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_PARAMETERS_CYPHER,
    library_data,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class UnitDefinitionTest(api.APITest):
    TEST_DB_NAME = "unittestsudf"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)
        db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
        import clinical_mdr_api.services.libraries.libraries as library_service
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        self.library = library_service.create(**library_data)
        catalogue_name = "catalogue"
        library_name = "Test library"
        ct_unit_cod = create_codelist(
            "CT Unit", "CTCodelist_000001", catalogue_name, library_name
        )
        create_ct_term(
            ct_unit_cod.codelist_uid,
            "CT Unit term 1",
            "unit1-ct-uid",
            1,
            catalogue_name,
            library_name,
        )
        create_ct_term(
            ct_unit_cod.codelist_uid,
            "CT Unit term 2",
            "unit1-ct-uid-patched",
            2,
            catalogue_name,
            library_name,
        )
        create_ct_term(
            ct_unit_cod.codelist_uid,
            "CT Unit term 3",
            "unit1-ct-uid-2",
            3,
            catalogue_name,
            library_name,
        )
        create_ct_term(
            ct_unit_cod.codelist_uid,
            "CT Unit term 4",
            "unit1-ct-uid-3",
            4,
            catalogue_name,
            library_name,
        )
        ct_unit_dim_cod = create_codelist(
            "CT Unit Dimension", "CTCodelist_000002", catalogue_name, library_name
        )
        create_ct_term(
            ct_unit_dim_cod.codelist_uid,
            "CT Unit Dim term 1",
            "unit1-dimension",
            1,
            catalogue_name,
            library_name,
        )
        create_ct_term(
            ct_unit_dim_cod.codelist_uid,
            "CT Unit Dim term 2",
            "unit1-dimension-2",
            2,
            catalogue_name,
            library_name,
        )
        create_ct_term(
            ct_unit_dim_cod.codelist_uid,
            "CT Unit Dim term 3",
            "unit1-dimension-patched",
            3,
            catalogue_name,
            library_name,
        )
        create_ct_term(
            ct_unit_dim_cod.codelist_uid,
            "CT Unit Dim term 4",
            "unit1-dimension-patched-2",
            4,
            catalogue_name,
            library_name,
        )
        create_ct_term(
            ct_unit_dim_cod.codelist_uid,
            "CT Unit Dim term 5",
            "other-dimension",
            5,
            catalogue_name,
            library_name,
        )
        ct_unit_subset = create_codelist(
            "CT Unit Subset", "CTCodelist_000003", catalogue_name, library_name
        )
        create_ct_term(
            ct_unit_subset.codelist_uid,
            "CT Unit Subset term 1",
            "unit-subset-uid-1",
            1,
            catalogue_name,
            library_name,
        )
        create_ct_term(
            ct_unit_subset.codelist_uid,
            "CT Unit Subset term 2",
            "unit-subset-uid-2",
            2,
            catalogue_name,
            library_name,
        )

    SCENARIO_PATHS = ["clinical_mdr_api/tests/data/scenarios/unit_definition.json"]

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "uid",
            "user_initials",
            "time",
            "path",
            "message",
        ]
