import os

from neomodel import db
from pydantic import BaseModel
from starlette.testclient import TestClient

import clinical_mdr_api.models.syntax_templates.objective_template as ct_models
import clinical_mdr_api.services.libraries.libraries as library_service
from clinical_mdr_api import main
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


class LibraryInstanceNameGenerationSingleParameterTest(api.APITest):
    TEST_DB_NAME = "unittestsnames"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        self.test_client = TestClient(main.app)
        self.library = library_service.create(**library_data)
        otdata = template_data.copy()
        otdata["name"] = "To investigate [Indication]"
        objective_template = ct_models.ObjectiveTemplateCreateInput(**otdata)
        self.objective_template = ObjectiveTemplateService().create(objective_template)
        if isinstance(self.objective_template, BaseModel):
            self.objective_template = self.objective_template.dict()
        ObjectiveTemplateService().approve(self.objective_template["uid"])
        self.data["otuid"] = self.objective_template["uid"]

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "library_instance_name_generation_single.json")
    ]

    def ignored_fields(self):
        return ["start_date", "end_date", "uid", "time"]


class LibraryInstanceNameGenerationMultiParameterTest1(api.APITest):
    TEST_DB_NAME = "unittestsnames"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        self.test_client = TestClient(main.app)
        self.library = library_service.create(**library_data)
        otdata = template_data.copy()
        otdata["name"] = "To investigate [Indication] and [Intervention]"
        objective_template = ct_models.ObjectiveTemplateCreateInput(**otdata)
        self.objective_template = ObjectiveTemplateService().create(objective_template)
        if isinstance(self.objective_template, BaseModel):
            self.objective_template = self.objective_template.dict()
        ObjectiveTemplateService().approve(self.objective_template["uid"])
        self.data["otuid"] = self.objective_template["uid"]
        self.data["otname"] = otdata["name"]
        self.data["otseperator"] = " and "

    SCENARIO_PATHS = [
        os.path.join(
            BASE_SCENARIO_PATH,
            "library_instance_name_generation_multiple_and_seperated.json",
        )
    ]

    def ignored_fields(self):
        return ["start_date", "end_date", "uid", "time"]


class LibraryInstanceNameGenerationMultiParameterTest2(api.APITest):
    TEST_DB_NAME = "unittestsnames"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        self.test_client = TestClient(main.app)
        self.library = library_service.create(**library_data)
        otdata = template_data.copy()
        otdata["name"] = "To investigate [Indication], [Intervention]"
        objective_template = ct_models.ObjectiveTemplateCreateInput(**otdata)
        self.objective_template = ObjectiveTemplateService().create(objective_template)
        if isinstance(self.objective_template, BaseModel):
            self.objective_template = self.objective_template.dict()
        ObjectiveTemplateService().approve(self.objective_template["uid"])
        self.data["otuid"] = self.objective_template["uid"]
        self.data["otname"] = otdata["name"]
        self.data["otseperator"] = ", "

    SCENARIO_PATHS = [
        os.path.join(
            BASE_SCENARIO_PATH, "library_instance_name_generation_multiple.json"
        )
    ]

    def ignored_fields(self):
        return ["start_date", "end_date", "uid", "time"]


class LibraryInstanceNameGenerationMultiParameterTest3(api.APITest):
    TEST_DB_NAME = "unittestsnames"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        self.test_client = TestClient(main.app)
        self.library = library_service.create(**library_data)
        otdata = template_data.copy()
        otdata["name"] = "To investigate [Indication] [Intervention]"
        objective_template = ct_models.ObjectiveTemplateCreateInput(**otdata)
        self.objective_template = ObjectiveTemplateService().create(objective_template)
        if isinstance(self.objective_template, BaseModel):
            self.objective_template = self.objective_template.dict()
        ObjectiveTemplateService().approve(self.objective_template["uid"])
        self.data["otuid"] = self.objective_template["uid"]
        self.data["otname"] = otdata["name"]
        self.data["otseperator"] = " "

    SCENARIO_PATHS = [
        os.path.join(
            BASE_SCENARIO_PATH, "library_instance_name_generation_multiple.json"
        )
    ]

    def ignored_fields(self):
        return ["start_date", "end_date", "uid", "time"]


class LibraryInstanceNameGenerationMultiParameterTest4(api.APITest):
    TEST_DB_NAME = "unittestsnames"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)

        self.test_client = TestClient(main.app)
        self.library = library_service.create(**library_data)
        otdata = template_data.copy()
        otdata["name"] = "To investigate [Indication] ([Intervention])"
        objective_template = ct_models.ObjectiveTemplateCreateInput(**otdata)
        self.objective_template = ObjectiveTemplateService().create(objective_template)
        if isinstance(self.objective_template, BaseModel):
            self.objective_template = self.objective_template.dict()
        ObjectiveTemplateService().approve(self.objective_template["uid"])
        self.data["otuid"] = self.objective_template["uid"]
        self.data["otname"] = otdata["name"]

    SCENARIO_PATHS = [
        os.path.join(
            BASE_SCENARIO_PATH,
            "library_instance_name_generation_multiple_brackets.json",
        )
    ]

    def ignored_fields(self):
        return ["start_date", "end_date", "uid", "time"]
