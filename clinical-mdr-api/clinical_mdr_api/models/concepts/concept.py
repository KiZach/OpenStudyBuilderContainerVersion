from abc import ABC
from datetime import datetime
from typing import Callable, Self

from pydantic import Field

from clinical_mdr_api.domains.concepts.simple_concepts.lag_time import LagTimeAR
from clinical_mdr_api.domains.concepts.simple_concepts.numeric_value import (
    NumericValueAR,
)
from clinical_mdr_api.domains.concepts.simple_concepts.numeric_value_with_unit import (
    NumericValueWithUnitAR,
)
from clinical_mdr_api.domains.concepts.simple_concepts.text_value import TextValueAR
from clinical_mdr_api.domains.concepts.simple_concepts.time_point import TimePointAR
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.models import _generic_descriptions
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel


class NoLibraryConceptModelNoName(BaseModel, ABC):
    start_date: datetime = Field(
        ...,
        title="endDate",
        description=_generic_descriptions.START_DATE,
        source="latest_version|start_date",
    )
    end_date: datetime | None = Field(
        None,
        title="endDate",
        description=_generic_descriptions.END_DATE,
        source="latest_version|end_date",
        nullable=True,
    )
    status: str
    version: str
    user_initials: str
    change_description: str
    uid: str


class NoLibraryConceptModel(NoLibraryConceptModelNoName):
    name: str


class NoLibraryConceptPostInput(BaseModel, ABC):
    name: str = Field(min_length=1)


class ConceptModel(NoLibraryConceptModel):
    library_name: str


class ConceptPostInput(NoLibraryConceptPostInput):
    library_name: str = "Sponsor"


class ConceptPatchInput(BaseModel, ABC):
    change_description: str
    name: str | None = None


class VersionProperties(BaseModel):
    start_date: datetime | None = Field(
        None,
        title="startDate",
        description=_generic_descriptions.START_DATE,
        source="latest_version|start_date",
        nullable=True,
    )
    end_date: datetime | None = Field(
        None,
        title="endDate",
        description=_generic_descriptions.END_DATE,
        source="latest_version|end_date",
        nullable=True,
    )
    status: str | None = Field(
        None,
        title="status",
        description="",
        source="latest_version|status",
        nullable=True,
    )
    version: str | None = Field(
        None,
        title="version",
        description="",
        source="latest_version|version",
        nullable=True,
    )
    change_description: str | None = Field(
        None,
        title="changeDescription",
        description="",
        source="latest_version|change_description",
        nullable=True,
    )
    user_initials: str | None = Field(
        None,
        title="userInitials",
        description="",
        source="latest_version|user_initials",
        nullable=True,
    )


class Concept(VersionProperties):
    class Config:
        orm_mode = True

    uid: str
    name: str = Field(
        ...,
        title="name",
        description="The name or the actual value. E.g. 'Systolic Blood Pressure', 'Body Temperature', 'Metformin', ...",
        source="has_latest_value.name",
    )
    name_sentence_case: str | None = Field(
        None,
        title="name_sentence_case",
        description="",
        source="has_latest_value.name_sentence_case",
        nullable=True,
    )
    definition: str | None = Field(
        None,
        title="definition",
        description="",
        source="has_latest_value.definition",
        nullable=True,
    )
    abbreviation: str | None = Field(
        None,
        title="abbreviation",
        description="",
        source="has_latest_value.abbreviation",
        nullable=True,
    )
    library_name: str = Field(
        ...,
        title="library_name",
        description="",
        source="has_library.name",
    )


class ConceptInput(BaseModel):
    name: str = Field(
        None,
        title="name",
        description="The name or the actual value. E.g. 'Systolic Blood Pressure', 'Body Temperature', 'Metformin', ...",
    )
    name_sentence_case: str | None = Field(
        None,
        title="name_sentence_case",
        description="",
    )
    definition: str | None = Field(
        None,
        title="definition",
        description="",
    )
    abbreviation: str | None = None
    library_name: str | None = None


class SimpleConcept(Concept):
    template_parameter: bool


class SimpleConceptInput(ConceptInput):
    template_parameter: bool | None = False


class TextValue(SimpleConcept):
    @classmethod
    def from_concept_ar(cls, text_value: TextValueAR) -> Self:
        return cls(
            uid=text_value.uid,
            library_name=Library.from_library_vo(text_value.library).name,
            name=text_value.concept_vo.name,
            name_sentence_case=text_value.concept_vo.name_sentence_case,
            definition=text_value.concept_vo.definition,
            abbreviation=text_value.concept_vo.abbreviation,
            template_parameter=text_value.concept_vo.is_template_parameter,
        )


class TextValueInput(SimpleConceptInput):
    name: str
    name_sentence_case: str | None = None


class VisitName(TextValue):
    pass


class VisitNameInput(TextValueInput):
    pass


class NumericValue(SimpleConcept):
    name: str
    value: float

    @classmethod
    def from_concept_ar(cls, numeric_value: NumericValueAR) -> Self:
        return cls(
            uid=numeric_value.uid,
            library_name=Library.from_library_vo(numeric_value.library).name,
            name=numeric_value.concept_vo.name,
            value=numeric_value.concept_vo.value,
            name_sentence_case=numeric_value.concept_vo.name_sentence_case,
            definition=numeric_value.concept_vo.definition,
            abbreviation=numeric_value.concept_vo.abbreviation,
            template_parameter=numeric_value.concept_vo.is_template_parameter,
        )


class NumericValueInput(SimpleConceptInput):
    value: float


class NumericValueWithUnit(NumericValue):
    unit_definition_uid: str
    unit_label: str

    @classmethod
    def from_concept_ar(
        cls,
        numeric_value: NumericValueWithUnitAR,
        find_unit_by_uid: Callable[[str], UnitDefinitionAR | None],
    ) -> Self:
        unit: UnitDefinitionAR = find_unit_by_uid(
            numeric_value.concept_vo.unit_definition_uid
        )
        return cls(
            uid=numeric_value.uid,
            library_name=Library.from_library_vo(numeric_value.library).name,
            name=numeric_value.concept_vo.name,
            value=numeric_value.concept_vo.value,
            name_sentence_case=numeric_value.concept_vo.name_sentence_case,
            definition=numeric_value.concept_vo.definition,
            abbreviation=numeric_value.concept_vo.abbreviation,
            template_parameter=numeric_value.concept_vo.is_template_parameter,
            unit_definition_uid=numeric_value.concept_vo.unit_definition_uid,
            unit_label=unit.concept_vo.name,
        )


class NumericValueWithUnitInput(NumericValueInput):
    unit_definition_uid: str


class SimpleNumericValueWithUnit(BaseModel):
    uid: str
    value: float
    unit_definition_uid: str
    unit_label: str

    @classmethod
    def from_concept_uid(
        cls,
        uid: str,
        find_unit_by_uid: Callable[[str], UnitDefinitionAR | None],
        find_numeric_value_by_uid: Callable[[str], NumericValueWithUnitAR | None],
    ) -> Self | None:
        concept = None
        if uid is not None:
            val: NumericValueWithUnitAR = find_numeric_value_by_uid(uid)

            if val is not None:
                unit: UnitDefinitionAR = find_unit_by_uid(
                    val.concept_vo.unit_definition_uid
                )

                concept = cls(
                    uid=val.uid,
                    unit_definition_uid=val.concept_vo.unit_definition_uid,
                    value=val.concept_vo.value,
                    unit_label=unit.concept_vo.name,
                )

        return concept


class LagTime(NumericValueWithUnit):
    sdtm_domain_uid: str

    @classmethod
    def from_concept_ar(
        cls,
        numeric_value: LagTimeAR,
        find_unit_by_uid: Callable[[str], UnitDefinitionAR | None],
    ) -> Self:
        unit: UnitDefinitionAR = find_unit_by_uid(
            numeric_value.concept_vo.unit_definition_uid
        )
        return cls(
            uid=numeric_value.uid,
            library_name=Library.from_library_vo(numeric_value.library).name,
            name=numeric_value.concept_vo.name,
            value=numeric_value.concept_vo.value,
            name_sentence_case=numeric_value.concept_vo.name_sentence_case,
            definition=numeric_value.concept_vo.definition,
            abbreviation=numeric_value.concept_vo.abbreviation,
            template_parameter=numeric_value.concept_vo.is_template_parameter,
            unit_definition_uid=numeric_value.concept_vo.unit_definition_uid,
            unit_label=unit.concept_vo.name,
            sdtm_domain_uid=numeric_value.concept_vo.sdtm_domain_uid,
        )


class LagTimeInput(NumericValueWithUnitInput):
    sdtm_domain_uid: str


class SimpleLagTime(BaseModel):
    value: float
    unit_definition_uid: str
    unit_label: str
    sdtm_domain_uid: str
    sdtm_domain_label: str

    @classmethod
    def from_concept_uid(
        cls,
        uid: str,
        find_unit_by_uid: Callable[[str], UnitDefinitionAR | None],
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
        find_lag_time_by_uid: Callable[[str], LagTimeAR | None],
    ) -> Self | None:
        concept = None
        if uid is not None:
            val: LagTimeAR = find_lag_time_by_uid(uid)

            if val is not None:
                unit: UnitDefinitionAR = find_unit_by_uid(
                    val.concept_vo.unit_definition_uid
                )

                sdtm_domain: CTTermNameAR = find_term_by_uid(
                    val.concept_vo.sdtm_domain_uid
                )

                concept = cls(
                    value=val.concept_vo.value,
                    unit_definition_uid=val.concept_vo.unit_definition_uid,
                    unit_label=unit.concept_vo.name,
                    sdtm_domain_uid=val.concept_vo.sdtm_domain_uid,
                    sdtm_domain_label=sdtm_domain.ct_term_vo.name,
                )

        return concept


class TimePoint(SimpleConcept):
    numeric_value_uid: str
    unit_definition_uid: str
    time_reference_uid: str

    @classmethod
    def from_concept_ar(cls, time_point: TimePointAR) -> Self:
        return cls(
            uid=time_point.uid,
            library_name=Library.from_library_vo(time_point.library).name,
            name=time_point.concept_vo.name,
            name_sentence_case=time_point.concept_vo.name_sentence_case,
            definition=time_point.concept_vo.definition,
            abbreviation=time_point.concept_vo.abbreviation,
            template_parameter=time_point.concept_vo.is_template_parameter,
            numeric_value_uid=time_point.concept_vo.numeric_value_uid,
            unit_definition_uid=time_point.concept_vo.unit_definition_uid,
            time_reference_uid=time_point.concept_vo.time_reference_uid,
        )


class TimePointInput(SimpleConceptInput):
    name_sentence_case: str | None = Field(
        None,
        title="name_sentence_case",
        description="",
    )
    numeric_value_uid: str
    unit_definition_uid: str
    time_reference_uid: str
