import datetime
from dataclasses import dataclass

from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)


@dataclass
class StudyStandardVersionVO:
    study_uid: str
    study_status: StudyStatus
    start_date: datetime.datetime
    author: str
    ct_package_uid: str
    uid: str | None = None
    end_date: datetime.datetime | None = None

    def edit_core_properties(
        self,
        ct_package_uid: str,
    ):
        self.ct_package_uid = ct_package_uid

    @property
    def possible_actions(self):
        if self.study_status == StudyStatus.DRAFT:
            return ["edit", "delete", "lock"]
        return None


@dataclass
class StudyStandardVersionHistoryVO(StudyStandardVersionVO):
    change_type: str | None = None
