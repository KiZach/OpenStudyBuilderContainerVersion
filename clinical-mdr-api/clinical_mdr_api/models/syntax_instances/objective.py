from datetime import datetime
from typing import Self

from pydantic import Field

from clinical_mdr_api.domains.syntax_instances.objective import ObjectiveAR
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.syntax_templates.objective_template import (
    ObjectiveTemplateNameUidLibrary,
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


class Objective(BaseModel):
    uid: str
    name: str | None = Field(None, nullable=True)
    name_plain: str | None = Field(None, nullable=True)

    start_date: datetime | None = Field(None, nullable=True)
    end_date: datetime | None = Field(None, nullable=True)
    status: str | None = Field(None, nullable=True)
    version: str | None = Field(None, nullable=True)
    change_description: str | None = Field(None, nullable=True)
    user_initials: str | None = Field(None, nullable=True)

    possible_actions: list[str] = Field(
        [],
        description=(
            "Holds those actions that can be performed on the objective. "
            "Actions are: 'approve', 'edit', 'inactivate', 'reactivate' and 'delete'."
        ),
    )

    objective_template: ObjectiveTemplateNameUidLibrary | None
    parameter_terms: list[MultiTemplateParameterTerm] = Field(
        [],
        description="Holds the parameter terms that are used within the objective. The terms are ordered as they occur in the objective name.",
    )
    library: Library | None = Field(None, nullable=True)

    study_count: int = Field(0, description="Count of studies referencing objective")

    @classmethod
    def from_objective_ar(cls, objective_ar: ObjectiveAR) -> Self:
        parameter_terms: list[MultiTemplateParameterTerm] = []
        for position, parameter in enumerate(objective_ar.get_parameters()):
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
            uid=objective_ar.uid,
            name=capitalize_first_letter_if_template_parameter(
                objective_ar.name,
                objective_ar.template_name_plain,
                objective_ar._template.parameter_terms,
            ),
            name_plain=capitalize_first_letter_if_template_parameter(
                objective_ar.name_plain,
                objective_ar.template_name_plain,
                objective_ar._template.parameter_terms,
            ),
            start_date=objective_ar.item_metadata.start_date,
            end_date=objective_ar.item_metadata.end_date,
            status=objective_ar.item_metadata.status.value,
            version=objective_ar.item_metadata.version,
            change_description=objective_ar.item_metadata.change_description,
            user_initials=objective_ar.item_metadata.user_initials,
            possible_actions=sorted(
                {_.value for _ in objective_ar.get_possible_actions()}
            ),
            objective_template=ObjectiveTemplateNameUidLibrary(
                name=objective_ar.template_name,
                name_plain=objective_ar.template_name_plain,
                uid=objective_ar.template_uid,
                sequence_id=objective_ar.template_sequence_id,
                library_name=objective_ar.template_library_name,
            ),
            library=Library.from_library_vo(objective_ar.library),
            study_count=objective_ar.study_count,
            parameter_terms=parameter_terms,
        )


class ObjectiveVersion(Objective):
    """
    Class for storing Objectives and calculation of differences
    """

    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )


class ObjectiveParameterInput(BaseModel):
    parameter_terms: list[TemplateParameterMultiSelectInput] = Field(
        None,
        title="parameter_terms",
        description="An ordered list of selected parameter terms that are used to replace the parameters of the objective template.",
    )


class ObjectiveEditInput(ObjectiveParameterInput):
    change_description: str = Field(
        ...,
        description="A short description about what has changed compared to the previous version.",
    )


class ObjectiveCreateInput(ObjectiveParameterInput):
    objective_template_uid: str = Field(
        ...,
        title="objective_template_uid",
        description="The unique id of the objective template that is used as the basis for the new objective.",
    )
    library_name: str = Field(
        None,
        title="library_name",
        description="If specified: The name of the library to which the objective will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
        "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true. \n\n"
        "If not specified: The library of the objective template will be used.",
    )
