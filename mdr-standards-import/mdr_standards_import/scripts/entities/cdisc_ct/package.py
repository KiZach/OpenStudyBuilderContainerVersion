from typing import Sequence
from mdr_standards_import.scripts.entities.inconsistency import Inconsistency
from mdr_standards_import.scripts.utils import string_to_boolean
from mdr_standards_import.scripts.entities.cdisc_ct.codelist import Codelist
from mdr_standards_import.scripts.entities.cdisc_ct.codelist_attributes import (
    CodelistAttributes,
)
from mdr_standards_import.scripts.entities.cdisc_ct.term import Term
from mdr_standards_import.scripts.entities.cdisc_ct.term_attributes import (
    TermAttributes,
)


class Package:
    def __init__(self, ct_import):
        self.__ct_import = ct_import

        # codelists are SHARED ACROSS PACKAGES
        # that means that other packages might have effects on
        # the entries here; e.g. other packages might add attributes or terms...
        self.__codelists: set[Codelist] = set()

        # a reference to the terms of a specific codelist FOR THIS PACKAGE only
        # the terms are not shared
        # - the key is the concept id of the codelist
        # - the value is a set of terms that belong to the codelist as defined in this package
        self.__codelist_terms_map: dict[str, set[Term]] = dict()

        # a dictionary used as hash map where
        # - the key is the concept id of the term and
        # - the value is the Term object
        # the uniqueness of a term is dependent on the code submission value of the term
        # this differentiation can only be done when all codelists have been loaded
        # during the differentiation, the preliminary terms are transformed into the `terms` set
        self.__preliminary_terms: dict[str, Term] = dict()

        self.href = ""

    def get_ct_import(self):
        return self.__ct_import

    def get_term_concept_ids_for_codelist(self, codelist: Codelist) -> "list[str]":
        return [
            term.concept_id
            for term in self.__codelist_terms_map.get(codelist.concept_id, set())
        ]

    def get_codelists(self) -> Sequence[Codelist]:
        """
        Returns the codelists of this package. Note that codelis are shared across packages.
        If you are interested in the terms of the package, use `package.get_terms()` instead.
        """
        return list(self.__codelists)

    def get_terms(self):
        if self.__codelist_terms_map is None or len(self.__codelist_terms_map) == 0:
            return []
        terms_of_this_package = set()

        for terms in self.__codelist_terms_map.values():
            terms_of_this_package = terms_of_this_package.union(terms)
        return terms_of_this_package

    def __set_attributes(
        self,
        name: str,
        effective_date: str,
        registration_status: str,
        label: str,
        description: str,
        source: str,
        href: str,
    ):
        self.set_name(name)
        self.set_catalogue_name(name)
        self.effective_date: str = effective_date
        self.registration_status: str = registration_status

        self.label: str = label
        self.description: str = description
        self.source: str = source
        self.href: str = href

    def set_name(self, name):
        self.name: str = name.upper() if name is not None else None

    def set_catalogue_name(self, name):
        self.catalogue_name: str = name[:-11].upper() if name is not None else None

    def set_href(self, href):
        self.href: str = href

    def load_from_json_data(self, package_json_data):
        self.__load_package_data(package_json_data)
        self.__differentiate_between_code_name_submission_values()

    def __load_package_data(self, package_json_data):
        self.__set_attributes(
            package_json_data.get("name", None),
            package_json_data.get("effectiveDate", None),
            package_json_data.get("registrationStatus", None),
            package_json_data.get("label", None),
            package_json_data.get("description", None),
            package_json_data.get("source", None),
            self.__get_href(package_json_data),
        )
        self.__load_codelists_data(package_json_data.get("codelists", []))

    def __get_href(self, package_json_data):
        href = None
        links = package_json_data.get("_links", None)
        if links:
            _self = links.get("self", None)
            if _self:
                href = _self.get("href", None)
        return href

    def __load_codelists_data(self, codelists_json_data):
        for json in codelists_json_data:
            codelist: Codelist = self.__ct_import.merge_codelist(
                json.get("conceptId", None)
            )
            attributes = CodelistAttributes(
                json.get("name", None),
                json.get("submissionValue", None),
                json.get("preferredTerm", None),
                json.get("definition", None),
                string_to_boolean(json.get("extensible", "false")),
                json.get("synonyms", None),
            )
            codelist.add_attributes(attributes, self)
            self.__load_terms_data(json.get("terms", []), codelist)
            self.__add_codelist(codelist)

    def __load_terms_data(self, terms_json_data, codelist: Codelist):
        for json in terms_json_data:
            term = self.__merge_preliminary_term(json.get("conceptId", None))
            # we don't know yet if the provided submission value is the
            # code or name submission value of that term
            # so we add it as one of the submission values for later differentiation
            term.add_submission_value(json.get("submissionValue", None), codelist, self)
            term.add_attributes(
                TermAttributes(
                    None,  # not known yet, see above
                    json.get("preferredTerm", None),
                    json.get("definition", None),
                    json.get("synonyms", None),
                ),
                codelist,
                self,
            )
            codelist.add_term(term)

    def __merge_preliminary_term(self, term_concept_id: str) -> Term:
        term: Term = self.__preliminary_terms.get(
            term_concept_id, Term(term_concept_id)
        )
        self.__preliminary_terms[term_concept_id] = term
        return term

    def __add_codelist(self, codelist: Codelist):
        self.__codelists.add(codelist)

    def __differentiate_between_code_name_submission_values(self):
        for preliminary_term in self.__preliminary_terms.values():
            self.__remove_term_from_codelists(preliminary_term)
            for (
                forked_term
            ) in preliminary_term.fork_term_based_on_code_submission_values(self):
                self.__add_term_to_codelists(forked_term)

    def __remove_term_from_codelists(self, old_term: Term):
        for codelist in old_term.get_codelists():
            codelist.remove_term(old_term)

    def __add_term_to_codelists(self, new_term: Term):
        term_copy = Term(new_term.concept_id, new_term.code_submission_value)
        for codelist in new_term.get_codelists():
            codelist.add_term(new_term)
            terms = self.__codelist_terms_map.get(codelist.concept_id, set())
            terms.add(term_copy)
            self.__codelist_terms_map[codelist.concept_id] = terms

    def get_inconsistencies(self, user_initials: str):
        inconsistencies = []
        if len(self.__codelists) == 0:
            message = Inconsistency.no_codelists_in_package_template.format(
                name=self.name, href=self.href
            )
            inconsistencies.append(
                Inconsistency(
                    Inconsistency.no_codelists_in_package_tagline,
                    message,
                    user_initials,
                )
            )

        return inconsistencies

    def __repr__(self):
        return self.to_string()

    def __str__(self):
        return self.to_string()

    def to_string(self):
        return f"{{\n  name='{self.name}'\n  catalogue_name='{self.catalogue_name}'\n  num_codelists={len(self.__codelists)}\n  num_terms={len(self.__preliminary_terms)}\n}}"
