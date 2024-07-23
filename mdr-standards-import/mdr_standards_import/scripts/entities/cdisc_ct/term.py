from typing import Sequence, TypeVar

from mdr_standards_import.scripts.entities.cdisc_ct.codelist_term_submission_value import (
    CodelistTermSubmissionValue,
)
from mdr_standards_import.scripts.entities.inconsistency import Inconsistency
from mdr_standards_import.scripts.entities.cdisc_ct.term_attributes import (
    TermAttributes,
)
from mdr_standards_import.scripts.entities.cdisc_ct.term_submission_value import (
    TermSubmissionValue,
)
from mdr_standards_import.scripts.entities.cdisc_ct.term_submission_value_pair import (
    TermSubmissionValuePair,
)
from mdr_standards_import.scripts.term_submission_value_differentiator import (
    TermSubmissionValueDifferentiator,
)

T = TypeVar("T", bound="Term")


class Term:
    def __init__(self, concept_id: str, code_submission_value: str = None):
        self.concept_id: str = concept_id

        self.code_submission_value: str = code_submission_value

        # a dictionary used as hash map where
        # - the key is the submission value (str) of the term
        # - the value is the TermSubmissionValue object
        self.__submission_values: dict[str, TermSubmissionValue] = dict()

        self.__attributes: TermAttributes = None
        self.__attributes_set: set[TermAttributes] = set()

    def get_term_submission_values(self):
        return self.__submission_values.values()

    def get_term_submission_value(self, submission_value: str) -> TermSubmissionValue:
        return self.__submission_values.get(submission_value, None)

    def add_submission_value(self, term_submission_value: str, codelist, package=None):
        """
        Adds a code or name submission value to the term in the context of a codelist.
        """
        tsv: TermSubmissionValue = self.__submission_values.get(
            term_submission_value, TermSubmissionValue(term_submission_value)
        )
        self.__submission_values[term_submission_value] = tsv
        tsv.add_codelist(codelist)
        tsv.add_package(package)

    def add_attributes_set(
        self, term_attributes_set: "set[TermAttributes]", codelist, package
    ):
        for attributes in term_attributes_set:
            self.add_attributes(attributes, codelist, package)

    def add_attributes(self, term_attributes: TermAttributes, codelist, package):
        self.__attributes_set.add(term_attributes)
        for attributes in self.__attributes_set:
            if (
                term_attributes == attributes
            ):  # this triggers a call to CodelistAttributes.__eq__()
                attributes.add_codelist(codelist)
                attributes.add_package(package)
                break

    def set_attributes(self, attributes):
        self.__attributes = attributes

    def get_inconsistent_attributes_set(self):
        if self.has_consistent_attributes():
            return []
        return self.__attributes_set

    def get_attributes_set(self):
        return self.__attributes_set

    def get_attributes(self):
        if self.__attributes is not None:
            # there was an inconsistency which was resolved
            return self.__attributes
        if self.__attributes_set is None or len(self.__attributes_set) == 0:
            return None
        # return the one existing entry or an arbitrary (in that case an inconsistency is logged)
        return list(self.__attributes_set)[0]

    def get_codelists(self):
        codelists = set()
        for submission_value in self.__submission_values.values():
            codelists = codelists.union(submission_value.get_codelists())
        return codelists

    def get_inconsistencies(self, user_initials: str):
        inconsistencies = []

        if len(self.__submission_values) == 0:
            print(
                f"TODO / INCONSISTENCY: len(self.submission_values) == 0; concept_id={self.concept_id}"
            )

        if not self.has_consistent_submission_values():
            codelist_concept_ids = set()
            package_names = set()
            for tsv in self.__submission_values.values():
                for codelist in tsv.get_codelists():
                    codelist_concept_ids.add(codelist.concept_id)
                for package in tsv.get_packages():
                    package_names.add(package.name)
            message = Inconsistency.inconsistent_term_submission_value_template.format(
                term_concept_id=self.concept_id,
                codelist_concept_ids=list(codelist_concept_ids),
                package_names=list(package_names),
            )
            inconsistency = Inconsistency(
                Inconsistency.inconsistent_term_submission_value_tagline,
                message,
                user_initials,
            )
            inconsistency.set_affected_term(self)
            inconsistencies.append(inconsistency)

        if len(self.__attributes_set) == 0:
            print(
                f"TODO / INCONSISTENCY: no term attributes; concept_id={self.concept_id}"
            )

        if len(self.__attributes_set) > 1:
            codelist_concept_ids = set()
            package_names = set()
            for attributes in self.__attributes_set:
                for codelist in attributes.get_codelists():
                    codelist_concept_ids.add(codelist.concept_id)
                for package in attributes.get_packages():
                    package_names.add(package.name)
            message = Inconsistency.inconsistent_term_attributes_template.format(
                term_concept_id=self.concept_id,
                codelist_concept_ids=list(codelist_concept_ids),
                package_names=list(package_names),
            )
            inconsistency = Inconsistency(
                Inconsistency.inconsistent_term_attributes_tagline,
                message,
                user_initials,
            )
            inconsistency.set_affected_term(self)
            inconsistencies.append(inconsistency)

        return inconsistencies

    def has_consistent_attributes(self) -> bool:
        return len(self.__attributes_set) == 1

    def has_consistent_submission_values(self) -> bool:
        for tsv in self.__get_codelist_term_submission_values():
            if not tsv.is_consistent():
                return False
        return True

    def fork_term_based_on_code_submission_values(self, package) -> Sequence[T]:
        pairs: Sequence[
            TermSubmissionValuePair
        ] = self.get_code_name_submission_value_pairs()

        map: dict[str, set(TermSubmissionValuePair)] = dict()
        for tsv_pair in pairs:
            code_submission_value = tsv_pair.get_code_submission_value()
            tsv_pairs = map.get(code_submission_value, set())
            tsv_pairs.add(tsv_pair)
            map[code_submission_value] = tsv_pairs

        forked_terms: Sequence[Term] = []
        for code_sv, pair in map.items():
            forked_terms.append(
                self.fork_for_code_submission_value(code_sv, pair, package)
            )
        return forked_terms

    def fork_for_code_submission_value(
        self,
        code_submission_value: str,
        tsv_pairs: Sequence[TermSubmissionValuePair],
        package,
    ) -> T:
        # check if we have the same term already in the import based on the new
        # unique identifier: concept id + code submissin value
        term: Term = package.get_ct_import().merge_term(
            self.concept_id, code_submission_value
        )

        for tsv_pair in tsv_pairs:
            # copy over all corresponding attributes
            code_codelist = tsv_pair.get_code_codelist()
            if tsv_pair.is_single():
                if not code_codelist.is_name_ok_for_single_codelist():
                    code_codelist.set_has_inconsistent_name()
                attr_set = self.__get_attributes_set(code_codelist)
                term.add_attributes_set(attr_set, code_codelist, package)
            else:
                name_codelist = tsv_pair.get_name_codelist()
                if tsv_pair.is_name_tsv_consistent():
                    nsv = tsv_pair.get_name_submission_value()
                    attr_set = self.__get_attributes_set(name_codelist, nsv)
                    term.add_attributes_set(attr_set, name_codelist, package)
                    term.add_attributes_set(attr_set, code_codelist, package)
                else:
                    for nsv in tsv_pair.get_name_submission_values():
                        attr_set = self.__get_attributes_set(name_codelist, nsv)
                        term.add_attributes_set(attr_set, name_codelist, package)
                    attr_set = self.__get_attributes_set(code_codelist)
                    term.add_attributes_set(attr_set, code_codelist, package)

            # also copy over all corresponding submission values
            # this includes code and name submission values
            # although the differentiation has been done and the term
            # has both properties set accordingly, we explicitly keep these
            # values including their source (codelist, package) so that we
            # are able to tell if there is an inconsistency
            codelists = (tsv_pair.get_code_codelist(), tsv_pair.get_name_codelist())
            for codelist in codelists:
                for submission_value in self.__get_submission_values_for_codelist(
                    codelist
                ):
                    term.add_submission_value(submission_value, codelist, package)

        return term

    def __get_submission_values_for_codelist(self, codelist) -> "set(str)":
        submission_values = set()
        if codelist is not None:
            for tsv in self.__submission_values.values():
                if codelist in tsv.get_codelists():
                    submission_values.add(tsv.get_value())
        return submission_values

    def __get_attributes_set(self, codelist, name_submission_value: str = None):
        attributes_set: set[TermAttributes] = set()
        for attributes in self.__attributes_set:
            if attributes.are_defined_in(codelist):
                if name_submission_value is not None:
                    new_attributes = attributes.copy()
                    new_attributes.name_submission_value = name_submission_value
                    attributes_set.add(new_attributes)
                else:
                    attributes_set.add(attributes)
        return attributes_set

    def get_code_name_submission_value_pairs(self) -> Sequence[TermSubmissionValuePair]:
        """
        return: a list of code/name codelist pairs.
            Each pair in the list will at least contain an entry for the code submission value.
            However, note that the list will also include those 'pairs' where no name submission value entry is present
            (so strictly spoken, these entries are no pairs).
        """

        submission_values: Sequence[
            CodelistTermSubmissionValue
        ] = self.__get_codelist_term_submission_values()

        remaining_values: Sequence[CodelistTermSubmissionValue] = submission_values
        unmatched_values: Sequence[CodelistTermSubmissionValue] = []
        set_of_term_submission_value_pairs = set()

        while len(remaining_values) >= 2:
            # compare the first entry with all other entries
            value = remaining_values[0]
            values_to_compare = remaining_values[1:]
            index, term_submission_value_pair = self.__find_term_submission_value_pair(
                value, values_to_compare
            )
            if index is None:
                unmatched_values.append(value)
                remaining_values = values_to_compare
            else:
                set_of_term_submission_value_pairs.add(term_submission_value_pair)
                del values_to_compare[index]
                remaining_values = values_to_compare

        for remaining_value in remaining_values:
            set_of_term_submission_value_pairs.add(
                TermSubmissionValuePair(remaining_value, None)
            )
        for unmatched_value in unmatched_values:
            set_of_term_submission_value_pairs.add(
                TermSubmissionValuePair(unmatched_value, None)
            )

        return list(set_of_term_submission_value_pairs)

    def __find_term_submission_value_pair(
        self,
        tsv1: CodelistTermSubmissionValue,
        other_tsvs: Sequence[CodelistTermSubmissionValue],
    ):
        index = 0
        for tsv2 in other_tsvs:
            try:
                submission_value_pair = (
                    TermSubmissionValueDifferentiator.get_term_submission_value_pair(
                        tsv1, tsv2
                    )
                )
                return index, submission_value_pair
            except:
                index += 1

        return None, None

    def __get_codelist_term_submission_values(
        self,
    ) -> Sequence[CodelistTermSubmissionValue]:
        """
        Transforms the submission value structure from
        - one <submission value>, multiple <codelists> to
        - one <codelist>, <submission value(s)>

        :return a list of `CodelistTermSubmissionValue` entries;
            per codelist that contains the term one entry will be generated pointing to the submission value(s)
        """
        codelist_term_submission_values: dict[str, CodelistTermSubmissionValue] = dict()
        for submission_value in self.__submission_values.values():
            for codelist in submission_value.get_codelists():
                codelist_term_submission_value = codelist_term_submission_values.get(
                    codelist.concept_id, CodelistTermSubmissionValue(codelist)
                )
                codelist_term_submission_values[
                    codelist.concept_id
                ] = codelist_term_submission_value
                codelist_term_submission_value.add_submission_value(
                    submission_value.get_value()
                )
        return list(codelist_term_submission_values.values())

    def get_number_of_codelists(self) -> int:
        codelists: set = set()
        for submission_value in self.__submission_values.values():
            codelists = codelists.union(submission_value.__codelists)
        return len(codelists)
