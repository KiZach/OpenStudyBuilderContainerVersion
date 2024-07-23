from mdr_standards_import.scripts.entities.inconsistency import Inconsistency
from mdr_standards_import.scripts.entities.cdisc_ct.term import Term
from mdr_standards_import.scripts.entities.cdisc_ct.codelist_attributes import (
    CodelistAttributes,
)


class Codelist:
    def __init__(self, concept_id: str):
        self.concept_id = concept_id

        self.__attributes = None
        self.__attributes_set: set[CodelistAttributes] = set()

        self.__terms: set[Term] = set()

        self.__has_inconsistent_terms: bool = False
        self.__has_inconsistent_name: bool = False

    def get_terms(self):
        return self.__terms

    def add_term(self, term):
        self.__terms.add(term)

    def remove_term(self, term):
        self.__terms.discard(term)

    def set_attributes(self, attributes):
        self.__attributes = attributes

    def get_attributes(self):
        if self.__attributes is not None:
            # there was an inconsistency which was resolved
            return self.__attributes
        if self.__attributes_set is None or len(self.__attributes_set) == 0:
            return None
        # return the one existing entry or an arbitrary (in that case an inconsistency is logged)
        return list(self.__attributes_set)[0]

    def get_name(self):
        attributes = self.get_attributes()
        if attributes is not None:
            return attributes.name
        return None

    def get_attributes_set(self):
        return self.__attributes_set

    def add_attributes(self, codelist_attributes: CodelistAttributes, package):
        self.__attributes_set.add(codelist_attributes)
        for attributes in self.__attributes_set:
            if (
                codelist_attributes == attributes
            ):  # this calls .__eq__ on the CodelistAttributes
                attributes.add_package(package)
                break

    def get_inconsistent_attributes_set(self):
        if self.has_consistent_attributes():
            return []
        return self.__attributes_set

    def get_inconsistencies(self, user_initials: str):
        inconsistencies = []
        if len(self.__terms) == 0:
            print(
                f"TODO / INCONSISTENCY: no terms in codelist with concept_id={self.concept_id}"
            )

        if len(self.__attributes_set) == 0:
            print(
                f"TODO / INCONSISTENCY: no codelist attributes; concept_id={self.concept_id}"
            )

        if len(self.__attributes_set) > 1:
            package_names = set()
            for attributes in self.__attributes_set:
                for package in attributes.get_packages():
                    package_names.add(package.name)
            message = Inconsistency.inconsistent_codelist_attributes_template.format(
                codelist_concept_id=self.concept_id,
                package_names=list(package_names),
            )
            inconsistency = Inconsistency(
                Inconsistency.inconsistent_codelist_attributes_tagline,
                message,
                user_initials,
            )
            inconsistency.set_affected_codelist(self)
            inconsistencies.append(inconsistency)

        if self.has_inconsistent_name():
            message = Inconsistency.unexpected_codelist_name_template.format(
                name=self.get_name(),
                codelist_concept_id=self.concept_id,
                expected_other_name=self.get_other_expected_name(),
            )
            inconsistency = Inconsistency(
                Inconsistency.unexpected_codelist_name_tagline, message, user_initials
            )
            inconsistency.set_affected_codelist(self)
            inconsistencies.append(inconsistency)

        return inconsistencies

    def get_name(self):
        if self.__attributes_set is None:
            return None
        name = None
        for attributes in self.__attributes_set:
            if name is None and attributes.name is not None:
                name = attributes.name
                continue
            if name is not None and name != attributes.name:
                raise Exception()
        return name

    def get_submission_value(self):
        if self.__attributes_set is None:
            return None
        submission_value = None
        for attributes in self.__attributes_set:
            if submission_value is None and attributes.submission_value is not None:
                submission_value = attributes.submission_value
                continue
            if (
                submission_value is not None
                and submission_value != attributes.submission_value
            ):
                raise Exception()
        return submission_value

    def is_name_ok_for_single_codelist(self) -> bool:
        """
        Assumes that this codelist is not part of a code/name codelist pair
        and checks if the name is as expected.
        """
        return self.get_name() is not None and not (
            self.get_name().lower().endswith(" name")
            or self.get_name().lower().endswith(" code")
        )

    def get_other_expected_name(self) -> str:
        if self.get_name() is None:
            return None
        if self.get_name().lower().endswith(" name"):
            return self.get_name()[0:-5] + " Code"
        else:
            return self.get_name()[0:-5] + " Name"

    def has_consistent_attributes(self) -> bool:
        return len(self.__attributes_set) == 1

    def has_inconsistent_terms(self):
        return self.__has_inconsistent_terms

    def set_has_inconsistent_terms(self):
        self.__has_inconsistent_terms = True

    def has_inconsistent_name(self):
        return self.__has_inconsistent_name

    def set_has_inconsistent_name(self):
        self.__has_inconsistent_name = True
