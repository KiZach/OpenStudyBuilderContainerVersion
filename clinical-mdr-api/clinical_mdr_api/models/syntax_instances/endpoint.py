from datetime import datetime
from typing import Self

from pydantic import Field

from clinical_mdr_api.domains.syntax_instances.endpoint import EndpointAR
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.syntax_templates.endpoint_template import (
    EndpointTemplateNameUidLibrary,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_multi_select_input import (
    IndexedTemplateParameterTerm,
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    MultiTemplateParameterTerm,
)
from clinical_mdr_api.models.utils import (
    BaseModel,
    capitalize_first_letter_if_template_parameter,
)


class Endpoint(BaseModel):
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
            "Holds those actions that can be performed on the endpoint. "
            "Actions are: 'approve', 'edit', 'inactivate', 'reactivate' and 'delete'."
        ),
    )

    endpoint_template: EndpointTemplateNameUidLibrary | None
    parameter_terms: list[MultiTemplateParameterTerm] | None = Field(
        None,
        description="Holds the parameter terms that are used within the endpoint. The terms are ordered as they occur in the endpoint name.",
    )
    # objective: Objective | None= None
    library: Library | None = Field(None, nullable=True)

    study_count: int = Field(0, description="Count of studies referencing endpoint")

    @classmethod
    def from_endpoint_ar(cls, endpoint_ar: EndpointAR) -> Self:
        parameter_terms: list[MultiTemplateParameterTerm] = []
        for position, parameter in enumerate(endpoint_ar.get_parameters()):
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
            uid=endpoint_ar.uid,
            name=capitalize_first_letter_if_template_parameter(
                endpoint_ar.name,
                endpoint_ar.template_name_plain,
                endpoint_ar._template.parameter_terms,
            ),
            name_plain=capitalize_first_letter_if_template_parameter(
                endpoint_ar.name_plain,
                endpoint_ar.template_name_plain,
                endpoint_ar._template.parameter_terms,
            ),
            start_date=endpoint_ar.item_metadata.start_date,
            end_date=endpoint_ar.item_metadata.end_date,
            status=endpoint_ar.item_metadata.status.value,
            version=endpoint_ar.item_metadata.version,
            change_description=endpoint_ar.item_metadata.change_description,
            user_initials=endpoint_ar.item_metadata.user_initials,
            possible_actions=sorted(
                {_.value for _ in endpoint_ar.get_possible_actions()}
            ),
            endpoint_template=EndpointTemplateNameUidLibrary(
                name=endpoint_ar.template_name,
                name_plain=endpoint_ar.template_name_plain,
                uid=endpoint_ar.template_uid,
                sequence_id=endpoint_ar.template_sequence_id,
                library_name=endpoint_ar.template_library_name,
            ),
            library=Library.from_library_vo(endpoint_ar.library),
            study_count=endpoint_ar.study_count,
            parameter_terms=parameter_terms,
        )


class EndpointVersion(Endpoint):
    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the endpoint (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )


class EndpointParameterInput(BaseModel):
    parameter_terms: list[TemplateParameterMultiSelectInput] = Field(
        ...,
        title="parameter_terms",
        description="An ordered list of selected parameter terms that are used to replace the parameters of the endpoint template.",
    )


class EndpointEditInput(EndpointParameterInput):
    change_description: str = Field(
        ...,
        description="A short description about what has changed compared to the previous version.",
    )


class EndpointCreateInput(EndpointParameterInput):
    endpoint_template_uid: str = Field(
        ...,
        title="endpoint_template_uid",
        description="The unique id of the endpoint template that is used as the basis for the new endpoint.",
    )
    library_name: str = Field(
        None,
        title="library_name",
        description="If specified: The name of the library to which the endpoint will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
        "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true. \n\n"
        "If not specified: The library of the endpoint template will be used.",
    )
