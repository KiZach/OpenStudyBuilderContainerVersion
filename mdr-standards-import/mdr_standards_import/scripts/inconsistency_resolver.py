from mdr_standards_import.scripts.entities.cdisc_ct.attributes import Attributes
from mdr_standards_import.scripts.entities.cdisc_ct.ct_import import CTImport
from mdr_standards_import.scripts.entities.inconsistency import Inconsistency
from mdr_standards_import.scripts.entities.resolution import Resolution


class InconsistencyResolver:

    user_initials = "iResolve"

    def __init__(
        self, resolutions: "list[Resolution]" = None, catalogue_priority=None
    ) -> None:
        __resolutions: list[Resolution] = list()
        __catalogue_priority = None

    @staticmethod
    def resolve(ct_import: CTImport) -> None:
        for inconsistency in ct_import.get_inconsistencies():
            if inconsistency.tagline == Inconsistency.unexpected_codelist_name_tagline:
                if inconsistency.affected_codelist.concept_id in ["C66788", "C170452"]:
                    inconsistency.comment = "Automatic resolution: ignore"
                    inconsistency.user_initials = InconsistencyResolver.user_initials
                    inconsistency.set_resolved()
            elif (
                inconsistency.tagline
                == Inconsistency.inconsistent_term_attributes_tagline
            ):
                term = inconsistency.affected_term
                if term.concept_id in ["C90473"]:
                    inconsistency.comment = "Automatic resolution: ignore"
                    inconsistency.user_initials = InconsistencyResolver.user_initials
                    inconsistency.set_resolved()
                else:
                    attributes_set: set[Attributes] = term.get_attributes_set()
                    for attributes in attributes_set:
                        if "SDTM CT" in [
                            package.catalogue_name
                            for package in attributes.get_packages()
                        ]:
                            term.set_attributes(attributes)
                            inconsistency.comment = (
                                "Automatic resolution: catalogue-priority"
                            )
                            inconsistency.user_initials = (
                                InconsistencyResolver.user_initials
                            )
                            inconsistency.set_resolved()
                            break
            elif inconsistency.tagline == Inconsistency.inconsistent_terms_tagline:
                inconsistency.comment = "Automatic resolution: ignore"
                inconsistency.user_initials = InconsistencyResolver.user_initials
                inconsistency.set_resolved()
            elif (
                inconsistency.tagline
                == Inconsistency.inconsistent_codelist_attributes_tagline
            ):
                codelist = inconsistency.affected_codelist
                attributes_set: set[Attributes] = codelist.get_attributes_set()
                for attributes in attributes_set:
                    if "SDTM CT" in [
                        package.catalogue_name for package in attributes.get_packages()
                    ]:
                        codelist.set_attributes(attributes)
                        inconsistency.comment = (
                            "Automatic resolution: catalogue-priority"
                        )
                        inconsistency.user_initials = (
                            InconsistencyResolver.user_initials
                        )
                        inconsistency.set_resolved()
                        break
