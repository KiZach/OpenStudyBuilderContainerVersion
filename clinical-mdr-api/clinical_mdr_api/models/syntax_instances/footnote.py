from datetime import datetime
from typing import Any, Callable, Self

from pydantic.fields import Field

from clinical_mdr_api.domain_repositories.models.syntax import FootnoteTemplateRoot
from clinical_mdr_api.domains.syntax_instances.footnote import FootnoteAR
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    CTTermNameAndAttributes,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.syntax_templates.footnote_template import (
    FootnoteTemplateNameUidLibrary,
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


class FootnoteTemplateWithType(FootnoteTemplateNameUidLibrary):
    type: CTTermNameAndAttributes | None = Field(None)


class Footnote(BaseModel):
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
            "Holds those actions that can be performed on the footnote. "
            "Actions are: None"
        ),
        remove_from_wildcard=True,
        exclude_from_orm=True,
    )
    footnote_template: FootnoteTemplateWithType | None
    parameter_terms: list[MultiTemplateParameterTerm] | None = Field(
        None,
        description="Holds the parameter terms that are used within the footnote. The terms are ordered as they occur in the footnote name.",
    )
    library: Library | None = None
    study_count: int = Field(0, description="Count of studies referencing footnote")

    @classmethod
    def from_footnote_ar(
        cls,
        footnote_ar: FootnoteAR,
    ) -> Self:
        parameter_terms: list[MultiTemplateParameterTerm] = []
        for position, parameter in enumerate(footnote_ar.get_parameters()):
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
            uid=footnote_ar.uid,
            name=capitalize_first_letter_if_template_parameter(
                footnote_ar.name,
                footnote_ar.template_name_plain,
                footnote_ar._template.parameter_terms,
            ),
            name_plain=capitalize_first_letter_if_template_parameter(
                footnote_ar.name_plain,
                footnote_ar.template_name_plain,
                footnote_ar._template.parameter_terms,
            ),
            start_date=footnote_ar.item_metadata.start_date,
            end_date=footnote_ar.item_metadata.end_date,
            status=footnote_ar.item_metadata.status.value,
            version=footnote_ar.item_metadata.version,
            change_description=footnote_ar.item_metadata.change_description,
            user_initials=footnote_ar.item_metadata.user_initials,
            possible_actions=sorted(
                {_.value for _ in footnote_ar.get_possible_actions()}
            ),
            footnote_template=FootnoteTemplateWithType(
                name=footnote_ar.template_name,
                name_plain=footnote_ar.name_plain,
                uid=footnote_ar.template_uid,
                sequence_id=footnote_ar.template_sequence_id,
                library_name=footnote_ar.template_library_name,
            ),
            library=Library.from_library_vo(footnote_ar.library),
            study_count=footnote_ar.study_count,
            parameter_terms=parameter_terms,
        )


class FootnoteWithType(Footnote):
    footnote_template: FootnoteTemplateWithType | None

    @classmethod
    def from_footnote_ar(
        cls,
        footnote_ar: FootnoteAR,
        syntax_template_node: FootnoteTemplateRoot,
        get_footnote_type_name: Callable[[str], Any],
        get_footnote_type_attributes: Callable[[str], Any],
    ) -> Self:
        parameter_terms: list[MultiTemplateParameterTerm] = []
        for position, parameter in enumerate(footnote_ar.get_parameters()):
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
            uid=footnote_ar.uid,
            name=capitalize_first_letter_if_template_parameter(
                footnote_ar.name,
                footnote_ar.template_name_plain,
                footnote_ar._template.parameter_terms,
            ),
            name_plain=capitalize_first_letter_if_template_parameter(
                footnote_ar.name_plain,
                footnote_ar.template_name_plain,
                footnote_ar._template.parameter_terms,
            ),
            start_date=footnote_ar.item_metadata.start_date,
            end_date=footnote_ar.item_metadata.end_date,
            status=footnote_ar.item_metadata.status.value,
            version=footnote_ar.item_metadata.version,
            change_description=footnote_ar.item_metadata.change_description,
            user_initials=footnote_ar.item_metadata.user_initials,
            possible_actions=sorted(
                {_.value for _ in footnote_ar.get_possible_actions()}
            ),
            footnote_template=FootnoteTemplateWithType(
                name=footnote_ar.template_name,
                name_plain=footnote_ar.name_plain,
                uid=footnote_ar.template_uid,
                sequence_id=footnote_ar.template_sequence_id,
                type=CTTermNameAndAttributes.from_ct_term_ars(
                    ct_term_name_ar=get_footnote_type_name(syntax_template_node),
                    ct_term_attributes_ar=get_footnote_type_attributes(
                        syntax_template_node
                    ),
                ),
                library_name=footnote_ar.template_library_name,
            ),
            library=Library.from_library_vo(footnote_ar.library),
            study_count=footnote_ar.study_count,
            parameter_terms=parameter_terms,
        )


class FootnoteVersion(FootnoteWithType):
    """
    Class for storing Footnote and calculation of differences
    """

    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the footnote (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )


class FootnoteParameterInput(BaseModel):
    parameter_terms: list[TemplateParameterMultiSelectInput] = Field(
        ...,
        title="parameter_terms",
        description="An ordered list of selected parameter terms that are used to replace the parameters of the footnote template.",
    )


class FootnoteEditInput(FootnoteParameterInput):
    change_description: str = Field(
        ...,
        description="A short description about what has changed compared to the previous version.",
    )


class FootnoteCreateInput(FootnoteParameterInput):
    footnote_template_uid: str = Field(
        ...,
        title="footnote_template_uid",
        description="The unique id of the footnote template that is used as the basis for the new footnote.",
    )
    library_name: str = Field(
        None,
        title="library_name",
        description="If specified: The name of the library to which the footnote will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* footnote can help. And \n"
        "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true. \n\n"
        "If not specified: The library of the footnote template will be used.",
    )
