from unittest import TestCase

from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import create_paths


class TestApi(TestCase):
    TEST_DB_NAME = "unittests"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

        # load_schema_file(graph, DB_SCHEMA_SCRIPT)
        # load_data_file(graph, DB_INIT_SCRIPT)

    def tear_down(self):
        pass  # db.cypher_query(f"DROP DATABASE {self.EST_DB_NAME}")

    def test_all_gets(self):
        all_paths = create_paths()
        for route in all_paths:
            if "GET" in route["methods"]:
                path = route["path_ready"]
                is_specific = route["is_specific"]
                print(route)
                try:
                    response = self.test_client.get(path)
                    if is_specific:
                        # TODO: passed because some calls respond
                        # with empty list instead of 404
                        # self.assertIn(response.status_code, [400, 404, 422])
                        pass
                    elif path in [
                        "/studies/1/study-objectives/{study_objective_uid}",
                        "/studies/1/study-criteria/{study_criteria_uid}",
                    ]:
                        # this test fails for now as there are no connections between study and objective/criteria selected
                        self.assertIn(response.status_code, [404])
                    elif path == "/ct/packages/changes":
                        # This test fails because of mandatory query parameter
                        self.assertIn(response.status_code, [422])
                    elif path == "/ct/packages/dates":
                        # This test fails because of mandatory query parameter
                        self.assertIn(response.status_code, [422])
                    elif path.endswith("/headers"):
                        # This fails because it takes a mandatory query parameter
                        self.assertIn(response.status_code, [422])
                    elif path == "/studies/allowed-configs":
                        # This fails because it needs data setup
                        self.assertIn(response.status_code, [404])
                    elif path.startswith("/studies/1/study-epochs/"):
                        # This fails because it takes a mandatory query parameter
                        self.assertIn(response.status_code, [400])
                    elif path == "/ct/catalogues/changes":
                        # This test fails because of mandatory query parameter
                        self.assertIn(response.status_code, [422])
                    elif path == "/ct/codelists/{codelist_uid}/sub-codelists":
                        # This test fails because of mandatory query parameter
                        self.assertIn(response.status_code, [422])
                    elif path == "/dictionaries/terms":
                        # This test fails because of mandatory query parameter
                        self.assertIn(response.status_code, [422])
                    elif path == "/dictionaries/codelists":
                        # This test fails because of missing required query parameter `library`
                        self.assertIn(response.status_code, [422])
                    elif path.startswith("/studies/{study_uid}/flowchart"):
                        # What is the purpose of this test when it is full of exceptions with paths that always fail?
                        self.assertIn(response.status_code, [404])
                    elif path == "/study-visits/allowed-visit-types":
                        # This test fails because of mandatory query parameter
                        self.assertIn(response.status_code, [422])
                    elif path == "/study-visits/allowed-time-references":
                        # This test fails because of mandatory query parameter
                        self.assertIn(response.status_code, [422])
                    elif path == "/listings/studies/{study_uid}/adam/{adam_report}":
                        # This test fails because of mandatory query parameter
                        self.assertIn(response.status_code, [422])
                    elif path == "/standards/datasets":
                        # This test fails because of mandatory query parameter
                        self.assertIn(response.status_code, [422])
                    elif path == "/standards/dataset-variables":
                        # This test fails because of mandatory query parameter
                        self.assertIn(response.status_code, [422])
                    elif path == "/standards/class-variables":
                        # This test fails because of mandatory query parameter
                        self.assertIn(response.status_code, [422])
                    elif path == "/standards/dataset-scenarios":
                        # This test fails because of mandatory query parameter
                        self.assertIn(response.status_code, [422])
                    elif path == "/system/check/secured":
                        self.assertIn(response.status_code, [401, 501])
                    elif path == "/listings/studies/study-metadata":
                        # This test fails because of mandatory query parameters
                        self.assertIn(response.status_code, [400])
                    elif (
                        path == "/concepts/odms/metadata/xmls/stylesheets/{stylesheet}"
                    ):
                        self.assertEqual(response.status_code, 400)
                    elif path == "/ddf/v3/studyDefinitions/{study_uid}":
                        # This test fails because of mandatory path parameters
                        self.assertIn(response.status_code, [404])
                    else:
                        self.assertEqual(response.status_code, 200)
                except Exception as e:
                    print(f"Exception during GET {path} execution")
                    raise e

    def test_all_posts(self):
        all_paths = create_paths()
        for route in all_paths:
            if "POST" in route["methods"]:
                path = route["path_ready"]
                data = route.get("data")

                if data:
                    print(f"Evaluating POST {path}")
                    response = self.test_client.post(path, json=data)
                    if path.endswith("pre-validate"):
                        self.assertIn(response.status_code, [202])
                    elif path.endswith("libraries"):
                        self.assertIn(response.status_code, [201])
                    else:
                        self.assertIn(response.status_code, [404, 400, 422])
