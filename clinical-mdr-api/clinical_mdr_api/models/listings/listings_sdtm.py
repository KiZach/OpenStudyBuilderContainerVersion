from typing import Any, Self

from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class StudyVisitListing(BaseModel):
    STUDYID: str = Field(
        title="Study Identifier", description="Unique identifier for a study."
    )
    DOMAIN: str = Field(
        title="Domain Abbreviation",
        description="Two-character abbreviation for the domain",
    )
    VISITNUM: int = Field(
        title="Visit Number",
        description="1. Clinical encounter number 2. Numeric version of VISIT, used for sorting.",
    )
    VISIT: str = Field(
        None,
        title="Visit Name",
        description="""1. Protocol-defined description of clinical encounter. 2. May
        be used in addition to VISITNUM and/or VISITDY as a text description of the clinical encounter.""",
    )
    VISITDY: int = Field(
        None,
        title="Planned Study Day of Visit",
        description="1. Planned study day of VISIT. 2. Due to its sequential nature, used for sorting.",
    )
    ARMCD: str = Field(
        None,
        title="Planned Arm Code",
        description="""
        1.ARMCD is limited to 20 characters and does not have special character restrictions. 
        The maximum length of ARMCD is longer than for other "short" variables to accommodate 
        the kind of values that are likely to be needed for crossover trials. For example, if 
        ARMCD values for a seven- period crossover were constructed using two-character abbreviations 
        for each treatment and separating hyphens, the length of ARMCD values would be 20. 2. If the 
        timing of Visits for a trial does not depend on which ARM a subject is in, then ARMCD should be null.
        """,
    )
    ARM: str = Field(
        None,
        title="Description of Planned Arm",
        description="""1. Name given to an Arm or Treatment Group. 2. If the timing
        of Visits for a trial does not depend on which Arm a subject is in, then Arm should be left blank.""",
    )
    TVSTRL: str = Field(
        None,
        title="Visit Start Rule",
        description="Rule describing when the Visit starts, in relation to the sequence of Elements.",
    )
    TVENRL: str = Field(
        None,
        title="Visit End Rule",
        description="Rule describing when the Visit ends, in relation to the sequence of Elements.",
    )

    @classmethod
    def from_query(cls, query_result: dict) -> Self:
        return cls(
            STUDYID=query_result["STUDYID"],
            DOMAIN=query_result["DOMAIN"],
            VISITNUM=query_result["VISITNUM"],
            VISIT=query_result["VISIT"],
            VISITDY=query_result["VISITDY"],
            ARMCD=query_result["ARMCD"],
            ARM=query_result["ARM"],
            TVSTRL=query_result["TVSTRL"],
            TVENRL=query_result["TVENRL"],
        )


class StudyArmListing(BaseModel):
    STUDYID: str = Field(
        title="Study Identifier", description="Unique identifier for a study."
    )
    DOMAIN: str = Field(
        title="Domain Abbreviation",
        description="Two-character abbreviation for the domain",
    )
    ARMCD: str = Field(
        None,
        title="Planned Arm Code",
        description="""
        1.ARMCD is limited to 20 characters and does not have special character restrictions. 
        The maximum length of ARMCD is longer than for other "short" variables to accommodate 
        the kind of values that are likely to be needed for crossover trials. For example, if 
        ARMCD values for a seven- period crossover were constructed using two-character abbreviations 
        for each treatment and separating hyphens, the length of ARMCD values would be 20. 2. If the 
        timing of Visits for a trial does not depend on which ARM a subject is in, then ARMCD should be null.
        """,
    )
    ARM: str = Field(
        None,
        title="Description of Planned Arm",
        description="""1. Name given to an Arm or Treatment Group. 2. If the timing
        of Visits for a trial does not depend on which Arm a subject is in, then Arm should be left blank.""",
    )
    TAETORD: str = Field(
        None,
        title="Planned Order of Element within Arm",
        description="Number that gives the order of the Element within the Arm",
    )
    ETCD: str = Field(
        None,
        title="Element Code",
        description="""
        ETCD (the companion to ELEMENT) is limited to 8 characters 
        and does not have special character restrictions. These values should be
         """,
    )

    ELEMENT: str = Field(
        None,
        title="Description of Element",
        description="The name of the Element. The same Element may occur more than once within an Arm.",
    )

    TABRANCH: str = Field(
        None,
        title="Branch",
        description="""
        Condition subject met, at a “branch” in the trial design at the end of this Element, 
        to be included in this Arm; (e.g., randomization to DRUG X).
         """,
    )

    TATRANS: str = Field(
        None,
        title="Transition Rule",
        description=""" If the trial design allows a subject to transition
        to an Element other than the next Element in sequence, 
        then the conditions for transitioning to those other Elements, 
        and the alternative Element sequences, are specified in this rule (e.g., Responders go to washout). """,
    )

    EPOCH: str = Field(
        None,
        title="Epoch",
        description="Name of the Trial Epoch with which this Element of the Arm is associated.",
    )

    @classmethod
    def from_query(cls, query_result: dict) -> Self:
        return cls(
            STUDYID=query_result["STUDYID"],
            DOMAIN=query_result["DOMAIN"],
            ARMCD=query_result["ARMCD"],
            ARM=query_result["ARM"],
            TAETORD=query_result["TAETORD"],
            ETCD=query_result["ETCD"],
            ELEMENT=query_result["ELEMENT"],
            TABRANCH=query_result["TABRANCH"],
            TATRANS=query_result["TATRANS"],
            EPOCH=query_result["EPOCH"],
        )


class StudyCriterionListing(BaseModel):
    STUDYID: str = Field(
        title="Study Identifier", description="Unique identifier for a study."
    )
    DOMAIN: str = Field(
        title="Domain Abbreviation",
        description="Two-character abbreviation for the domain",
    )
    IETESTCD: str = Field(
        title="Incl/Excl Criterion Short Name",
        description="""
        Short name IETEST. It can be used as a column name when converting a dataset from a vertical to a horizontal format.
        The value in IETESTCD cannot be longer than 8 characters, nor can it start with a number (e.g., "1TEST"). IETESTCD
        cannot contain characters other than letters, numbers, or underscores. The prefix "IE" is used to ensure consistency
        with the IE domain.
        """,
    )
    IETEST: str = Field(
        None,
        title="Inclusion/Exclusion Criterion",
        description="""
        Full text of the inclusion or exclusion criterion. The prefix "IE" is used to ensure consistency with the IE domain.
        """,
    )
    IECAT: str = Field(
        None,
        title="Inclusion/Exclusion Category",
        description="""
        Used for categorization of the inclusion or exclusion criteria.
        """,
    )
    IESCAT: str = Field(
        None,
        title="Inclusion/Exclusion Subcategory",
        description="""
        A further categorization of the exception criterion.
        Can be used to distinguish criteria for a sub-study or for to categorize as
        a major or minor exceptions. Examples: MAJOR, MINOR.
        """,
    )
    TIRL: str = Field(
        None,
        title="Inclusion/Exclusion Criterion Rule",
        description="""
        Rule that expresses the criterion in computer-executable form (see assumption 4 below).
        """,
    )
    TIVERS: str = Field(
        None,
        title="Protocol Criteria Versions",
        description="The number of this version of the Inclusion/Exclusion criteria. May be omitted if there is only one version.",
    )

    @classmethod
    def from_query(cls, query_result: dict) -> Self:
        return cls(
            STUDYID=query_result["STUDYID"],
            DOMAIN=query_result["DOMAIN"],
            IETESTCD=query_result["IETESTCD"],
            IETEST=query_result["IETEST"],
            IECAT=query_result["IECAT"],
            IESCAT=query_result["IESCAT"],
            TIRL=query_result["TIRL"],
            TIVERS=query_result["TIVERS"],
        )


class StudySummaryListing(BaseModel):
    STUDYID: str = Field(
        title="Study Identifier", description="Unique identifier for a study."
    )
    DOMAIN: str = Field(
        title="Domain Abbreviation",
        description="Two-character abbreviation for the domain",
    )
    TSPARMCD: str = Field(
        None,
        title="Trial Summary Parameter Short Name",
        description="""
        TSPARMCD (the companion to TSPARM) is limited to 8 characters and does not have special character restrictions.
        These values should be short for ease of use in programming, but it is not expected that TSPARMCD will need to
        serve as variable names. Examples: AGEMIN, AGEMAX
        """,
    )
    TSPARM: str = Field(
        None,
        title="Trial Summary Parameter",
        description="""
        Term for the Trial Summary Parameter. The value in TSPARM cannot be longer than 40 characters.
        Examples Planned Minimum Age of Subjects, Planned Maximum Age of Subjects
        """,
    )
    TSVAL: str | list[Any] = Field(
        None,
        title="Parameter Value",
        description="""
        Value of TSPARM. Example: "ASTHMA" when TSPARM value is "Trial Indication".
        TSVAL can only be null when TSVALNF is populated. Text over 200 characters can be added to additional columns TSVAL1-TSVALn.
        """,
    )
    TSVALNF: str = Field(
        None,
        title="Parameter Null Flavor",
        description="""
        Null flavor for the value of TSPARM, to be populated if and only if TSVAL is null.
        """,
    )
    TSVALCD: str = Field(
        None,
        title="Parameter Value Code",
        description="""
        This is the code of the term in TSVAL. For example; 6CW7F3G59X is the code for Gabapentin,
        C49488 is the code for Y. The length of this variable can be longer than 8 to accommodate
        the length of the external terminology.
        """,
    )
    TSVCDREF: str = Field(
        None,
        title="Name of the Reference Terminology",
        description="The name of the Reference Terminology from which TSVALCD is taken. For example; CDISC, SNOMED, ISO 8601.",
    )
    TSVCDVER: str = Field(
        None,
        title="Version of the Reference Terminology",
        description="The version number of the Reference Terminology, if applicable.",
    )

    @classmethod
    def from_query(cls, query_result: dict) -> Self:
        return cls(
            STUDYID=query_result["STUDYID"],
            DOMAIN=query_result["DOMAIN"],
            TSPARMCD=query_result["TSPARMCD"],
            TSPARM=query_result["TSPARM"],
            TSVAL=query_result["TSVAL"],
            TSVALNF=query_result["TSVALNF"],
            TSVALCD=query_result["TSVALCD"],
            TSVCDREF=query_result["TSVCDREF"],
            TSVCDVER=query_result["TSVCDVER"],
        )


class StudyElementListing(BaseModel):
    STUDYID: str = Field(
        title="Study Identifier", description="Unique identifier for a study."
    )
    DOMAIN: str = Field(
        title="Domain Abbreviation",
        description="Two-character abbreviation for the domain",
    )
    ETCD: str = Field(
        None,
        title="Element Code",
        description="""
        ETCD (the companion to ELEMENT) is limited to 8 characters 
        and does not have special character restrictions. These values should be
         """,
    )
    ELEMENT: str = Field(
        None,
        title="Description of Element",
        description="The name of the Element. The same Element may occur more than once within an Arm.",
    )
    TESTRL: str = Field(
        None,
        title="Rule for Start of Element",
        description="Rule for Start of Element Char Rule Expresses rule for beginning Element",
    )
    TEENRL: str = Field(
        None,
        title="Rule for End of Element",
        description=""" Rule for End of Element Char Rule Expresses rule for ending Element.
        Either TEENRL or TEDUR must be present for each Element """,
    )
    TEDUR: str = Field(
        None,
        title="Planned Duration of Element",
        description="""Planned Duration of Element Char ISO 8601
        Timing Planned Duration of Element in ISO 8601 format. 
        Used when the rule for ending the Element is applied after a fixed duration. 
        """,
    )

    @classmethod
    def from_query(cls, query_result: dict) -> Self:
        return cls(
            STUDYID=query_result["STUDYID"],
            DOMAIN=query_result["DOMAIN"],
            ETCD=query_result["ETCD"],
            ELEMENT=query_result["ELEMENT"],
            TESTRL=query_result["TESTRL"],
            TEENRL=query_result["TEENRL"],
            TEDUR=query_result["TEDUR"],
        )


class StudyDiseaseMilestoneListing(BaseModel):
    STUDYID: str = Field(
        title="Study Identifier", description="Unique identifier for a study."
    )
    DOMAIN: str = Field(
        title="Domain Abbreviation",
        description="Two-character abbreviation for the domain",
    )
    MIDSTYPE: str = Field(
        None,
        title="Disease Milestone Type",
        description="""
        The type of Disease Milestone. Example: "HYPOGLYCEMIC EVENT".
         """,
    )
    TMDEF: str = Field(
        None,
        title="Disease Milestone Definition",
        description="Definition of the Disease Milestone.",
    )
    TMRPT: str = Field(
        None,
        title="Disease Milestone Repetition Indicator",
        description="""
        Indicates whether this is a Disease Milestone that can occur only once ('N') 
        or a type of Disease Milestone that can occur multiple times ('Y').
        """,
    )

    @classmethod
    def from_query(cls, query_result: dict) -> Self:
        return cls(
            STUDYID=query_result["STUDYID"],
            DOMAIN=query_result["DOMAIN"],
            MIDSTYPE=query_result["MIDSTYPE"],
            TMDEF=query_result["TMDEF"],
            TMRPT=query_result["TMRPT"],
        )
