from datetime import datetime
from typing import Self

from pydantic import Field

from clinical_mdr_api.domains.syntax_templates.timeframe_template import (
    TimeframeTemplateAR,
)
from clinical_mdr_api.models.libraries.library import ItemCounts, Library
from clinical_mdr_api.models.syntax_templates.template_parameter import (
    TemplateParameter,
)
from clinical_mdr_api.models.utils import BaseModel


class TimeframeTemplateName(BaseModel):
    name: str = Field(
        ...,
        description="""
            The actual value/content. It may include parameters
            referenced by simple strings in square brackets [].
            """,
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


class TimeframeTemplateNameUid(TimeframeTemplateName):
    uid: str = Field(..., description="The unique id of the timeframe template.")
    sequence_id: str | None = Field(None, nullable=True)


class TimeframeTemplateNameUidLibrary(TimeframeTemplateNameUid):
    library_name: str = Field(...)


class TimeframeTemplate(TimeframeTemplateNameUid):
    start_date: datetime | None = Field(
        default_factory=datetime.utcnow,
        description="""
            Part of the metadata: The point in time when the
            (version of the) timeframe template was created.
            The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00'
            for October 31, 2020 at 6pm in UTC+2 timezone.
            """,
    )
    end_date: datetime | None = Field(
        default_factory=datetime.utcnow,
        description="Part of the metadata: The point in time when the version of the timeframe template was closed (and a new one was created). "
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
        nullable=True,
    )
    status: str | None = Field(
        None,
        description="The status in which the (version of the) timeframe template is in. "
        "Possible values are: 'Final', 'Draft' or 'Retired'.",
        nullable=True,
    )
    version: str | None = Field(
        None,
        description="The version number of the (version of the) timeframe template. "
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
        description="The initials of the user that triggered the change of the timeframe template.",
        nullable=True,
    )
    possible_actions: list[str] = Field(
        [],
        description=(
            "Holds those actions that can be performed on the timeframe template. "
            "Actions are: 'approve', 'edit', 'new_version', 'inactivate', 'reactivate' and 'delete'."
        ),
    )
    parameters: list[TemplateParameter] = Field(
        [], description="Those parameters that are used by the timeframe template."
    )
    library: Library | None = Field(
        None,
        description="The library to which the timeframe template belongs.",
        nullable=True,
    )

    @classmethod
    def from_timeframe_template_ar(
        cls, timeframe_template_ar: TimeframeTemplateAR
    ) -> Self:
        return cls(
            uid=timeframe_template_ar.uid,
            sequence_id=timeframe_template_ar.sequence_id,
            name=timeframe_template_ar.name,
            name_plain=timeframe_template_ar.name_plain,
            guidance_text=timeframe_template_ar.guidance_text,
            start_date=timeframe_template_ar.item_metadata.start_date,
            end_date=timeframe_template_ar.item_metadata.end_date,
            status=timeframe_template_ar.item_metadata.status.value,
            version=timeframe_template_ar.item_metadata.version,
            change_description=timeframe_template_ar.item_metadata.change_description,
            user_initials=timeframe_template_ar.item_metadata.user_initials,
            possible_actions=sorted(
                [_.value for _ in timeframe_template_ar.get_possible_actions()]
            ),
            library=Library.from_library_vo(timeframe_template_ar.library),
            parameters=[
                TemplateParameter(name=_)
                for _ in timeframe_template_ar.template_value.parameter_names
            ],
        )


class TimeframeTemplateWithCount(TimeframeTemplate):
    counts: ItemCounts | None = Field(
        None, description="Optional counts of objective instantiations"
    )

    @classmethod
    def from_timeframe_template_ar(
        cls, timeframe_template_ar: TimeframeTemplateAR
    ) -> Self:
        timeframe_template = super().from_timeframe_template_ar(timeframe_template_ar)
        if timeframe_template_ar.counts is not None:
            timeframe_template.counts = ItemCounts(
                draft=timeframe_template_ar.counts.count_draft,
                final=timeframe_template_ar.counts.count_final,
                retired=timeframe_template_ar.counts.count_retired,
                total=timeframe_template_ar.counts.count_total,
            )
        return timeframe_template


class TimeframeTemplateVersion(TimeframeTemplate):
    """
    Class for storing Timeframe Templates and calculation of differences
    """

    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the timeframe template (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )


class TimeframeTemplateNameInput(BaseModel):
    name: str = Field(
        ...,
        description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
        min_length=1,
    )
    guidance_text: str | None = Field(
        None, description="Optional guidance text for using the template."
    )


class TimeframeTemplateCreateInput(TimeframeTemplateNameInput):
    library_name: str | None = Field(
        "Sponsor",
        description="If specified: The name of the library to which the timeframe template will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
        "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true.",
    )


class TimeframeTemplateEditInput(TimeframeTemplateNameInput):
    change_description: str = Field(
        ...,
        description="A short description about what has changed compared to the previous version.",
    )
