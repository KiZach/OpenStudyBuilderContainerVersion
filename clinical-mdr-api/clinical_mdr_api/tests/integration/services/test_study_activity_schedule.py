import unittest

from neomodel import db

from clinical_mdr_api import models
from clinical_mdr_api.services.studies.study_activity_schedule import (
    StudyActivityScheduleService,
)
from clinical_mdr_api.tests.integration.utils import data_library
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_library_data,
    create_study_activity,
    create_study_epoch,
    create_study_visit_codelists,
    create_visit_with_update,
    get_unit_uid_by_name,
)


class StudyActivityScheduleTestCase(unittest.TestCase):
    def setUp(self):
        inject_and_clear_db("studyactivitiescheduletest.schedule")
        create_library_data()
        db.cypher_query(data_library.STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(data_library.STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(data_library.STARTUP_ACTIVITIES)
        db.cypher_query(
            data_library.get_codelist_with_term_cypher("EFFICACY", "Flowchart Group")
        )
        db.cypher_query(data_library.STARTUP_CT_CATALOGUE_CYPHER)
        db.cypher_query(data_library.STARTUP_SINGLE_STUDY_CYPHER)
        create_study_visit_codelists()
        self.epoch1 = create_study_epoch("EpochSubType_0001")
        self.epoch2 = create_study_epoch("EpochSubType_0002")
        self.epoch3 = create_study_epoch("EpochSubType_0003")
        self.day_uid = get_unit_uid_by_name("day")
        super().setUp()

    def test_create_delete_schedule(self):
        baseline = create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0001",
            time_reference_uid="VisitSubType_0001",
            time_value=0,
            time_unit_uid=self.day_uid,
        )
        sa1 = create_study_activity("study_root")
        service = StudyActivityScheduleService()
        schedule = service.create(
            "study_root",
            models.StudyActivityScheduleCreateInput(
                study_activity_uid=sa1.study_activity_uid, study_visit_uid=baseline.uid
            ),
        )
        schedules = service.get_all_schedules("study_root")
        assert len(schedules) == 1

        service.delete("study_root", schedule.study_activity_schedule_uid)
        schedules = service.get_all_schedules("study_root")
        assert len(schedules) == 0

    def test_batch_operations(self):
        baseline = create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0001",
            time_reference_uid="VisitSubType_0001",
            time_value=0,
            time_unit_uid=self.day_uid,
        )
        create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0003",
            time_reference_uid="VisitSubType_0001",
            time_value=4,
            time_unit_uid=self.day_uid,
        )
        sa1 = create_study_activity("study_root")
        sa2 = create_study_activity(
            "study_root",
            activity_uid="activity_root3",
            activity_subgroup_uid="activity_subgroup_root3",
            activity_group_uid="activity_group_root3",
        )
        service = StudyActivityScheduleService()
        service.handle_batch_operations(
            "study_root",
            [
                models.StudyActivityScheduleBatchInput(
                    method="POST",
                    content=models.StudyActivityScheduleCreateInput(
                        study_activity_uid=sa1.study_activity_uid,
                        study_visit_uid=baseline.uid,
                    ),
                ),
                models.StudyActivityScheduleBatchInput(
                    method="POST",
                    content=models.StudyActivityScheduleCreateInput(
                        study_activity_uid=sa2.study_activity_uid,
                        study_visit_uid=baseline.uid,
                    ),
                ),
            ],
        )
        schedules = service.get_all_schedules("study_root")
        assert len(schedules) == 2

        service.handle_batch_operations(
            "study_root",
            [
                models.StudyActivityScheduleBatchInput(
                    method="DELETE",
                    content=models.StudyActivityScheduleDeleteInput(
                        uid=schedules[0].study_activity_schedule_uid
                    ),
                ),
                models.StudyActivityScheduleBatchInput(
                    method="DELETE",
                    content=models.StudyActivityScheduleDeleteInput(
                        uid=schedules[1].study_activity_schedule_uid
                    ),
                ),
            ],
        )
        schedules = service.get_all_schedules("study_root")
        assert len(schedules) == 0
