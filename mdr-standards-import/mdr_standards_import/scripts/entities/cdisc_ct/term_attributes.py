from typing import Sequence
from mdr_standards_import.scripts.entities.cdisc_ct.attributes import Attributes


class TermAttributes(Attributes):
    def __init__(
        self,
        name_submission_value: str,
        preferred_term: str,
        definition: str,
        synonyms: Sequence[str],
    ):
        super().__init__(preferred_term, definition, synonyms)

        self.name_submission_value: str = name_submission_value

        self.__codelists: set = set()

    def copy(self):
        synonyms = self.synonyms.copy() if self.synonyms is not None else None
        attributes = TermAttributes(
            self.name_submission_value, self.preferred_term, self.definition, synonyms
        )
        # don't copy codelists
        # don't copy packages
        return attributes

    def add_codelist(self, codelist):
        if codelist is not None:
            self.__codelists.add(codelist)

    def get_codelists(self):
        return self.__codelists

    def are_defined_in(self, codelist):
        return codelist in self.__codelists

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented

        # codelists is not part of the equality check
        return (
            super().__eq__(other)
            and self.name_submission_value == other.name_submission_value
        )

    def __hash__(self):
        # codelists is not part of the equality check
        return super().__hash__() ^ hash((self.name_submission_value))

    def __repr__(self):
        return self.to_string()

    def __str__(self):
        return self.to_string()

    def to_string(self):
        codelist_concept_ids = [codelist.concept_id for codelist in self.__codelists]
        return f"{{codelists: {codelist_concept_ids}; attribs: {self.preferred_term}, {self.definition}, {self.synonyms}}}"
