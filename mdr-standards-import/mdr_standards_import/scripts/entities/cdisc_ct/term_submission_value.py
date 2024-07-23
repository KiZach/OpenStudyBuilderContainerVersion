class TermSubmissionValue:
    """
    Represents one submission value of an arbitrary term including
    a reference to all codelists that contain the term.

    The submisson value is either the code or the name submission value.
    """

    def __init__(self, term_submission_value: str, codelist=None, package=None):
        self.__term_submission_value: str = term_submission_value
        self.__codelists: set = set()
        self.__packages: set = set()

        if package is not None:
            self.add_package(package)

        if codelist is not None:
            self.add_codelist(codelist)

    def get_codelists(self):
        return self.__codelists

    def add_codelist(self, codelist):
        """
        Adds the specified codelist to the context of the submission value.
        Has no effect if the codelist was already set.
        """
        self.__codelists.add(codelist)

    def get_packages(self):
        return self.__packages

    def add_package(self, package):
        """
        Adds the specified package to the context of the submission value.
        Has no effect if the package was already set.
        """
        if package is not None:
            self.__packages.add(package)

    def get_value(self):
        return self.__term_submission_value

    def __repr__(self):
        return self.to_string()

    def __str__(self):
        return self.to_string()

    def to_string(self):
        return (
            f"{{value='{self.__term_submission_value}', codelists={self.__codelists}}}"
        )
