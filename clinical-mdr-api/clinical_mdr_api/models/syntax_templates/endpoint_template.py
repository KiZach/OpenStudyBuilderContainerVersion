from datetime import datetime
from typing import Self

from pydantic import Field

from clinical_mdr_api.domains.syntax_templates.endpoint_template import (
    EndpointTemplateAR,
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


class EndpointTemplateName(BaseModel):
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


class EndpointTemplateNameUid(EndpointTemplateName):
    uid: str = Field(..., description="The unique id of the endpoint template.")
    sequence_id: str | None = Field(None, nullable=True)


class EndpointTemplateNameUidLibrary(EndpointTemplateNameUid):
    library_name: str = Field(...)


class EndpointTemplate(EndpointTemplateNameUid):
    start_date: datetime | None = Field(
        default_factory=datetime.utcnow,
        description="Part of the metadata: The point in time when the (version of the) endpoint template was created. "
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
    )
    end_date: datetime | None = Field(
        default_factory=datetime.utcnow,
        description="Part of the metadata: The point in time when the version of the endpoint template was closed (and a new one was created). "
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
        nullable=True,
    )
    status: str | None = Field(
        None,
        description="The status in which the (version of the) endpoint template is in. "
        "Possible values are: 'Final', 'Draft' or 'Retired'.",
        nullable=True,
    )
    version: str | None = Field(
        None,
        description="The version number of the (version of the) endpoint template. "
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
        description="The initials of the user that triggered the change of the endpoint template.",
        nullable=True,
    )
    possible_actions: list[str] = Field(
        [],
        description=(
            "Holds those actions that can be performed on the endpoint template. "
            "Actions are: 'approve', 'edit', 'new_version', 'inactivate', 'reactivate' and 'delete'."
        ),
    )
    parameters: list[TemplateParameter] = Field(
        [], description="Those parameters that are used by the endpoint template."
    )
    library: Library | None = Field(
        None,
        description="The library to which the endpoint template belongs.",
        nullable=True,
    )

    # Template indexings
    indications: list[SimpleTermModel] = Field(
        [],
        description="The study indications, conditions, diseases or disorders in scope for the template.",
    )
    categories: list[SimpleCTTermNameAndAttributes] = Field(
        [], description="A list of categories the template belongs to."
    )
    sub_categories: list[SimpleCTTermNameAndAttributes] = Field(
        [], description="A list of sub-categories the template belongs to."
    )

    study_count: int = Field(0, description="Count of studies referencing template")

    @classmethod
    def from_endpoint_template_ar(
        cls, endpoint_template_ar: EndpointTemplateAR
    ) -> Self:
        return cls(
            uid=endpoint_template_ar.uid,
            sequence_id=endpoint_template_ar.sequence_id,
            name=endpoint_template_ar.name,
            name_plain=endpoint_template_ar.name_plain,
            guidance_text=endpoint_template_ar.guidance_text,
            start_date=endpoint_template_ar.item_metadata.start_date,
            end_date=endpoint_template_ar.item_metadata.end_date,
            status=endpoint_template_ar.item_metadata.status.value,
            version=endpoint_template_ar.item_metadata.version,
            change_description=endpoint_template_ar.item_metadata.change_description,
            user_initials=endpoint_template_ar.item_metadata.user_initials,
            possible_actions=sorted(
                [_.value for _ in endpoint_template_ar.get_possible_actions()]
            ),
            library=Library.from_library_vo(endpoint_template_ar.library),
            indications=endpoint_template_ar.indications,
            categories=endpoint_template_ar.categories,
            sub_categories=endpoint_template_ar.sub_categories,
            study_count=endpoint_template_ar.study_count,
            parameters=[
                TemplateParameter(name=_)
                for _ in endpoint_template_ar.template_value.parameter_names
            ],
        )


class EndpointTemplateWithCount(EndpointTemplate):
    counts: ItemCounts | None = Field(
        None, description="Optional counts of objective instantiations"
    )

    @classmethod
    def from_endpoint_template_ar(
        cls, endpoint_template_ar: EndpointTemplateAR
    ) -> Self:
        endpoint_template = super().from_endpoint_template_ar(endpoint_template_ar)
        if endpoint_template_ar.counts is not None:
            endpoint_template.counts = ItemCounts(
                draft=endpoint_template_ar.counts.count_draft,
                final=endpoint_template_ar.counts.count_final,
                retired=endpoint_template_ar.counts.count_retired,
                total=endpoint_template_ar.counts.count_total,
            )
        return endpoint_template


class EndpointTemplateVersion(EndpointTemplate):
    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the endpoint template (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )


class EndpointTemplateNameInput(BaseModel):
    name: str = Field(
        ...,
        description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
        min_length=1,
    )
    guidance_text: str | None = Field(
        None, description="Optional guidance text for using the template."
    )


class EndpointTemplateCreateInput(EndpointTemplateNameInput):
    study_uid: str | None = Field(
        None,
        description="The UID of the Study in scope of which given template is being created.",
    )
    library_name: str | None = Field(
        "Sponsor",
        description="If specified: The name of the library to which the endpoint template will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
        "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true.",
    )
    indication_uids: list[str] | None = Field(
        None,
        description="A list of UID of the study indications, conditions, diseases or disorders to attach the template to.",
    )
    category_uids: list[str] | None = Field(
        None, description="A list of UID of the categories to attach the template to."
    )
    sub_category_uids: list[str] | None = Field(
        None,
        description="A list of UID of the sub_categories to attach the template to.",
    )


class EndpointTemplateEditInput(EndpointTemplateNameInput):
    change_description: str = Field(
        ...,
        description="A short description about what has changed compared to the previous version.",
    )


class EndpointTemplateEditIndexingsInput(BaseModel):
    indication_uids: list[str] | None = Field(
        None,
        description="A list of UID of the study indications, conditions, diseases or disorders to attach the template to.",
    )
    category_uids: list[str] | None = Field(
        None, description="A list of UID of the categories to attach the template to."
    )
    sub_category_uids: list[str] | None = Field(
        None,
        description="A list of UID of the sub_categories to attach the template to.",
    )
