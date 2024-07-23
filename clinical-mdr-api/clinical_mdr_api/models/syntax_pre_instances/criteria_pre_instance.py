from datetime import datetime
from typing import Self

from pydantic import Field

from clinical_mdr_api.domains.syntax_pre_instances.criteria_pre_instance import (
    CriteriaPreInstanceAR,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameAndAttributes,
    SimpleTermModel,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.syntax_pre_instances.generic_pre_instance import (
    PreInstanceInput,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    IndexedTemplateParameterTerm,
    MultiTemplateParameterTerm,
)
from clinical_mdr_api.models.utils import (
    BaseModel,
    capitalize_first_letter_if_template_parameter,
)


class CriteriaPreInstance(BaseModel):
    uid: str
    sequence_id: str | None = Field(None, nullable=True)
    template_uid: str
    template_name: str
    template_type_uid: str | None = Field(None, nullable=True)
    guidance_text: str | None = Field(None, nullable=True)
    name: str | None = Field(None, nullable=True)
    name_plain: str | None = Field(None, nullable=True)
    start_date: datetime | None = Field(None, nullable=True)
    end_date: datetime | None = Field(None, nullable=True)
    status: str | None = Field(None, nullable=True)
    version: str | None = Field(None, nullable=True)
    change_description: str | None = Field(None, nullable=True)
    user_initials: str | None = Field(None, nullable=True)
    parameter_terms: list[MultiTemplateParameterTerm] = Field(
        [],
        description="Holds the parameter terms that are used within the criteria. The terms are ordered as they occur in the criteria name.",
    )
    indications: list[SimpleTermModel] = Field(
        [],
        description="The study indications, conditions, diseases or disorders in scope for the pre-instance.",
    )
    categories: list[SimpleCTTermNameAndAttributes] = Field(
        [], description="A list of categories the pre-instance belongs to."
    )
    sub_categories: list[SimpleCTTermNameAndAttributes] = Field(
        [], description="A list of sub-categories the pre-instance belongs to."
    )
    library: Library | None = Field(None, nullable=True)
    possible_actions: list[str] = Field([])

    @classmethod
    def from_criteria_pre_instance_ar(
        cls, criteria_pre_instance_ar: CriteriaPreInstanceAR
    ) -> Self:
        parameter_terms: list[MultiTemplateParameterTerm] = []
        for position, parameter in enumerate(criteria_pre_instance_ar.get_parameters()):
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
            uid=criteria_pre_instance_ar.uid,
            sequence_id=criteria_pre_instance_ar.sequence_id,
            template_uid=criteria_pre_instance_ar.template_uid,
            template_name=criteria_pre_instance_ar.template_name,
            template_type_uid=criteria_pre_instance_ar.type.term_uid,
            name=capitalize_first_letter_if_template_parameter(
                criteria_pre_instance_ar.name,
                criteria_pre_instance_ar.template_name_plain,
                criteria_pre_instance_ar._template.parameter_terms,
            ),
            name_plain=capitalize_first_letter_if_template_parameter(
                criteria_pre_instance_ar.name_plain,
                criteria_pre_instance_ar.template_name_plain,
                criteria_pre_instance_ar._template.parameter_terms,
            ),
            guidance_text=(
                criteria_pre_instance_ar._template.guidance_text
                if criteria_pre_instance_ar.guidance_text is None
                else criteria_pre_instance_ar.guidance_text
            ),
            start_date=criteria_pre_instance_ar.item_metadata.start_date,
            end_date=criteria_pre_instance_ar.item_metadata.end_date,
            status=criteria_pre_instance_ar.item_metadata.status.value,
            version=criteria_pre_instance_ar.item_metadata.version,
            change_description=criteria_pre_instance_ar.item_metadata.change_description,
            user_initials=criteria_pre_instance_ar.item_metadata.user_initials,
            library=Library.from_library_vo(criteria_pre_instance_ar.library),
            parameter_terms=parameter_terms,
            indications=criteria_pre_instance_ar.indications,
            categories=criteria_pre_instance_ar.categories,
            sub_categories=criteria_pre_instance_ar.sub_categories,
            possible_actions=sorted(
                {_.value for _ in criteria_pre_instance_ar.get_possible_actions()}
            ),
        )


class CriteriaPreInstanceIndexingsInput(BaseModel):
    indication_uids: list[str] | None = Field(
        None,
        description="A list of UID of the study indications, conditions, diseases or disorders to attach the pre-instance to.",
    )
    category_uids: list[str] | None = Field(
        None,
        description="A list of UID of the categories to attach the pre-instance to.",
    )
    sub_category_uids: list[str] | None = Field(
        None,
        description="A list of UID of the sub_categories to attach the pre-instance to.",
    )


class CriteriaPreInstanceCreateInput(PreInstanceInput):
    indication_uids: list[str]
    category_uids: list[str]
    sub_category_uids: list[str]


class CriteriaPreInstanceEditInput(PreInstanceInput):
    guidance_text: str | None = Field(
        None,
        description="Guidance text or None. If None is provided then the value will be inherited from the parent template.",
        nullable=True,
    )
    change_description: str = Field(
        ...,
        description="A short description about what has changed compared to the previous version.",
    )


class CriteriaPreInstanceVersion(CriteriaPreInstance):
    """
    Class for storing Criteria Pre-Instances and calculation of differences
    """

    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the criteria (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )
