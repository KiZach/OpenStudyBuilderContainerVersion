# pylint: disable=redefined-outer-name,unused-argument

import logging
from collections import defaultdict
from copy import deepcopy

import pytest

from clinical_mdr_api import config, models
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyActivitySchedule,
    StudySoAFootnote,
)
from clinical_mdr_api.domains.controlled_terminologies.utils import TermParentType
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_soa_footnote import SoAItemType
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstance,
)
from clinical_mdr_api.models.study_selections.study_epoch import StudyEpoch
from clinical_mdr_api.models.study_selections.study_soa_footnote import ReferencedItem
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.concepts.unit_definitions.unit_definition import (
    UnitDefinitionService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_codelist import (
    CTCodelistService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_term import CTTermService
from clinical_mdr_api.services.studies.study_activity_instance_selection import (
    StudyActivityInstanceSelectionService,
)
from clinical_mdr_api.services.studies.study_activity_schedule import (
    StudyActivityScheduleService,
)
from clinical_mdr_api.services.studies.study_activity_selection import (
    StudyActivitySelectionService,
)
from clinical_mdr_api.services.studies.study_epoch import StudyEpochService
from clinical_mdr_api.services.studies.study_flowchart import StudyFlowchartService
from clinical_mdr_api.services.studies.study_flowchart import _ as _gettext
from clinical_mdr_api.services.studies.study_visit import StudyVisitService
from clinical_mdr_api.services.utils.table_f import TableRow, TableWithFootnotes
from clinical_mdr_api.tests.integration.utils.data_library import inject_base_data
from clinical_mdr_api.tests.integration.utils.utils import LIBRARY_NAME, TestUtils
from clinical_mdr_api.tests.unit.services.test_study_flowchart import (
    check_hidden_row_propagation,
)

EPOCHS = {
    "Screening": {"color_hash": "#80DEEAFF"},
    "Treatment": {"color_hash": "#C5E1A5FF"},
    "Follow-Up": {"color_hash": "#BCAAA4FF"},
}
VISITS = {
    "V1": {
        "epoch": "Screening",
        "visit_contact_mode": "On Site Visit",
        "is_global_anchor_visit": True,
        "day": 0,
        "min_window": -7,
        "max_window": 3,
    },
    "V2": {
        "epoch": "Treatment",
        "visit_contact_mode": "On Site Visit",
        "day": 7,
        "min_window": -1,
        "max_window": 1,
    },
    "V3": {
        "epoch": "Treatment",
        "visit_contact_mode": "On Site Visit",
        "day": 21,
        "min_window": -1,
        "max_window": 1,
    },
    "V4": {
        "epoch": "Follow-Up",
        "consecutive_visit_group": "V4-5",
        "visit_contact_mode": "On Site Visit",
        "day": 28,
        "min_window": -1,
        "max_window": 1,
    },
    "V5": {
        "epoch": "Follow-Up",
        "consecutive_visit_group": "V4-5",
        "visit_contact_mode": "On Site Visit",
        "day": 35,
        "min_window": -1,
        "max_window": 1,
    },
    "V6": {
        "epoch": "Follow-Up",
        "visit_contact_mode": "Virtual Visit",
        "day": 49,
        "min_window": -3,
        "max_window": 3,
    },
}

# Mind if an activity is scheduled for a visit of a visit-group, then it must be scheduled for all visits of the group.
# Testing for safeguards on this is not in the scope of the tests of the SoA feature.
ACTIVITIES = {
    "Randomized": {
        "soa_group": "SUBJECT RELATED INFORMATION",
        "group": "Randomization",
        "subgroup": "Randomisation",
        "visits": ["V1"],
        "show_soa_group": False,
        "show_group": True,
        "show_subgroup": True,
        "show_activity": False,
        "instances": [
            {
                "class": "Randomization class",
                "name": "Randomized inst.",
                "topic_code": "RANDTC",
                "adam_param_code": "RADAM",
            }
        ],
    },
    "Weight": {
        "soa_group": "SUBJECT RELATED INFORMATION",
        "group": "General",
        "subgroup": "Body Measurements",
        "visits": ["V1", "V3"],
        "show_soa_group": False,
        "show_group": True,
        "show_subgroup": True,
        "show_activity": False,
        "instances": [
            {
                "class": "Weighting class",
                "name": "Weight in kg",
                "topic_code": "WEIGHTkg",
                "adam_param_code": "Adam Heavy",
            },
            {
                "class": "Weighting class",
                "name": "Weight in stones",
                "topic_code": "WEIGHTST",
                "adam_param_code": "Lightadam",
            },
        ],
    },
    "I agree": {
        "soa_group": "INFORMED CONSENT",
        "library_name": config.REQUESTED_LIBRARY_NAME,
        "is_data_collected": True,
        "visits": ["V6"],
        "show_soa_group": True,
        "show_group": False,
        "show_subgroup": False,
        "show_activity": True,
    },
    "Eligibility Criteria Met": {
        "soa_group": "SUBJECT RELATED INFORMATION",
        "group": "Eligibility Criteria",
        "subgroup": "Eligibility Criteria",
        "is_data_collected": False,
        "visits": [],
        "show_soa_group": False,
        "show_group": True,
        "show_subgroup": True,
        "show_activity": False,
        "instances": [
            {
                "class": "Eligibility Class",
                "name": "Subject is a human",
                "topic_code": "HUMAN",
                "adam_param_code": "HUM",
            },
            {
                "class": "Eligibility Class",
                "name": "Subject has one heart",
                "topic_code": "ONEHEART",
                "adam_param_code": "HEART1",
            },
        ],
    },
    "Parental Consent Obtained": {
        "soa_group": "SUBJECT RELATED INFORMATION",
        "group": "Eligibility Criteria",
        "subgroup": None,
        "library_name": config.REQUESTED_LIBRARY_NAME,
        "is_data_collected": False,
        "visits": [],
        "show_soa_group": False,
        "show_group": True,
        "show_subgroup": False,
        "show_activity": False,
    },
    "Systolic Blood Pressure": {
        "soa_group": "SAFETY",
        "group": "Vital Signs",
        "subgroup": "Vital Signs",
        "visits": ["V1", "V3", "V6"],
        "show_soa_group": True,
        "show_group": True,
        "show_subgroup": True,
        "show_activity": False,
    },
    "LDL Cholesterol": {
        "soa_group": "SUBJECT RELATED INFORMATION",
        "group": "Laboratory Assessments",
        "subgroup": "Lipids",
        "visits": ["V1"],
        "show_soa_group": False,
        "show_group": True,
        "show_subgroup": False,
        "show_activity": False,
    },
    "Mean glucose": {
        "soa_group": "SAFETY",
        "group": "General",
        "subgroup": "Self Measured Plasma glucose",
        "visits": ["V1", "V6"],
        "show_soa_group": True,
        "show_group": True,
        "show_subgroup": False,
        "show_activity": False,
    },
    "Creatine Kinase MM": {
        "soa_group": "EFFICACY",
        "group": "Laboratory Assessments",
        "subgroup": "Biochemistry",
        "visits": [],
        "show_soa_group": False,
        "show_group": False,
        "show_subgroup": False,
        "show_activity": True,
    },
    "Cholesterol": {
        "soa_group": "SUBJECT RELATED INFORMATION",
        "group": "Laboratory Assessments",
        "subgroup": "Lipids",
        "visits": ["V1", "V6"],
        "show_soa_group": False,
        "show_group": True,
        "show_subgroup": False,
        "show_activity": True,
    },
    "Height": {
        "soa_group": "SUBJECT RELATED INFORMATION",
        "group": "General",
        "subgroup": "Body Measurements",
        "visits": ["V1", "V2"],
        "show_soa_group": False,
        "show_group": True,
        "show_subgroup": True,
        "show_activity": False,
        "instances": [
            {
                "class": "Height class",
                "name": "Height cm",
                "topic_code": "Heigh-cm",
                "adam_param_code": "cmHeight",
            }
        ],
    },
    "Diastolic Blood Pressure": {
        "soa_group": "SAFETY",
        "group": "Vital Signs",
        "subgroup": "Vital Signs",
        "visits": ["V1", "V3", "V6"],
        "show_soa_group": True,
        "show_group": True,
        "show_subgroup": True,
        "show_activity": False,
    },
    "HbA1c": {
        "soa_group": "EFFICACY",
        "group": "Laboratory Assessments",
        "subgroup": "Glucose Metabolism",
        "visits": ["V1", "V2", "V4", "V5", "V6"],
        "show_soa_group": False,
        "show_group": False,
        "show_subgroup": True,
        "show_activity": False,
    },
    "HDL Cholesterol": {
        "soa_group": "SUBJECT RELATED INFORMATION",
        "group": "Laboratory Assessments",
        "subgroup": "Lipids",
        "visits": ["V4", "V5"],
        "show_soa_group": False,
        "show_group": True,
        "show_subgroup": False,
        "show_activity": False,
    },
    "Pulse Rate": {
        "soa_group": "SAFETY",
        "group": "Vital Signs",
        "subgroup": "Vital Signs",
        "visits": ["V2", "V4", "V5", "V6"],
        "show_soa_group": True,
        "show_group": True,
        "show_subgroup": True,
        "show_activity": False,
        "instances": [
            {
                "class": "Pulse class",
                "name": "Pulse per minuate",
                "topic_code": "pulman",
                "adam_param_code": "ppm",
            },
            {
                "class": "Pulse class",
                "name": "Evaluation point",
                "topic_code": "pulloc",
                "adam_param_code": "pudl",
            },
        ],
    },
    "Over 18": {
        "soa_group": "SUBJECT RELATED INFORMATION",
        "group": "Eligibility Criteria",
        "subgroup": "Other Eligibility Criteria",
        "library_name": config.REQUESTED_LIBRARY_NAME,
        "is_data_collected": False,
        "visits": [],
        "show_soa_group": False,
        "show_group": False,
        "show_subgroup": True,
        "show_activity": False,
    },
    "Albumin": {
        "soa_group": "SAFETY",
        "group": "AE Requiring Additional Data",
        "subgroup": "Laboratory Assessments",
        "visits": ["V2", "V3"],
        "show_soa_group": True,
        "show_group": False,
        "show_subgroup": False,
        "show_activity": False,
    },
}

FOOTNOTES = {
    "Dilution of hyperreal in ion-exchanged water applied orally": [],
    "Pharmacokinetic dance of molecules within the bloodstream": [
        {"type": SoAItemType.STUDY_VISIT.value, "name": "V4"},
        {
            "type": SoAItemType.STUDY_ACTIVITY_SCHEDULE.value,
            "visit": "V2",
            "activity": "Pulse Rate",
        },
        {"type": SoAItemType.STUDY_ACTIVITY.value, "name": "Diastolic Blood Pressure"},
    ],
    "Pharmacological jigsaw puzzle assembles a mosaic of therapeutic agents to paint the canvas of wellness": [
        {"type": SoAItemType.STUDY_SOA_GROUP.value, "name": "INFORMED CONSENT"},
        {
            "type": SoAItemType.STUDY_ACTIVITY_SCHEDULE.value,
            "visit": "V6",
            "activity": "Cholesterol",
        },
        {
            "type": SoAItemType.STUDY_ACTIVITY_SCHEDULE.value,
            "visit": "V1",
            "activity": "Cholesterol",
        },
        {
            "type": SoAItemType.STUDY_ACTIVITY_SCHEDULE.value,
            "visit": "V6",
            "activity": "I agree",
        },
        {"type": SoAItemType.STUDY_ACTIVITY_SUBGROUP.value, "name": "Lipids"},
        {"type": SoAItemType.STUDY_ACTIVITY.value, "name": "Parental Consent Obtained"},
        {"type": SoAItemType.STUDY_ACTIVITY_GROUP.value, "name": "General"},
    ],
    "In the desert of uncertainty, faith is the oasis": [],
    "The best way to predict your future is to create it": [
        {
            "type": SoAItemType.STUDY_ACTIVITY_SCHEDULE.value,
            "visit": "V3",
            "activity": "Albumin",
        },
    ],
    "Therapeutic gold under the guidance of synthetic sorcery": [
        {"type": SoAItemType.STUDY_EPOCH.value, "name": "Treatment"},
        {
            "type": SoAItemType.STUDY_ACTIVITY_SCHEDULE.value,
            "visit": "V5",
            "activity": "HDL Cholesterol",
        },
        {
            "type": SoAItemType.STUDY_ACTIVITY_SCHEDULE.value,
            "visit": "V2",
            "activity": "Height",
        },
        {
            "type": SoAItemType.STUDY_ACTIVITY_SCHEDULE.value,
            "visit": "V6",
            "activity": "I agree",
        },
        {"type": SoAItemType.STUDY_ACTIVITY_GROUP.value, "name": "Vital Signs"},
        {"type": SoAItemType.STUDY_ACTIVITY.value, "name": "Diastolic Blood Pressure"},
        {"type": SoAItemType.STUDY_ACTIVITY.value, "name": "I agree"},
    ],
    "When the winds of change blow, only those who adjust their sails find their destined harbor.": [
        {"type": SoAItemType.STUDY_ACTIVITY.value, "name": "Albumin"},
    ],
}

USER_INITIALS = "unknown-user"

log = logging.getLogger(__name__)


class TestData:
    database_name: str
    study: models.study_selections.study.Study
    unit_definitions: dict[str, models.UnitDefinitionModel]
    epoch_terms: dict[str, models.CTTerm]
    study_epochs: dict[str, StudyEpoch]
    visit_type_terms: dict[str, models.CTTerm]
    visit_contact_terms: dict[str, models.CTTerm]
    visit_timeref_terms: dict[str, models.CTTerm]
    study_visits: dict[str, models.StudyVisit]
    soa_group_terms: dict[str, models.CTTerm]
    activities: dict[str, models.Activity]
    activity_instances: dict[str, ActivityInstance]
    study_activities: dict[str, models.StudySelectionActivity]
    study_activity_instances: dict[str, models.StudySelectionActivityInstance]
    study_activity_schedules: list[StudyActivitySchedule]
    footnote_types: dict[str, models.CTTerm]
    footnotes: dict[str, models.Footnote]
    soa_footnotes: list[StudySoAFootnote]


def study_version(study: models.study_selections.study.Study) -> str:
    """Returns study version as string"""
    if (
        study.current_metadata.version_metadata.study_status
        == StudyStatus.RELEASED.value
    ):
        return study.current_metadata.version_metadata.version_number
    return study.current_metadata.version_metadata.version_timestamp.strftime(
        "LATEST on %Y-%m-%d %H:%M:%S Z"
    )


@pytest.fixture(scope="module")
def tst_data(request, temp_database):
    """Initialize test data"""
    test_data = TestData()

    log.info("%s fixture: injecting magic data", request.fixturename)
    test_data.study = inject_base_data()

    test_data.unit_definitions = {
        u.name: u
        for u in UnitDefinitionService(meta_repository=MetaRepository(USER_INITIALS))
        .get_all(library_name=LIBRARY_NAME)
        .items
    }

    test_data.epoch_terms = create_epoch_terms()

    test_data.study_epochs = create_study_epochs(
        EPOCHS, test_data.study, test_data.epoch_terms
    )

    test_data.visit_type_terms = create_visit_type_terms()

    test_data.visit_contact_terms = create_visit_contact_terms()

    test_data.visit_timeref_terms = create_visit_timeref_terms()

    test_data.study_visits = create_study_visits(
        VISITS,
        test_data.study,
        test_data.study_epochs,
        test_data.unit_definitions,
        test_data.visit_contact_terms,
        test_data.visit_timeref_terms,
        test_data.visit_type_terms,
    )

    test_data.soa_group_terms = create_soa_group_terms()

    test_data.activities = create_activities()

    TestUtils.lock_and_unlock_study(test_data.study.uid)

    test_data.study_activities = create_study_activities(
        test_data.study, test_data.activities, test_data.soa_group_terms
    )

    test_data.activity_instances = create_activity_instances(test_data.activities)

    test_data.study_activity_instances = get_study_activity_instances(test_data.study)

    test_data.study_activity_schedules = create_study_activity_schedules(
        test_data.study,
        test_data.study_activities,
        test_data.study_visits,
    )

    test_data.footnote_types = create_footnote_types()

    test_data.footnotes = create_footnotes(
        FOOTNOTES,
        test_data.footnote_types,
    )

    test_data.soa_footnotes = create_soa_footnotes(
        FOOTNOTES,
        test_data.footnotes,
        test_data.study,
        test_data.study_epochs,
        test_data.study_visits,
        test_data.study_activities,
        test_data.study_activity_instances,
        test_data.study_activity_schedules,
    )

    # Patch SoA Preferences as tests do not yet support baseline_as_time_zero
    TestUtils.patch_soa_preferences(test_data.study.uid, baseline_as_time_zero=False)

    return test_data


def create_epoch_terms() -> dict[str, models.CTTerm]:
    log.debug("creating epoch terms")

    ct_codelist_service = CTCodelistService()
    ct_term_service = CTTermService()
    terms: list[models.CTTerm] = []

    codelist = TestUtils.create_ct_codelist(
        name=config.STUDY_EPOCH_EPOCH_NAME,
        sponsor_preferred_name=config.STUDY_EPOCH_EPOCH_NAME,
        submission_value="EPOCH",
        extensible=True,
        library_name="CDISC",
        approve=True,
    )

    log.info(
        "created codelist: %s [%s]",
        codelist.name,
        codelist.codelist_uid,
    )

    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            code_submission_value="SCREENING",
            sponsor_preferred_name="Screening",
            # concept_id is missing
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            code_submission_value="FOLLOW-UP",
            sponsor_preferred_name="Follow-Up",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            code_submission_value="OBSERVATION",
            sponsor_preferred_name="Observation",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            code_submission_value="RUN-IN",
            sponsor_preferred_name="Run-in",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            code_submission_value="TREATMENT",
            sponsor_preferred_name="Treatment",
        )
    )

    for term in terms:
        ct_term_service.add_parent(
            term.term_uid,
            term.term_uid,
            TermParentType.PARENT_TYPE.value,
        )
        ct_term_service.add_parent(
            term.term_uid,
            term.term_uid,
            TermParentType.PARENT_SUB_TYPE.value,
        )
        ct_term_service.add_parent(
            term.term_uid,
            term.term_uid,
            TermParentType.VALID_FOR_EPOCH_TYPE.value,
        )

    codelist = TestUtils.create_ct_codelist(
        name=config.STUDY_EPOCH_TYPE_NAME,
        sponsor_preferred_name=config.STUDY_EPOCH_TYPE_NAME,
        submission_value="EPOCHTP",
        extensible=True,
        library_name="Sponsor",
        approve=True,
    )

    log.info(
        "created codelist: %s [%s]",
        codelist.name,
        codelist.codelist_uid,
    )

    for term in terms:
        ct_codelist_service.add_term(
            codelist_uid=codelist.codelist_uid, term_uid=term.term_uid, order=1
        )

    codelist = TestUtils.create_ct_codelist(
        name=config.STUDY_EPOCH_SUBTYPE_NAME,
        sponsor_preferred_name=config.STUDY_EPOCH_SUBTYPE_NAME,
        submission_value="EPOCHSTP",
        extensible=True,
        library_name="Sponsor",
        approve=True,
    )

    log.info(
        "created codelist: %s [%s]",
        codelist.name,
        codelist.codelist_uid,
    )

    for term in terms:
        ct_codelist_service.add_term(
            codelist_uid=codelist.codelist_uid, term_uid=term.term_uid, order=1
        )

    log.info(
        "created epoch terms: %s",
        {term.term_uid: term.sponsor_preferred_name for term in terms},
    )

    return {term.sponsor_preferred_name: term for term in terms}


def create_study_epochs(epoch_dict, study, epoch_terms) -> dict[str, StudyEpoch]:
    log.debug("creating StudyEpochs")

    epochs = {}

    for k, epo in epoch_dict.items():
        epoch = TestUtils.create_study_epoch(
            study_uid=study.uid,
            epoch_subtype=epoch_terms[k].term_uid,
            color_hash=epo.get("color_hash"),
        )

        epochs[k] = epoch

    log.info(
        "created StudyEpochs: %s",
        {epoch.uid: epoch.epoch_subtype_name for epoch in epochs.values()},
    )

    return epochs


def create_visit_type_terms() -> dict[str, models.CTTerm]:
    log.debug("creating visit type terms")

    terms: list[models.CTTerm] = []

    codelist = TestUtils.create_ct_codelist(
        name=config.STUDY_VISIT_TYPE_NAME,
        sponsor_preferred_name=config.STUDY_VISIT_TYPE_NAME,
        submission_value="TIMELB",
        extensible=True,
        approve=True,
    )

    log.info(
        "created codelist: %s [%s]",
        codelist.name,
        codelist.codelist_uid,
    )

    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="V_End of treatment",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="V_End of trial",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="V_Follow-up",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="V_Informed consent",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="V_No treatment",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="V_Non-visit",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="V_Randomisation",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="V_Screening",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="V_Treatment",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="V_Unscheduled",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="V_Washout",
        )
    )

    log.info(
        "visit type terms: %s",
        {term.term_uid: term.sponsor_preferred_name for term in terms},
    )

    return {term.sponsor_preferred_name: term for term in terms}


def create_visit_contact_terms() -> dict[str, models.CTTerm]:
    log.debug("creating visit contact terms")

    terms: list[models.CTTerm] = []

    codelist = TestUtils.create_ct_codelist(
        name=config.STUDY_VISIT_CONTACT_MODE_NAME,
        sponsor_preferred_name=config.STUDY_VISIT_CONTACT_MODE_NAME,
        submission_value="VISCNTMD",
        extensible=True,
        approve=True,
    )

    log.info(
        "created codelist: %s [%s]",
        codelist.name,
        codelist.codelist_uid,
    )

    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="On Site Visit",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="Phone Contact",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="Virtual Visit",
        )
    )

    log.info(
        "visit contact terms: %s",
        {term.term_uid: term.sponsor_preferred_name for term in terms},
    )

    return {term.sponsor_preferred_name: term for term in terms}


def create_visit_timeref_terms() -> dict[str, models.CTTerm]:
    log.debug("creating visit time-point-reference terms")

    terms: list[models.CTTerm] = []

    codelist = TestUtils.create_ct_codelist(
        name=config.STUDY_VISIT_TIMEREF_NAME,
        sponsor_preferred_name=config.STUDY_VISIT_TIMEREF_NAME,
        extensible=True,
        approve=True,
    )

    log.info(
        "created codelist: %s [%s]",
        codelist.name,
        codelist.codelist_uid,
    )

    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="BASELINE",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="Global anchor visit",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="BASELINE2",
        )
    )

    log.info(
        "visit time-point-reference terms: %s",
        {term.term_uid: term.sponsor_preferred_name for term in terms},
    )

    return {term.sponsor_preferred_name: term for term in terms}


def create_study_visits(
    visits_dict,
    study,
    study_epochs,
    unit_definitions,
    visit_contact_terms,
    visit_timeref_terms,
    visit_type_terms,
) -> dict[str, models.StudyVisit]:
    log.debug("creating StudyVisits")

    visits = {}

    for k, vis in visits_dict.items():
        epoch = study_epochs[vis["epoch"]]

        visit = TestUtils.create_study_visit(
            study_uid=study.uid,
            study_epoch_uid=epoch.uid,
            visit_type_uid=visit_type_terms["V_Treatment"].term_uid,
            time_reference_uid=visit_timeref_terms["Global anchor visit"].term_uid,
            time_value=vis["day"],
            time_unit_uid=unit_definitions["day"].uid,
            visit_sublabel_codelist_uid=None,
            visit_sublabel_reference=None,
            consecutive_visit_group=vis.get("consecutive_visit_group"),
            show_visit=True,
            min_visit_window_value=vis.get("min_window", 0),
            max_visit_window_value=vis.get("max_window", 0),
            visit_window_unit_uid=unit_definitions["day"].uid,
            description=None,
            start_rule=None,
            end_rule=None,
            visit_contact_mode_uid=visit_contact_terms[
                vis["visit_contact_mode"]
            ].term_uid,
            epoch_allocation_uid=None,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
            is_global_anchor_visit=vis.get("is_global_anchor_visit", False),
        )

        visits[k] = visit

    log.info(
        "StudyVisits: %s",
        {k: visit.uid for k, visit in visits.items()},
    )

    return visits


def create_soa_group_terms() -> dict[str, models.CTTerm]:
    log.debug("creating SoA Group terms")

    terms: list[models.CTTerm] = []

    codelist = TestUtils.create_ct_codelist(
        name="Flowchart Group",
        sponsor_preferred_name="Flowchart Group",
        submission_value="FLWCRTGRP",
        extensible=True,
        approve=True,
    )

    log.info(
        "created codelist: %s [%s]",
        codelist.name,
        codelist.codelist_uid,
    )

    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="INFORMED CONSENT",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="ELIGIBILITY AND OTHER CRITERIA",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="SUBJECT RELATED INFORMATION",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="EFFICACY",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="SAFETY",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="GENETICS",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="PHARMACOKINETICS",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="PHARMACODYNAMICS",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="BIOMARKERS",
        )
    )
    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="HIDDEN",
        )
    )

    log.info(
        "created SoA Group terms: %s",
        {term.term_uid: term.sponsor_preferred_name for term in terms},
    )

    return {term.sponsor_preferred_name: term for term in terms}


def create_activities() -> dict[str, models.Activity]:
    log.debug("creating Activities")

    activity_groups = {}
    activity_subgroups = {}
    activities = {}

    for name, act in reversed(ACTIVITIES.items()):
        group_name = act.get("group")
        if group_name and group_name not in activity_groups:
            activity_groups[group_name] = TestUtils.create_activity_group(
                name=group_name
            )

        subgroup_name = act.get("subgroup")
        if subgroup_name and subgroup_name not in activity_subgroups:
            activity_subgroups[subgroup_name] = TestUtils.create_activity_subgroup(
                name=subgroup_name,
                activity_groups=[activity_groups[group_name].uid] if group_name else [],
            )

        activities[name] = TestUtils.create_activity(
            name=name,
            activity_groups=[activity_groups[group_name].uid] if group_name else [],
            activity_subgroups=(
                [activity_subgroups[subgroup_name].uid] if subgroup_name else []
            ),
            library_name=act.get("library_name", "Sponsor"),
        )

    log.info(
        "created Activities: %s",
        {activity.uid: activity.name for activity in activities.values()},
    )

    return activities


def create_activity_instances(activities) -> dict[str, list[ActivityInstance]]:
    log.debug("creating ActivityInstances")

    activity_instances = {}
    activity_instance_classes = {}

    for name, act in ACTIVITIES.items():
        for inst in act.get("instances", []):
            instance_class = activity_instance_classes.get(inst["class"])
            if not instance_class:
                activity_instance_classes[inst["class"]] = (
                    instance_class := TestUtils.create_activity_instance_class(
                        name=inst["class"]
                    )
                )

            activity = activities[name]

            activity_instance = TestUtils.create_activity_instance(
                name=inst["name"],
                activity_instance_class_uid=instance_class.uid,
                name_sentence_case=inst["name"].lower(),
                topic_code=inst.get("topic_code", None),
                adam_param_code=inst.get("adam_param_code", None),
                is_required_for_activity=True,
                activities=[activity.uid],
                activity_groups=(
                    [activity.activity_groupings[0].activity_group_uid]
                    if activity.activity_groupings
                    else []
                ),
                activity_subgroups=(
                    [activity.activity_groupings[0].activity_subgroup_uid]
                    if activity.activity_groupings
                    else []
                ),
                activity_items=[],
            )

            activity_instances.setdefault(name, []).append(activity_instance)

    log.info(
        "created ActivityInstances: %s",
        {
            activity_instance.uid: activity_instance.name
            for activity_instance_list in activity_instances.values()
            for activity_instance in activity_instance_list
        },
    )

    return activity_instances


def create_study_activities(
    study, activities, soa_group_terms
) -> dict[str, models.StudySelectionActivity]:
    log.debug("creating StudyActivities")

    study_activites = {}

    for name, act in ACTIVITIES.items():
        activity = activities[name]

        study_activity = TestUtils.create_study_activity(
            study_uid=study.uid,
            activity_uid=activity.uid,
            activity_group_uid=(
                activity.activity_groupings[0].activity_group_uid
                if activity.activity_groupings
                else None
            ),
            activity_subgroup_uid=(
                activity.activity_groupings[0].activity_subgroup_uid
                if activity.activity_groupings
                else None
            ),
            soa_group_term_uid=(
                soa_group_terms[act["soa_group"]].term_uid
                if act.get("soa_group")
                else None
            ),
        )

        TestUtils.patch_study_activity_schedule(
            study_uid=study.uid,
            study_selection_uid=study_activity.study_activity_uid,
            show_activity_in_protocol_flowchart=act.get("show_activity"),
            show_activity_subgroup_in_protocol_flowchart=act.get("show_subgroup"),
            show_activity_group_in_protocol_flowchart=act.get("show_group"),
            show_soa_group_in_protocol_flowchart=act.get("show_soa_group", False),
            soa_group_term_uid=(
                soa_group_terms[act["soa_group"]].term_uid
                if act.get("soa_group")
                else None
            ),
        )

        study_activites[name] = study_activity

    log.info(
        "created StudyActivities: %s",
        {
            sa.study_activity_uid: f"{sa.activity.name}"
            for sa in study_activites.values()
        },
    )

    return study_activites


def get_study_activity_instances(
    study,
) -> dict[str, models.StudySelectionActivityInstance]:
    log.debug("fetching StudyActivityInstances")

    study_activity_instances: list[models.StudySelectionActivityInstance] = (
        StudyActivityInstanceSelectionService()
        .get_all_selection(study_uid=study.uid)
        .items
    )

    log.info(
        "fetched StudyActivityInstances: %s",
        ", ".join(sai.study_activity_instance_uid for sai in study_activity_instances),
    )

    study_activity_instance_map = {
        ssa.study_activity_uid: ssa for ssa in study_activity_instances
    }

    return study_activity_instance_map


def create_study_activity_schedules(
    study, study_activities, study_visits
) -> list[StudyActivitySchedule]:
    log.debug("creating StudyActivitySchedules")

    schedules = []

    for activity_name, act in ACTIVITIES.items():
        for visit_name in act.get("visits", []):
            schedule = TestUtils.create_study_activity_schedule(
                study_uid=study.uid,
                study_activity_uid=study_activities[activity_name].study_activity_uid,
                study_visit_uid=study_visits[visit_name].uid,
            )
            schedules.append(schedule)

    log.info(
        "created StudyActivitySchedules: %s",
        ", ".join(schedule.study_activity_schedule_uid for schedule in schedules),
    )

    return schedules


def create_footnote_types() -> dict[str, models.CTTerm]:
    log.debug("creating footnote-type terms")

    terms: list[models.CTTerm] = []

    codelist = TestUtils.create_ct_codelist(
        name="Footnote Type",
        sponsor_preferred_name="Footnote Type",
        submission_value="FTNTTP",
        extensible=True,
        approve=True,
    )

    log.info(
        "created codelist: %s [%s]",
        codelist.name,
        codelist.codelist_uid,
    )

    terms.append(
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="SoA Footnote",
            code_submission_value="SOAFOOTNOTE",
            name_submission_value="SOAFOOTNOTE",
        )
    )

    log.info(
        "visit footnote-type terms: %s",
        {term.term_uid: term.sponsor_preferred_name for term in terms},
    )

    return {term.sponsor_preferred_name: term for term in terms}


def create_footnotes(footnotes_dict, footnote_types) -> dict[str, models.Footnote]:
    log.debug("creating footnotes")

    footnotes: dict[str, models.Footnote] = {}

    for name in footnotes_dict:
        template: models.FootnoteTemplate = TestUtils.create_footnote_template(
            name=f"<p>{name}</p>",
            library_name=config.REQUESTED_LIBRARY_NAME,
            type_uid=footnote_types["SoA Footnote"].term_uid,
            approve=True,
        )
        footnotes[name] = TestUtils.create_footnote(
            footnote_template_uid=template.uid,
            library_name=config.REQUESTED_LIBRARY_NAME,
            approve=True,
        )

    log.info(
        "created Footnotes: %s",
        {fn.uid: {"template": fn.footnote_template.uid} for fn in footnotes.values()},
    )

    return footnotes


def create_soa_footnotes(
    footnotes_dict,
    footnotes,
    study,
    study_epochs,
    study_visits,
    study_activities,
    study_activity_instances,
    study_activity_schedules,
) -> list[StudySoAFootnote]:
    log.debug("creating StudySoAFootnotes")

    # Map activity group names to uid
    study_soa_group_uids = defaultdict(set)
    study_activity_group_uids = defaultdict(set)
    study_activity_subgroup_uids = defaultdict(set)

    for activities in (
        study_activities.values(),
        study_activity_instances.values(),
    ):
        for activity in activities:
            study_soa_group_uids[activity.study_soa_group.soa_group_name].add(
                activity.study_soa_group.study_soa_group_uid
            )

            if activity.study_activity_group:
                study_activity_group_uids[
                    activity.study_activity_group.activity_group_name
                ].add(activity.study_activity_group.study_activity_group_uid)

            if activity.study_activity_subgroup:
                study_activity_subgroup_uids[
                    activity.study_activity_subgroup.activity_subgroup_name
                ].add(activity.study_activity_subgroup.study_activity_subgroup_uid)

    # Map activity+visit uids to schedule uids
    study_activity_schedule_uids = {}
    for schedule in study_activity_schedules:
        study_activity_schedule_uids[
            schedule.study_activity_uid, schedule.study_visit_uid
        ] = schedule.study_activity_schedule_uid

    soa_footnotes: list[StudySoAFootnote] = []

    for name, refs in footnotes_dict.items():
        footnote: models.Footnote = footnotes[name]
        referenced_items = []

        for ref in refs:
            uids = set()
            typ = ref.get("type")
            assert typ
            assert typ in {t.value for t in SoAItemType}

            if typ == SoAItemType.STUDY_ACTIVITY_SCHEDULE.value:
                visit_name = ref.get("visit")
                activity_name = ref.get("activity")

                assert visit_name and activity_name

                assert visit_name in study_visits
                visit_uid = study_visits[visit_name].uid

                assert activity_name in study_activities
                activity_uid = study_activities[activity_name].study_activity_uid
                name = activity_name

                assert (
                    activity_uid,
                    visit_uid,
                ) in study_activity_schedule_uids, (
                    f"{typ} '{name}' not scheduled for visit '{visit_name}'"
                )
                uids = {study_activity_schedule_uids[activity_uid, visit_uid]}
                name = f"{name} {visit_name}"

            else:
                assert (name := ref.get("name"))

                if typ == SoAItemType.STUDY_EPOCH.value:
                    assert name in study_epochs
                    uids = {study_epochs[name].uid}

                if typ == SoAItemType.STUDY_VISIT.value:
                    assert name in study_visits
                    uids = {study_visits[name].uid}

                if typ == SoAItemType.STUDY_ACTIVITY.value:
                    assert name in study_activities
                    uids = {study_activities[name].study_activity_uid}

                if typ == SoAItemType.STUDY_SOA_GROUP.value:
                    assert name in study_soa_group_uids
                    uids = study_soa_group_uids[name]

                if typ == SoAItemType.STUDY_ACTIVITY_GROUP.value:
                    assert name in study_activity_group_uids
                    uids = study_activity_group_uids[name]

                if typ == SoAItemType.STUDY_ACTIVITY_SUBGROUP.value:
                    assert name in study_activity_subgroup_uids
                    uids = study_activity_subgroup_uids[name]

            assert uids, f"Footnote reference type '{typ}' not implemented"

            for uid in uids:
                referenced_items.append(
                    ReferencedItem(item_name=name, item_type=typ, item_uid=uid)
                )

        soa_footnotes.append(
            TestUtils.create_study_soa_footnote(
                study_uid=study.uid,
                footnote_template_uid=footnote.footnote_template.uid,
                referenced_items=referenced_items,
            )
        )

    log.info(
        "created StudySoAFootnotes: %s",
        {fn.uid: {"template": fn.footnote_template.uid} for fn in footnotes.values()},
    )

    return soa_footnotes


@pytest.fixture(scope="module")
def detailed_soa_table__days(tst_data: TestData) -> TableWithFootnotes:
    """get non-operational SoA table directly from StudyFlowchartService"""
    service = StudyFlowchartService()
    soa_table = service.get_flowchart_table(
        study_uid=tst_data.study.uid, operational=False, time_unit="day"
    )
    return soa_table


@pytest.fixture(scope="module")
def detailed_soa_table__weeks(tst_data: TestData) -> TableWithFootnotes:
    """get non-operational SoA table directly from StudyFlowchartService"""
    service = StudyFlowchartService()
    soa_table = service.get_flowchart_table(
        study_uid=tst_data.study.uid, operational=False, time_unit="week"
    )
    return soa_table


@pytest.fixture(scope="module")
def protocol_soa_table__days(tst_data: TestData) -> TableWithFootnotes:
    """get non-operational SoA table directly from StudyFlowchartService"""
    service = StudyFlowchartService()
    soa_table = service.get_flowchart_table(
        study_uid=tst_data.study.uid, hide_soa_groups=True, time_unit="day"
    )
    StudyFlowchartService.propagate_hidden_rows(soa_table)
    return soa_table


@pytest.fixture(scope="module")
def protocol_soa_table__weeks(tst_data: TestData) -> TableWithFootnotes:
    """get non-operational SoA table directly from StudyFlowchartService"""
    service = StudyFlowchartService()
    soa_table = service.get_flowchart_table(
        study_uid=tst_data.study.uid, hide_soa_groups=True, time_unit="week"
    )
    StudyFlowchartService.propagate_hidden_rows(soa_table)
    return soa_table


@pytest.fixture(scope="module")
def operational_soa_table__days(tst_data: TestData) -> TableWithFootnotes:
    """get non-operational SoA table directly from StudyFlowchartService"""
    service = StudyFlowchartService()
    soa_table = service.get_flowchart_table(
        study_uid=tst_data.study.uid, operational=True, time_unit="day"
    )
    return soa_table


@pytest.fixture(scope="module")
def operational_soa_table__weeks(tst_data: TestData) -> TableWithFootnotes:
    """get non-operational SoA table directly from StudyFlowchartService"""
    service = StudyFlowchartService()
    soa_table = service.get_flowchart_table(
        study_uid=tst_data.study.uid, operational=True, time_unit="week"
    )
    return soa_table


@pytest.mark.parametrize(
    "time_unit, operational, hide_soa_groups",
    [
        (None, None, False),
        (None, False, False),
        (None, True, False),
        ("day", None, False),
        ("day", False, False),
        ("day", True, False),
        ("week", None, False),
        ("week", False, False),
        ("week", True, False),
        (None, False, True),
        ("week", None, True),
        ("day", None, True),
    ],
)
def test_get_flowchart_table(
    tst_data: TestData,
    time_unit: str,
    operational: bool,
    hide_soa_groups: bool,
):
    service = StudyFlowchartService()
    table = service.get_flowchart_table(
        study_uid=tst_data.study.uid,
        operational=operational,
        time_unit=time_unit,
        hide_soa_groups=hide_soa_groups,
    )

    # Collect test data for comparation

    if time_unit is None:
        service = StudyFlowchartService()
        time_unit = service.get_preferred_time_unit(study_uid=tst_data.study.uid)

    study_epochs: list[StudyEpoch] = (
        StudyEpochService()
        .get_all_epochs(study_uid=tst_data.study.uid, sort_by={"order": True})
        .items
    )
    study_visits: list[models.StudyVisit] = (
        StudyVisitService(study_uid=tst_data.study.uid)
        .get_all_visits(study_uid=tst_data.study.uid, sort_by={"order": True})
        .items
    )
    study_activities_map: dict[str, models.StudySelectionActivity] = {
        ssa.study_activity_uid: ssa
        for ssa in StudyActivitySelectionService()
        .get_all_selection(study_uid=tst_data.study.uid)
        .items
    }
    study_activity_instances_map: list[models.StudySelectionActivityInstance] = {
        ssai.study_activity_instance_uid: ssai
        for ssai in StudyActivityInstanceSelectionService()
        .get_all_selection(study_uid=tst_data.study.uid)
        .items
    }
    study_activity_schedules: list[
        models.StudyActivitySchedule
    ] = StudyActivityScheduleService().get_all_schedules(
        study_uid=tst_data.study.uid,
        operational=operational,
    )

    # Test title
    assert table.title == _gettext("protocol_flowchart")

    # Test dimensions
    check_flowchart_table_dimensions(table)

    # Test first header row
    check_flowchart_table_first_row(table, operational, study_epochs, study_visits)

    # Test visit header rows
    visit_idx_by_uid = check_flowchart_table_visit_rows(
        table, operational, time_unit, study_visits
    )

    # Test the rest of the rows

    rows_by_uid = {}
    row_idx_by_uid = {}
    soa_group_id = activity_group_id = activity_subgroup_id = activity_uid = None

    for idx, row in enumerate(
        table.rows[table.num_header_rows :], start=table.num_header_rows
    ):
        study_selection = None

        for ref in row.cells[0].refs or []:
            assert (
                ref and ref.uid
            ), f"Referenced uid must not be empty in row {idx} column 0"

            if ref.type == "CTTerm":
                soa_group_id = ref.uid
                activity_group_id = activity_subgroup_id = activity_uid = None

            if ref.type == "ActivityGroup":
                activity_group_id = ref.uid
                activity_subgroup_id = activity_uid = None

            if ref.type == "ActivitySubGroup":
                activity_subgroup_id = ref.uid
                activity_uid = None

            if ref.type == SoAItemType.STUDY_ACTIVITY.value:
                activity_uid = ref.uid
                study_selection: models.StudySelectionActivity = study_activities_map[
                    ref.uid
                ]

            if ref.type == SoAItemType.STUDY_ACTIVITY_INSTANCE.value:
                study_selection: models.StudySelectionActivityInstance = (
                    study_activity_instances_map[ref.uid]
                )
                assert study_selection.study_activity_uid == activity_uid

            if hide_soa_groups and soa_group_id is None and ref.type == "ActivityGroup":
                assert activity_group_id not in rows_by_uid, (
                    f"With hide_soa_groups and non-visible SoAGroup, "
                    f"only one row should reference {activity_group_id} until row {idx}"
                )

            rows_by_uid[ref.uid] = row
            row_idx_by_uid[ref.uid] = idx

        if study_selection:
            # THEN parent group rows are present in SoA
            # THEN parent group rows come in order (soa_group > activity_group > activity_subgroup [ > activity ] [ > activity_instance ])

            if (
                hide_soa_groups
                and not study_selection.show_soa_group_in_protocol_flowchart
            ):
                assert (
                    soa_group_id is None
                ), "With hide_soa_groups non-visible SoA Groups should be excluded"

            else:
                assert (
                    study_selection.study_soa_group.soa_group_term_uid == soa_group_id
                )

            assert (
                study_selection.study_activity_group.activity_group_uid
                == activity_group_id
            )

            assert (
                study_selection.study_activity_subgroup.activity_subgroup_uid
                == activity_subgroup_id
            )

            assert_error_msg = (
                f"Parent rows are not in order: SoAGroup[{row_idx_by_uid.get(soa_group_id)}]"
                f" ActivityGroup[{row_idx_by_uid.get(activity_group_id)}]"
                f" ActivitySubGroup[{row_idx_by_uid.get(activity_subgroup_id)}]"
                f" {study_selection.study_activity_uid}[{idx}]"
            )
            prev = -1
            for i in filter(
                lambda x: x is not None,
                (
                    row_idx_by_uid.get(soa_group_id),
                    row_idx_by_uid.get(activity_group_id),
                    row_idx_by_uid.get(activity_subgroup_id),
                    idx,
                ),
            ):
                assert i > prev, assert_error_msg
                prev = i

    # THEN all study activities are present in detailed and operational SoA tables (regardless whether scheduled for any visit)
    for activity in tst_data.study_activities.values():
        if (
            operational
            and activity.activity.library_name == config.REQUESTED_LIBRARY_NAME
        ):
            # THEN Study Activity Placeholders are not shown in operational SoA
            assert (
                activity.study_activity_uid not in rows_by_uid
            ), f"{activity.study_activity_uid} should not be shown in operational SoA table"
        else:
            assert (
                activity.study_activity_uid in rows_by_uid
            ), f"{activity.study_activity_uid} not found in SoA table"

    # THEN all study activity instances are present in operational SoA table (regardless whether scheduled for any visit)
    if operational:
        for activity in tst_data.study_activity_instances.values():
            if activity.activity_instance:
                assert (
                    activity.study_activity_instance_uid in rows_by_uid
                ), f"{activity.study_activity_instance_uid} not found in SoA table"

    for sas in study_activity_schedules:
        if operational and sas.study_activity_instance_uid:
            assert (
                sas.study_activity_instance_uid in study_activity_instances_map
            ), f"StudyActivityInstance {sas.study_activity_instance_uid} not found"
            study_activity_instance = study_activity_instances_map[
                sas.study_activity_instance_uid
            ]
            study_activity = study_activities_map[
                study_activity_instance.study_activity_uid
            ]

        else:
            assert (
                sas.study_activity_uid in study_activities_map
            ), f"StudyActivity {sas.study_activity_uid} not found"
            study_activity = study_activities_map[sas.study_activity_uid]

        assert (
            sas.study_visit_uid in visit_idx_by_uid
        ), f"No column reference to visit {sas.study_visit_uid}"
        col_idx = visit_idx_by_uid[sas.study_visit_uid]

        # WHEN not operational SoA
        if not operational:
            assert (
                sas.study_activity_uid in rows_by_uid
            ), f"No row with reference to activity {sas.study_activity_uid}"
            row: TableRow = rows_by_uid[sas.study_activity_uid]

            # THEN Activity name in 1st row
            assert row.cells[0].text == study_activity.activity.name

            # THEN scheduled activities have crosses for visits
            assert row.cells[col_idx].text == "X", (
                f"Scheduled {sas.study_activity_schedule_uid} activity {sas.study_activity_uid}"
                f" for visit {sas.study_visit_uid} has no cross on visible StudyActivity level"
            )

            # THEN show/hide row based on show_activity_in_protocol_flowchart property
            assert row.hide == (not study_activity.show_activity_in_protocol_flowchart)

        # WHEN operational SoA
        # study_activity_instance.activity_instance is None for Activity Instance Placeholders
        elif (
            sas.study_activity_instance_uid
            and study_activity_instance.activity_instance
        ):
            assert (
                sas.study_activity_instance_uid in rows_by_uid
            ), f"Row not found with reference to StudyActivityInstance.uid {sas.study_activity_instance_uid}"
            row = rows_by_uid[sas.study_activity_instance_uid]

            # THEN Activity Instance name in 1st row
            assert row.cells[0].text == study_activity_instance.activity_instance.name

            # THEN Topic code is in 2nd row
            assert row.cells[1].text == (
                study_activity_instance.activity_instance.topic_code or ""
            )

            # THEN ADaM param code is in 3nd row
            assert row.cells[2].text == (
                study_activity_instance.activity_instance.adam_param_code or ""
            )

            # THEN scheduled activity instances have crosses for visits
            assert row.cells[col_idx].text == "X", (
                f"Scheduled {sas.study_activity_schedule_uid} activity {sas.study_activity_uid}"
                f" instance {sas.study_activity_instance_uid} for visit {sas.study_visit_uid}"
                " has no cross on visible StudyActivityInstance level"
            )

            # THEN show/hide row based on show_activity_instance_in_protocol_flowchart property
            assert row.hide == (
                not study_activity_instance.show_activity_instance_in_protocol_flowchart
            )

    if operational:
        ensure_flowchart_table_has_no_footnotes(table)
    else:
        check_flowchart_table_footnotes(table, tst_data.soa_footnotes)


def check_flowchart_table_dimensions(table):
    """tests dimensions of SoA table"""

    num_cols = sum(cell.span for cell in table.rows[0].cells)
    for i, row in enumerate(table.rows[1:], start=1):
        # THEN number of columns are the same in all rows
        assert len(row.cells) <= num_cols, f"Unexpected number of columns in row {i}"
        assert (
            sum(cell.span for cell in row.cells) == num_cols
        ), f"Unexpected span of columns in row {i}"
    # THEN table has 4 header rows
    assert table.num_header_rows == 4
    # THEN table has 1 header column
    assert table.num_header_cols == 1


def check_flowchart_table_first_row(table, operational, study_epochs, study_visits):
    """tests first header row of study SoA table"""

    row = table.rows[0]

    # THEN first header row is visible
    assert not row.hide

    # THEN first cell text is empty
    assert not row.cells[0].text

    if operational:
        # THEN has operational SoA column headers
        assert row.cells[1].text == _gettext("topic_code")
        assert row.cells[2].text == _gettext("adam_param_code")

    num_visits_per_epoch = defaultdict(int)
    # only one visit per group is considered
    visit: models.StudyVisit
    for _, e in {
        (visit.consecutive_visit_group or visit.visit_name, visit.study_epoch_name)
        for visit in study_visits
    }:
        num_visits_per_epoch[e] += 1

    i = 3 if operational else 1
    epoch: StudyEpoch
    for epoch in study_epochs:
        cell = row.cells[i]

        # THEN cell style is header1
        assert cell.style == "header1"

        # THEN cell text is epoch name
        assert cell.text == epoch.epoch_name

        # THEN cell refs
        assert len(cell.refs) == 1
        assert cell.refs[0].type == SoAItemType.STUDY_EPOCH.value
        assert cell.refs[0].uid == epoch.uid

        # THEN span is number of visits
        assert cell.span == num_visits_per_epoch[epoch.epoch_name]

        for j in range(1, cell.span):
            # THEN span of following cells are 0 for the next visits of the epoch
            assert row.cells[i + j].span == 0

            # THEN text of following cells are empty
            assert not row.cells[i + j].text

        i += cell.span


def check_flowchart_table_visit_rows(table, operational, time_unit, study_visits):
    """test visit header rows of SoA table"""

    # THEN Second row label text is
    assert table.rows[1].cells[0].text == _gettext("visit_short_name")

    # THEN Third row label text is
    assert _gettext(
        f"study_{time_unit}"
    ), f"translation key not found: study_{time_unit}"
    assert table.rows[2].cells[0].text == _gettext(f"study_{time_unit}")

    # THEN Fourth row label text is
    assert table.rows[3].cells[0].text == _gettext("visit_window")

    for i in range(1, 4):
        # THEN Rows label style
        assert table.rows[i].cells[0].style == f"header{i+1}"

        # THEN Rows are visible
        assert not table.rows[i].hide

    visit_groups: dict[str, models.StudyVisit] = {}
    visit_idx_by_uid: dict[str, int] = {}
    for visit in study_visits:
        group_name = visit.consecutive_visit_group or visit.visit_name
        visit_groups.setdefault(group_name, []).append(visit)
        visit_idx_by_uid[visit.uid] = len(visit_groups) + (2 if operational else 0)

    for i, (group_name, visits) in enumerate(
        visit_groups.items(), start=3 if operational else 1
    ):
        visit = visits[0]

        # THEN visits name in second row
        assert (
            table.rows[1].cells[i].text == visit.consecutive_visit_group
            or visit.visit_name
        )

        # THEN visits ref in second row
        assert len(table.rows[1].cells[i].refs) == len(visits)
        assert {ref.type for ref in table.rows[1].cells[i].refs} == {
            SoAItemType.STUDY_VISIT.value
        }, "Invalid reference type"
        assert {ref.uid for ref in table.rows[1].cells[i].refs} == {
            visit.uid for visit in visits
        }, "Referenced visit uids does not match"

        # THEN study weeks/days in second row
        if len(visits) > 1:
            if time_unit == "week":
                assert (
                    table.rows[2].cells[i].text
                    == f"{visits[0].study_week_number:d}-{visits[-1].study_week_number:d}"
                )
            else:
                assert (
                    table.rows[2].cells[i].text
                    == f"{visits[0].study_day_number:d}-{visits[-1].study_day_number:d}"
                )
        else:
            if time_unit == "week":
                assert table.rows[2].cells[i].text == str(visit.study_week_number)
            else:
                assert table.rows[2].cells[i].text == str(visit.study_day_number)

        # THEN text in forth row
        if visit.min_visit_window_value == -visit.max_visit_window_value:
            assert (
                table.rows[3].cells[i].text == f"±{visit.max_visit_window_value:0.0f}"
            )
        else:
            assert (
                table.rows[3].cells[i].text
                == f"{visit.min_visit_window_value:+0.0f}/{visit.max_visit_window_value:+0.0f}"
            )

    for i, cell in enumerate(table.rows[0].cells):
        if cell.text and cell.span:
            # THEN first row cell style is header1
            assert cell.style == "header2" if operational and i < 2 else "header1"

    for cell in table.rows[1].cells:
        # THEN second row cell span is 1
        assert cell.span == 1
        if cell.text:
            # THEN second row cell style is header2
            assert cell.style == "header2"

    for cell in table.rows[2].cells:
        # THEN third row cell span is 1
        assert cell.span == 1
        if cell.text:
            # THEN third row cell style is header3
            assert cell.style == "header3"

    # THEN forth row style is header4
    for cell in table.rows[3].cells:
        # THEN forth row cell span is 1
        if cell.text and cell.span:
            assert cell.style == "header4"

    return visit_idx_by_uid


def check_flowchart_table_footnotes(table: dict, soa_footnotes: list[StudySoAFootnote]):
    """check footnotes and their references in flowchart table"""

    symbol_ref_uid_map: dict[str, set] = defaultdict(set)
    soa_ref_uids = set()

    for r_idx, row in enumerate(table.rows):
        for c_idx, cell in enumerate(row.cells):
            has_footnotes = cell.footnotes

            if has_footnotes:
                assert (
                    cell.refs
                ), f"Cell [{r_idx},{c_idx}] without references should not have any footnotes"

            if not cell.refs:
                continue

            for ref in cell.refs:
                soa_ref_uids.add(ref.uid)

                if has_footnotes:
                    for symbol in cell.footnotes:
                        symbol_ref_uid_map[symbol].add(ref.uid)

    keys = list(symbol_ref_uid_map.keys())
    assert keys == sorted(keys), "Invalid order of footnotes symbols"

    if keys:
        assert table.footnotes, "Missing table footnotes"

    assert list(table.footnotes.keys()) == sorted(
        table.footnotes.keys()
    ), "Invalid footnote order"
    assert set(keys).issubset(
        table.footnotes.keys()
    ), "Invalid footnote symbols or missing footnote for symbol"

    footnote_uid_symbol_map: dict[str, str] = {
        fn.uid: sym for sym, fn in table.footnotes.items()
    }

    for footnote in soa_footnotes:
        assert (
            footnote.uid in footnote_uid_symbol_map
        ), f"No symbol found for footnote {footnote.uid}"
        symbol = footnote_uid_symbol_map[footnote.uid]

        # THEN verify footnote text matches footnote template text
        assert (
            table.footnotes[symbol].text_plain == footnote.footnote_template.name_plain
        )
        assert table.footnotes[symbol].text_html == footnote.footnote_template.name

        # Must filter out uids not giving any SoA row unless Activities can share StudyActivityGroup and SubGroup nodes
        footnote_referenced_uids = {
            ref.item_uid
            for ref in footnote.referenced_items
            if ref.item_uid in soa_ref_uids
        }
        referenced_uids_in_soa = set(symbol_ref_uid_map[symbol])

        if footnote_referenced_uids:
            # THEN verify footnotes are referenced in SoA
            footnote_uids_not_referenced_in_soa = (
                footnote_referenced_uids - referenced_uids_in_soa
            )
            assert not footnote_uids_not_referenced_in_soa

        else:
            # THEN a footnote without references should not be referenced in any cell of the SoA
            assert not referenced_uids_in_soa


def ensure_flowchart_table_has_no_footnotes(table: dict):
    """ensure SoA flowchart does not have footnotes"""

    for r_idx, row in enumerate(table.rows):
        for c_idx, cell in enumerate(row.cells):
            assert (
                not cell.footnotes
            ), f"flowchart table should not have footnote symbols row {r_idx} col {c_idx}"

    assert not table.footnotes, "flowchart should not have footnotes"


@pytest.mark.parametrize(
    "soa_table_fixture_name",
    ["protocol_soa_table__days", "protocol_soa_table__weeks"],
)
def test_propagate_hidden_rows(request, soa_table_fixture_name):
    """Validates propagation of crosses and footnotes from hidden rows to the first visible parent row"""
    soa_table_fixture_name: TableWithFootnotes = deepcopy(
        request.getfixturevalue(soa_table_fixture_name)
    )
    StudyFlowchartService.propagate_hidden_rows(soa_table_fixture_name)
    check_hidden_row_propagation(soa_table_fixture_name)


def test_get_flowchart_item_uid_coordinates(
    tst_data: TestData, detailed_soa_table__weeks: TableWithFootnotes
):
    service = StudyFlowchartService()
    results = service.get_flowchart_item_uid_coordinates(study_uid=tst_data.study.uid)
    assert isinstance(results, dict)

    collected_coordinates: dict(str, tuple(int, int)) = {
        ref.uid: (r_idx, c_idx)
        for r_idx, row in enumerate(detailed_soa_table__weeks.rows)
        for c_idx, cell in enumerate(row.cells)
        if cell.refs
        for ref in cell.refs
        if ref.type
        in {
            SoAItemType.STUDY_EPOCH.value,
            SoAItemType.STUDY_VISIT.value,
            SoAItemType.STUDY_SOA_GROUP.value,
            SoAItemType.STUDY_ACTIVITY_GROUP.value,
            SoAItemType.STUDY_ACTIVITY_SUBGROUP.value,
            SoAItemType.STUDY_ACTIVITY.value,
            SoAItemType.STUDY_ACTIVITY_SCHEDULE,
        }
    }

    # collected coordinates is a subset of get_flowchart_item_uid_coordinates() because of grouped visits
    for uid, expected_coordinates in collected_coordinates.items():
        assert uid in results, f"Missing coordinates for uid: {uid}"
        returned_coordinates = results.get(uid)
        assert isinstance(
            returned_coordinates, tuple
        ), f"Unexpected coordinates type {type(returned_coordinates)} for uid: {uid}"
        assert (
            len(returned_coordinates) == 2
        ), f"Unexpected length of coordinates {len(returned_coordinates)} for uid: {uid}"
        for i in range(2):
            assert isinstance(
                returned_coordinates[i], int
            ), f"Unexpected coordinates type {type(returned_coordinates)} for uid: {uid}"
            assert (
                returned_coordinates[i] >= 0
            ), f"Negative coordinates {returned_coordinates} for uid: {uid}"

        assert (
            returned_coordinates == expected_coordinates
        ), f"Coordinates mismatch, expected {expected_coordinates} returned {returned_coordinates} for uid: {uid}"

    # THEN all StudyEpochs have coordinates
    study_epoch: StudyEpoch
    for study_epoch in (
        StudyEpochService()
        .get_all_epochs(study_uid=tst_data.study.uid, sort_by={"order": True})
        .items
    ):
        assert results.pop(
            study_epoch.uid, None
        ), f"Missing coordinates of StudyEpoch[{study_epoch.uid}]"

    # THEN all StudyVisits have coordinates
    study_visit: models.StudyVisit
    for study_visit in (
        StudyVisitService(study_uid=tst_data.study.uid)
        .get_all_visits(study_uid=tst_data.study.uid, sort_by={"order": True})
        .items
    ):
        assert results.pop(
            study_visit.uid, None
        ), f"Missing coordinates of StudyVisit[{study_visit.uid}]"

    shared_soa_groups = []
    shared_study_activity_groups = []
    shared_study_activity_subgroups = []
    study_selection_activity: models.StudySelectionActivity
    for study_selection_activity in (
        StudyActivitySelectionService()
        .get_all_selection(study_uid=tst_data.study.uid)
        .items
    ):
        # THEN all StudySelectionActivity have coordinates
        assert results.pop(study_selection_activity.study_activity_uid, None), (
            f"Missing coordinates of StudySelectionActivity[{study_selection_activity.study_activity_uid}]: "
            + study_selection_activity.study_activity_uid
        )
        if (
            study_selection_activity.study_soa_group.study_soa_group_uid
            not in shared_soa_groups
        ):
            # THEN all StudySoAGroups have coordinates
            assert results.pop(
                study_selection_activity.study_soa_group.study_soa_group_uid, None
            ), (
                f"Missing coordinates of StudySelectionActivity[{study_selection_activity.study_activity_uid}]: "
                + study_selection_activity.study_soa_group.study_soa_group_uid
            )
            shared_soa_groups.append(
                study_selection_activity.study_soa_group.study_soa_group_uid
            )

        if (
            study_selection_activity.study_activity_group.study_activity_group_uid
            and study_selection_activity.study_activity_group.study_activity_group_uid
            not in shared_study_activity_groups
        ):
            # THEN all StudyActivityGroups have coordinates
            assert results.pop(
                study_selection_activity.study_activity_group.study_activity_group_uid,
                None,
            ), (
                f"Missing coordinates of StudySelectionActivity[{study_selection_activity.study_activity_uid}]: "
                + study_selection_activity.study_activity_group.study_activity_group_uid
            )
            shared_study_activity_groups.append(
                study_selection_activity.study_activity_group.study_activity_group_uid
            )

        # THEN all StudyActivitySubGroups have coordinates
        if (
            study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid
            and study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid
            not in shared_study_activity_subgroups
        ):
            assert results.pop(
                study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid,
                None,
            ), (
                f"Missing coordinates of StudySelectionActivity[{study_selection_activity.study_activity_uid}]: "
                + study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid
            )
            shared_study_activity_subgroups.append(
                study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid
            )

    # THEN all StudyActivitySchedules have coordinates
    study_activity_schedule: models.StudyActivitySchedule
    for study_activity_schedule in StudyActivityScheduleService().get_all_schedules(
        study_uid=tst_data.study.uid, operational=False
    ):
        assert results.pop(
            study_activity_schedule.study_activity_schedule_uid, None
        ), f"Missing coordinates of StudyActivitySchedule[{study_activity_schedule.study_activity_schedule_uid}]"

    # After removing all expected keys from the dict, we expect no more coordinates left in there
    assert not results, "Unexpected coordinates"


@pytest.mark.parametrize(
    "protocol_flowchart",
    [None, True, False],
)
def test_download_detailed_soa_content(
    tst_data: TestData,
    protocol_flowchart: bool | None,
):
    """Test returned data of download_detailed_soa_content"""

    study_uid = tst_data.study.uid
    service = StudyFlowchartService()
    results = service.download_detailed_soa_content(
        study_uid=study_uid,
        protocol_flowchart=protocol_flowchart,
    )
    assert results
    assert isinstance(results, list)

    schedules = StudyActivityScheduleService().get_all_schedules(
        study_uid=study_uid,
        operational=False,
    )
    study_visits_map: dict[str, models.StudyVisit] = {
        svis.uid: svis
        for svis in StudyVisitService(study_uid=tst_data.study.uid)
        .get_all_visits(study_uid=study_uid, sort_by={"order": True})
        .items
    }
    study_activities_map: dict[str, models.StudySelectionActivity] = {
        ssa.study_activity_uid: ssa
        for ssa in StudyActivitySelectionService()
        .get_all_selection(study_uid=study_uid)
        .items
    }

    if protocol_flowchart:
        schedules = [
            sched
            for sched in schedules
            if study_activities_map[
                sched.study_activity_uid
            ].show_activity_in_protocol_flowchart
        ]

    assert len(results) == len(schedules), "record count mismatch"

    sched: StudyActivitySchedule
    for i, (res, sched) in enumerate(zip(results, schedules)):
        study_activity = study_activities_map[sched.study_activity_uid]
        study_visit = study_visits_map[sched.study_visit_uid]

        assert len(res.keys()) == 8, f"record #{i} property count mismatch"
        assert res["study_version"] == study_version(tst_data.study) or res[
            "study_version"
        ].startswith("LATEST on 20")
        assert (
            res["study_number"]
            == tst_data.study.current_metadata.identification_metadata.study_number
        )
        assert res["epoch"] == study_visit.study_epoch_name
        assert res["visit"] == study_visit.visit_short_name
        assert res["soa_group"] == study_activity.study_soa_group.soa_group_name
        assert (
            res["activity_group"]
            == study_activity.study_activity_group.activity_group_name
        )
        assert (
            res["activity_subgroup"]
            == study_activity.study_activity_subgroup.activity_subgroup_name
        )
        assert res["activity"] == study_activity.activity.name


def test_download_operational_soa_content(
    tst_data: TestData,
):
    """Test returned data of download_operational_soa_content"""

    study_uid = tst_data.study.uid
    service = StudyFlowchartService()
    results = service.download_operational_soa_content(
        study_uid=study_uid,
    )
    assert results
    assert isinstance(results, list)

    schedules = StudyActivityScheduleService().get_all_schedules(
        study_uid=study_uid,
        operational=True,
    )
    study_visits_map: dict[str, models.StudyVisit] = {
        svis.uid: svis
        for svis in StudyVisitService(study_uid=tst_data.study.uid)
        .get_all_visits(study_uid=study_uid, sort_by={"order": True})
        .items
    }
    study_activities_map: dict[str, models.StudySelectionActivity] = {
        ssa.study_activity_uid: ssa
        for ssa in StudyActivitySelectionService()
        .get_all_selection(study_uid=study_uid)
        .items
    }
    study_activity_instances_map: dict[str, models.StudySelectionActivityInstance] = {
        sais.study_activity_instance_uid: sais
        for sais in StudyActivityInstanceSelectionService()
        .get_all_selection(
            study_uid=study_uid,
            filter_by={
                "activity.library_name": {
                    "v": [config.REQUESTED_LIBRARY_NAME],
                    "op": "ne",
                }
            },
        )
        .items
    }

    assert len(results) == len(schedules), "record count mismatch"

    sched: StudyActivitySchedule
    for i, (res, sched) in enumerate(zip(results, schedules)):
        study_activity = study_activities_map[sched.study_activity_uid]
        study_activity_intance = study_activity_instances_map[
            sched.study_activity_instance_uid
        ]
        study_visit = study_visits_map[sched.study_visit_uid]

        assert len(res.keys()) == 11, f"record #{i} property count mismatch"
        assert res["study_version"] == study_version(tst_data.study) or res[
            "study_version"
        ].startswith("LATEST on 20")
        assert (
            res["study_number"]
            == tst_data.study.current_metadata.identification_metadata.study_number
        )
        assert res["epoch"] == study_visit.study_epoch_name
        assert res["visit"] == study_visit.visit_short_name
        assert res["soa_group"] == study_activity.study_soa_group.soa_group_name
        assert (
            res["activity_group"]
            == study_activity.study_activity_group.activity_group_name
        )
        assert (
            res["activity_subgroup"]
            == study_activity.study_activity_subgroup.activity_subgroup_name
        )
        assert res["activity"] == study_activity.activity.name

        assert res["activity_instance"] == (
            study_activity_intance.activity_instance.name
            if study_activity_intance.activity_instance
            else None
        )
        assert res["param_code"] == (
            study_activity_intance.activity_instance.adam_param_code
            if study_activity_intance.activity_instance
            else None
        )
        assert res["topic_code"] == (
            study_activity_intance.activity_instance.topic_code
            if study_activity_intance.activity_instance
            else None
        )
