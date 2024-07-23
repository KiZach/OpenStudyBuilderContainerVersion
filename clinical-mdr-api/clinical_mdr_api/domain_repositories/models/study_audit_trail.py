from neomodel import One, RelationshipFrom, RelationshipTo, StringProperty, ZeroOrOne

from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNode,
    ClinicalMdrRel,
    ConjunctionRelation,
    ZonedDateTimeProperty,
)


class StudyAction(ClinicalMdrNode):
    audit_trail = RelationshipFrom(
        ".study.StudyRoot", "AUDIT_TRAIL", model=ClinicalMdrRel
    )
    date = ZonedDateTimeProperty()
    status = StringProperty()
    user_initials = StringProperty()
    has_before = RelationshipTo(
        ".study_selections.StudySelection",
        "BEFORE",
        model=ConjunctionRelation,
        cardinality=ZeroOrOne,
    )
    has_after = RelationshipTo(
        ".study_selections.StudySelection",
        "AFTER",
        model=ConjunctionRelation,
        cardinality=One,
    )
    study_value_has_before = RelationshipTo(
        ".study.StudyValue",
        "BEFORE",
        model=ConjunctionRelation,
        cardinality=ZeroOrOne,
    )
    study_value_node_has_after = RelationshipTo(
        ".study.StudyValue",
        "AFTER",
        model=ConjunctionRelation,
        cardinality=One,
    )
    study_field_has_before = RelationshipTo(
        ".study_field.StudyField",
        "BEFORE",
        model=ConjunctionRelation,
        cardinality=ZeroOrOne,
    )
    study_field_node_has_after = RelationshipTo(
        ".study_field.StudyField",
        "AFTER",
        model=ConjunctionRelation,
        cardinality=One,
    )
    study_selection_metadata_has_before = RelationshipTo(
        ".study_selections.StudySelectionMetadata",
        "BEFORE",
        model=ConjunctionRelation,
        cardinality=ZeroOrOne,
    )
    study_selection_metadata_has_after = RelationshipTo(
        ".study_selections.StudySelectionMetadata",
        "AFTER",
        model=ConjunctionRelation,
        cardinality=One,
    )


class Delete(StudyAction):
    pass


class Create(StudyAction):
    pass


class Edit(StudyAction):
    pass
