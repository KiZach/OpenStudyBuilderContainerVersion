from neomodel import One, RelationshipTo, StringProperty, ZeroOrMore, ZeroOrOne

from clinical_mdr_api.domain_repositories.models.active_substance import (
    ActiveSubstanceRoot,
)
from clinical_mdr_api.domain_repositories.models.concepts import (
    ConceptRoot,
    ConceptValue,
    LagTimeRoot,
    NumericValueWithUnitRoot,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.dictionary import DictionaryTermRoot
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNode,
    ClinicalMdrRel,
    VersionRelationship,
)


class Ingredient(ClinicalMdrNode):
    external_id = StringProperty()

    has_substance = RelationshipTo(
        ActiveSubstanceRoot, "HAS_SUBSTANCE", cardinality=One, model=ClinicalMdrRel
    )
    has_strength_value = RelationshipTo(
        NumericValueWithUnitRoot,
        "HAS_STRENGTH_VALUE",
        cardinality=ZeroOrOne,
        model=ClinicalMdrRel,
    )
    has_half_life = RelationshipTo(
        NumericValueWithUnitRoot,
        "HAS_HALF_LIFE",
        cardinality=ZeroOrOne,
        model=ClinicalMdrRel,
    )
    has_lag_time = RelationshipTo(
        LagTimeRoot, "HAS_LAG_TIME", cardinality=ZeroOrMore, model=ClinicalMdrRel
    )


class IngredientFormulation(ClinicalMdrNode):
    external_id = StringProperty()
    name = StringProperty()

    has_ingredient = RelationshipTo(
        Ingredient, "HAS_INGREDIENT", cardinality=ZeroOrMore, model=ClinicalMdrRel
    )


class PharmaceuticalProductValue(ConceptValue):
    has_unii_value = RelationshipTo(
        DictionaryTermRoot,
        "HAS_UNII_VALUE",
        cardinality=ZeroOrOne,
        model=ClinicalMdrRel,
    )
    has_formulation = RelationshipTo(
        IngredientFormulation,
        "HAS_FORMULATION",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )
    has_dosage_form = RelationshipTo(
        CTTermRoot, "HAS_DOSAGE_FORM", cardinality=ZeroOrMore, model=ClinicalMdrRel
    )
    has_route_of_administration = RelationshipTo(
        CTTermRoot,
        "HAS_ROUTE_OF_ADMINISTRATION",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )


class PharmaceuticalProductRoot(ConceptRoot):
    has_version = RelationshipTo(
        PharmaceuticalProductValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        PharmaceuticalProductValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        PharmaceuticalProductValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        PharmaceuticalProductValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        PharmaceuticalProductValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )
