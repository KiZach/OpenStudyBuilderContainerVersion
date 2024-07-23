from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api import exceptions
from clinical_mdr_api.domains.concepts.simple_concepts.numeric_value import (
    NumericValueAR,
)
from clinical_mdr_api.domains.concepts.simple_concepts.simple_concept import (
    SimpleConceptAR,
    SimpleConceptVO,
)
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR


@dataclass(frozen=True)
class TimePointVO(SimpleConceptVO):
    unit_definition_uid: str
    numeric_value_uid: str
    time_reference_uid: str

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        name_sentence_case: str | None,
        definition: str | None,
        abbreviation: str | None,
        is_template_parameter: bool,
        unit_definition_uid: str,
        numeric_value_uid: str,
        time_reference_uid: str,
    ) -> Self:
        simple_concept_vo = cls(
            name=name,
            name_sentence_case=name_sentence_case,
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=is_template_parameter,
            unit_definition_uid=unit_definition_uid,
            numeric_value_uid=numeric_value_uid,
            time_reference_uid=time_reference_uid,
        )

        return simple_concept_vo

    @classmethod
    def from_input_values(
        cls,
        name_sentence_case: str | None,
        definition: str | None,
        abbreviation: str | None,
        is_template_parameter: bool,
        unit_definition_uid: str,
        numeric_value_uid: str,
        time_reference_uid: str,
        find_numeric_value_by_uid: Callable[[str], NumericValueAR],
        find_unit_definition_by_uid: Callable[[str], UnitDefinitionAR],
        find_time_reference_by_uid: Callable[[str], CTTermNameAR],
    ) -> Self:
        numeric_value = find_numeric_value_by_uid(numeric_value_uid)
        if numeric_value is None:
            raise exceptions.ValidationException(
                f"{cls.__name__} tried to connect to non-existent numeric value identified by uid ({numeric_value_uid})"
            )

        unit_definition = find_unit_definition_by_uid(unit_definition_uid)
        if unit_definition is None:
            raise exceptions.ValidationException(
                f"{cls.__name__} tried to connect to non-existent unit definition identified by uid ({unit_definition_uid})"
            )

        time_reference = find_time_reference_by_uid(time_reference_uid)
        if time_reference is None:
            raise exceptions.ValidationException(
                f"{cls.__name__} tried to connect to non-existent CTTermRoot identified by uid ({time_reference_uid})"
            )

        simple_concept_vo = cls(
            name=f"{numeric_value.name} {unit_definition.name} after {time_reference.name}",
            name_sentence_case=name_sentence_case,
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=is_template_parameter,
            unit_definition_uid=unit_definition_uid,
            numeric_value_uid=numeric_value_uid,
            time_reference_uid=time_reference_uid,
        )

        return simple_concept_vo


class TimePointAR(SimpleConceptAR):
    _concept_vo: TimePointVO
