from neomodel import (  # ZeroOrOne,
    One,
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
    ZeroOrMore,
)

from clinical_mdr_api.domain_repositories.models.controlled_terminology import CTPackage
from clinical_mdr_api.domain_repositories.models.generic import ClinicalMdrRel
from clinical_mdr_api.domain_repositories.models.study import StudyValue
from clinical_mdr_api.domain_repositories.models.study_selections import StudySelection


class StudyStandardVersion(StudySelection):
    study_value = RelationshipFrom(
        StudyValue, "HAS_STUDY_STANDARD_VERSION", cardinality=ZeroOrMore
    )
    status = StringProperty()
    has_ct_package = RelationshipTo(
        CTPackage,
        "HAS_CT_PACKAGE",
        model=ClinicalMdrRel,
        cardinality=One,
    )
