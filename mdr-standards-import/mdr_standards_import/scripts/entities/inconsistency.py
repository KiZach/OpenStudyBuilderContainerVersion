import datetime


class Inconsistency:
    no_codelists_in_package_tagline = "no codelists in package"
    no_codelists_in_package_template = (
        "The package with the name='{name}' does not have any codelists; href='{href}'."
    )

    inconsistent_codelist_attributes_tagline = "inconsistent codelist attributes"
    inconsistent_codelist_attributes_template = (
        "The codelist with the conceptId='{codelist_concept_id}' "
        "has inconsistent attributes across different packages; "
        "packages={package_names}."
    )

    inconsistent_term_attributes_tagline = "inconsistent term attributes"
    inconsistent_term_attributes_template = (
        "The term with the conceptId='{term_concept_id}' "
        "has inconsistent attributes across different codelists; "
        "codelists={codelist_concept_ids}; "
        "packages={package_names}."
    )

    inconsistent_terms_tagline = "inconsistent terms"
    inconsistent_terms_template = (
        "The codelist with the conceptId='{codelist_concept_id}' "
        "has an inconsistent set of terms defined across different packages; "
        "packages={package_names}."
    )

    unexpected_codelist_name_tagline = "unexpected codelist name"
    unexpected_codelist_name_template = (
        "The name='{name}' of the codelist with the conceptId='{codelist_concept_id}' "
        "indicates that there is a second codelist with the expectedName='{expected_other_name}'. "
        "However, we could not find such a second codelist."
    )

    inconsistent_term_submission_value_tagline = "inconsistent term submission values"
    inconsistent_term_submission_value_template = (
        "The term with the conceptId='{term_concept_id}' has an inconsistent "
        "set of submission values defined; "
        "codelists='{codelist_concept_ids}', packages={package_names}."
    )

    def __init__(self, tagline: str, message: str, user_initials: str):
        self.date_time: str = datetime.datetime.now().astimezone().isoformat()
        self.tagline = tagline
        self.message = message
        self.comment = None
        self.user_initials = user_initials

        self.affected_package = None
        self.affected_codelist = None
        self.affected_term = None

        self.__is_resolved = False

    def set_affected_package(self, package):
        self.affected_package = package

    def set_affected_codelist(self, codelist):
        self.affected_codelist = codelist

    def set_affected_term(self, term):
        self.affected_term = term

    def is_resolved(self):
        return self.__is_resolved

    def set_resolved(self):
        self.__is_resolved = True
