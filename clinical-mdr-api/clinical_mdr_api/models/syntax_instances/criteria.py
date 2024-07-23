from datetime import datetime
from typing import Self

from pydantic.fields import Field

from clinical_mdr_api.domains.syntax_instances.criteria import CriteriaAR
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameAndAttributes,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.syntax_templates.criteria_template import (
    CriteriaTemplateNameUidLibrary,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_multi_select_input import (
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    IndexedTemplateParameterTerm,
    MultiTemplateParameterTerm,
)
from clinical_mdr_api.models.utils import (
    BaseModel,
    capitalize_first_letter_if_template_parameter,
)


class CriteriaTemplateWithType(CriteriaTemplateNameUidLibrary):
    type: SimpleCTTermNameAndAttributes | None


class Criteria(BaseModel):
    uid: str
    name: str | None = Field(None, nullable=True)
    name_plain: str | None = Field(None, nullable=True)

    start_date: datetime | None = Field(None, nullable=True)
    end_date: datetime | None = Field(None, nullable=True)
    status: str | None = Field(None, nullable=True)
    version: str | None = Field(None, nullable=True)
    change_description: str | None = Field(None, nullable=True)
    user_initials: str | None = Field(None, nullable=True)

    possible_actions: list[str] | None = Field(
        None,
        description=(
            "Holds those actions that can be performed on the criteria. "
            "Actions are: None"
        ),
    )

    criteria_template: CriteriaTemplateNameUidLibrary | None
    parameter_terms: list[MultiTemplateParameterTerm] | None = Field(
        None,
        description="Holds the parameter terms that are used within the criteria. The terms are ordered as they occur in the criteria name.",
    )
    library: Library | None = None

    study_count: int = Field(0, description="Count of studies referencing criteria")

    @classmethod
    def from_criteria_ar(
        cls,
        criteria_ar: CriteriaAR,
    ) -> Self:
        parameter_terms: list[MultiTemplateParameterTerm] = []
        for position, parameter in enumerate(criteria_ar.get_parameters()):
            terms: list[IndexedTemplateParameterTerm] = []
            for index, parameter_term in enumerate(parameter.parameters):
                indexed_template_parameter_term = IndexedTemplateParameterTerm(
                    index=index + 1,
                    uid=parameter_term.uid,
                    name=parameter_term.value,
                    type=parameter.parameter_name,
                )
                terms.append(indexed_template_parameter_term)
            conjunction = parameter.conjunction

            parameter_terms.append(
                MultiTemplateParameterTerm(
                    conjunction=conjunction, position=position + 1, terms=terms
                )
            )
        return cls(
            uid=criteria_ar.uid,
            name=capitalize_first_letter_if_template_parameter(
                criteria_ar.name,
                criteria_ar.template_name_plain,
                criteria_ar._template.parameter_terms,
            ),
            name_plain=capitalize_first_letter_if_template_parameter(
                criteria_ar.name_plain,
                criteria_ar.template_name_plain,
                criteria_ar._template.parameter_terms,
            ),
            start_date=criteria_ar.item_metadata.start_date,
            end_date=criteria_ar.item_metadata.end_date,
            status=criteria_ar.item_metadata.status.value,
            version=criteria_ar.item_metadata.version,
            change_description=criteria_ar.item_metadata.change_description,
            user_initials=criteria_ar.item_metadata.user_initials,
            possible_actions=sorted(
                {_.value for _ in criteria_ar.get_possible_actions()}
            ),
            criteria_template=CriteriaTemplateNameUidLibrary(
                name=criteria_ar.template_name,
                name_plain=criteria_ar.template_name_plain,
                uid=criteria_ar.template_uid,
                sequence_id=criteria_ar.template_sequence_id,
                guidance_text=criteria_ar.guidance_text,
                library_name=criteria_ar.template_library_name,
            ),
            library=Library.from_library_vo(criteria_ar.library),
            study_count=criteria_ar.study_count,
            parameter_terms=parameter_terms,
        )


class CriteriaWithType(Criteria):
    criteria_template: CriteriaTemplateWithType | None

    @classmethod
    def from_criteria_ar(cls, criteria_ar: CriteriaAR) -> Self:
        parameter_terms: list[MultiTemplateParameterTerm] = []
        for position, parameter in enumerate(criteria_ar.get_parameters()):
            terms: list[IndexedTemplateParameterTerm] = []
            for index, parameter_term in enumerate(parameter.parameters):
                indexed_template_parameter_term = IndexedTemplateParameterTerm(
                    index=index + 1,
                    uid=parameter_term.uid,
                    name=parameter_term.value,
                    type=parameter.parameter_name,
                )
                terms.append(indexed_template_parameter_term)
            conjunction = parameter.conjunction

            parameter_terms.append(
                MultiTemplateParameterTerm(
                    conjunction=conjunction, position=position + 1, terms=terms
                )
            )
        return cls(
            uid=criteria_ar.uid,
            name=capitalize_first_letter_if_template_parameter(
                criteria_ar.name,
                criteria_ar.template_name_plain,
                criteria_ar._template.parameter_terms,
            ),
            name_plain=capitalize_first_letter_if_template_parameter(
                criteria_ar.name_plain,
                criteria_ar.template_name_plain,
                criteria_ar._template.parameter_terms,
            ),
            start_date=criteria_ar.item_metadata.start_date,
            end_date=criteria_ar.item_metadata.end_date,
            status=criteria_ar.item_metadata.status.value,
            version=criteria_ar.item_metadata.version,
            change_description=criteria_ar.item_metadata.change_description,
            user_initials=criteria_ar.item_metadata.user_initials,
            possible_actions=sorted(
                {_.value for _ in criteria_ar.get_possible_actions()}
            ),
            criteria_template=CriteriaTemplateWithType(
                name=criteria_ar.template_name,
                name_plain=criteria_ar.template_name_plain,
                uid=criteria_ar.template_uid,
                sequence_id=criteria_ar.template_sequence_id,
                guidance_text=criteria_ar.guidance_text,
                type=criteria_ar._template.template_type,
                library_name=criteria_ar.template_library_name,
            ),
            library=Library.from_library_vo(criteria_ar.library),
            study_count=criteria_ar.study_count,
            parameter_terms=parameter_terms,
        )


class CriteriaVersion(CriteriaWithType):
    """
    Class for storing Criteria and calculation of differences
    """

    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the criteria (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )


class CriteriaParameterInput(BaseModel):
    parameter_terms: list[TemplateParameterMultiSelectInput] = Field(
        ...,
        title="parameter_terms",
        description="An ordered list of selected parameter terms that are used to replace the parameters of the criteria template.",
    )


class CriteriaEditInput(CriteriaParameterInput):
    change_description: str = Field(
        ...,
        description="A short description about what has changed compared to the previous version.",
    )


class CriteriaCreateInput(CriteriaParameterInput):
    criteria_template_uid: str = Field(
        ...,
        title="criteria_template_uid",
        description="The unique id of the criteria template that is used as the basis for the new criteria.",
    )
    library_name: str = Field(
        None,
        title="library_name",
        description="If specified: The name of the library to which the criteria will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* criteria can help. And \n"
        "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true. \n\n"
        "If not specified: The library of the criteria template will be used.",
    )


class CriteriaUpdateWithCriteriaKeyInput(CriteriaParameterInput):
    criteria_template_uid: str = Field(
        ...,
        title="criteria_template_uid",
        description="The unique id of the criteria template that is used as the basis for the new criteria.",
    )
    library_name: str = Field(
        None,
        title="library_name",
        description="If specified: The name of the library to which the criteria will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* criteria can help. And \n"
        "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true. \n\n"
        "If not specified: The library of the criteria template will be used.",
    )
    key_criteria: bool = Field(
        ...,
        title="key_criteria",
        description="New value to set for the key_criteria property of the selection",
    )
