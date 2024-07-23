from mdr_standards_import.scripts.entities.cdisc_ct.codelist import Codelist
from mdr_standards_import.scripts.entities.cdisc_ct.codelist_attributes import (
    CodelistAttributes,
)
from mdr_standards_import.scripts.entities.cdisc_ct.ct_import import CTImport
from mdr_standards_import.scripts.entities.inconsistency import Inconsistency
from mdr_standards_import.scripts.entities.cdisc_ct.package import Package
from mdr_standards_import.scripts.entities.cdisc_ct.term import Term
from mdr_standards_import.scripts.entities.cdisc_ct.term_attributes import (
    TermAttributes,
)
from mdr_standards_import.scripts.entities.cdisc_ct.term_submission_value_pair import (
    TermSubmissionValuePair,
)
from mdr_standards_import.scripts.entities.cdisc_ct.codelist_term_submission_value import (
    CodelistTermSubmissionValue,
)


class TestCTImport:

    # Test-Case i01
    def test__check_for_inconsistencies__i01__ok(self):
        # given
        ct_import = CTImport(None, None)
        package = Package(ct_import)

        term_T01 = {
            "conceptId": "T01",
            "submissionValue": "SM T01",
            "definition": "Definition T01",
            "preferredTerm": "Peferred Term T01",
            "synonyms": ["Synonym T01"],
        }
        json_data = {
            "name": "TEST A CT 2024-06-30",
            "codelists": [
                {
                    "conceptId": "C01",
                    "extensible": "true",
                    "name": "Codelist C01 Code",  # <- inconsistency
                    "submissionValue": "SM C01",
                    "terms": [term_T01],
                }
            ],
        }

        # when
        package.load_from_json_data(json_data)
        ct_import.add_package(package)

        ct_import.check_for_inconsistencies()

        # then
        assert len(ct_import.get_inconsistencies()) == 1
        taglines = [i.tagline for i in ct_import.get_inconsistencies()]
        assert Inconsistency.unexpected_codelist_name_tagline in taglines
        inconcistencty = list(ct_import.get_inconsistencies())[0]
        assert inconcistencty.affected_codelist is not None

    # Test-Case i02
    def test__check_for_inconsistencies__i02__ok(self):
        # given
        ct_import = CTImport(None, None)
        package = Package(ct_import)

        term_C43820 = {
            "conceptId": "C43820",
            "submissionValue": "MedDRA",
            "preferredTerm": "MedDRA",
        }
        json_data = {
            "name": "SDTM CT 2014-09-26",
            "codelists": [
                {
                    "conceptId": "C66788",
                    "extensible": "true",
                    "name": "Dictionary Name",  # <- inconsistency
                    "submissionValue": "DICTNAM",
                    "terms": [term_C43820],
                }
            ],
        }

        # when
        package.load_from_json_data(json_data)
        ct_import.add_package(package)

        ct_import.check_for_inconsistencies()

        # then
        assert len(ct_import.get_inconsistencies()) == 1
        taglines = [i.tagline for i in ct_import.get_inconsistencies()]
        assert Inconsistency.unexpected_codelist_name_tagline in taglines
        inconcistencty = list(ct_import.get_inconsistencies())[0]
        assert inconcistencty.affected_codelist is not None

    # Test-Case i03
    def test__check_for_inconsistencies__i03__ok(self):
        # given
        ct_import = CTImport("2024-06-30", "TST")
        package_a = Package(ct_import)
        package_b = Package(ct_import)

        term_T01 = {
            "conceptId": "T01",
            "submissionValue": "SM T01",
            "definition": "Definition T01",
            "preferredTerm": "Peferred Term T01",
            "synonyms": ["Synonym T01"],
        }
        term_T02 = {
            "conceptId": "T02",
            "submissionValue": "SM T02",
            "definition": "Definition T02",
            "preferredTerm": "Peferred Term T02",
            "synonyms": ["Synonym T02"],
        }
        json_data_a = {
            "name": "TEST A CT 2024-06-30",
            "codelists": [
                {
                    "conceptId": "C01",
                    "extensible": "true",
                    "name": "Codelist C01",
                    "submissionValue": "SM C01",  # <- inconsistency
                    "terms": [term_T01, term_T02],  # <- inconsistency
                }
            ],
        }
        json_data_b = {
            "name": "TEST B CT 2024-06-30",
            "codelists": [
                {
                    "conceptId": "C01",
                    "extensible": "true",
                    "name": "Codelist C01",
                    "submissionValue": "SM C01 !!",  # <- inconsistency
                    "terms": [term_T01],  # <- inconsistency
                }
            ],
        }

        # when
        package_a.load_from_json_data(json_data_a)
        ct_import.add_package(package_a)

        package_b.load_from_json_data(json_data_b)
        ct_import.add_package(package_b)

        ct_import.check_for_inconsistencies()

        # then
        assert len(ct_import.get_inconsistencies()) == 2
        taglines = [i.tagline for i in ct_import.get_inconsistencies()]
        assert Inconsistency.inconsistent_codelist_attributes_tagline in taglines
        assert Inconsistency.inconsistent_terms_tagline in taglines
        assert len(ct_import.get_codelists()) == 1
        codelist_C01: Codelist = list(ct_import.get_codelists())[0]
        assert codelist_C01.has_consistent_attributes() == False
        assert codelist_C01.has_inconsistent_terms() == True
        assert len(package_a.get_term_concept_ids_for_codelist(codelist_C01)) == 2
        assert len(package_b.get_term_concept_ids_for_codelist(codelist_C01)) == 1
        for term in codelist_C01.get_terms():
            assert term.has_consistent_attributes()
            assert term.has_consistent_submission_values()

    # Test-Case i04
    def test__check_for_inconsistencies__i04__ok(self):
        # given
        ct_import = CTImport("2024-06-30", "TST")
        package_a = Package(ct_import)
        package_b = Package(ct_import)

        term_T01a = {
            "conceptId": "T01",
            "submissionValue": "SM T01",
            "definition": "Definition T01",
            "preferredTerm": "Peferred Term T01",
            "synonyms": ["Synonym T01"],
        }
        term_T01b = {
            "conceptId": "T01",
            "submissionValue": "SM T01",
            "definition": "Definition T01",
            "preferredTerm": "Peferred Term T01 !!",  # <- inconsistency
            "synonyms": ["Synonym T01"],
        }

        json_data_a = {
            "name": "TEST A CT 2024-06-30",
            "codelists": [
                {
                    "conceptId": "C01",
                    "extensible": "true",
                    "name": "Codelist C01",
                    "submissionValue": "SM C01",
                    "terms": [term_T01a],
                }
            ],
        }
        json_data_b = {
            "name": "TEST B CT 2024-06-30",
            "codelists": [
                {
                    "conceptId": "C01",
                    "extensible": "true",
                    "name": "Codelist C01",
                    "submissionValue": "SM C01",
                    "terms": [term_T01b],
                }
            ],
        }

        # when
        package_a.load_from_json_data(json_data_a)
        ct_import.add_package(package_a)

        package_b.load_from_json_data(json_data_b)
        ct_import.add_package(package_b)

        ct_import.check_for_inconsistencies()

        # then
        assert len(ct_import.get_inconsistencies()) == 1
        taglines = [i.tagline for i in ct_import.get_inconsistencies()]
        assert Inconsistency.inconsistent_term_attributes_tagline in taglines

        assert len(ct_import.get_codelists()) == 1
        codelist_C01: Codelist = list(ct_import.get_codelists())[0]
        for term in codelist_C01.get_terms():
            assert term.has_consistent_attributes() == False

    # Test-Case i05
    def test__check_for_inconsistencies__i05__ok(self):
        # given
        ct_import = CTImport("2024-06-30", "TST")
        package = Package(ct_import)
        json_data = {"name": "TEST A CT 2024-06-30", "codelists": []}

        # when
        package.load_from_json_data(json_data)
        ct_import.add_package(package)

        ct_import.check_for_inconsistencies()

        # then
        assert len(ct_import.get_inconsistencies()) == 1
        taglines = [i.tagline for i in ct_import.get_inconsistencies()]
        assert Inconsistency.no_codelists_in_package_tagline in taglines

    # Test-Case i06
    def test__check_for_inconsistencies__i06__ok(self):
        # given
        ct_import = CTImport("2024-06-30", "TST")
        package_a = Package(ct_import)
        package_b = Package(ct_import)

        term_T01a = {
            "conceptId": "T01",
            "submissionValue": "SM T01 Code",
            "definition": "Definition T01",
            "preferredTerm": "Peferred Term T01",
            "synonyms": ["Synonym T01"],
        }
        term_T01b = {
            "conceptId": "T01",
            "submissionValue": "SM T01 Name",
            "definition": "Definition T01",
            "preferredTerm": "Peferred Term T01",
            "synonyms": ["Synonym T01"],
        }
        term_T01c = {
            "conceptId": "T01",
            "submissionValue": "SM T01 !!",  # <- inconsistency
            "definition": "Definition T01",
            "preferredTerm": "Peferred Term T01",
            "synonyms": ["Synonym T01"],
        }

        json_data_a = {
            "name": "TEST A CT 2024-06-30",
            "codelists": [
                {
                    "conceptId": "C01",
                    "extensible": "true",
                    "name": "Codelist C01 Code",
                    "submissionValue": "SM C01",
                    "terms": [term_T01a],
                },
                {
                    "conceptId": "C02",
                    "extensible": "true",
                    "name": "Codelist C01 Name",
                    "submissionValue": "SM C02",
                    "terms": [term_T01b],
                },
            ],
        }
        json_data_b = {
            "name": "TEST B CT 2024-06-30",
            "codelists": [  # <- inconsistency
                {
                    "conceptId": "C02",
                    "extensible": "true",
                    "name": "Codelist C01 Name",
                    "submissionValue": "SM C02",
                    "terms": [term_T01c],  # <- inconsistency
                }
            ],
        }

        # when
        package_a.load_from_json_data(json_data_a)
        ct_import.add_package(package_a)

        package_b.load_from_json_data(json_data_b)
        ct_import.add_package(package_b)

        ct_import.check_for_inconsistencies()

        # then
        assert len(ct_import.get_inconsistencies()) == 1
        taglines = [i.tagline for i in ct_import.get_inconsistencies()]
        assert Inconsistency.unexpected_codelist_name_tagline in taglines
        # there is no inconsistent_term_submission_value_tagline in taglines
        # since this type of inconsistency is only checked on package level and not across packages

    # Test-Case i07
    def test__check_for_inconsistencies__i07__ok(self):
        # given
        ct_import = CTImport("2024-06-30", "TST")
        package_a = Package(ct_import)

        term_T01a = {
            "conceptId": "T01",
            # <- inconsistency
            "definition": "Definition T01",
            "preferredTerm": "Peferred Term T01",
            "synonyms": ["Synonym T01"],
        }
        term_T01b = {
            "conceptId": "T01",
            "submissionValue": "SM T01 Name",
            "definition": "Definition T01",
            "preferredTerm": "Peferred Term T01",
            "synonyms": ["Synonym T01"],
        }

        json_data = {
            "name": "TEST A CT 2024-06-30",
            "codelists": [
                {
                    "conceptId": "C01",
                    "extensible": "true",
                    "name": "Codelist C01",
                    "submissionValue": "SM CD",
                    "terms": [term_T01a],
                },
                {
                    "conceptId": "C02",
                    "extensible": "true",
                    "name": "Codelist C01",
                    "submissionValue": "SM",
                    "terms": [term_T01b],
                },
            ],
        }

        # when
        package_a.load_from_json_data(json_data)
        ct_import.add_package(package_a)

        ct_import.check_for_inconsistencies()

        # then
        assert len(ct_import.get_inconsistencies()) == 1
        taglines = [i.tagline for i in ct_import.get_inconsistencies()]
        assert Inconsistency.inconsistent_term_submission_value_tagline in taglines
        inconcistencty = list(ct_import.get_inconsistencies())[0]
        assert inconcistencty.affected_term is not None
