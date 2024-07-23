import datetime
from mdr_standards_import.scripts.entities.inconsistency import Inconsistency
from mdr_standards_import.scripts.entities.cdisc_ct.term import Term
from mdr_standards_import.scripts.entities.cdisc_ct.codelist import Codelist
from mdr_standards_import.scripts.entities.cdisc_ct.package import Package
from mdr_standards_import.scripts.utils import are_sets_equal, make_uid_from_concept_and_submval


class CTImport:
    def __init__(self, effective_date: str, user_initials: str):
        self.effective_date: str = effective_date
        self.import_date_time: str = datetime.datetime.now().astimezone().isoformat()
        self.user_initials: str = user_initials
        self.automatic_resolution_done: bool = False

        self.__packages: list[Package] = []

        # a dictionary used as hash map where
        # - the key is the concept id of the codelist and
        # - the value is the Codelist object
        self.__codelists: dict[str, Codelist] = dict()

        # a dictionary used as hash map where
        # - the key is the unique identifier of the term and
        # - the value is the Term object
        self.__terms: dict[str, Term] = dict()

        self.__inconsistencies: list[Inconsistency] = []

    def get_packages(self):
        return self.__packages

    def get_codelists(self):
        return self.__codelists.values()

    def get_terms(self):
        return self.__terms.values()

    def get_inconsistencies(self):
        return self.__inconsistencies

    def add_package(self, package: Package):
        self.__packages.append(package)

    def merge_codelist(self, codelist_concept_id: str) -> Codelist:
        codelist: Codelist = self.__codelists.get(
            codelist_concept_id, Codelist(codelist_concept_id)
        )
        self.__codelists[codelist_concept_id] = codelist
        return codelist

    # TODO code_submission_value
    def merge_term(self, term_concept_id: str, code_submission_value: str) -> Term:
        key: str = make_uid_from_concept_and_submval(term_concept_id, code_submission_value)
        term: Term = self.__terms.get(
            key, Term(term_concept_id, code_submission_value))
        self.__terms[key] = term
        return term

    def check_for_inconsistencies(self):
        self.__check_packages()
        self.__check_codelists()
        self.__check_terms()

    def __check_packages(self):
        for package in self.__packages:
            self.__inconsistencies.extend(
                package.get_inconsistencies(self.user_initials)
            )

    def __check_codelists(self):
        for codelist in self.__codelists.values():
            self.__inconsistencies.extend(
                codelist.get_inconsistencies(self.user_initials)
            )

            package_names: set[str] = set()
            term_concept_ids_of_import = set(
                [term.concept_id for term in codelist.get_terms()]
            )

            for package in self.__packages:
                term_concept_ids_of_package = package.get_term_concept_ids_for_codelist(
                    codelist
                )
                if len(term_concept_ids_of_package) > 0 and not are_sets_equal(
                    term_concept_ids_of_import, term_concept_ids_of_package
                ):
                    package_names.add(package.name)

            if len(package_names) > 0:
                codelist.set_has_inconsistent_terms()
                message = Inconsistency.inconsistent_terms_template.format(
                    codelist_concept_id=codelist.concept_id,
                    package_names=list(package_names),
                )
                inconsistency = Inconsistency(
                    Inconsistency.inconsistent_terms_tagline,
                    message,
                    self.user_initials,
                )
                inconsistency.set_affected_codelist(codelist)
                self.__inconsistencies.append(inconsistency)

    def __check_terms(self):
        for term in self.__terms.values():
            self.__inconsistencies.extend(term.get_inconsistencies(self.user_initials))
