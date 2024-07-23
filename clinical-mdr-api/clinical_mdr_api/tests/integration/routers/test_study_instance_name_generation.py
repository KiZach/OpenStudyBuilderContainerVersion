import os

from neomodel import db
from pydantic import BaseModel
from starlette.testclient import TestClient

import clinical_mdr_api.models.syntax_templates.objective_template as ot_models
import clinical_mdr_api.services.libraries.libraries as library_service
from clinical_mdr_api import main
from clinical_mdr_api.services.syntax_templates.objective_templates import (
    ObjectiveTemplateService,
)
from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
    CREATE_NA_TEMPLATE_PARAMETER,
    STARTUP_CT_TERM_NAME_CYPHER,
    STARTUP_PARAMETERS_CYPHER,
    STARTUP_STUDY_CYPHER,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"

library_data = {"name": "Test library", "is_editable": True}

ot_data = {
    "name": "Test_Name_OT",
    "library": library_data,
    "library_name": "Test library",
}


class StudyInstanceNameGenerationParameterTest(api.APITest):
    TEST_DB_NAME = "unittestsnames"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(CREATE_NA_TEMPLATE_PARAMETER)
        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
        db.cypher_query(STARTUP_STUDY_CYPHER)
        self.test_client = TestClient(main.app)
        self.library = library_service.create(**library_data)
        otdata = ot_data.copy()
        otdata["name"] = "To investigate [Indication]"
        objective_template = ot_models.ObjectiveTemplateCreateInput(**otdata)
        self.objective_template = ObjectiveTemplateService().create(objective_template)
        if isinstance(self.objective_template, BaseModel):
            self.objective_template = self.objective_template.dict()
        ObjectiveTemplateService().approve(self.objective_template["uid"])
        self.data["otuid"] = self.objective_template["uid"]

    SCENARIO_PATHS = [
        os.path.join(
            BASE_SCENARIO_PATH,
            "library_instance_name_generation_study_context_single.json",
        )
    ]

    def ignored_fields(self):
        return ["start_date", "end_date", "uid", "time", "study_version"]
