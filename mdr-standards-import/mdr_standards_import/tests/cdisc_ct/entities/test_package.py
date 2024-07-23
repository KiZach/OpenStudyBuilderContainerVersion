from mdr_standards_import.scripts.entities.cdisc_ct.package import Package
from mdr_standards_import.scripts.entities.cdisc_ct.ct_import import CTImport


class TestPackage:
    def test__load_from_json_data__one_term__ok(self):
        # given
        ct_import = CTImport("2021-10-30", "TST")
        package = Package(ct_import)

        term_C48152 = {"conceptId": "C48152", "submissionValue": "ug"}
        json_data = {
            "name": "CDASH CT 2014-09-26",
            "codelists": [
                {
                    "conceptId": "C78417",
                    "name": "Concomitant Medication Dose Units",
                    "submissionValue": "CMDOSU",
                    "terms": [term_C48152],
                },
                {
                    "conceptId": "C78428",
                    "name": "Total Volume Administration Unit",
                    "submissionValue": "EXVOLTU",
                    "terms": [term_C48152],
                },
                {
                    "conceptId": "C78423",
                    "name": "Units for Exposure",
                    "submissionValue": "EXDOSU",
                    "terms": [term_C48152],
                },
                {
                    "conceptId": "C78430",
                    "name": "Units for Planned Exposure",
                    "submissionValue": "EXPDOSEU",
                    "terms": [term_C48152],
                },
            ],
        }

        # when
        package.load_from_json_data(json_data)

        # then
        assert len(package.get_terms()) == 1

    def test__set_catalogue_name____ok(self):
        # given
        package = Package(CTImport(None, None))

        # when
        package.set_catalogue_name("TesT 5A CT 2024-06-30")

        # then
        assert package.catalogue_name == "TEST 5A CT"

    def test__set_name____ok(self):
        # given
        package = Package(CTImport(None, None))

        # when
        package.set_name("TesT 5A CT 2024-06-30")

        # then
        assert package.name == "TEST 5A CT 2024-06-30"
