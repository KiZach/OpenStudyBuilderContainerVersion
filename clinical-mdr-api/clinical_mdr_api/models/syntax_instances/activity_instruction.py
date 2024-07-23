from datetime import datetime
from typing import Self

from pydantic import Field

from clinical_mdr_api.domains.syntax_instances.activity_instruction import (
    ActivityInstructionAR,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.syntax_templates.activity_instruction_template import (
    ActivityInstructionTemplateNameUidLibrary,
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


class ActivityInstructionNameUid(BaseModel):
    uid: str
    name: str | None = Field(None, nullable=True)
    name_plain: str | None = Field(None, nullable=True)


class ActivityInstruction(ActivityInstructionNameUid):
    start_date: datetime | None = Field(None, nullable=True)
    end_date: datetime | None = Field(None, nullable=True)
    status: str | None = Field(None, nullable=True)
    version: str | None = Field(None, nullable=True)
    change_description: str | None = Field(None, nullable=True)
    user_initials: str | None = Field(None, nullable=True)
    activity_instruction_template: ActivityInstructionTemplateNameUidLibrary | None
    parameter_terms: list[MultiTemplateParameterTerm] = Field(
        [],
        description="""Holds the parameter terms that are used within the activity
        instruction. The terms are ordered as they occur in the activity instruction name.""",
    )
    library: Library | None = Field(None, nullable=True)

    study_count: int = Field(
        0, description="Count of studies referencing activity instruction"
    )
    possible_actions: list[str] | None = Field(
        None,
        description=(
            "Holds those actions that can be performed on the endpoint. "
            "Actions are: 'approve', 'edit', 'inactivate', 'reactivate' and 'delete'."
        ),
    )

    @classmethod
    def from_activity_instruction_ar(
        cls, activity_instruction_ar: ActivityInstructionAR
    ) -> Self:
        parameter_terms: list[MultiTemplateParameterTerm] = []
        for position, parameter in enumerate(activity_instruction_ar.get_parameters()):
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
            uid=activity_instruction_ar.uid,
            name=capitalize_first_letter_if_template_parameter(
                activity_instruction_ar.name,
                activity_instruction_ar.template_name_plain,
                activity_instruction_ar._template.parameter_terms,
            ),
            name_plain=capitalize_first_letter_if_template_parameter(
                activity_instruction_ar.name_plain,
                activity_instruction_ar.template_name_plain,
                activity_instruction_ar._template.parameter_terms,
            ),
            start_date=activity_instruction_ar.item_metadata.start_date,
            end_date=activity_instruction_ar.item_metadata.end_date,
            status=activity_instruction_ar.item_metadata.status.value,
            version=activity_instruction_ar.item_metadata.version,
            change_description=activity_instruction_ar.item_metadata.change_description,
            user_initials=activity_instruction_ar.item_metadata.user_initials,
            activity_instruction_template=ActivityInstructionTemplateNameUidLibrary(
                name=activity_instruction_ar.template_name,
                name_plain=activity_instruction_ar.template_name_plain,
                uid=activity_instruction_ar.template_uid,
                sequence_id=activity_instruction_ar.template_sequence_id,
                library_name=activity_instruction_ar.template_library_name,
            ),
            library=Library.from_library_vo(activity_instruction_ar.library),
            study_count=activity_instruction_ar.study_count,
            parameter_terms=parameter_terms,
            possible_actions=sorted(
                {_.value for _ in activity_instruction_ar.get_possible_actions()}
            ),
        )


class ActivityInstructionVersion(ActivityInstruction):
    """
    Class for storing Activity Instructions and calculation of differences
    """

    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the activity instruction (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )


class ActivityInstructionParameterInput(BaseModel):
    parameter_terms: list[TemplateParameterMultiSelectInput] = Field(
        None,
        title="parameter_terms",
        description="An ordered list of selected parameter terms that are used to replace the parameters of the activity instruction template.",
    )


class ActivityInstructionEditInput(ActivityInstructionParameterInput):
    change_description: str = Field(
        ...,
        description="A short description about what has changed compared to the previous version.",
    )


class ActivityInstructionCreateInput(BaseModel):
    activity_instruction_template_uid: str = Field(
        ...,
        title="activity_instruction_template_uid",
        description="The unique id of the activity instruction template that is used as the basis for the new activity instruction.",
    )
    parameter_terms: list[TemplateParameterMultiSelectInput] = Field(
        ...,
        title="parameter_terms",
        description="An ordered list of selected parameter terms that are used to replace the parameters of the activity instruction template.",
    )
    library_name: str = Field(
        None,
        title="library_name",
        description="If specified: The name of the library to which the criteria will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* criteria can help. And \n"
        "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true. \n\n"
        "If not specified: The library of the criteria template will be used.",
        nullable=True,
    )
