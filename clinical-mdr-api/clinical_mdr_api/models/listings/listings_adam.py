from typing import Self

from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class StudyEndpntAdamListing(BaseModel):
    STUDYID: str = Field(
        ..., title="Study Identifier", description="Unique identifier for a study."
    )
    OBJTVLVL: str | None = Field(
        None,
        title="Objective Level",
        description="Objective Level",
    )
    OBJTV: str = Field(
        ...,
        title="Objective",
        description="Objective",
    )
    OBJTVPT: str = Field(
        None,
        title="Objective Plain Text",
        description="""Objective Plain Text""",
    )
    ENDPNTLVL: str | None = Field(
        None,
        title="Endpoint Level",
        description="Endpoint Level",
    )
    ENDPNTSL: str | None = Field(
        None,
        title="Endpoint Sub-level",
        description="Endpoint Sub-level",
    )
    ENDPNT: str | None = Field(
        None,
        title="Endpoint Plain",
        description="Endpoint Plain",
    )
    ENDPNTPT: str | None = Field(
        None,
        title="Endpoint Plain Text",
        description="Endpoint Plain Text",
    )
    UNITDEF: str | None = Field(
        None,
        title="Unit Definition",
        description="Unit Definition",
    )
    UNIT: str | None = Field(
        None,
        title="Unit",
        description="Unit",
    )
    TMFRM: str | None = Field(
        None,
        title="Time Frame",
        description="Time Frame",
    )
    TMFRMPT: str | None = Field(
        None,
        title="Time Frame Plain Text",
        description="Time Frame Plain Text",
    )
    RACT: list[str] | None = Field(
        None,
        title="Related Activities",
        description="Array list for all related Activity Group as Template Parameter in either Objective or Endpoint",
    )
    RACTSGRP: list[str] | None = Field(
        None,
        title="Related Activity Subroups",
        description="Array list for all related Activity Subgroup as Template Parameter in either Objective or Endpoint",
    )
    RACTGRP: list[str] | None = Field(
        None,
        title="Related Activity Groups",
        description="Array list for all related Activity Group as Template Parameter in either Objective or Endpoint",
    )
    RACTINST: list[str] | None = Field(
        None,
        title="Related Activity Instances",
        description="Array list for all related Activity Instamces as Template Parameter in either Objective or Endpoint",
    )

    @classmethod
    def from_query(cls, query_result: dict) -> Self:
        return cls(
            STUDYID=query_result["STUDYID"],
            OBJTVLVL=query_result["OBJTVLVL"],
            OBJTV=query_result["OBJTV"],
            OBJTVPT=query_result["OBJTVPT"],
            ENDPNTLVL=query_result["ENDPNTLVL"],
            ENDPNTSL=query_result["ENDPNTSL"],
            ENDPNT=query_result["ENDPNT"],
            ENDPNTPT=query_result["ENDPNTPT"],
            UNITDEF=query_result["UNITDEF"],
            UNIT=query_result["UNIT"],
            TMFRM=query_result["TMFRM"],
            TMFRMPT=query_result["TMFRMPT"],
            RACT=query_result["RACT"],
            RACTSGRP=query_result["RACTSGRP"],
            RACTGRP=query_result["RACTGRP"],
            RACTINST=query_result["RACTINST"],
        )


class StudyVisitAdamListing(BaseModel):
    STUDYID: str = Field(
        title="Study Identifier", description="Unique identifier for a study."
    )
    VISTPCD: str = Field(
        title="Visit Type Code",
        description="Visit Type Code",
    )
    AVISITN: int = Field(
        title="Visit Number",
        description="1. Clinical encounter number 2. Numeric version of VISIT, used for sorting.",
    )
    AVISIT: str = Field(
        None,
        title="Visit Name",
        description="""1. Protocol-defined description of clinical encounter. 2. May
        be used in addition to VISITNUM and/or VISITDY as a text description of the clinical encounter.""",
    )
    AVISIT1N: int = Field(
        None,
        title="Planned Study Day of Visit",
        description="1. Planned study day of VISIT. 2. Due to its sequential nature, used for sorting.",
    )
    VISLABEL: str = Field(
        None,
        title="Visit Label",
        description="Visit Label",
    )
    AVISIT1: str = Field(
        None,
        title="Planned day",
        description="Planned day",
    )
    AVISIT2: str = Field(
        None,
        title="Planned Week Text",
        description="Planned Week Text",
    )
    AVISIT2N: str = Field(
        None,
        title="Planned Week Number",
        description="Planned Week Number",
    )

    @classmethod
    def from_query(cls, query_result: dict) -> Self:
        return cls(
            STUDYID=query_result["STUDYID"],
            VISTPCD=query_result["VISIT_TYPE_NAME"],
            AVISITN=query_result["VISIT_NUM"],
            AVISIT=query_result["VISIT_NAME"],
            AVISIT1N=query_result["DAY_VALUE"],
            VISLABEL=query_result["VISIT_SHORT_LABEL"],
            AVISIT1=query_result["DAY_NAME"],
            AVISIT2=query_result["WEEK_NAME"],
            AVISIT2N=query_result["WEEK_VALUE"],
        )
