from datetime import datetime
from typing import Self

from pydantic import Field

from clinical_mdr_api.domains.syntax_templates.criteria_template import (
    CriteriaTemplateAR,
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


class CriteriaTemplateName(BaseModel):
    name: str = Field(
        ...,
        description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
    )
    name_plain: str = Field(
        ...,
        description="The plain text version of the name property, stripped of HTML tags",
    )
    guidance_text: str | None = Field(
        None,
        description="Optional guidance text for using the template.",
        nullable=True,
    )


class CriteriaTemplateNameUid(CriteriaTemplateName):
    uid: str = Field(..., description="The unique id of the criteria template.")
    sequence_id: str | None = Field(None, nullable=True)


class CriteriaTemplateNameUidLibrary(CriteriaTemplateNameUid):
    library_name: str = Field(...)


class CriteriaTemplate(CriteriaTemplateNameUid):
    start_date: datetime | None = Field(
        default_factory=datetime.utcnow,
        description="Part of the metadata: The point in time when the (version of the) criteria template was created. "
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
    )
    end_date: datetime | None = Field(
        default_factory=datetime.utcnow,
        description="Part of the metadata: The point in time when the version of the criteria template was closed (and a new one was created). "
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
        nullable=True,
    )
    status: str | None = Field(
        None,
        description="The status in which the (version of the) criteria template is in. "
        "Possible values are: 'Final', 'Draft' or 'Retired'.",
        nullable=True,
    )
    version: str | None = Field(
        None,
        description="The version number of the (version of the) criteria template. "
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
        description="The initials of the user that triggered the change of the criteria template.",
        nullable=True,
    )
    possible_actions: list[str] = Field(
        [],
        description=(
            "Holds those actions that can be performed on the criteria template. "
            "Actions are: 'approve', 'edit', 'new_version', 'inactivate', 'reactivate' and 'delete'."
        ),
    )
    parameters: list[TemplateParameter] = Field(
        [], description="Those parameters that are used by the criteria template."
    )
    library: Library | None = Field(
        None,
        description="The library to which the criteria template belongs.",
        nullable=True,
    )

    # Template indexings
    type: SimpleCTTermNameAndAttributes | None = Field(
        None, description="The criteria type.", nullable=True
    )
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
    def from_criteria_template_ar(
        cls, criteria_template_ar: CriteriaTemplateAR
    ) -> Self:
        return cls(
            uid=criteria_template_ar.uid,
            sequence_id=criteria_template_ar.sequence_id,
            name=criteria_template_ar.name,
            name_plain=criteria_template_ar.name_plain,
            guidance_text=criteria_template_ar.guidance_text,
            start_date=criteria_template_ar.item_metadata.start_date,
            end_date=criteria_template_ar.item_metadata.end_date,
            status=criteria_template_ar.item_metadata.status.value,
            version=criteria_template_ar.item_metadata.version,
            change_description=criteria_template_ar.item_metadata.change_description,
            user_initials=criteria_template_ar.item_metadata.user_initials,
            possible_actions=sorted(
                [_.value for _ in criteria_template_ar.get_possible_actions()]
            ),
            library=Library.from_library_vo(criteria_template_ar.library),
            type=criteria_template_ar.type,
            indications=criteria_template_ar.indications,
            categories=criteria_template_ar.categories,
            sub_categories=criteria_template_ar.sub_categories,
            study_count=criteria_template_ar.study_count,
            parameters=[
                TemplateParameter(name=_)
                for _ in criteria_template_ar.template_value.parameter_names
            ],
        )


class CriteriaTemplateWithCount(CriteriaTemplate):
    counts: ItemCounts | None = Field(
        None, description="Optional counts of criteria instantiations"
    )

    @classmethod
    def from_criteria_template_ar(
        cls, criteria_template_ar: CriteriaTemplateAR
    ) -> Self:
        criteria_template = super().from_criteria_template_ar(criteria_template_ar)
        if criteria_template_ar.counts is not None:
            criteria_template.counts = ItemCounts(
                draft=criteria_template_ar.counts.count_draft,
                final=criteria_template_ar.counts.count_final,
                retired=criteria_template_ar.counts.count_retired,
                total=criteria_template_ar.counts.count_total,
            )
        return criteria_template


class CriteriaTemplateVersion(CriteriaTemplate):
    """
    Class for storing Criteria Templates and calculation of differences
    """

    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the criteria template (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )


class CriteriaTemplateNameInput(BaseModel):
    name: str = Field(
        ...,
        description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
        min_length=1,
    )
    guidance_text: str | None = Field(
        None, description="Optional guidance text for using the template."
    )


class CriteriaTemplateCreateInput(CriteriaTemplateNameInput):
    study_uid: str | None = Field(
        None,
        description="The UID of the Study in scope of which given template is being created.",
    )
    library_name: str | None = Field(
        "Sponsor",
        description="If specified: The name of the library to which the criteria template will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
        "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true.",
    )
    type_uid: str = Field(
        ...,
        description="The UID of the criteria type to attach the template to.",
        min_length=1,
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


class CriteriaTemplateEditInput(CriteriaTemplateNameInput):
    change_description: str = Field(
        ...,
        description="A short description about what has changed compared to the previous version.",
    )


class CriteriaTemplateEditIndexingsInput(BaseModel):
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
