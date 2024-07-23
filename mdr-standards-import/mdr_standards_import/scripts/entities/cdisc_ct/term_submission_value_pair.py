from mdr_standards_import.scripts.entities.cdisc_ct.codelist_term_submission_value import (
    CodelistTermSubmissionValue,
)


class TermSubmissionValuePair:
    def __init__(
        self,
        code_tsv: CodelistTermSubmissionValue,
        name_tsv: CodelistTermSubmissionValue,
    ):
        self.__code_tsv: CodelistTermSubmissionValue = code_tsv
        self.__name_tsv: CodelistTermSubmissionValue = name_tsv

    def is_single(self):
        return self.__name_tsv is None

    def get_code_codelist(self):
        return self.__code_tsv.get_codelist() if self.__code_tsv is not None else None

    def get_name_codelist(self):
        return self.__name_tsv.get_codelist() if self.__name_tsv is not None else None

    def get_code_submission_value(self) -> str:
        return self.__code_tsv.get_value() if self.__code_tsv is not None else None

    def get_name_submission_value(self) -> str:
        return self.__name_tsv.get_value() if self.__name_tsv is not None else None

    def get_name_submission_values(self) -> "set[str]":
        return self.__name_tsv.get_values() if self.__name_tsv is not None else set()

    def is_name_tsv_consistent(self):
        return self.__name_tsv.is_consistent()

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return (
            self.__code_tsv == other.__code_tsv and self.__name_tsv == other.__name_tsv
        )

    def __hash__(self):
        return hash((self.__code_tsv, self.__name_tsv))

    def __repr__(self):
        return self.to_string()

    def __str__(self):
        return self.to_string()

    def to_string(self):
        return f"{{code_tsv={self.__code_tsv}, name_tsv={self.__name_tsv}}}"
