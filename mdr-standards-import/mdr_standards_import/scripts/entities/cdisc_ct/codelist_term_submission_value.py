from mdr_standards_import.scripts.utils import are_lists_equal


class CodelistTermSubmissionValue:
    """
    This class is meaningful in the context of a term.
    It holds
    - one of the codelists that contain the term and
    - a list of term submission values defined by the codelist

    Typically this list includes only one term submission value;
    It is considered to be an inconsistency if there are multiple term submission values.
    Cf. Codelist C66726, Term C42911: SDTM CT 2018-12-21 vs. SEND CT 2018-12-21
    """

    def __init__(self, codelist):
        self.__codelist = codelist
        self.__term_submission_values: set[str] = set()

    def add_submission_value(self, term_submission_value: str):
        if term_submission_value is None:
            return
        self.__term_submission_values.add(term_submission_value)

    def get_codelist(self):
        return self.__codelist

    def get_value(self):
        if len(self.__term_submission_values) > 0:
            return list(self.__term_submission_values)[0]
        else:
            return None

    def get_values(self) -> "set[str]":
        return self.__term_submission_values

    def is_consistent(self) -> bool:
        return len(self.__term_submission_values) == 1

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return (
            self.__codelist.concept_id == other.__codelist.concept_id
            and are_lists_equal(
                self.__term_submission_values, other.__term_submission_values
            )
        )

    def __hash__(self):
        return hash((self.__codelist.concept_id, tuple(self.__term_submission_values)))

    def __repr__(self):
        return self.to_string()

    def __str__(self):
        return self.to_string()

    def to_string(self):
        return f"{{codelist.concept_id='{self.__codelist.concept_id}', term_submission_values={self.__term_submission_values}}}"
