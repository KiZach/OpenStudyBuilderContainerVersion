import datetime
from dataclasses import dataclass


@dataclass
class StudyActivityInstructionVO:
    study_uid: str
    study_activity_uid: str | None
    activity_instruction_uid: str | None

    # Study selection Versioning
    start_date: datetime.datetime
    user_initials: str | None

    uid: str | None = None
    activity_instruction_name: str | None = None
