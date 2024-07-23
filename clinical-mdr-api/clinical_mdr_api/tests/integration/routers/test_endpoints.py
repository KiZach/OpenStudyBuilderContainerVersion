import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.models import EndpointTemplate
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.syntax_templates.endpoint_templates import (
    EndpointTemplateService,
)
from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_PARAMETERS_CYPHER,
    library_data,
    template_data,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class EndpointTest(api.APITest):
    TEST_DB_NAME = "endpoints"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)

        import clinical_mdr_api.models.syntax_templates.endpoint_template as ep_models
        import clinical_mdr_api.services.libraries.libraries as library_service
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        self.library = library_service.create(**library_data)
        epdata = template_data.copy()
        epdata["name"] = "Test [Indication]"
        endpoint_template = ep_models.EndpointTemplateCreateInput(**epdata)
        self.endpoint_template = EndpointTemplateService().create(endpoint_template)
        assert isinstance(self.endpoint_template, EndpointTemplate)
        EndpointTemplateService().approve(self.endpoint_template.uid)
        self.data["etuid"] = self.endpoint_template.uid
        print(self.endpoint_template.uid)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "endpoints.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "uid", "time"]


# @pytest.mark.skip
class EndpointNegativeTest(EndpointTest):
    TEST_DB_NAME = "endpoints"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)

        import clinical_mdr_api.models.syntax_templates.endpoint_template as ep_models
        import clinical_mdr_api.services.libraries.libraries as library_service
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        self.library = library_service.create(name="Test library", is_editable=True)
        etdata = template_data.copy()
        endpoint_template = ep_models.EndpointTemplateCreateInput(**etdata)
        self.endpoint_template = EndpointTemplateService().create(endpoint_template)
        assert isinstance(self.endpoint_template, EndpointTemplate)
        EndpointTemplateService().approve(self.endpoint_template.uid)
        self.data["etuid"] = self.endpoint_template.uid
        etdt = template_data.copy()
        etdt["name"] = "Name not approved"
        endpoint_template = ep_models.EndpointTemplateCreateInput(**etdt)
        self.not_approved_et = EndpointTemplateService().create(endpoint_template)
        assert isinstance(self.not_approved_et, EndpointTemplate)
        self.data["etuidna"] = self.not_approved_et.uid

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "endpoint_negative.json")]

    def post_test(self):
        def check_endpoints_empty():
            repos = MetaRepository()
            data = repos.endpoint_repository.get_all()
            self.assertListEqual(list(data), [[], 0])

        check_endpoints_empty()

    def ignored_fields(self):
        return ["start_date", "end_date", "time", "uid"]


# @pytest.mark.skip
class EndpointVersioningTest(EndpointTest):
    TEST_DB_NAME = "endpoints"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)

        import clinical_mdr_api.models.syntax_templates.endpoint_template as ep_models
        import clinical_mdr_api.services.libraries.libraries as library_service
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        self.library = library_service.create(**library_data)
        epdata = template_data.copy()
        epdata["name"] = "Test [Indication]"
        endpoint_template = ep_models.EndpointTemplateCreateInput(**epdata)
        self.endpoint_template = EndpointTemplateService().create(endpoint_template)
        assert isinstance(self.endpoint_template, EndpointTemplate)
        EndpointTemplateService().approve(self.endpoint_template.uid)
        self.data["etuid"] = self.endpoint_template.uid

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "endpoint_versioning.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "time", "path", "uid"]
