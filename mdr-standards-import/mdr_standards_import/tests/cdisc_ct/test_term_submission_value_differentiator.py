from mdr_standards_import.scripts.entities.cdisc_ct.codelist import Codelist
from mdr_standards_import.scripts.entities.cdisc_ct.codelist_attributes import (
    CodelistAttributes,
)
from mdr_standards_import.scripts.entities.cdisc_ct.codelist_term_submission_value import (
    CodelistTermSubmissionValue,
)
from mdr_standards_import.scripts.term_submission_value_differentiator import (
    TermSubmissionValueDifferentiator,
)


class TestTermSubmissionValueDifferentiator:
    # cf. Test-Case 08
    def test__get_term_submission_value_pair__on_code1__ok(self):
        # given
        codelist1 = Codelist("C114117")
        codelist1.add_attributes(
            CodelistAttributes(
                "Morphology Test Code", "MOTESTCD", None, None, None, None
            ),
            None,
        )
        tsv1 = CodelistTermSubmissionValue(codelist1)
        tsv1.add_submission_value("WIDTH")

        codelist2 = Codelist("C114116")
        codelist2.add_attributes(
            CodelistAttributes(
                "Morphology Test Name", "MOTEST", None, None, None, None
            ),
            None,
        )
        tsv2 = CodelistTermSubmissionValue(codelist2)
        tsv2.add_submission_value("Width")

        # when
        pair = TermSubmissionValueDifferentiator.get_term_submission_value_pair(
            tsv1, tsv2
        )

        # then
        assert pair.get_code_codelist() == codelist1
        assert pair.get_code_submission_value() == "WIDTH"
        assert pair.get_name_codelist() == codelist2
        assert pair.get_name_submission_value() == "Width"

    def test__get_term_submission_value_pair__on_code2__ok(self):
        # given
        codelist1 = Codelist("C150779")
        codelist1.add_attributes(
            CodelistAttributes(
                "Functional Assessment of Cancer Therapy/Gynecologic Oncology Group-Neurotoxicity Version 4 Questionnaire Test Name",
                "FAC057TN",
                None,
                None,
                None,
                None,
            ),
            None,
        )
        tsv1 = CodelistTermSubmissionValue(codelist1)
        tsv1.add_submission_value("A")

        codelist2 = Codelist("C150780")
        codelist2.add_attributes(
            CodelistAttributes(
                "Functional Assessment of Cancer Functional Assessment of Cancer Therapy/Gynecologic Oncology Group-Neurotoxicity Version 4 Questionnaire Test Code",
                "FAC057TC",
                None,
                None,
                None,
                None,
            ),
            None,
        )
        tsv2 = CodelistTermSubmissionValue(codelist2)
        tsv2.add_submission_value("B")

        # when
        pair = TermSubmissionValueDifferentiator.get_term_submission_value_pair(
            tsv1, tsv2
        )

        # then
        assert pair.get_code_codelist() == codelist2
        assert pair.get_code_submission_value() == "B"
        assert pair.get_name_codelist() == codelist1
        assert pair.get_name_submission_value() == "A"

    def test__get_term_submission_value_pair__on_name__ok(self):
        # given
        codelist1 = Codelist("C89981")
        codelist1.add_attributes(
            CodelistAttributes(
                "SEND Subject Characteristics Test Code",
                "SBCCDSND",
                None,
                None,
                None,
                None,
            ),
            None,
        )
        tsv1 = CodelistTermSubmissionValue(codelist1)
        tsv1.add_submission_value("SPLRLOC")

        codelist2 = Codelist("C89980")
        codelist2.add_attributes(
            CodelistAttributes(
                "SEND Subject Characteristics Test Name",
                "SBCSND",
                None,
                None,
                None,
                None,
            ),
            None,
        )
        tsv2 = CodelistTermSubmissionValue(codelist2)
        tsv2.add_submission_value("Test Subject Supplier Site")

        # when
        pair = TermSubmissionValueDifferentiator.get_term_submission_value_pair(
            tsv1, tsv2
        )

        # then
        assert pair.get_code_codelist() == codelist1
        assert pair.get_code_submission_value() == "SPLRLOC"
        assert pair.get_name_codelist() == codelist2
        assert pair.get_name_submission_value() == "Test Subject Supplier Site"
