import uuid
from typing import Callable

from usdm_model import Activity as USDMActivity
from usdm_model import AliasCode as USDMAliasCode
from usdm_model import Code as USDMCode
from usdm_model import Encounter as USDMEncounter
from usdm_model import Endpoint as USDMEndpoint
from usdm_model import Objective as USDMObjective
from usdm_model import Organization as USDMOrganization
from usdm_model import Procedure as USDMProcedure
from usdm_model import ScheduledActivityInstance
from usdm_model import ScheduleTimeline as USDMScheduleTimeline
from usdm_model import Study as USDMStudy
from usdm_model import StudyArm
from usdm_model import StudyCell as USDMStudyCell
from usdm_model import StudyDesign as USDMStudyDesign
from usdm_model import StudyDesignPopulation as USDMStudyDesignPopulation
from usdm_model import StudyElement as USDMStudyElement
from usdm_model import StudyEpoch
from usdm_model import StudyIdentifier as USDMStudyIdentifier
from usdm_model import StudyIntervention as USDMStudyIntervention
from usdm_model import StudyVersion as USDMStudyVersion
from usdm_model import Timing as USDMTiming
from usdm_model import TransitionRule as USDMTransitionRule

from clinical_mdr_api.models.study_selections.study import Study as OSBStudy


def get_ddf_timing_type_code_before():
    return USDMCode(
        id=str(uuid.uuid4()),
        code="C201264",
        codeSystem="http://www.cdisc.org",
        codeSystemVersion="2023-09-29",
        decode="Before",
    )


def get_ddf_timing_type_code_after():
    return USDMCode(
        id=str(uuid.uuid4()),
        code="C201264",
        codeSystem="http://www.cdisc.org",
        codeSystemVersion="2023-09-29",
        decode="After",
    )


def get_ddf_timing_type_code_fixed():
    return USDMCode(
        id=str(uuid.uuid4()),
        code="C201264",
        codeSystem="http://www.cdisc.org",
        codeSystemVersion="2023-09-29",
        decode="Fixed Reference",
    )


def get_ddf_timing_iso_duration_value(time_value: int, time_unit_name: str) -> str:
    timing_value = "P"
    abs_time_value = abs(time_value)
    if time_unit_name == "days":
        timing_value = timing_value + f"{abs_time_value}D"
    elif time_unit_name == "hours":
        timing_value = timing_value + f"T{abs_time_value}H"
    else:
        raise ValueError(f"Unsupported time unit {time_unit_name}")
    return timing_value


def get_ddf_timing_relative_to_from():
    return USDMCode(
        id=str(uuid.uuid4()),
        code="C201265",
        codeSystem="http://www.cdisc.org",
        codeSystemVersion="2023-09-29",
        decode="Start to Start",
    )


class USDMMapper:
    def __init__(
        self,
        get_osb_study_design_cells: Callable,
        get_osb_study_arms: Callable,
        get_osb_study_epochs: Callable,
        get_osb_study_elements: Callable,
        get_osb_study_endpoints: Callable,
        get_osb_study_visits: Callable,
        get_osb_study_activities: Callable,
        get_osb_activity_schedules: Callable,
    ):
        self._get_osb_study_design_cells = get_osb_study_design_cells
        self._get_osb_study_arms = get_osb_study_arms
        self._get_osb_study_epochs = get_osb_study_epochs
        self._get_osb_study_elements = get_osb_study_elements
        self._get_osb_study_endpoints = get_osb_study_endpoints
        self._get_osb_study_visits = get_osb_study_visits
        self._get_osb_study_activities = get_osb_study_activities
        self._get_osb_activity_schedules = get_osb_activity_schedules

    def map(self, study: OSBStudy) -> USDMStudy:
        usdm_study = USDMStudy()
        usdm_study.id = uuid.uuid4()
        # usdm_study.name = study.uid
        usdm_study.label = self._get_study_label(study)

        # Set DDF study description
        usdm_study.description = self._get_study_description(study)
        usdm_version = USDMStudyVersion(
            id=str(uuid.uuid4()),
            studyTitle="",
            versionIdentifier="",
            rationale="",
            studyAcronym="",
        )

        # Set DDF study title in version
        usdm_version.studyTitle = self._get_study_title(study)
        # Set DDF study type in version
        usdm_version.type = self._get_study_type(study)
        # Set DDF study version identifier
        usdm_version.versionIdentifier = self._get_study_version(study)
        # Set DDF study identifier in version
        usdm_version.studyIdentifiers = self._get_study_identifier(study)
        # Set DDF study phase
        usdm_version.studyPhase = self._get_study_phase(study)
        # Set DDF study design
        usdm_version.studyDesigns = self._get_study_designs(study)

        # Set DDF study versions
        usdm_study.versions = [usdm_version]

        return usdm_study

    def _get_intervention_model(self, study: OSBStudy):
        ddf_intervention_model = USDMCode(
            id=str(uuid.uuid4()),
            code=study.current_metadata.study_intervention.intervention_model_code.term_uid
            if study.current_metadata.study_intervention.intervention_model_code
            is not None
            else "",
            codeSystem="openstudybuilder.org",
            codeSystemVersion="",
            decode=study.current_metadata.study_intervention.intervention_model_code.name
            if study.current_metadata.study_intervention.intervention_model_code
            is not None
            else "",
        )
        return ddf_intervention_model

    def _get_study_arms(self, study: OSBStudy):
        # TODO: don't create object if arm_type is None
        osb_study_arms = self._get_osb_study_arms(study.uid).items
        return [
            StudyArm(
                id=str(uuid.uuid4()),
                name=sa.name,
                description=sa.description,
                type=USDMCode(
                    id=str(uuid.uuid4()),
                    code=getattr(
                        getattr(sa, "arm_type", ""), "sponsor_preferred_name", ""
                    ),
                    codeSystem="openstudybuilder.org",
                    codeSystemVersion="",
                    decode="",
                ),
                dataOriginDescription="",
                dataOriginType=USDMCode(
                    id=str(uuid.uuid4()),
                    code="",
                    codeSystem="openstudybuilder.org",
                    codeSystemVersion="",
                    decode="",
                ),
            )
            for sa in osb_study_arms
        ]

    def _get_study_cells(self, study: OSBStudy):
        osb_design_cells = self._get_osb_study_design_cells(study.uid)
        return [
            USDMStudyCell(
                id=str(uuid.uuid4()),
                armId=dc.study_arm_uid,
                epochId=dc.study_epoch_uid,
                elementIds=[dc.study_element_uid],
            )
            for dc in osb_design_cells
            if dc.study_arm_uid is not None
            and dc.study_epoch_uid is not None
            and dc.study_element_uid is not None
        ]

    def _get_study_description(self, study: OSBStudy):
        identification_metadata = getattr(
            getattr(study, "current_metadata", None), "identification_metadata", None
        )
        return getattr(identification_metadata, "description", None)

    def _get_study_designs(self, study: OSBStudy):
        # Create DDF study design and set intervention model
        ddf_study_design = USDMStudyDesign(
            id=str(uuid.uuid4()),
            name="Study Design",
            arms=[],
            studyCells=[],
            rationale="",
            epochs=[],
            interventionModel=self._get_intervention_model(study),
        )

        # Set therapeutic areas
        ddf_study_design.therapeuticAreas = self._get_therapeutic_areas(study)

        # Set trial type codes
        ddf_study_design.trialTypes = self._get_trial_type_codes(study)

        # Set trial intent type codes
        ddf_study_design.trialTypes = self._get_trial_intent_types_codes(study)

        # Set study cells
        ddf_study_design.studyCells = self._get_study_cells(study)

        # Set study elements
        ddf_study_design.elements = self._get_study_elements(study)

        # Set study arms
        ddf_study_design.arms = self._get_study_arms(study)

        # Set study epochs
        ddf_study_design.epochs = self._get_study_epochs(study)

        # Set study population
        ddf_study_design.population = self._get_study_population(study)

        # Set study objectives and endpoints
        ddf_study_design.objectives = self._get_study_objectives(study)

        # Set study interventions
        # TODO: mappings to be reviewed and verified
        # ddf_study_design.studyInterventions = self._get_study_interventions(study)

        # Set study visits/encounters
        ddf_study_design.encounters = self._get_study_encounters(study)

        # Set study activities
        ddf_study_design.activities = self._get_study_activities(study)

        # Set schedule timeline
        ddf_study_design.scheduleTimelines = self._get_study_schedule_timelines(study)

        return [ddf_study_design]

    def _get_study_activities(self, study: OSBStudy):
        osb_study_activities = self._get_osb_study_activities(study.uid).items
        return [
            USDMActivity(
                id=a.study_activity_uid,
                name=a.study_activity_subgroup.activity_subgroup_name,
                isConditional=False,  # TODO hardcoded
                definedProcedures=[
                    USDMProcedure(
                        id=str(uuid.uuid4()),
                        name=a.activity.name,
                        procedureType="",
                        code=USDMCode(
                            id=str(uuid.uuid4()),
                            code="",
                            codeSystem="openstudybuilder.org",
                            codeSystemVersion="",
                            decode="",
                        ),
                        isConditional=False,  # TODO hardcoded
                    )
                ]
                if a.activity is not None and a.activity.name is not None
                else [],
            )
            for a in osb_study_activities
        ]

    def _get_study_elements(self, study: OSBStudy):
        osb_study_elements = self._get_osb_study_elements(study.uid).items
        return [
            USDMStudyElement(
                id=str(uuid.uuid4()), name=se.name, description=se.description
            )
            for se in osb_study_elements
        ]

    def _get_study_epochs(self, study: OSBStudy):
        osb_study_epochs = self._get_osb_study_epochs(study.uid).items

        # Since order is not mandatory in StudyEpoch, add next and previous IDs only
        # if order is available for every epoch
        osb_study_epochs_order_numbers = [e.order for e in osb_study_epochs]
        add_next_and_previous_ids = False
        if all(n is not None for n in osb_study_epochs_order_numbers) and len(
            osb_study_epochs_order_numbers
        ) == len(osb_study_epochs):
            add_next_and_previous_ids = True
            osb_study_epochs.sort(key=lambda e: e.order, reverse=False)

        ddf_study_epochs = [
            StudyEpoch(
                id=se.uid,
                name=se.epoch_name,
                description=se.description,
                type=USDMCode(
                    id=str(uuid.uuid4()),
                    code=se.epoch_type,
                    codeSystem="openstudybuilder.org",
                    codeSystemVersion="",
                    decode=se.epoch_type_name,
                ),
                nextId=str(osb_study_epochs[i + 1].uid)
                if add_next_and_previous_ids and i + 1 < len(osb_study_epochs)
                else None,
                previousId=str(osb_study_epochs[i - 1].uid)
                if add_next_and_previous_ids and i - 1 >= 0
                else None,
            )
            for i, se in enumerate(osb_study_epochs)
        ]
        return ddf_study_epochs

    def _get_study_identifier(self, study: OSBStudy):
        osb_identification_metadata = getattr(
            getattr(study, "current_metadata", None), "identification_metadata", None
        )
        osb_registry_identifiers = getattr(
            osb_identification_metadata, "registry_identifiers", None
        )
        osb_study_identifier_id = str(
            getattr(osb_registry_identifiers, "eudract_id", "")
        )
        osb_organization_id = getattr(osb_registry_identifiers, "ct_gov_id", " ")
        if osb_study_identifier_id is None or osb_organization_id is None:
            return []
        organization = USDMOrganization(
            id=str(uuid.uuid4()),
            name=osb_organization_id,
            identifier=osb_organization_id,
            identifierScheme="",
            type=USDMCode(
                id=str(uuid.uuid4()),
                code="",
                codeSystem="openstudybuilder.org",
                codeSystemVersion="",
                decode="",
            ),
        )
        study_identifier = USDMStudyIdentifier(
            id=str(uuid.uuid4()),
            studyIdentifier=osb_study_identifier_id,
            studyIdentifierScope=organization,
        )
        return [study_identifier]

    def _get_study_interventions(self, study: OSBStudy):
        osb_study_intervention = study.current_metadata.study_intervention
        usdm_study_intervention_codes = []

        if osb_study_intervention.intervention_model_code is not None:
            intervention_model_code = USDMCode(
                id=str(uuid.uuid4()),
                code=osb_study_intervention.intervention_model_code.term_uid,
                codeSystem="openstudybuilder.org",
                codeSystemVersion="",
                decode=osb_study_intervention.intervention_model_code.name,
            )
            usdm_study_intervention_codes.append(intervention_model_code)

        if osb_study_intervention.intervention_type_code is not None:
            intervention_type_code = USDMCode(
                id=str(uuid.uuid4()),
                code=osb_study_intervention.intervention_type_code.term_uid,
                codeSystem="openstudybuilder.org",
                codeSystemVersion="",
                decode=osb_study_intervention.intervention_type_code.name,
            )
            usdm_study_intervention_codes.append(intervention_type_code)

        if osb_study_intervention.control_type_code is not None:
            intervention_control_type_code = USDMCode(
                id=str(uuid.uuid4()),
                code=osb_study_intervention.control_type_code.term_uid,
                codeSystem="openstudybuilder.org",
                codeSystemVersion="",
                decode=osb_study_intervention.control_type_code.name,
            )
            usdm_study_intervention_codes.append(intervention_control_type_code)

        if osb_study_intervention.trial_blinding_schema_code is not None:
            intervention_trial_blinding_schema_code = USDMCode(
                id=str(uuid.uuid4()),
                code=osb_study_intervention.trial_blinding_schema_code.term_uid,
                codeSystem="openstudybuilder.org",
                codeSystemVersion="",
                decode=osb_study_intervention.trial_blinding_schema_code.name,
            )
            usdm_study_intervention_codes.append(
                intervention_trial_blinding_schema_code
            )

        if osb_study_intervention.trial_intent_types_codes is not None:
            intervention_trial_intent_types_codes = [
                USDMCode(
                    id=str(uuid.uuid4()),
                    code=type_code.term_uid,
                    codeSystem="openstudybuilder.org",
                    codeSystemVersion="",
                    decode=type_code.name,
                )
                for type_code in osb_study_intervention.trial_intent_types_codes
            ]
            usdm_study_intervention_codes.append(intervention_trial_intent_types_codes)

        return USDMStudyIntervention(
            id=str(uuid.uuid4()),
            name="Study Intervention",
            description=osb_study_intervention.intervention_model_code.name
            if osb_study_intervention.intervention_model_code.name is not None
            else None,
            codes=usdm_study_intervention_codes,
            # TODO: mandatory attributes missing
        )

    def _get_study_label(self, study: OSBStudy):
        if study.current_metadata is not None:
            if study.current_metadata.study_description is not None:
                return study.current_metadata.study_description.study_short_title
        return None

    def _get_study_objectives(self, study: OSBStudy):
        osb_study_endpoints = self._get_osb_study_endpoints(
            study.uid, no_brackets=True
        ).items
        return [
            USDMObjective(
                id=str(uuid.uuid4()),
                instanceType="OBJECTIVE",
                text="",
                level=USDMCode(
                    id=str(uuid.uuid4()),
                    code=se.study_objective.objective_level.term_uid,
                    codeSystem="openstudybuilder.org",
                    codeSystemVersion="",
                    decode=se.study_objective.objective_level.sponsor_preferred_name,
                )
                if se.study_objective.objective_level is not None
                else None,
                name=se.study_objective.objective.uid,
                description=se.study_objective.objective.name,
                endpoints=[
                    USDMEndpoint(
                        id=str(uuid.uuid4()),
                        name=se.endpoint.uid,
                        description=se.endpoint.name,
                        instanceType="ENDPOINT",
                        text="",
                        purpose="",
                        level=USDMCode(
                            id=str(uuid.uuid4()),
                            code=se.endpoint_level.term_uid,
                            codeSystem="openstudybuilder.org",
                            codeSystemVersion="",
                            decode=se.endpoint_level.sponsor_preferred_name,
                        )
                        if se.endpoint_level is not None
                        else None,
                    )
                ]
                if se.endpoint is not None
                else [],
            )
            for se in osb_study_endpoints
            if se.study_objective is not None
        ]

    def _get_study_phase(self, study: OSBStudy):
        # TODO don't create object if trial_phase_code is None
        osb_study_design = getattr(
            getattr(study, "current_metadata", None), "high_level_study_design", None
        )
        osb_trial_phase_code = getattr(osb_study_design, "trial_phase_code", None)
        study_phase_code = USDMCode(
            id=str(uuid.uuid4()),
            code=getattr(osb_trial_phase_code, "term_uid", ""),
            codeSystem="openstudybuilder.org",
            codeSystemVersion="",
            decode=getattr(osb_trial_phase_code, "name", ""),
        )
        study_phase = USDMAliasCode(id=str(uuid.uuid4()), standardCode=study_phase_code)
        return study_phase

    def _get_study_population(self, study: OSBStudy):
        osb_study_population = study.current_metadata.study_population
        population = USDMStudyDesignPopulation(
            id=str(uuid.uuid4()),
            name="Study Design Population",
            plannedSex=[
                USDMCode(
                    id=str(uuid.uuid4()),
                    code=osb_study_population.sex_of_participants_code.term_uid
                    if osb_study_population.sex_of_participants_code is not None
                    else "",
                    codeSystem="openstudybuilder.org",
                    codeSystemVersion="",
                    decode=osb_study_population.sex_of_participants_code.name
                    if osb_study_population.sex_of_participants_code is not None
                    else "",
                )
            ],
        )
        return population

    def _get_study_schedule_timelines(self, study):
        osb_study_activity_schedules = self._get_osb_activity_schedules(study.uid)
        osb_study_visits = self._get_osb_study_visits(study.uid).items

        # Create main timeline
        usdm_timeline_id = str(uuid.uuid4())
        usdm_timeline = USDMScheduleTimeline(
            id=usdm_timeline_id,
            name="Main Timeline",
            mainTimeline=True,
            entryCondition="",
            entryId="",
            instances=[],
        )

        # Create scheduled instances
        timeline_instances = []
        osb_global_anchor_visit = next(
            (v for v in osb_study_visits if v.is_global_anchor_visit is True), None
        )
        osb_global_anchor_study_activity_schedule = next(
            (
                sas
                for sas in osb_study_activity_schedules
                if sas.study_visit_uid == osb_global_anchor_visit.uid
            ),
            None,
        )
        for osb_schedule in osb_study_activity_schedules:
            osb_visit = next(
                (v for v in osb_study_visits if v.uid == osb_schedule.study_visit_uid),
                None,
            )
            if (
                osb_visit
                and osb_global_anchor_visit
                and osb_global_anchor_study_activity_schedule
            ):
                timeline_instance = ScheduledActivityInstance(
                    id=osb_schedule.study_activity_schedule_uid,
                    timelineId=usdm_timeline_id,
                    instanceType="ACTIVITY",
                    encounterId=osb_schedule.study_visit_uid,
                    activityIds=[osb_schedule.study_activity_uid],
                    epochId=osb_visit.study_epoch_uid,
                )

                if osb_visit.time_value < 0:
                    ddf_timing_code = get_ddf_timing_type_code_before()
                elif osb_visit.time_value > 0:
                    ddf_timing_code = get_ddf_timing_type_code_after()
                else:
                    ddf_timing_code = get_ddf_timing_type_code_fixed()

                ddf_timing_id = str(uuid.uuid4())
                ddf_timing_window_available = all(
                    [
                        osb_visit.min_visit_window_value is not None,
                        osb_visit.max_visit_window_value is not None,
                        osb_visit.min_visit_window_value != 0
                        or osb_visit.max_visit_window_value != 0,
                    ]
                )
                ddf_timing = USDMTiming(
                    id=ddf_timing_id,
                    name=ddf_timing_id,
                    label=osb_visit.study_epoch_name,
                    description=osb_visit.study_epoch_name,
                    type=ddf_timing_code,
                    relativeToFrom=get_ddf_timing_relative_to_from(),
                    value=get_ddf_timing_iso_duration_value(
                        osb_visit.time_value, osb_visit.time_unit_name
                    ),
                    relativeFromScheduledInstanceId=osb_schedule.study_activity_schedule_uid,
                    relativeToScheduledInstanceId=osb_global_anchor_study_activity_schedule.study_activity_schedule_uid,
                    windowLower=get_ddf_timing_iso_duration_value(
                        osb_visit.min_visit_window_value,
                        osb_visit.visit_window_unit_name,
                    )
                    if ddf_timing_window_available
                    else None,
                    windowUpper=get_ddf_timing_iso_duration_value(
                        osb_visit.max_visit_window_value,
                        osb_visit.visit_window_unit_name,
                    )
                    if ddf_timing_window_available
                    else None,
                    window=f"{osb_visit.min_visit_window_value}..{osb_visit.max_visit_window_value} {osb_visit.visit_window_unit_name}"
                    if ddf_timing_window_available
                    else None,
                )
                timeline_instance.timings = [ddf_timing]
                timeline_instances.append(timeline_instance)

        usdm_timeline.instances = timeline_instances
        return [usdm_timeline]

    def _get_study_title(self, study: OSBStudy):
        osb_current_metadata = getattr(study, "current_metadata", None)
        study_title = getattr(
            getattr(osb_current_metadata, "study_description", None), "study_title", ""
        )
        if study_title is not None:
            return study_title
        return ""

    def _get_study_type(self, study: OSBStudy):
        # TODO: don't create object if type code is None
        osb_study_design = getattr(
            getattr(study, "current_metadata", None), "high_level_study_design", None
        )
        osb_study_type_code = getattr(osb_study_design, "study_type_code", None)
        code = USDMCode(
            id=str(uuid.uuid4()),
            code=getattr(osb_study_type_code, "term_uid", ""),
            codeSystem="openstudybuilder.org",
            codeSystemVersion="",
            decode=getattr(osb_study_type_code, "name", ""),
        )
        return code

    def _get_study_version(self, study: OSBStudy):
        osb_current_metadata = getattr(study, "current_metadata", None)
        return str(
            getattr(
                getattr(osb_current_metadata, "version_metadata", None),
                "version_number",
                "",
            )
        )

    def _get_study_encounters(self, study: OSBStudy):
        osb_study_visits = self._get_osb_study_visits(study.uid).items
        ordered_osb_study_visits = sorted(
            osb_study_visits, key=lambda sv: sv.visit_number, reverse=False
        )
        ddf_encounters = [
            USDMEncounter(
                id=str(sv.uid),
                name=sv.visit_name,
                description=sv.description,
                type=USDMCode(
                    id=str(uuid.uuid4()),
                    code=sv.visit_type_uid,
                    codeSystem="openstudybuilder.org",
                    codeSystemVersion="",
                    decode=sv.visit_type_name,
                ),
                transitionStartRule=USDMTransitionRule(
                    id=str(uuid.uuid4()),
                    name="Transition Start Rule",
                    text=sv.start_rule if sv.start_rule is not None else "",
                ),
                transitionEndRule=USDMTransitionRule(
                    id=str(uuid.uuid4()),
                    name="Transition End Rule",
                    text=sv.end_rule if sv.end_rule is not None else "",
                ),
                contactModes=[
                    USDMCode(
                        id=str(uuid.uuid4()),
                        code=sv.visit_contact_mode_uid,
                        codeSystem="openstudybuilder.org",
                        codeSystemVersion="",
                        decode=sv.visit_contact_mode_name,
                    )
                ],
                nextId=str(ordered_osb_study_visits[i + 1].uid)
                if i + 1 < len(ordered_osb_study_visits)
                else None,
                previousId=str(ordered_osb_study_visits[i - 1].uid)
                if i - 1 >= 0
                else None,
            )
            for i, sv in enumerate(ordered_osb_study_visits)
        ]

        return ddf_encounters

    def _get_therapeutic_areas(self, study):
        osb_current_metadata = getattr(study, "current_metadata", None)
        osb_study_population = getattr(osb_current_metadata, "study_population", None)
        if osb_study_population:
            return [
                USDMCode(
                    id=str(uuid.uuid4()),
                    code=osb_therapeutic_area_code.term_uid,
                    codeSystem="openstudybuilder.org",
                    codeSystemVersion="",
                    decode=osb_therapeutic_area_code.name,
                )
                for osb_therapeutic_area_code in study.current_metadata.study_population.therapeutic_area_codes
            ]
        return []

    def _get_trial_intent_types_codes(self, study):
        osb_current_metadata = getattr(study, "current_metadata", None)
        osb_study_intervention = getattr(
            osb_current_metadata, "study_intervention", None
        )
        if osb_study_intervention:
            return [
                USDMCode(
                    id=str(uuid.uuid4()),
                    code=osb_trial_intent_type_code.term_uid,
                    codeSystem="openstudybuilder.org",
                    codeSystemVersion="",
                    decode=osb_trial_intent_type_code.name,
                )
                for osb_trial_intent_type_code in study.current_metadata.study_intervention.trial_intent_types_codes
            ]
        return []

    def _get_trial_type_codes(self, study: OSBStudy):
        return [
            USDMCode(
                id=str(uuid.uuid4()),
                code=osb_trial_type_code.term_uid,
                codeSystem="openstudybuilder.org",
                codeSystemVersion="",
                decode=osb_trial_type_code.name,
            )
            for osb_trial_type_code in study.current_metadata.high_level_study_design.trial_type_codes
        ]
