import os

from neomodel import db
from pydantic import BaseModel
from starlette.testclient import TestClient

from clinical_mdr_api.models.syntax_templates.timeframe_template import (
    TimeframeTemplate,
)
from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_PARAMETERS_CYPHER,
    library_data,
    template_data,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class TimeframeTest(api.APITest):
    TEST_DB_NAME = "unitteststimeframes"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)

        import clinical_mdr_api.services.libraries.libraries as library_service
        import clinical_mdr_api.services.syntax_templates.timeframe_templates as tt_service

        _service = tt_service.TimeframeTemplateService()
        import clinical_mdr_api.models.syntax_templates.timeframe_template as tt_models
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        self.library = library_service.create(**library_data)
        ttdata = template_data.copy()
        ttdata["name"] = "Test [Indication]"
        timeframe_template = tt_models.TimeframeTemplateCreateInput(**ttdata)
        self.timeframe_template = _service.create(timeframe_template)
        if isinstance(self.timeframe_template, BaseModel):
            self.timeframe_template = self.timeframe_template.dict()
        _service.approve(self.timeframe_template["uid"])
        self.data["ttuid"] = self.timeframe_template["uid"]
        ttdata = template_data.copy()
        ttdata["name"] = "Test [Indication] and [Intervention]"
        timeframe_template = tt_models.TimeframeTemplateCreateInput(**ttdata)
        self.tt2 = _service.create(timeframe_template)
        if isinstance(self.tt2, BaseModel):
            self.tt2 = self.tt2.dict()
        _service.approve(self.tt2["uid"])
        self.data["ttuid2"] = self.tt2["uid"]

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "timeframes.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "uid", "time"]


class TimeframeNegativeTest(api.APITest):
    TEST_DB_NAME = "unitteststimeframes"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)

        import clinical_mdr_api.services.libraries.libraries as library_service
        import clinical_mdr_api.services.syntax_templates.timeframe_templates as tt_service

        _service = tt_service.TimeframeTemplateService()
        import clinical_mdr_api.models.syntax_templates.timeframe_template as tt_models
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        self.library = library_service.create(name="Test library", is_editable=True)
        ttdata = template_data.copy()
        ttdata["name"] = "Test [Indication]"
        timeframe_template = tt_models.TimeframeTemplateCreateInput(**ttdata)
        self.timeframe_template = _service.create(timeframe_template)
        tt_uid = (
            self.timeframe_template.uid
            if isinstance(self.timeframe_template, TimeframeTemplate)
            else self.timeframe_template["uid"]
        )
        _service.approve(tt_uid)
        self.data["ttuid"] = tt_uid
        ttdt = template_data.copy()
        ttdt["name"] = "Name not approved"
        timeframe_template = tt_models.TimeframeTemplateCreateInput(**ttdt)
        self.not_approved_tt = _service.create(timeframe_template)
        not_approved_tt_uid = (
            self.not_approved_tt.uid
            if isinstance(self.not_approved_tt, TimeframeTemplate)
            else self.not_approved_tt["uid"]
        )
        self.data["ttuidna"] = not_approved_tt_uid

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "timeframe_negative.json")]

    def post_test(self):
        def check_timeframes_empty():
            from clinical_mdr_api.domain_repositories.syntax_instances.timeframe_repository import (
                TimeframeRepository,
            )

            timeframes = TimeframeRepository()
            data = list(timeframes.get_all())
            self.assertListEqual(data, [[], 0])

        check_timeframes_empty()

    def ignored_fields(self):
        return ["start_date", "end_date", "time", "uid"]


class TimeframeVersioningTest(api.APITest):
    TEST_DB_NAME = "unitteststimeframes"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)

        import clinical_mdr_api.services.libraries.libraries as library_service
        import clinical_mdr_api.services.syntax_templates.timeframe_templates as tt_service

        _service = tt_service.TimeframeTemplateService()
        import clinical_mdr_api.models.syntax_templates.timeframe_template as tt_models
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        self.library = library_service.create(**library_data)
        timeframe_template = tt_models.TimeframeTemplateCreateInput(**template_data)
        self.timeframe_template = _service.create(timeframe_template)
        tt_uid = (
            self.timeframe_template.uid
            if isinstance(self.timeframe_template, TimeframeTemplate)
            else self.timeframe_template["uid"]
        )
        _service.approve(tt_uid)
        self.data["ttuid"] = tt_uid

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "timeframe_versioning.json")]

    def ignored_fields(self):
        return ["start_date", "end_date", "time", "path", "uid"]
