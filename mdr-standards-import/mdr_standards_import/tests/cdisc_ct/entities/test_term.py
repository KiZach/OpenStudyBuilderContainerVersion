from mdr_standards_import.scripts.entities.cdisc_ct.codelist import Codelist
from mdr_standards_import.scripts.entities.cdisc_ct.codelist_attributes import (
    CodelistAttributes,
)
from mdr_standards_import.scripts.entities.cdisc_ct.ct_import import CTImport
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


class TestTerm:
    def test__add_submission_value__same_sv__one_value(self):
        # given
        term = Term("C123")

        # when
        term.add_submission_value("SV1", Codelist("C1"))
        term.add_submission_value("SV1", Codelist("C2"))

        # then
        assert term.has_consistent_submission_values()
        assert len(term.get_term_submission_values()) == 1
        assert len(term.get_term_submission_value("SV1").get_codelists()) == 2
        codelist_concept_ids = [
            codelist.concept_id
            for codelist in term.get_term_submission_value("SV1").get_codelists()
        ]
        assert "C1" in codelist_concept_ids
        assert "C2" in codelist_concept_ids

    def test__add_submission_value__different_svs__two_values(self):
        # given
        term = Term("C123")

        # when
        term.add_submission_value("SV1", Codelist("C1"))
        term.add_submission_value("SV2", Codelist("C2"))

        # then
        assert term.has_consistent_submission_values()
        assert len(term.get_term_submission_values()) == 2
        assert "C1" in [
            codelist.concept_id
            for codelist in term.get_term_submission_value("SV1").get_codelists()
        ]
        assert "C2" in [
            codelist.concept_id
            for codelist in term.get_term_submission_value("SV2").get_codelists()
        ]

    def test__add_submission_value__different_svs__two_values(self):
        # given
        term = Term("C123")
        codelist1 = Codelist("C1")

        # when
        term.add_submission_value("SV1", codelist1)
        term.add_submission_value("SV2", codelist1)

        # then
        assert term.has_consistent_submission_values() == False
        assert len(term.get_term_submission_values()) == 2
        assert "C1" in [
            codelist.concept_id
            for codelist in term.get_term_submission_value("SV1").get_codelists()
        ]
        assert "C1" in [
            codelist.concept_id
            for codelist in term.get_term_submission_value("SV2").get_codelists()
        ]

    def test__add_attributes__same_attributes__consistent(self):
        # given
        term = Term("C123")
        attributes1 = TermAttributes("nsv", "preferred_term", "definition", ["1", "2"])
        attributes2 = TermAttributes("nsv", "preferred_term", "definition", ["2", "1"])
        codelist1 = Codelist("C1")
        codelist2 = Codelist("C2")

        # when
        term.add_attributes(attributes1, codelist1, None)
        term.add_attributes(attributes2, codelist2, None)

        # then
        assert term.has_consistent_attributes() is True
        attributes: TermAttributes = term.get_attributes()
        assert len(attributes.get_codelists()) == 2
        assert attributes.are_defined_in(codelist1)
        assert attributes.are_defined_in(codelist2)

    def test__add_attributes__different_nsv__inconsistent(self):
        # given
        term = Term("C123")
        attributes1 = TermAttributes("nsv1", "preferred_term", "definition", [])
        attributes2 = TermAttributes("nsv2", "preferred_term", "definition", [])

        # when
        term.add_attributes(attributes1, None, None)
        term.add_attributes(attributes2, None, None)

        # then
        assert term.has_consistent_attributes() is False

    def test__add_attributes__different_pterm__inconsistent(self):
        # given
        term = Term("C123")
        attributes1 = TermAttributes("nsv", "preferred_term1", "definition", [])
        attributes2 = TermAttributes("nsv", "preferred_term2", "definition", [])

        # when
        term.add_attributes(attributes1, None, None)
        term.add_attributes(attributes2, None, None)

        # then
        assert term.has_consistent_attributes() is False

    def test__add_attributes__different_definition__inconsistent(self):
        # given
        term = Term("C123")
        attributes1 = TermAttributes("nsv", "preferred_term", "definition1", [])
        attributes2 = TermAttributes("nsv", "preferred_term", "definition2", [])

        # when
        term.add_attributes(attributes1, None, None)
        term.add_attributes(attributes2, None, None)

        # then
        assert term.has_consistent_attributes() is False

    def test__add_attributes__different_synonyms__inconsistent(self):
        # given
        term = Term("C123")
        attributes1 = TermAttributes("nsv", "preferred_term", "definition", ["A", "b"])
        attributes2 = TermAttributes("nsv", "preferred_term", "definition", ["a", "b"])

        # when
        term.add_attributes(attributes1, None, None)
        term.add_attributes(attributes2, None, None)

        # then
        assert term.has_consistent_attributes() is False

    # get_code_name_submission_value_pairs

    def test__get_code_name_submission_value_pairs__two_pairs__ok(self):
        # given
        term = Term("t")

        codelist1 = Codelist("c")
        codelist1.add_attributes(
            CodelistAttributes("x", "y", None, None, None, None), None
        )
        term.add_submission_value("z", codelist1)

        # when
        pairs = term.get_code_name_submission_value_pairs()

        # then
        assert len(pairs) == 1

    # cf. Test-Case 08
    def test__get_code_name_submission_value_pairs__two_pairs__ok(self):
        # given
        term = Term("C25345")

        codelist1 = Codelist("C114117")
        codelist1.add_attributes(
            CodelistAttributes(
                "Morphology Test Code", "MOTESTCD", None, None, None, None
            ),
            None,
        )
        term.add_submission_value("WIDTH", codelist1)

        codelist2 = Codelist("C114116")
        codelist2.add_attributes(
            CodelistAttributes(
                "Morphology Test Name", "MOTEST", None, None, None, None
            ),
            None,
        )
        term.add_submission_value("Width", codelist2)

        codelist3 = Codelist("C95121")
        codelist3.add_attributes(
            CodelistAttributes(
                "Physical Properties Test Code", "PHSPRPCD", None, None, None, None
            ),
            None,
        )
        term.add_submission_value("WIDTH", codelist3)

        codelist4 = Codelist("C95120")
        codelist4.add_attributes(
            CodelistAttributes(
                "Physical Properties Test Name", "PHSPRP", None, None, None, None
            ),
            None,
        )
        term.add_submission_value("Width", codelist4)

        # when
        pairs = term.get_code_name_submission_value_pairs()

        # then
        assert len(pairs) == 2

    def test__get_code_name_submission_value_pairs__two_pairs_plus_one__ok(self):
        # given
        term = Term("C25345")

        codelist1 = Codelist("C114117")
        codelist1.add_attributes(
            CodelistAttributes(
                "Morphology Test Code", "MOTESTCD", None, None, None, None
            ),
            None,
        )
        term.add_submission_value("WIDTH", codelist1)

        codelist2 = Codelist("C114116")
        codelist2.add_attributes(
            CodelistAttributes(
                "Morphology Test Name", "MOTEST", None, None, None, None
            ),
            None,
        )
        term.add_submission_value("Width", codelist2)

        codelist3 = Codelist("C95121")
        codelist3.add_attributes(
            CodelistAttributes(
                "Physical Properties Test Code", "PHSPRPCD", None, None, None, None
            ),
            None,
        )
        term.add_submission_value("WIDTH", codelist3)

        codelist4 = Codelist("C95120")
        codelist4.add_attributes(
            CodelistAttributes(
                "Physical Properties Test Name", "PHSPRP", None, None, None, None
            ),
            None,
        )
        term.add_submission_value("Width", codelist4)

        codelist5 = Codelist("C00000")
        codelist5.add_attributes(
            CodelistAttributes("Something", "X", None, None, None, None), None
        )
        term.add_submission_value("OTHER", codelist5)

        codelist6 = Codelist("C99999")
        codelist6.add_attributes(
            CodelistAttributes("Something Else", "X", None, None, None, None), None
        )
        term.add_submission_value("WIDTH", codelist6)

        # when
        pairs = term.get_code_name_submission_value_pairs()

        # then
        assert len(pairs) == 4

    def test__get_code_name_submission_value_pairs__two_singles__ok(self):
        # given
        term = Term("C64527")

        codelist1 = Codelist("C78745")
        codelist1.add_attributes(
            CodelistAttributes(
                "Exposure Dosing Frequency per Interval",
                "EXDOSFRQ",
                None,
                None,
                None,
                None,
            ),
            None,
        )
        term.add_submission_value("TID", codelist1)

        codelist2 = Codelist("C78419")
        codelist2.add_attributes(
            CodelistAttributes(
                "Concomitant Medication Dosing Frequency per Interval",
                "CMDOSFRQ",
                None,
                None,
                None,
                None,
            ),
            None,
        )
        term.add_submission_value("TID", codelist2)

        # when
        pairs = term.get_code_name_submission_value_pairs()

        # then
        assert len(pairs) == 2

    def test__fork_for_tsv_pair(self):
        # given
        term = Term("1")
        attributes = TermAttributes("nsv", "pt", "d1", [])

        codelist1 = Codelist("C114117")
        term.add_attributes(attributes, codelist1, None)

        codelist1.add_attributes(
            CodelistAttributes(
                "Morphology Test Code", "MOTESTCD", None, None, None, None
            ),
            None,
        )
        code_tsv = CodelistTermSubmissionValue(codelist1)
        code_tsv.add_submission_value("WIDTH")
        tsv_pair = TermSubmissionValuePair(code_tsv, None)

        package = Package(CTImport(None, None))

        # when
        new_term = term.fork_for_code_submission_value("WIDTH", [tsv_pair], package)
        same_term = term.fork_for_code_submission_value("WIDTH", [tsv_pair], package)

        # then
        assert new_term.has_consistent_attributes()
        assert new_term == same_term

    # cf. Test-Case i06
    def test__get_code_name_submission_value_pairs__i06_ok(self):
        # given
        term = Term("T01")
        codelist_C01 = Codelist("C01")
        term.add_submission_value("SM T01 Code", codelist_C01)
        codelist_C01.add_attributes(
            CodelistAttributes("Codelist C01 Code", "SM C01", None, None, None, None),
            None,
        )

        codelist_C02 = Codelist("C02")
        term.add_submission_value("SM T01 Name", codelist_C02)
        codelist_C02.add_attributes(
            CodelistAttributes("Codelist C01 Name", "SM C02", None, None, None, None),
            None,
        )

        # when
        pairs = term.get_code_name_submission_value_pairs()

        # then
        assert len(pairs) == 1
        assert list(pairs)[0].get_name_submission_value() == "SM T01 Name"
