from datetime import datetime
from typing import Self

from pydantic import Field

from clinical_mdr_api.domains.syntax_templates.objective_template import (
    ObjectiveTemplateAR,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameAndAttributes,
    SimpleTermModel,
)
from clinical_mdr_api.models.libraries.library import ItemCounts, Library
from clinical_mdr_api.models.syntax_templates.template_parameter import (
    TemplateParameter,
)
from clinical_mdr_api.models.utils import BaseModel

IS_CONFIRMATORY_TESTING_DESC = (
    "Indicates if template is related to confirmatory testing. Defaults to False."
)


class ObjectiveTemplateName(BaseModel):
    name: str | None = Field(
        ...,
        description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
    )
    name_plain: str | None = Field(
        ...,
        description="The plain text version of the name property, stripped of HTML tags",
    )
    guidance_text: str | None = Field(
        None,
        description="Optional guidance text for using the template.",
        nullable=True,
    )


class ObjectiveTemplateNameUid(ObjectiveTemplateName):
    uid: str = Field(..., description="The unique id of the objective template.")
    sequence_id: str | None = Field(None, nullable=True)


class ObjectiveTemplateNameUidLibrary(ObjectiveTemplateNameUid):
    library_name: str = Field(...)


class ObjectiveTemplate(ObjectiveTemplateNameUid):
    start_date: datetime | None = Field(
        default_factory=datetime.utcnow,
        description="Part of the metadata: The point in time when the (version of the) objective template was created. "
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
    )
    end_date: datetime | None = Field(
        default_factory=datetime.utcnow,
        description="Part of the metadata: The point in time when the version of the objective template was closed (and a new one was created). "
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
        nullable=True,
    )
    status: str | None = Field(
        None,
        description="The status in which the (version of the) objective template is in. "
        "Possible values are: 'Final', 'Draft' or 'Retired'.",
        nullable=True,
    )
    version: str | None = Field(
        None,
        description="The version number of the (version of the) objective template. "
        "The format is: <major>.<minor> where <major> and <minor> are digits. E.g. '0.1', '0.2', '1.0', ...",
        nullable=True,
    )
    change_description: str | None = Field(
        None,
        description="A short description about what has changed compared to the previous version.",
        nullable=True,
    )
    user_initials: str | None = Field(
        None,
        description="The initials of the user that triggered the change of the objective template.",
        nullable=True,
    )
    possible_actions: list[str] = Field(
        [],
        description=(
            "Holds those actions that can be performed on the objective template. "
            "Actions are: 'approve', 'edit', 'new_version', 'inactivate', 'reactivate' and 'delete'."
        ),
    )
    parameters: list[TemplateParameter] | None = Field(
        None,
        description="Those parameters that are used by the objective template.",
        nullable=True,
    )
    library: Library | None = Field(
        None,
        description="The library to which the objective template belongs.",
        nullable=True,
    )

    # Template indexings
    indications: list[SimpleTermModel] = Field(
        [],
        description="The study indications, conditions, diseases or disorders in scope for the template.",
    )
    is_confirmatory_testing: bool = Field(
        False, description="Indicates if template is related to confirmatory testing."
    )
    categories: list[SimpleCTTermNameAndAttributes] = Field(
        [], description="A list of categories the template belongs to."
    )

    study_count: int = Field(0, description="Count of studies referencing template")

    @classmethod
    def from_objective_template_ar(
        cls, objective_template_ar: ObjectiveTemplateAR
    ) -> Self:
        return cls(
            uid=objective_template_ar.uid,
            sequence_id=objective_template_ar.sequence_id,
            name=objective_template_ar.name,
            name_plain=objective_template_ar.name_plain,
            guidance_text=objective_template_ar.guidance_text,
            start_date=objective_template_ar.item_metadata.start_date,
            end_date=objective_template_ar.item_metadata.end_date,
            status=objective_template_ar.item_metadata.status.value,
            version=objective_template_ar.item_metadata.version,
            change_description=objective_template_ar.item_metadata.change_description,
            user_initials=objective_template_ar.item_metadata.user_initials,
            possible_actions=sorted(
                [_.value for _ in objective_template_ar.get_possible_actions()]
            ),
            library=Library.from_library_vo(objective_template_ar.library),
            is_confirmatory_testing=False
            if objective_template_ar.is_confirmatory_testing is None
            else objective_template_ar.is_confirmatory_testing,
            indications=objective_template_ar.indications,
            categories=objective_template_ar.categories,
            study_count=objective_template_ar.study_count,
            parameters=[
                TemplateParameter(name=_)
                for _ in objective_template_ar.template_value.parameter_names
            ],
        )


class ObjectiveTemplateWithCount(ObjectiveTemplate):
    counts: ItemCounts | None = Field(
        None, description="Optional counts of objective instantiations"
    )

    @classmethod
    def from_objective_template_ar(
        cls, objective_template_ar: ObjectiveTemplateAR
    ) -> Self:
        objective_template = super().from_objective_template_ar(objective_template_ar)
        if objective_template_ar.counts is not None:
            objective_template.counts = ItemCounts(
                draft=objective_template_ar.counts.count_draft,
                final=objective_template_ar.counts.count_final,
                retired=objective_template_ar.counts.count_retired,
                total=objective_template_ar.counts.count_total,
            )
        return objective_template


class ObjectiveTemplateVersion(ObjectiveTemplate):
    """
    Class for storing Objective Templates and calculation of differences
    """

    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective template (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )


class ObjectiveTemplateNameInput(BaseModel):
    name: str = Field(
        ...,
        description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
        min_length=1,
    )
    guidance_text: str | None = Field(
        None, description="Optional guidance text for using the template."
    )


class ObjectiveTemplateCreateInput(ObjectiveTemplateNameInput):
    study_uid: str | None = Field(
        None,
        description="The UID of the Study in scope of which given template is being created.",
    )
    library_name: str | None = Field(
        "Sponsor",
        description="If specified: The name of the library to which the objective template will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
        "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true.",
    )
    indication_uids: list[str] | None = Field(
        None,
        description="A list of UID of the study indications, conditions, diseases or disorders to attach the template to.",
    )
    is_confirmatory_testing: bool = Field(
        False, description=IS_CONFIRMATORY_TESTING_DESC
    )
    category_uids: list[str] | None = Field(
        None, description="A list of UID of the categories to attach the template to."
    )


class ObjectiveTemplateEditInput(ObjectiveTemplateNameInput):
    change_description: str = Field(
        ...,
        description="A short description about what has changed compared to the previous version.",
    )


class ObjectiveTemplateEditIndexingsInput(BaseModel):
    indication_uids: list[str] | None = Field(
        None,
        description="A list of UID of the study indications, conditions, diseases or disorders to attach the template to.",
    )
    category_uids: list[str] | None = Field(
        None, description="A list of UID of the categories to attach the template to."
    )
    is_confirmatory_testing: bool = Field(
        False, description=IS_CONFIRMATORY_TESTING_DESC
    )
