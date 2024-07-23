from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Self

from clinical_mdr_api import exceptions
from clinical_mdr_api.domains.concepts.simple_concepts.numeric_value_with_unit import (
    NumericValueWithUnitAR,
    NumericValueWithUnitVO,
)
from clinical_mdr_api.domains.concepts.simple_concepts.simple_concept import (
    SimpleConceptVO,
)
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)


@dataclass(frozen=True)
class LagTimeVO(NumericValueWithUnitVO):
    sdtm_domain_uid: str

    @classmethod
    def derive_value_property(cls, value):
        return int(value) if value.is_integer() else value

    @classmethod
    def from_repository_values(
        cls,
        value: float,
        definition: str | None,
        abbreviation: str | None,
        is_template_parameter: bool,
        unit_definition_uid: str,
        sdtm_domain_uid: str,
    ) -> Self:
        value = cls.derive_value_property(value=value)
        simple_concept_vo = cls(
            name=str(value),
            value=value,
            name_sentence_case=str(value).lower(),
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=is_template_parameter,
            unit_definition_uid=unit_definition_uid,
            sdtm_domain_uid=sdtm_domain_uid,
        )

        return simple_concept_vo

    @classmethod
    def from_input_values(
        cls,
        value: float,
        definition: str | None,
        abbreviation: str | None,
        is_template_parameter: bool,
        find_unit_definition_by_uid: Callable[[str], UnitDefinitionAR],
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
        unit_definition_uid: str,
        sdtm_domain_uid: str,
    ) -> Self:
        unit_definition = find_unit_definition_by_uid(unit_definition_uid)
        if unit_definition is None:
            raise exceptions.ValidationException(
                f"{cls.__name__} tried to connect to non-existent unit definition identified by uid ({unit_definition_uid})"
            )

        sdtm_domain = find_term_by_uid(sdtm_domain_uid)
        if sdtm_domain is None:
            raise exceptions.ValidationException(
                f"{cls.__name__} tried to connect to non-existent sdtm domain identified by uid ({sdtm_domain_uid})"
            )
        value = cls.derive_value_property(value=value)
        simple_concept_vo = cls(
            name=f"{value} [{unit_definition_uid}] for SDTM domain [{sdtm_domain_uid}]",
            value=value,
            name_sentence_case=str(value).lower(),
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=is_template_parameter,
            unit_definition_uid=unit_definition_uid,
            sdtm_domain_uid=sdtm_domain_uid,
        )

        return simple_concept_vo


class LagTimeAR(NumericValueWithUnitAR):
    _concept_vo: LagTimeVO

    @property
    def concept_vo(self) -> LagTimeVO:
        return self._concept_vo

    @classmethod
    def from_input_values(
        cls,
        *,
        author: str,
        simple_concept_vo: SimpleConceptVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str | None] = (lambda: None),
        find_uid_by_value_unit_and_domain_callback: Callable[
            [str, str, str], str | None
        ]
        | None = None,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO(
            _change_description="Initial version",
            _status=LibraryItemStatus.FINAL,
            _author=author,
            _start_date=datetime.now(timezone.utc),
            _end_date=None,
            _major_version=1,
            _minor_version=0,
        )

        if not library.is_editable:
            raise exceptions.BusinessLogicException(
                f"The library with the name='{library.name}' does not allow to create objects."
            )

        # Check whether simple concept with the same value/unit/domain already exists. If yes, return its uid, otherwise None.
        simple_concept_uid = find_uid_by_value_unit_and_domain_callback(
            getattr(simple_concept_vo, "value", None),
            getattr(simple_concept_vo, "unit_definition_uid", None),
            getattr(simple_concept_vo, "sdtm_domain_uid", None),
        )

        simple_concept_ar = cls(
            _uid=generate_uid_callback()
            if simple_concept_uid is None
            else simple_concept_uid,
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=simple_concept_vo,
        )
        return simple_concept_ar
