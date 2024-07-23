from neomodel import (
    ArrayProperty,
    BooleanProperty,
    DateProperty,
    IntegerProperty,
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
    ZeroOrOne,
)

from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNode,
    ClinicalMdrNodeWithUID,
    ClinicalMdrRel,
    Library,
    VersionRelationship,
    ZonedDateTimeProperty,
)


class CTPackage(ClinicalMdrNodeWithUID):
    name = StringProperty()
    label = StringProperty()
    description = StringProperty()
    href = StringProperty()
    registration_status = StringProperty()
    source = StringProperty()
    import_date = ZonedDateTimeProperty()
    effective_date = DateProperty()
    user_initials = StringProperty()
    contains_package = RelationshipFrom(
        "CTCatalogue", "CONTAINS_PACKAGE", model=ClinicalMdrRel, cardinality=ZeroOrOne
    )
    extends_package = RelationshipTo(
        "CTPackage", "EXTENDS_PACKAGE", model=ClinicalMdrRel, cardinality=ZeroOrOne
    )


# abstract class created to easily detect nodes as
# Controlled Terminology items in generic implementation
class ControlledTerminology(ClinicalMdrNode):
    __abstract_node__ = True


class ControlledTerminologyWithUID(ClinicalMdrNodeWithUID):
    __abstract_node__ = True


class CTCodelistAttributesValue(ControlledTerminology):
    name = StringProperty()
    submission_value = StringProperty()
    preferred_term = StringProperty()
    definition = StringProperty()
    extensible = BooleanProperty()
    synonyms = ArrayProperty()


class CTCodelistAttributesRoot(ControlledTerminology):
    has_version = RelationshipTo(
        CTCodelistAttributesValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        CTCodelistAttributesValue, "LATEST", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        CTCodelistAttributesValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        CTCodelistAttributesValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        CTCodelistAttributesValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    has_root = RelationshipFrom(
        "CTCodelistRoot", "HAS_ATTRIBUTES_ROOT", model=ClinicalMdrRel
    )


class CTCodelistNameValue(ControlledTerminology):
    __optional_labels__ = ["TemplateParameter"]
    name = StringProperty()


class CTCodelistNameRoot(ControlledTerminology):
    has_version = RelationshipTo(
        CTCodelistNameValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        CTCodelistNameValue, "LATEST", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        CTCodelistNameValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        CTCodelistNameValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        CTCodelistNameValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    has_root = RelationshipFrom("CTCodelistRoot", "HAS_NAME_ROOT", model=ClinicalMdrRel)


class CTTermAttributesValue(ControlledTerminology):
    concept_id = StringProperty()
    code_submission_value = StringProperty()
    name_submission_value = StringProperty()
    preferred_term = StringProperty()
    definition = StringProperty()
    synonyms = ArrayProperty()


class CTTermAttributesRoot(ControlledTerminology):
    has_version = RelationshipTo(
        CTTermAttributesValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        CTTermAttributesValue, "LATEST", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        CTTermAttributesValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        CTTermAttributesValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        CTTermAttributesValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    has_root = RelationshipFrom(
        "CTTermRoot", "HAS_ATTRIBUTES_ROOT", model=ClinicalMdrRel
    )


class CTTermNameValue(ControlledTerminology):
    __optional_labels__ = ["TemplateParameterTermValue"]
    name = StringProperty()
    name_sentence_case = StringProperty()


class CTTermNameRoot(ControlledTerminology):
    __optional_labels__ = ["TemplateParameterTermRoot"]
    has_version = RelationshipTo(
        CTTermNameValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(CTTermNameValue, "LATEST", model=ClinicalMdrRel)
    latest_final = RelationshipTo(CTTermNameValue, "LATEST_FINAL", model=ClinicalMdrRel)
    latest_retired = RelationshipTo(
        CTTermNameValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(CTTermNameValue, "LATEST_DRAFT", model=ClinicalMdrRel)
    has_root = RelationshipFrom("CTTermRoot", "HAS_NAME_ROOT", model=ClinicalMdrRel)


# pylint: disable=abstract-method
class CodelistTermRelationship(ClinicalMdrRel):
    """
    A `CodelistTermRelationship` represents a relationship between a `CTCodelistRoot` and a `CTTermRoot` node.
    In the graph, these are persisted as `HAS_TERM`, `HAD_TERM`.
    """

    start_date = ZonedDateTimeProperty()
    end_date = ZonedDateTimeProperty()
    user_initials = StringProperty()
    order = IntegerProperty()


class CTCodelistRoot(ControlledTerminologyWithUID):
    LIBRARY_REL_TYPE = "CONTAINS_CODELIST"
    has_child_codelist = RelationshipFrom(
        "CTCodelistRoot", "HAS_PARENT_CODELIST", model=ClinicalMdrRel
    )
    has_parent_codelist = RelationshipTo(
        "CTCodelistRoot", "HAS_PARENT_CODELIST", model=ClinicalMdrRel
    )
    has_name_root = RelationshipTo(
        CTCodelistNameRoot, "HAS_NAME_ROOT", model=ClinicalMdrRel
    )
    has_attributes_root = RelationshipTo(
        CTCodelistAttributesRoot, "HAS_ATTRIBUTES_ROOT", model=ClinicalMdrRel
    )
    has_codelist = RelationshipFrom("CTCatalogue", "HAS_CODELIST", model=ClinicalMdrRel)
    has_library = RelationshipFrom(Library, LIBRARY_REL_TYPE, model=ClinicalMdrRel)
    has_term = RelationshipTo("CTTermRoot", "HAS_TERM", model=CodelistTermRelationship)
    had_term = RelationshipTo("CTTermRoot", "HAD_TERM", model=CodelistTermRelationship)


class CTTermRoot(ControlledTerminologyWithUID):
    LIBRARY_REL_TYPE = "CONTAINS_TERM"
    has_name_root = RelationshipTo(
        CTTermNameRoot, "HAS_NAME_ROOT", model=ClinicalMdrRel
    )
    has_attributes_root = RelationshipTo(
        CTTermAttributesRoot, "HAS_ATTRIBUTES_ROOT", model=ClinicalMdrRel
    )
    has_library = RelationshipFrom(Library, LIBRARY_REL_TYPE)
    has_term = RelationshipFrom(
        CTCodelistRoot, "HAS_TERM", model=CodelistTermRelationship
    )
    had_term = RelationshipFrom(
        CTCodelistRoot, "HAD_TERM", model=CodelistTermRelationship
    )
    has_parent_type = RelationshipTo(
        "CTTermRoot", "HAS_PARENT_TYPE", model=ClinicalMdrRel
    )
    has_parent_subtype = RelationshipTo(
        "CTTermRoot", "HAS_PARENT_SUB_TYPE", model=ClinicalMdrRel
    )
    valid_for_epoch_type = RelationshipTo(
        "CTTermRoot", "VALID_FOR_EPOCH_TYPE", model=ClinicalMdrRel
    )


class CTCatalogue(ClinicalMdrNode):
    name = StringProperty()
    contains_package = RelationshipTo(
        CTPackage, "CONTAINS_PACKAGE", model=ClinicalMdrRel
    )
    has_codelist = RelationshipTo(CTCodelistRoot, "HAS_CODELIST", model=ClinicalMdrRel)
    contains_catalogue = RelationshipFrom(
        Library, "CONTAINS_CATALOGUE", model=ClinicalMdrRel
    )
