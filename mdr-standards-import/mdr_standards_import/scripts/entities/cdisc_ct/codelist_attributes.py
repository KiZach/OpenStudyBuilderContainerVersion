from typing import Sequence
from mdr_standards_import.scripts.entities.cdisc_ct.attributes import Attributes


class CodelistAttributes(Attributes):
    def __init__(
        self,
        name: str,
        submission_value: str,
        preferred_term: str,
        definition: str,
        extensible: bool,
        synonyms: Sequence[str],
    ):
        super().__init__(preferred_term, definition, synonyms)

        self.name = name
        self.submission_value = submission_value

        self.extensible = extensible
        self.synonyms = synonyms

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return (
            super().__eq__(other)
            and self.name == other.name
            and self.submission_value == other.submission_value
            and self.extensible == other.extensible
        )

    def __hash__(self):
        return super().__hash__() ^ hash(
            (self.name, self.submission_value, self.extensible)
        )
