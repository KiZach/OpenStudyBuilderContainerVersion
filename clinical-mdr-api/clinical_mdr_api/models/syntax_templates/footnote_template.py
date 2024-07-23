from datetime import datetime
from typing import Self

from pydantic import Field

from clinical_mdr_api.domains.syntax_templates.footnote_template import (
    FootnoteTemplateAR,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameAndAttributes,
    SimpleTermModel,
)
from clinical_mdr_api.models.generic_models import SimpleNameModel
from clinical_mdr_api.models.libraries.library import ItemCounts, Library
from clinical_mdr_api.models.syntax_templates.template_parameter import (
    TemplateParameter,
)
from clinical_mdr_api.models.utils import BaseModel


class FootnoteTemplateName(BaseModel):
    name: str | None = Field(
        None,
        description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
    )
    name_plain: str | None = Field(
        None,
        description="The plain text version of the name property, stripped of HTML tags",
    )


class FootnoteTemplateNameUid(FootnoteTemplateName):
    uid: str | None = Field(
        None,
        description="The unique id of the footnote template.",
    )
    sequence_id: str | None = Field(
        None,
        nullable=True,
    )


class FootnoteTemplateNameUidLibrary(FootnoteTemplateNameUid):
    library_name: str = Field(...)


class FootnoteTemplate(FootnoteTemplateNameUid):
    start_date: datetime | None = Field(
        default_factory=datetime.utcnow,
        description="Part of the metadata: The point in time when the (version of the) footnote template was created. "
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
    )
    end_date: datetime | None = Field(
        default_factory=datetime.utcnow,
        description="Part of the metadata: The point in time when the version of the footnote template was closed (and a new one was created). "
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
        nullable=True,
    )
    status: str | None = Field(
        None,
        description="The status in which the (version of the) footnote template is in. "
        "Possible values are: 'Final', 'Draft' or 'Retired'.",
        nullable=True,
    )
    version: str | None = Field(
        None,
        description="The version number of the (version of the) footnote template. "
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
        description="The initials of the user that triggered the change of the footnote template.",
        nullable=True,
    )
    possible_actions: list[str] = Field(
        [],
        description=(
            "Holds those actions that can be performed on the footnote template. "
            "Actions are: 'approve', 'edit', 'new_version', 'inactivate', 'reactivate' and 'delete'."
        ),
    )
    parameters: list[TemplateParameter] = Field(
        [],
        description="Those parameters that are used by the footnote template.",
    )
    library: Library | None = Field(
        None,
        description="The library to which the footnote template belongs.",
        nullable=True,
    )

    # Template indexings
    type: SimpleCTTermNameAndAttributes | None = Field(
        None,
        description="The footnote type.",
        nullable=True,
    )
    indications: list[SimpleTermModel] = Field(
        [],
        description="The study indications, conditions, diseases or disorders in scope for the template.",
    )
    activities: list[SimpleNameModel] = Field(
        [],
        description="The activities in scope for the template",
    )
    activity_groups: list[SimpleNameModel] = Field(
        [],
        description="The activity groups in scope for the template",
    )
    activity_subgroups: list[SimpleNameModel] = Field(
        [],
        description="The activity sub groups in scope for the template",
    )
    study_count: int = Field(
        0,
        description="Count of studies referencing template",
    )

    @classmethod
    def from_footnote_template_ar(
        cls, footnote_template_ar: FootnoteTemplateAR
    ) -> Self:
        return cls(
            uid=footnote_template_ar.uid,
            sequence_id=footnote_template_ar.sequence_id,
            name=footnote_template_ar.name,
            name_plain=footnote_template_ar.name_plain,
            start_date=footnote_template_ar.item_metadata.start_date,
            end_date=footnote_template_ar.item_metadata.end_date,
            status=footnote_template_ar.item_metadata.status.value,
            version=footnote_template_ar.item_metadata.version,
            change_description=footnote_template_ar.item_metadata.change_description,
            user_initials=footnote_template_ar.item_metadata.user_initials,
            possible_actions=sorted(
                [_.value for _ in footnote_template_ar.get_possible_actions()]
            ),
            library=Library.from_library_vo(footnote_template_ar.library),
            type=footnote_template_ar.type,
            indications=footnote_template_ar.indications,
            activities=footnote_template_ar.activities,
            activity_groups=footnote_template_ar.activity_groups,
            activity_subgroups=footnote_template_ar.activity_subgroups,
            study_count=footnote_template_ar.study_count,
            parameters=[
                TemplateParameter(name=_)
                for _ in footnote_template_ar.template_value.parameter_names
            ],
        )


class FootnoteTemplateWithCount(FootnoteTemplate):
    counts: ItemCounts | None = Field(
        None, description="Optional counts of footnote instantiations"
    )

    @classmethod
    def from_footnote_template_ar(
        cls, footnote_template_ar: FootnoteTemplateAR
    ) -> Self:
        footnote_template = super().from_footnote_template_ar(footnote_template_ar)
        if footnote_template_ar.counts is not None:
            footnote_template.counts = ItemCounts(
                draft=footnote_template_ar.counts.count_draft,
                final=footnote_template_ar.counts.count_final,
                retired=footnote_template_ar.counts.count_retired,
                total=footnote_template_ar.counts.count_total,
            )
        return footnote_template


class FootnoteTemplateVersion(FootnoteTemplate):
    """
    Class for storing Footnote Templates and calculation of differences
    """

    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the footnote template (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )


class FootnoteTemplateNameInput(BaseModel):
    name: str = Field(
        ...,
        description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
        min_length=1,
    )


class FootnoteTemplateCreateInput(FootnoteTemplateNameInput):
    study_uid: str | None = Field(
        None,
        description="The UID of the Study in scope of which given template is being created.",
    )
    library_name: str | None = Field(
        "Sponsor",
        description="If specified: The name of the library to which the footnote template will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
        "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true.",
    )
    type_uid: str = Field(
        ...,
        description="The UID of the footnote type to attach the template to.",
        min_length=1,
    )
    indication_uids: list[str] | None = Field(
        None,
        description="A list of UID of the study indications, conditions, diseases or disorders to attach the template to.",
    )
    activity_uids: list[str] | None = Field(
        None, description="A list of UID of the activities to attach the template to."
    )
    activity_group_uids: list[str] | None = Field(
        None,
        description="A list of UID of the activity subgroups to attach the template to.",
    )
    activity_subgroup_uids: list[str] | None = Field(
        None,
        description="A list of UID of the activity groups to attach the template to.",
    )


class FootnoteTemplateEditInput(FootnoteTemplateNameInput):
    change_description: str = Field(
        ...,
        description="A short description about what has changed compared to the previous version.",
    )


class FootnoteTemplateEditIndexingsInput(BaseModel):
    indication_uids: list[str] | None = Field(
        None,
        description="A list of UID of the study indications, conditions, diseases or disorders to attach the template to.",
    )
    activity_uids: list[str] | None = Field(
        None, description="A list of UID of the activities to attach the template to."
    )
    activity_group_uids: list[str] | None = Field(
        None,
        description="A list of UID of the activity groups to attach the template to.",
    )
    activity_subgroup_uids: list[str] | None = Field(
        None,
        description="A list of UID of the activity sub groups to attach the template to.",
    )
