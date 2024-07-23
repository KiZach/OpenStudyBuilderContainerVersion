from json import loads

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.data.odm_xml import (
    clinspark_input,
    clinspark_output,
    import_input1,
    import_input2,
    import_input3,
    import_input4,
    import_input5,
    import_input6,
    import_output1,
    import_output2,
)
from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_TERM_ATTRIBUTES_CYPHER,
    STARTUP_ODM_VENDOR_ATTRIBUTES,
    STARTUP_ODM_VENDOR_ELEMENTS,
    STARTUP_ODM_VENDOR_NAMESPACES,
    STARTUP_UNIT_DEFINITIONS,
)


class OdmXmlImporterTest(api.APITest):
    TEST_DB_NAME = "odmxmlimporter"
    CONTENT_TYPE = "application/xml"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ODM_VENDOR_NAMESPACES)
        db.cypher_query(STARTUP_ODM_VENDOR_ELEMENTS)
        db.cypher_query(STARTUP_ODM_VENDOR_ATTRIBUTES)
        db.cypher_query(STARTUP_UNIT_DEFINITIONS)
        db.cypher_query(STARTUP_CT_TERM_ATTRIBUTES_CYPHER)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    def ignored_fields(self):
        return [
            "start_date",
            "end_date",
            "user_initials",
        ]

    def test_import_odm_xml(self):
        response = self.test_client.post(
            "concepts/odms/metadata/xmls/import",
            files={"xml_file": ("odm.xml", import_input1, self.CONTENT_TYPE)},
        )

        self.check(import_output1, loads(response.content))

    def test_import_odm_vendor_with_csv_mapper(self):
        response = self.test_client.post(
            "concepts/odms/metadata/xmls/import",
            files={
                "xml_file": ("odm.xml", import_input2, self.CONTENT_TYPE),
                "mapper_file": (
                    "mapper.csv",
                    "type,parent,from_name,to_name,to_alias,from_alias,alias_context\n"
                    "attribute,,Repeated,Repeating,,,\n"
                    "element,,NameOne,cs:nameOne,,,\n"
                    "element,,Alias,,,true,CompletionInstructions\n"
                    "element,*,Alias,,,true,ImplementationNotes\n"
                    "attribute,,CompletionInstructions,osb:instruction,,,\n"
                    "attribute,*,ImplementationNotes,osb:sponsorInstruction,,,\n",
                    "text/csv",
                ),
            },
        )

        self.check(import_output2, loads(response.content))

    def test_import_clinspark_odm_xml(self):
        db.cypher_query("MERGE (:CTCatalogue {name:'CDASH CT'})")
        response = self.test_client.post(
            "concepts/odms/metadata/xmls/import?exporter=clinspark",
            files={"xml_file": ("clinspark.xml", clinspark_input, self.CONTENT_TYPE)},
        )

        self.check(clinspark_output, loads(response.content))

    def test_throw_exception_if_file_is_not_xml(self):
        response = self.test_client.post(
            "concepts/odms/metadata/xmls/import",
            files={
                "xml_file": (
                    "mapper.json",
                    "",
                    "application/json",
                )
            },
        )

        self.assertEqual(response.status_code, 400)
        rs = loads(response.content)
        self.assertEqual(rs["type"], "BusinessLogicException")
        self.assertEqual(rs["message"], "Only XML format is supported.")

    def test_throw_exception_if_vendor_attributes_dont_match_their_regex(self):
        response = self.test_client.post(
            "concepts/odms/metadata/xmls/import",
            files={"xml_file": ("odm.xml", import_input4, self.CONTENT_TYPE)},
        )

        self.assertEqual(response.status_code, 400)
        rs = loads(response.content)
        self.assertEqual(rs["type"], "BusinessLogicException")
        self.assertEqual(
            rs["message"],
            "Provided values for following attributes don't match their regex pattern:\n\n{'odm_vendor_attribute3': '^[a-zA-Z]+$'}",
        )

    def test_throw_exception_if_ref_vendor_attributes_dont_match_their_regex(self):
        response = self.test_client.post(
            "concepts/odms/metadata/xmls/import",
            files={"xml_file": ("odm.xml", import_input5, self.CONTENT_TYPE)},
        )

        self.assertEqual(response.status_code, 400)
        rs = loads(response.content)
        self.assertEqual(rs["type"], "BusinessLogicException")
        self.assertEqual(
            rs["message"],
            "Provided values for following attributes don't match their regex pattern:\n\n{'odm_vendor_attribute3': '^[a-zA-Z]+$'}",
        )

    def test_throw_exception_if_measurementunits_dont_exist(self):
        response = self.test_client.post(
            "concepts/odms/metadata/xmls/import",
            files={"xml_file": ("odm.xml", import_input3, self.CONTENT_TYPE)},
        )

        self.assertEqual(response.status_code, 400)
        rs = loads(response.content)
        self.assertEqual(rs["type"], "BusinessLogicException")
        self.assertEqual(
            rs["message"],
            "MeasurementUnits identified by following OIDs {'wrong name'} don't match any Unit Definition.",
        )

    def test_throw_exception_if_measurementunitref_refers_to_non_present_measurementunit(
        self,
    ):
        response = self.test_client.post(
            "concepts/odms/metadata/xmls/import",
            files={"xml_file": ("odm.xml", import_input6, self.CONTENT_TYPE)},
        )

        self.assertEqual(response.status_code, 400)
        rs = loads(response.content)
        self.assertEqual(rs["type"], "BusinessLogicException")
        self.assertEqual(
            rs["message"],
            "MeasurementUnit with OID ('name1') was not provided.",
        )
