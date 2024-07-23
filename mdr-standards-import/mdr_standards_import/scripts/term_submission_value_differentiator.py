from mdr_standards_import.scripts.entities.cdisc_ct.codelist_term_submission_value import (
    CodelistTermSubmissionValue,
)
from mdr_standards_import.scripts.entities.cdisc_ct.term_submission_value_pair import (
    TermSubmissionValuePair,
)
from mdr_standards_import.scripts.utils import get_same_start_string


class TermSubmissionValueDifferentiator:
    @staticmethod
    def get_term_submission_value_pair(
        tsv1: CodelistTermSubmissionValue, tsv2: CodelistTermSubmissionValue
    ) -> TermSubmissionValuePair:
        try:
            return TermSubmissionValueDifferentiator.__get_term_submission_value_pair_by_codelist_submission_value(
                tsv1, tsv2
            )
        except:
            return TermSubmissionValueDifferentiator.__get_term_submission_value_pair_by_codelist_name(
                tsv1, tsv2
            )

    @staticmethod
    def __get_term_submission_value_pair_by_codelist_submission_value(
        tsv1: CodelistTermSubmissionValue, tsv2: CodelistTermSubmissionValue
    ) -> TermSubmissionValuePair:
        codelist_submission_value1 = tsv1.get_codelist().get_submission_value()
        codelist_submission_value2 = tsv2.get_codelist().get_submission_value()

        # this is the common start string of the two codelist submission values
        same_submission_value_start = get_same_start_string(
            codelist_submission_value1, codelist_submission_value2
        )

        suffix_submission_value1 = codelist_submission_value1[
            len(same_submission_value_start) :
        ].lower()
        suffix_submission_value2 = codelist_submission_value2[
            len(same_submission_value_start) :
        ].lower()

        last_two_chars1 = codelist_submission_value1[-2:].lower()

        if suffix_submission_value1 == " cd" or suffix_submission_value1 == "cd":
            return TermSubmissionValuePair(tsv1, tsv2)
        elif suffix_submission_value2 == " cd" or suffix_submission_value2 == "cd":
            return TermSubmissionValuePair(tsv2, tsv1)
        elif (
            suffix_submission_value1 == "c"
            and last_two_chars1 == "tc"
            and suffix_submission_value2 == "n"
        ):
            return TermSubmissionValuePair(tsv1, tsv2)
        elif (
            suffix_submission_value2 == "c"
            and suffix_submission_value1 == "n"
            and last_two_chars1 == "tn"
        ):
            return TermSubmissionValuePair(tsv2, tsv1)

        raise Exception()

    @staticmethod
    def __get_term_submission_value_pair_by_codelist_name(
        tsv1: CodelistTermSubmissionValue, tsv2: CodelistTermSubmissionValue
    ) -> TermSubmissionValuePair:
        codelist_name1 = tsv1.get_codelist().get_name()
        codelist_name2 = tsv2.get_codelist().get_name()

        # this is the common start string of the two codelist names
        same_codelist_start = get_same_start_string(codelist_name1, codelist_name2)

        suffix_codelist1 = codelist_name1[len(same_codelist_start) :].lower()
        suffix_codelist2 = codelist_name2[len(same_codelist_start) :].lower()
        if suffix_codelist1 == " name" or suffix_codelist1 == "name":
            return TermSubmissionValuePair(tsv2, tsv1)
        elif suffix_codelist2 == " name" or suffix_codelist2 == "name":
            return TermSubmissionValuePair(tsv1, tsv2)
        elif suffix_codelist1 == " code" or suffix_codelist1 == "code":
            return TermSubmissionValuePair(tsv1, tsv2)
        elif suffix_codelist2 == " code" or suffix_codelist2 == "code":
            return TermSubmissionValuePair(tsv2, tsv1)

        raise Exception()
