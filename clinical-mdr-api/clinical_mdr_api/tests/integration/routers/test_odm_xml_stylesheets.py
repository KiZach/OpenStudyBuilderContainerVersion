import xml.etree.ElementTree as ET
from json import loads
from unittest import TestCase

from starlette.testclient import TestClient

from clinical_mdr_api.config import XML_STYLESHEET_DIR_PATH
from clinical_mdr_api.tests.utils.utils import xml_diff


class OdmXmlStylesheetTest(TestCase):
    def setUp(self):
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    def test_get_available_stylesheet_names(self):
        response = self.test_client.get("concepts/odms/metadata/xmls/stylesheets")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["blank", "sdtm"])

    def test_get_specific_stylesheet(self):
        response = self.test_client.get("concepts/odms/metadata/xmls/stylesheets/blank")

        with open(
            XML_STYLESHEET_DIR_PATH + "blank.xsl", mode="r", encoding="utf-8"
        ) as file:
            expected_xml = file.read()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("content-type"), "application/xml")

        expected_xml = ET.fromstring(expected_xml)
        actual_xml = ET.fromstring(response.content)

        xml_diff(expected_xml, actual_xml)

    def test_throw_exception_if_stylesheet_doesnt_exist(self):
        response = self.test_client.get(
            "concepts/odms/metadata/xmls/stylesheets/wrong",
        )

        self.assertEqual(response.status_code, 400)
        rs = loads(response.content)
        self.assertEqual(rs["type"], "BusinessLogicException")
        self.assertEqual(rs["message"], "Stylesheet with name (wrong) not found.")

    def test_throw_exception_if_stylesheet_name_contains_disallowed_character(self):
        for name in ["bla_nk", "blank.", "bla%nk"]:
            response = self.test_client.get(
                f"concepts/odms/metadata/xmls/stylesheets/{name}",
            )

            self.assertEqual(response.status_code, 400)
            rs = loads(response.content)
            self.assertEqual(rs["type"], "ValidationException")
            self.assertEqual(
                rs["message"],
                "Stylesheet name must only contain letters, numbers and hyphens.",
            )
