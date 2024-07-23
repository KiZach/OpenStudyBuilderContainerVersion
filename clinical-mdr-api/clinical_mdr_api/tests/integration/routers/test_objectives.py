import os

from neomodel import db
from pydantic import BaseModel
from starlette.testclient import TestClient

from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.syntax_templates.objective_templates import (
    ObjectiveTemplateService,
)
from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
    STARTUP_PARAMETERS_CYPHER,
    library_data,
    template_data,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class ObjectiveTest(api.APITest):
    TEST_DB_NAME = "objectives"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)

        import clinical_mdr_api.models.syntax_templates.objective_template as ct_models
        import clinical_mdr_api.services.libraries.libraries as library_service
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        self.library = library_service.create(**library_data)
        otdata = template_data.copy()
        otdata["name"] = "Test [Indication]"
        objective_template = ct_models.ObjectiveTemplateCreateInput(**otdata)
        self.objective_template = ObjectiveTemplateService().create(objective_template)
        if isinstance(self.objective_template, BaseModel):
            self.objective_template = self.objective_template.dict()
        ObjectiveTemplateService().approve(self.objective_template["uid"])
        self.data["otuid"] = self.objective_template["uid"]

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "objectives.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "uid", "time"]


# @pytest.mark.skip
class ObjectiveNegativeTest(api.APITest):
    TEST_DB_NAME = "objectives"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)

        import clinical_mdr_api.models.syntax_templates.objective_template as ct_models
        import clinical_mdr_api.services.libraries.libraries as library_service
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        self.library = library_service.create(name="Test library", is_editable=True)
        otdata = template_data.copy()
        objective_template = ct_models.ObjectiveTemplateCreateInput(**otdata)
        self.objective_template = ObjectiveTemplateService().create(objective_template)
        if isinstance(self.objective_template, BaseModel):
            self.objective_template = self.objective_template.dict()
        ObjectiveTemplateService().approve(self.objective_template["uid"])
        self.data["otuid"] = self.objective_template["uid"]
        otdt = template_data.copy()
        otdt["name"] = "Name not approved"
        objective_template = ct_models.ObjectiveTemplateCreateInput(**otdt)
        self.not_approved_ot = ObjectiveTemplateService().create(objective_template)
        if isinstance(self.not_approved_ot, BaseModel):
            self.not_approved_ot = self.not_approved_ot.dict()
        self.data["otuidna"] = self.not_approved_ot["uid"]

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "objective_negative.json")]

    def post_test(self):
        def check_objectives_empty():
            repos = MetaRepository()
            data = list(repos.objective_repository.get_all())
            self.assertListEqual(data, [[], 0])

        check_objectives_empty()

    def ignored_fields(self):
        return ["start_date", "end_date", "time", "uid"]


# @pytest.mark.skip
class ObjectiveVersioningTest(api.APITest):
    TEST_DB_NAME = "objectives"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)

        import clinical_mdr_api.models.syntax_templates.objective_template as ct_models
        import clinical_mdr_api.services.libraries.libraries as library_service
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        self.library = library_service.create(**library_data)
        objective_template = ct_models.ObjectiveTemplateCreateInput(**template_data)
        self.objective_template = ObjectiveTemplateService().create(objective_template)
        if isinstance(self.objective_template, BaseModel):
            self.objective_template = self.objective_template.dict()
        ObjectiveTemplateService().approve(self.objective_template["uid"])
        self.data["otuid"] = self.objective_template["uid"]

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "objective_versioning.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "time", "path", "uid"]
