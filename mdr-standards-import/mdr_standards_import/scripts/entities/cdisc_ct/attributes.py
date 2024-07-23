from typing import Sequence

from mdr_standards_import.scripts.utils import are_lists_equal


class Attributes:
    def __init__(self, preferred_term: str, definition: str, synonyms: Sequence[str]):
        self.preferred_term = preferred_term
        self.definition = definition
        self.synonyms = synonyms

        self.__packages: set = set()

    def get_packages(self):
        return self.__packages

    def add_package(self, package):
        if package is not None:
            self.__packages.add(package)

    def __eq__(self, other):
        # packages is not part of the equality check
        if not isinstance(other, type(self)):
            return NotImplemented
        return (
            self.preferred_term == other.preferred_term
            and self.definition == other.definition
            and are_lists_equal(self.synonyms, other.synonyms)
        )

    def __hash__(self):
        # packages is not part of the hash
        synonyms = self.synonyms.copy() if self.synonyms is not None else []
        synonyms.sort()
        return hash((self.preferred_term, self.definition, tuple(synonyms)))
