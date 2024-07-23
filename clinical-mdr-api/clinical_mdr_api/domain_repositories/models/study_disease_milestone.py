from neomodel import (
    BooleanProperty,
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
    ZeroOrMore,
    ZeroOrOne,
)

from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import ClinicalMdrRel
from clinical_mdr_api.domain_repositories.models.study import StudyValue
from clinical_mdr_api.domain_repositories.models.study_selections import StudySelection


class StudyDiseaseMilestone(StudySelection):
    study_value = RelationshipFrom(
        StudyValue, "HAS_STUDY_DISEASE_MILESTONE", cardinality=ZeroOrMore
    )
    status = StringProperty()
    has_disease_milestone_type = RelationshipTo(
        CTTermRoot,
        "HAS_DISEASE_MILESTONE_TYPE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    repetition_indicator = BooleanProperty()
