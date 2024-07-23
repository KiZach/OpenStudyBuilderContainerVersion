import dataclasses
import datetime
from typing import Any

from neomodel import Q, db

from clinical_mdr_api import config as settings
from clinical_mdr_api import exceptions
from clinical_mdr_api.config import (
    ANCHOR_VISIT_IN_VISIT_GROUP,
    GLOBAL_ANCHOR_VISIT_NAME,
    NON_VISIT_NUMBER,
    PREVIOUS_VISIT_NAME,
    UNSCHEDULED_VISIT_NUMBER,
)
from clinical_mdr_api.domain_repositories.models._utils import to_relation_trees
from clinical_mdr_api.domain_repositories.models.study_visit import (
    StudyVisit as StudyVisitNeoModel,
)
from clinical_mdr_api.domain_repositories.study_selections.study_visit_repository import (
    get_valid_time_references_for_study,
    get_valid_visit_types_for_epoch_type,
)
from clinical_mdr_api.domains.concepts.simple_concepts.numeric_value import (
    NumericValueAR,
    NumericValueType,
    NumericValueVO,
)
from clinical_mdr_api.domains.concepts.simple_concepts.study_day import (
    StudyDayAR,
    StudyDayVO,
)
from clinical_mdr_api.domains.concepts.simple_concepts.study_duration_days import (
    StudyDurationDaysAR,
    StudyDurationDaysVO,
)
from clinical_mdr_api.domains.concepts.simple_concepts.study_duration_weeks import (
    StudyDurationWeeksAR,
    StudyDurationWeeksVO,
)
from clinical_mdr_api.domains.concepts.simple_concepts.study_week import (
    StudyWeekAR,
    StudyWeekVO,
)
from clinical_mdr_api.domains.concepts.simple_concepts.time_point import (
    TimePointAR,
    TimePointVO,
)
from clinical_mdr_api.domains.concepts.simple_concepts.visit_name import (
    VisitNameAR,
    VisitNameVO,
)
from clinical_mdr_api.domains.concepts.simple_concepts.week_in_study import (
    WeekInStudyAR,
    WeekInStudyVO,
)
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_epoch import (
    EpochNamedTuple,
    EpochSubtypeNamedTuple,
    EpochTypeNamedTuple,
    StudyEpochEpoch,
    StudyEpochSubType,
    StudyEpochType,
    StudyEpochVO,
    TimelineAR,
)
from clinical_mdr_api.domains.study_selections.study_visit import (
    NumericValue,
    StudyVisitContactMode,
    StudyVisitEpochAllocation,
    StudyVisitHistoryVO,
    StudyVisitRepeatingFrequency,
    StudyVisitTimeReference,
    StudyVisitType,
    StudyVisitVO,
    TextValue,
    TimePoint,
    TimeUnit,
    VisitClass,
    VisitContactModeNamedTuple,
    VisitEpochAllocationNamedTuple,
    VisitRepeatingFrequencyNamedTuple,
    VisitSubclass,
    VisitTimeReferenceNamedTuple,
    VisitTypeNamedTuple,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.exceptions import BusinessLogicException, ValidationException
from clinical_mdr_api.models import StudyActivityScheduleCreateInput, StudyVisit
from clinical_mdr_api.models.study_selections.study_visit import (
    AllowedTimeReferences,
    AllowedVisitTypesForEpochType,
    SimpleStudyVisit,
    StudyVisitCreateInput,
    StudyVisitEditInput,
    StudyVisitVersion,
)
from clinical_mdr_api.models.utils import (
    GenericFilteringReturn,
    get_latest_on_datetime_str,
)
from clinical_mdr_api.oauth.user import user
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    calculate_diffs,
    calculate_diffs_history,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)
from clinical_mdr_api.services.studies.study_activity_schedule import (
    StudyActivityScheduleService,
)
from clinical_mdr_api.telemetry import trace_calls


class StudyVisitService:
    def __init__(
        self,
        study_uid: str,
        study_value_version: str | None = None,
    ):
        self._repos = MetaRepository()
        self.repo = self._repos.study_visit_repository
        self.author = user().id()
        self.terms_at_specific_datetime = self._extract_effective_date(
            study_uid=study_uid,
            study_value_version=study_value_version,
        )
        self._create_ctlist_map()
        self._day_unit, self._week_unit = self.repo.get_day_week_units()

    def _extract_effective_date(self, study_uid, study_value_version: str = None):
        study_standard_version = self._repos.study_standard_version_repository.find_standard_version_in_study(
            study_uid=study_uid,
            study_value_version=study_value_version,
        )
        terms_at_specific_date = None
        if study_standard_version:
            terms_at_specific_date = self._repos.ct_package_repository.find_by_uid(
                study_standard_version[0].ct_package_uid
            ).effective_date
        return (
            datetime.datetime(
                terms_at_specific_date.year,
                terms_at_specific_date.month,
                terms_at_specific_date.day,
                23,
                59,
                59,
                999999,
            )
            if terms_at_specific_date
            else None
        )

    def _create_ctlist_map(self):
        self.study_epoch_types = self.repo.fetch_ctlist(
            settings.STUDY_EPOCH_TYPE_NAME,
            effective_date=self.terms_at_specific_datetime,
        )

        StudyEpochType.clear()
        StudyEpochType.update(
            (uid, EpochTypeNamedTuple(uid, name))
            for uid, name in self.study_epoch_types.items()
        )

        self.study_epoch_subtypes = self.repo.fetch_ctlist(
            settings.STUDY_EPOCH_SUBTYPE_NAME,
            effective_date=self.terms_at_specific_datetime,
        )

        StudyEpochSubType.clear()
        StudyEpochSubType.update(
            (uid, EpochSubtypeNamedTuple(uid, name))
            for uid, name in self.study_epoch_subtypes.items()
        )

        self.study_epoch_epochs = self.repo.fetch_ctlist(
            settings.STUDY_EPOCH_EPOCH_NAME,
            effective_date=self.terms_at_specific_datetime,
        )

        StudyEpochEpoch.clear()
        StudyEpochEpoch.update(
            (uid, EpochNamedTuple(uid, name))
            for uid, name in self.study_epoch_epochs.items()
        )

        self.study_visit_types = self.repo.fetch_ctlist(
            settings.STUDY_VISIT_TYPE_NAME,
            effective_date=self.terms_at_specific_datetime,
        )

        StudyVisitType.clear()
        StudyVisitType.update(
            (uid, VisitTypeNamedTuple(uid, name))
            for uid, name in self.study_visit_types.items()
        )

        self.study_visit_repeating_frequency = self.repo.fetch_ctlist(
            settings.STUDY_VISIT_REPEATING_FREQUENCY,
            effective_date=self.terms_at_specific_datetime,
        )

        StudyVisitRepeatingFrequency.clear()
        StudyVisitRepeatingFrequency.update(
            (uid, VisitRepeatingFrequencyNamedTuple(uid, name))
            for uid, name in self.study_visit_repeating_frequency.items()
        )

        self.study_visit_timeref = self.repo.fetch_ctlist(
            settings.STUDY_VISIT_TIMEREF_NAME,
            effective_date=self.terms_at_specific_datetime,
        )

        StudyVisitTimeReference.clear()
        StudyVisitTimeReference.update(
            (uid, VisitTimeReferenceNamedTuple(uid, name))
            for uid, name in self.study_visit_timeref.items()
        )

        self.study_visit_contact_mode = self.repo.fetch_ctlist(
            settings.STUDY_VISIT_CONTACT_MODE_NAME,
            effective_date=self.terms_at_specific_datetime,
        )

        StudyVisitContactMode.clear()
        StudyVisitContactMode.update(
            (uid, VisitContactModeNamedTuple(uid, name))
            for uid, name in self.study_visit_contact_mode.items()
        )

        self.study_visit_epoch_allocation = self.repo.fetch_ctlist(
            settings.STUDY_VISIT_EPOCH_ALLOCATION_NAME,
            effective_date=self.terms_at_specific_datetime,
        )

        StudyVisitEpochAllocation.clear()
        StudyVisitEpochAllocation.update(
            (uid, VisitEpochAllocationNamedTuple(uid, name))
            for uid, name in self.study_visit_epoch_allocation.items()
        )

        self.study_visit_sublabels = self.repo.fetch_ctlist(
            settings.STUDY_VISIT_SUBLABEL,
            effective_date=self.terms_at_specific_datetime,
        )

    def get_valid_visit_types_for_epoch_type(self, epoch_type_uid: str, study_uid: str):
        resp = []
        for uid, name in get_valid_visit_types_for_epoch_type(
            epoch_type_uid=epoch_type_uid, study_uid=study_uid
        ).items():
            resp.append(
                AllowedVisitTypesForEpochType(visit_type_uid=uid, visit_type_name=name)
            )

        resp.sort(key=lambda visit_type: visit_type.visit_type_name)

        return resp

    def get_allowed_time_references_for_study(self, study_uid: str):
        resp = []
        for uid, name in get_valid_time_references_for_study(
            study_uid=study_uid, effective_date=self.terms_at_specific_datetime
        ).items():
            resp.append(
                AllowedTimeReferences(time_reference_uid=uid, time_reference_name=name)
            )
        # if we don't have any visits we have to remove 'previous visit' time reference
        if self.repo.count_study_visits(study_uid=study_uid) < 1:
            resp = [
                item for item in resp if item.time_reference_name != PREVIOUS_VISIT_NAME
            ]

        resp.sort(key=lambda time_reference: time_reference.time_reference_name)

        return resp

    def _transform_all_to_response_model(
        self,
        visit: StudyVisitVO,
        study_activity_count: int | None = None,
        study_value_version: str | None = None,
    ) -> StudyVisit:
        timepoint = visit.timepoint
        return StudyVisit(
            uid=visit.uid,
            study_uid=visit.study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            study_epoch_uid=visit.epoch_uid,
            study_epoch_name=visit.epoch.epoch.value,
            epoch_uid=visit.epoch.epoch.name,
            order=visit.visit_order,
            visit_type_uid=visit.visit_type.name,
            visit_type_name=visit.visit_type.value,
            time_reference_uid=(
                timepoint.visit_timereference.name if timepoint else None
            ),
            time_reference_name=(
                timepoint.visit_timereference.value if timepoint else None
            ),
            time_value=timepoint.visit_value if timepoint else None,
            time_unit_uid=timepoint.time_unit_uid if timepoint else None,
            time_unit_name=(
                visit.time_unit_object.name if visit.time_unit_object else None
            ),
            duration_time=visit.get_absolute_duration() if timepoint else None,
            duration_time_unit=timepoint.time_unit_uid if timepoint else None,
            study_day_number=visit.study_day_number if visit.study_day else None,
            study_day_label=visit.study_day_label if visit.study_day else None,
            study_duration_days=visit.study_duration_days.value
            if visit.study_duration_days
            else None,
            study_duration_days_label=(
                visit.study_duration_days_label if visit.study_duration_days else None
            ),
            study_week_number=visit.study_week_number if visit.study_week else None,
            study_week_label=visit.study_week_label if visit.study_week else None,
            study_duration_weeks=visit.study_duration_weeks.value
            if visit.study_duration_weeks
            else None,
            study_duration_weeks_label=(
                visit.study_duration_weeks_label if visit.study_duration_weeks else None
            ),
            week_in_study_label=(
                visit.week_in_study_label if visit.week_in_study else None
            ),
            visit_number=visit.visit_number,
            visit_subnumber=visit.visit_subnumber,
            unique_visit_number=visit.unique_visit_number,
            visit_subname=visit.visit_subname,
            visit_sublabel=visit.visit_sublabel,
            visit_sublabel_reference=visit.visit_sublabel_reference,
            visit_name=visit.visit_name,
            visit_short_name=visit.visit_short_name,
            consecutive_visit_group=visit.consecutive_visit_group,
            show_visit=visit.show_visit,
            min_visit_window_value=visit.visit_window_min,
            max_visit_window_value=visit.visit_window_max,
            visit_window_unit_uid=visit.window_unit_uid,
            visit_window_unit_name=(
                visit.window_unit_object.name if visit.window_unit_object else None
            ),
            description=visit.description,
            start_rule=visit.start_rule,
            end_rule=visit.end_rule,
            visit_contact_mode_uid=visit.visit_contact_mode.name,
            visit_contact_mode_name=visit.visit_contact_mode.value,
            epoch_allocation_uid=(
                visit.epoch_allocation.name if visit.epoch_allocation else None
            ),
            epoch_allocation_name=(
                visit.epoch_allocation.value if visit.epoch_allocation else None
            ),
            visit_type=visit.visit_type.name,
            status=visit.status.value,
            start_date=visit.start_date.strftime(settings.DATE_TIME_FORMAT),
            user_initials=visit.author,
            possible_actions=visit.possible_actions,
            study_activity_count=study_activity_count,
            visit_class=visit.visit_class.name,
            visit_subclass=visit.visit_subclass.name if visit.visit_subclass else None,
            is_global_anchor_visit=visit.is_global_anchor_visit,
            is_soa_milestone=visit.is_soa_milestone,
            repeating_frequency_uid=(
                visit.repeating_frequency.name if visit.repeating_frequency else None
            ),
            repeating_frequency_name=(
                visit.repeating_frequency.value if visit.repeating_frequency else None
            ),
        )

    def _transform_all_to_response_history_model(
        self, visit: StudyVisitHistoryVO
    ) -> StudyVisit:
        study_visit: StudyVisit = self._transform_all_to_response_model(visit)
        study_visit.change_type = visit.change_type
        study_visit.end_date = (
            visit.end_date.strftime(settings.DATE_TIME_FORMAT)
            if visit.end_date
            else None
        )
        return study_visit

    def _get_all_visits(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[StudyVisitVO]:
        repos = self._repos
        try:
            study_visits = self.repo.find_all_visits_by_study_uid(
                study_uid=study_uid, study_value_version=study_value_version
            )
            timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
            assert study_visits is not None
            return timeline.ordered_study_visits
        finally:
            repos.close()

    def get_amount_of_visits_in_given_epoch(
        self, study_uid: str, study_epoch_uid: str
    ) -> int:
        visits_in_given_study_epoch = to_relation_trees(
            StudyVisitNeoModel.nodes.fetch_relations().filter(
                study_epoch_has_study_visit__uid=study_epoch_uid,
                has_study_visit__latest_value__uid=study_uid,
            )
        )
        return len(visits_in_given_study_epoch)

    def get_global_anchor_visit(self, study_uid: str) -> SimpleStudyVisit | None:
        global_anchor_visit = to_relation_trees(
            StudyVisitNeoModel.nodes.fetch_relations(
                "has_visit_name__has_latest_value",
                "has_visit_type__has_name_root__has_latest_value",
            ).filter(
                has_study_visit__latest_value__uid=study_uid,
                is_global_anchor_visit=True,
            )
        )
        if len(global_anchor_visit) > 0:
            return SimpleStudyVisit.from_orm(global_anchor_visit[0])
        raise exceptions.NotFoundException(
            f"Global anchor visit for study '{study_uid}' does not exist"
        )

    def get_anchor_visits_in_a_group_of_subvisits(
        self, study_uid: str
    ) -> list[SimpleStudyVisit]:
        anchor_visits_in_a_group_of_subv = to_relation_trees(
            StudyVisitNeoModel.nodes.fetch_relations(
                "has_visit_name__has_latest_value",
                "has_visit_type__has_name_root__has_latest_value",
            ).filter(
                has_study_visit__latest_value__uid=study_uid,
                visit_subclass=VisitSubclass.ANCHOR_VISIT_IN_GROUP_OF_SUBV.name,
            )
        )
        return [
            SimpleStudyVisit.from_orm(anchor_visit)
            for anchor_visit in anchor_visits_in_a_group_of_subv
        ]

    def get_anchor_for_special_visit(self, study_uid: str) -> list[SimpleStudyVisit]:
        anchor_visits_for_special_visit = to_relation_trees(
            StudyVisitNeoModel.nodes.fetch_relations(
                "has_visit_name__has_latest_value",
                "has_visit_type__has_name_root__has_latest_value",
            ).filter(
                Q(visit_subclass=VisitSubclass.SINGLE_VISIT.name)
                | Q(visit_subclass=VisitSubclass.ANCHOR_VISIT_IN_GROUP_OF_SUBV.name),
                visit_class=VisitClass.SINGLE_VISIT.name,
                has_study_visit__latest_value__uid=study_uid,
            )
        )
        return sorted(
            [
                SimpleStudyVisit.from_orm(anchor_visit)
                for anchor_visit in anchor_visits_for_special_visit
            ],
            key=lambda visit: int(visit.visit_name.split()[1]),
        )

    @trace_calls
    def get_all_visits(
        self,
        study_uid: str,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn[StudyVisit]:
        visits = self._get_all_visits(
            study_uid, study_value_version=study_value_version
        )
        visits = [
            self._transform_all_to_response_model(
                visit,
                study_activity_count=self.repo.count_activities(
                    visit_uid=visit.uid, study_value_version=study_value_version
                ),
                study_value_version=study_value_version,
            )
            for visit in visits
        ]

        filtered_visits = service_level_generic_filtering(
            items=visits,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )
        return filtered_visits

    def get_distinct_values_for_header(
        self,
        study_uid: str,
        field_name: str,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        result_count: int = 10,
        study_value_version: str | None = None,
    ):
        all_items = self.get_all_visits(
            study_uid=study_uid, study_value_version=study_value_version
        )

        # Do filtering, sorting, pagination and count
        header_values = service_level_generic_header_filtering(
            items=all_items.items,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            result_count=result_count,
        )
        # Return values for field_name
        return header_values

    @db.transaction
    def get_all_references(self, study_uid: str) -> list[StudyVisit]:
        def is_reference(visit: StudyVisitVO):
            if visit.visit_type.value in self.study_visit_timeref.values():
                return True
            return False

        visits = self._get_all_visits(study_uid)

        return [
            self._transform_all_to_response_model(visit)
            for visit in visits
            if is_reference(visit)
        ]

    @db.transaction
    def find_by_uid(
        self, study_uid: str, uid: str, study_value_version: str | None = None
    ) -> StudyVisit:
        """
        finds latest version of visit by uid, status ans version
        if user do not give status and version - will be overwritten by DRAFT
        """
        repos = self._repos
        try:
            study_visit = self.repo.find_by_uid(
                study_uid=study_uid, uid=uid, study_value_version=study_value_version
            )

            study_visits = self.repo.find_all_visits_by_study_uid(
                study_visit.study_uid, study_value_version=study_value_version
            )
            timeline = TimelineAR(study_uid=study_visit.study_uid, _visits=study_visits)
            assert study_visits is not None
            for ordered_study_visit in timeline.ordered_study_visits:
                if ordered_study_visit.uid == study_visit.uid:
                    return self._transform_all_to_response_model(
                        ordered_study_visit,
                        study_activity_count=self.repo.count_activities(
                            visit_uid=study_visit.uid,
                            study_value_version=study_value_version,
                        ),
                    )
        finally:
            repos.close()

        return None

    def _validate_derived_properties(
        self, visit_vo: StudyVisitVO, ordered_visits: list[StudyVisitVO]
    ):
        if (
            visit_vo.visit_class != VisitClass.SPECIAL_VISIT
            and visit_vo.visit_subclass
            != VisitSubclass.ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV
        ):
            error_dict = {}
            chronological_order_dict = {}
            for idx, visit in enumerate(ordered_visits):
                if visit_vo.uid != visit.uid:
                    if visit_vo.visit_number == visit.visit_number:
                        error_dict["visit number"] = visit_vo.visit_number
                    if visit_vo.unique_visit_number == visit.unique_visit_number:
                        error_dict["unique visit number"] = visit_vo.unique_visit_number
                    if visit_vo.visit_name == visit.visit_name:
                        error_dict["visit name"] = visit_vo.visit_name
                    if visit_vo.visit_short_name == visit.visit_short_name:
                        error_dict["visit short name"] = visit_vo.visit_short_name
                elif visit_vo.uid == visit.uid:
                    if idx == 0 and len(ordered_visits) > 1:
                        # if the neighbour Visit is Subvisit, visit_number and unique_visit_number may be defined out of chronological order
                        if (
                            ordered_visits[idx + 1].visit_subclass
                            == VisitSubclass.SINGLE_VISIT
                        ):
                            if (
                                visit_vo.visit_number
                                > ordered_visits[idx + 1].visit_number
                            ):
                                chronological_order_dict[
                                    "visit number"
                                ] = visit_vo.visit_number
                            if (
                                visit_vo.unique_visit_number
                                > ordered_visits[idx + 1].unique_visit_number
                            ):
                                chronological_order_dict[
                                    "unique visit number"
                                ] = visit_vo.unique_visit_number
                    # if the neighbour Visit is Subvisit, visit_number and unique_visit_number may be defined out of chronological order
                    elif idx + 1 == len(ordered_visits) and len(ordered_visits) > 1:
                        if (
                            ordered_visits[idx - 1].visit_subclass
                            == VisitSubclass.SINGLE_VISIT
                        ):
                            if (
                                visit_vo.visit_number
                                < ordered_visits[idx - 1].visit_number
                            ):
                                chronological_order_dict[
                                    "visit number"
                                ] = visit_vo.visit_number
                            if (
                                visit_vo.unique_visit_number
                                < ordered_visits[idx - 1].unique_visit_number
                            ):
                                chronological_order_dict[
                                    "unique visit number"
                                ] = visit_vo.unique_visit_number
                    elif len(ordered_visits) > 2:
                        # if the neighbour Visits are Subvisits, visit_number and unique_visit_number may be defined out of chronological order
                        if (
                            ordered_visits[idx - 1].visit_subclass
                            == VisitSubclass.SINGLE_VISIT
                            and ordered_visits[idx + 1].visit_subclass
                            == VisitSubclass.SINGLE_VISIT
                        ):
                            if (
                                visit_vo.visit_number
                                < ordered_visits[idx - 1].visit_number
                                or visit_vo.visit_number
                                > ordered_visits[idx + 1].visit_number
                            ):
                                chronological_order_dict[
                                    "visit number"
                                ] = visit_vo.visit_number
                            if (
                                visit_vo.unique_visit_number
                                < ordered_visits[idx - 1].unique_visit_number
                                or visit_vo.unique_visit_number
                                > ordered_visits[idx + 1].unique_visit_number
                            ):
                                chronological_order_dict[
                                    "unique visit number"
                                ] = visit_vo.unique_visit_number
            if chronological_order_dict:
                count = len(chronological_order_dict)
                joined_error = " and ".join(
                    [f"{v} in field {k}" for k, v in chronological_order_dict.items()]
                )
                error_msg = f"Value{'s' if count > 1 else ''} {joined_error} {'are' if count > 1 else 'is'}"
                error_msg += " not defined in chronological order by study visit timing"
                if visit_vo.visit_class == VisitClass.SINGLE_VISIT:
                    error_msg += " as a manually defined value exsits. Change the manually defined value before this visit can be defined."
                raise ValidationException(error_msg)
            if error_dict:
                count = len(error_dict)
                joined_error = " and ".join(
                    [f"{k} - {v}" for k, v in error_dict.items()]
                )
                error_msg = f"Field{'s' if count > 1 else ''} {joined_error} {'are' if count > 1 else 'is'} not unique for the Study"
                if visit_vo.visit_class == VisitClass.SINGLE_VISIT:
                    error_msg += " as a manually defined value exists. Change the manually defined value before this visit can be defined."
                raise exceptions.ValidationException(error_msg)

    def _validate_visit(
        self,
        visit_input: StudyVisitCreateInput,
        visit_vo: StudyVisitVO,
        timeline: TimelineAR,
        create: bool = True,
        preview: bool = False,
    ):
        visit_classes_without_timing = (
            VisitClass.NON_VISIT,
            VisitClass.UNSCHEDULED_VISIT,
            VisitClass.SPECIAL_VISIT,
        )
        is_time_reference_visit = False
        if (
            visit_vo.visit_class
            not in (
                VisitClass.NON_VISIT,
                VisitClass.UNSCHEDULED_VISIT,
                VisitClass.SPECIAL_VISIT,
            )
            and visit_vo.visit_type.value
            == visit_vo.timepoint.visit_timereference.value
        ):
            is_time_reference_visit = True

        if len(timeline._visits) == 0:
            is_first_reference_visit = (
                visit_vo.visit_type.value in StudyVisitTimeReference
            )
            is_reference_visit = is_first_reference_visit
        else:
            is_first_reference_visit = False
            is_reference_visit = visit_vo.visit_type.value in StudyVisitTimeReference

        if (
            is_first_reference_visit
            and visit_vo.visit_class not in visit_classes_without_timing
        ):
            if (
                visit_vo.timepoint.visit_value != 0
                and visit_vo.timepoint.visit_timereference.value.lower()
                != GLOBAL_ANCHOR_VISIT_NAME.lower()
            ):
                raise exceptions.ValidationException(
                    "The first visit should have time span set to 0 or reference to GLOBAL ANCHOR VISIT"
                )
            for visit in timeline._visits:
                if (
                    visit.visit_type == visit_vo.visit_type
                    and visit.uid != visit_vo.uid
                ):
                    raise exceptions.ValidationException(
                        f"There can be only one visit with the following visit type {visit_vo.visit_type.value}"
                    )

        if (
            is_reference_visit
            and visit_vo.visit_class not in visit_classes_without_timing
        ):
            for visit in [
                vis
                for vis in timeline._visits
                if vis.visit_class not in visit_classes_without_timing
            ]:
                if (
                    # if we found another visit with the same visit type
                    visit.visit_type == visit_vo.visit_type
                    # if visit with the same visit type had selected the same value for visit type and time reference
                    and visit.visit_type.value
                    == visit.timepoint.visit_timereference.value
                    # if visit we are creating has the same value selected as visit type and time reference
                    and is_time_reference_visit
                    and visit.uid != visit_vo.uid
                ):
                    raise exceptions.ValidationException(
                        f"There can be only one visit with the following visit type {visit_vo.visit_type.value} that works as time reference"
                    )

        reference_found = False
        if (
            not is_first_reference_visit
            and not is_time_reference_visit
            and visit_vo.visit_class not in visit_classes_without_timing
        ):
            reference_name = StudyVisitTimeReference[visit_input.time_reference_uid]
            for visit in timeline._visits:
                if visit.visit_type.value == reference_name.value:
                    reference_found = True
            if not reference_found and reference_name.value.lower() not in [
                PREVIOUS_VISIT_NAME.lower(),
                GLOBAL_ANCHOR_VISIT_NAME.lower(),
                ANCHOR_VISIT_IN_VISIT_GROUP.lower(),
            ]:
                raise exceptions.ValidationException(
                    f"Time reference of type: {visit_vo.timepoint.visit_timereference.value} wasn't used by previous visits as visit type"
                )

        if visit_vo.is_global_anchor_visit:
            if visit_vo.timepoint.visit_value != 0:
                raise exceptions.ValidationException(
                    "The global anchor visit must take place at day 0."
                )
            if create:
                for visit in timeline._visits:
                    if visit.is_global_anchor_visit:
                        raise exceptions.ValidationException(
                            "There can be only one global anchor visit"
                        )

        if (
            visit_vo.visit_subclass == VisitSubclass.REPEATING_VISIT
            and not visit_vo.repeating_frequency
        ):
            raise exceptions.ValidationException(
                "Repeating Frequency must be provided for Repeating Visits."
            )

        if visit_vo.visit_class not in (
            VisitClass.NON_VISIT,
            VisitClass.UNSCHEDULED_VISIT,
        ):
            if (
                visit_vo.visit_class == VisitClass.SPECIAL_VISIT
                and visit_vo.visit_sublabel_reference is None
            ):
                raise exceptions.ValidationException(
                    "Special Visit has to time reference to some other visit."
                )

            if create:
                timeline.add_visit(visit_vo)
                ordered_visits = timeline.ordered_study_visits
                self._validate_derived_properties(
                    visit_vo=visit_vo, ordered_visits=ordered_visits
                )

                for index, visit in enumerate(ordered_visits):
                    if visit_vo.visit_class != VisitClass.SPECIAL_VISIT:
                        if (
                            visit.get_absolute_duration()
                            == visit_vo.get_absolute_duration()
                            and visit.uid != visit_vo.uid
                        ):
                            raise exceptions.ValidationException(
                                f"There already exists a visit with timing set to {visit.timepoint.visit_value}"
                            )
                        if index + 2 < len(ordered_visits):
                            # we check whether the created visit is not from the epoch that sits
                            # out of the epoch schedule
                            if visit.epoch.order > ordered_visits[
                                index + 2
                            ].epoch.order and ordered_visits[
                                index + 2
                            ].visit_class not in (
                                VisitClass.NON_VISIT,
                                VisitClass.UNSCHEDULED_VISIT,
                            ):
                                raise exceptions.ValidationException(
                                    f"Visit with study day {visit.study_day_number} from "
                                    f"epoch with order ({visit.epoch.order}) ({visit.epoch.epoch.value}) is out of order with "
                                    f"visit with study day {ordered_visits[index+2].study_day_number} from epoch with order "
                                    f"({ordered_visits[index+2].epoch.order}) ({ordered_visits[index+2].epoch.epoch.value})"
                                )
                    elif (
                        visit_vo.visit_class == VisitClass.SPECIAL_VISIT
                        and visit.visit_class == VisitClass.SPECIAL_VISIT
                        and visit_vo.epoch_uid == visit.epoch_uid
                        and visit.uid != visit_vo.uid
                    ):
                        raise exceptions.ValidationException(
                            f"There already exists a Special visit {visit.uid} in the following epoch {visit.epoch_connector.epoch.value}"
                        )
            else:
                ordered_visits = timeline.ordered_study_visits
                for index, visit in enumerate(ordered_visits):
                    if (
                        visit_vo.visit_class != VisitClass.SPECIAL_VISIT
                        and visit.get_absolute_duration()
                        == visit_vo.get_absolute_duration()
                        and visit.uid != visit_vo.uid
                    ):
                        raise exceptions.ValidationException(
                            f"There already exists a visit with timing set to {visit.timepoint.visit_value}"
                        )
                self._validate_derived_properties(
                    visit_vo=visit_vo, ordered_visits=ordered_visits
                )

            if not preview:
                study_epochs = (
                    self._repos.study_epoch_repository.find_all_epochs_by_study(
                        study_uid=visit_vo.study_uid
                    )
                )
                timeline.collect_visits_to_epochs(study_epochs)

                for epoch in study_epochs:
                    if epoch.uid == visit_input.study_epoch_uid:
                        if epoch.previous_visit and (
                            visit_vo.get_absolute_duration()
                            < epoch.previous_visit.get_absolute_duration()
                        ):
                            raise exceptions.ValidationException(
                                "The following visit can't be created as previous epoch "
                                f"({epoch.previous_visit.epoch.epoch.value}) "
                                f"ends at the {epoch.previous_visit.study_day_number} study day"
                            )
                        if epoch.next_visit and (
                            visit_vo.get_absolute_duration()
                            > epoch.next_visit.get_absolute_duration()
                        ):
                            raise exceptions.ValidationException(
                                "The following visit can't be created as the next epoch "
                                f"({epoch.next_visit.epoch.epoch.value}) "
                                f"starts at the {epoch.next_visit.study_day_number} study day"
                            )
            if create:
                timeline.remove_visit(visit_vo)

        if visit_input.visit_sublabel_codelist_uid and (
            visit_input.visit_sublabel_codelist_uid not in self.study_visit_sublabels
        ):
            raise exceptions.ValidationException(
                "Visit Sub Label codelist is not used properly"
            )
        if visit_input.visit_contact_mode_uid not in self.study_visit_contact_mode:
            raise exceptions.ValidationException(
                f"The following CTTerm identified by uid {visit_input.visit_contact_mode_uid} is not a valid"
                f"Visit Contact Mode term."
            )

    def _get_sponsor_library_vo(self):
        lib = self._repos.library_repository.find_by_name(name="Sponsor")
        return LibraryVO.from_input_values_2(
            library_name=lib.library_name,
            is_library_editable_callback=lambda _: lib.is_editable,
        )

    def _create_visit_name_simple_concept(self, visit_name: str):
        visit_name_ar = VisitNameAR.from_input_values(
            author=self.author,
            simple_concept_vo=VisitNameVO.from_repository_values(
                name=visit_name,
                name_sentence_case=visit_name.lower(),
                definition=None,
                abbreviation=None,
                is_template_parameter=True,
            ),
            library=self._get_sponsor_library_vo(),
            generate_uid_callback=self._repos.visit_name_repository.generate_uid,
            find_uid_by_name_callback=self._repos.visit_name_repository.find_uid_by_name,
        )
        self._repos.visit_name_repository.save(visit_name_ar)
        visit_name = TextValue(uid=visit_name_ar.uid, name=visit_name_ar.name)
        return visit_name

    def _create_numeric_value_simple_concept(
        self, value: int, numeric_value_type: NumericValueType
    ):
        if numeric_value_type == NumericValueType.NUMERIC_VALUE:
            aggregate_class = NumericValueAR
            value_object_class = NumericValueVO
            repository_class = self._repos.numeric_value_repository
        elif numeric_value_type == NumericValueType.STUDY_DAY:
            aggregate_class = StudyDayAR
            value_object_class = StudyDayVO
            repository_class = self._repos.study_day_repository
        elif numeric_value_type == NumericValueType.STUDY_DURATION_DAYS:
            aggregate_class = StudyDurationDaysAR
            value_object_class = StudyDurationDaysVO
            repository_class = self._repos.study_duration_days_repository
        elif numeric_value_type == NumericValueType.STUDY_WEEK:
            aggregate_class = StudyWeekAR
            value_object_class = StudyWeekVO
            repository_class = self._repos.study_week_repository
        elif numeric_value_type == NumericValueType.STUDY_DURATION_WEEKS:
            aggregate_class = StudyDurationWeeksAR
            value_object_class = StudyDurationWeeksVO
            repository_class = self._repos.study_duration_weeks_repository
        elif numeric_value_type == NumericValueType.WEEK_IN_STUDY:
            aggregate_class = WeekInStudyAR
            value_object_class = WeekInStudyVO
            repository_class = self._repos.week_in_study_repository
        else:
            raise exceptions.ValidationException(
                f"Unknown numeric value type to create {numeric_value_type.value}"
            )

        numeric_ar = aggregate_class.from_input_values(
            author=self.author,
            simple_concept_vo=value_object_class.from_input_values(
                value=float(value),
                definition=None,
                abbreviation=None,
                is_template_parameter=True,
            ),
            library=self._get_sponsor_library_vo(),
            generate_uid_callback=repository_class.generate_uid,
            find_uid_by_name_callback=repository_class.find_uid_by_name,
        )
        repository_class.save(numeric_ar)
        numeric_value_object = NumericValue(
            uid=numeric_ar.uid, value=numeric_ar.concept_vo.value
        )
        return numeric_value_object

    def _create_timepoint_simple_concept(
        self, study_visit_input: StudyVisitCreateInput
    ):
        numeric_ar = self._create_numeric_value_simple_concept(
            value=study_visit_input.time_value,
            numeric_value_type=NumericValueType.NUMERIC_VALUE,
        )
        timepoint_ar = TimePointAR.from_input_values(
            author=self.author,
            simple_concept_vo=TimePointVO.from_input_values(
                name_sentence_case=None,
                definition=None,
                abbreviation=None,
                is_template_parameter=True,
                numeric_value_uid=numeric_ar.uid,
                unit_definition_uid=study_visit_input.time_unit_uid,
                time_reference_uid=study_visit_input.time_reference_uid,
                find_numeric_value_by_uid=self._repos.numeric_value_repository.find_by_uid_2,
                find_unit_definition_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
                find_time_reference_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            ),
            library=self._get_sponsor_library_vo(),
            generate_uid_callback=self._repos.time_point_repository.generate_uid,
            find_uid_by_name_callback=self._repos.time_point_repository.find_uid_by_name,
        )
        self._repos.time_point_repository.save(timepoint_ar)
        timepoint_object = TimePoint(
            uid=timepoint_ar.uid,
            visit_timereference=StudyVisitTimeReference[
                study_visit_input.time_reference_uid
            ],
            time_unit_uid=study_visit_input.time_unit_uid,
            visit_value=study_visit_input.time_value,
        )
        return timepoint_object

    def derive_visit_number(self, visit_class: VisitClass):
        if visit_class == VisitClass.NON_VISIT:
            return NON_VISIT_NUMBER
        if visit_class == VisitClass.UNSCHEDULED_VISIT:
            return UNSCHEDULED_VISIT_NUMBER
        return 1

    def _from_input_values(
        self, create_input: StudyVisitCreateInput, epoch: StudyEpochVO
    ):
        unit_repository = self._repos.unit_definition_repository
        if create_input.time_unit_uid:
            req_time_unit_ar: UnitDefinitionAR = unit_repository.find_by_uid_2(
                create_input.time_unit_uid
            )
            req_time_unit = req_time_unit_ar.concept_vo
        else:
            req_time_unit = None
        if create_input.visit_window_unit_uid:
            window_time_unit_ar: UnitDefinitionAR = unit_repository.find_by_uid_2(
                create_input.visit_window_unit_uid
            )
            window_time_unit = window_time_unit_ar.concept_vo
            window_unit_object = TimeUnit(
                name=window_time_unit.name,
                conversion_factor_to_master=window_time_unit.conversion_factor_to_master,
                from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
            )
        else:
            window_unit_object = None
        if (
            create_input.visit_sublabel_codelist_uid != ""
            and create_input.visit_sublabel_codelist_uid is not None
        ):
            visit_sublabel = self.study_visit_sublabels[
                create_input.visit_sublabel_codelist_uid
            ]
        else:
            visit_sublabel = None

        if req_time_unit:
            time_unit_object = TimeUnit(
                name=req_time_unit.name,
                conversion_factor_to_master=req_time_unit.conversion_factor_to_master,
                from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
            )
        else:
            time_unit_object = None
        day_unit_object = TimeUnit(
            name="day",
            conversion_factor_to_master=self._day_unit.concept_vo.conversion_factor_to_master,
            from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
        )

        week_unit_object = TimeUnit(
            name="Week",
            conversion_factor_to_master=self._week_unit.concept_vo.conversion_factor_to_master,
            from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
        )
        visit_class = (
            VisitClass[create_input.visit_class] if create_input.visit_class else None
        )
        visit_subclass = (
            VisitSubclass[create_input.visit_subclass]
            if create_input.visit_subclass
            else None
        )
        study_visit_vo = StudyVisitVO(
            uid=self.repo.generate_uid(),
            visit_sublabel=visit_sublabel,
            visit_sublabel_uid=create_input.visit_sublabel_codelist_uid,
            visit_sublabel_reference=create_input.visit_sublabel_reference,
            consecutive_visit_group=create_input.consecutive_visit_group,
            show_visit=create_input.show_visit,
            visit_window_min=create_input.min_visit_window_value,
            visit_window_max=create_input.max_visit_window_value,
            window_unit_uid=create_input.visit_window_unit_uid,
            window_unit_object=window_unit_object,
            time_unit_object=time_unit_object,
            description=create_input.description,
            start_rule=create_input.start_rule,
            end_rule=create_input.end_rule,
            visit_contact_mode=StudyVisitContactMode[
                create_input.visit_contact_mode_uid
            ],
            epoch_allocation=(
                StudyVisitEpochAllocation[create_input.epoch_allocation_uid]
                if create_input.epoch_allocation_uid
                else None
            ),
            visit_type=StudyVisitType[create_input.visit_type_uid],
            start_date=datetime.datetime.now(datetime.timezone.utc),
            author=self.author,
            status=StudyStatus.DRAFT,
            day_unit_object=day_unit_object,
            week_unit_object=week_unit_object,
            epoch_connector=epoch,
            visit_class=visit_class,
            visit_subclass=visit_subclass if create_input.visit_subclass else None,
            is_global_anchor_visit=create_input.is_global_anchor_visit,
            is_soa_milestone=create_input.is_soa_milestone,
            visit_number=self.derive_visit_number(visit_class=visit_class),
            visit_order=self.derive_visit_number(visit_class=visit_class),
            repeating_frequency=StudyVisitRepeatingFrequency[
                create_input.repeating_frequency_uid
            ]
            if create_input.repeating_frequency_uid
            else None,
        )
        if study_visit_vo.visit_class not in [
            VisitClass.NON_VISIT,
            VisitClass.UNSCHEDULED_VISIT,
            VisitClass.SPECIAL_VISIT,
        ]:
            missing_fields = []
            if create_input.time_unit_uid is None:
                missing_fields.append("time_unit_uid")
            if create_input.time_reference_uid is None:
                missing_fields.append("time_reference_uid")
            if create_input.time_value is None:
                missing_fields.append("time_value")
            if missing_fields:
                raise ValidationException(
                    f"The following fields are missing ({missing_fields}) for the Visit with the ({visit_class.value}) visit class"
                )
            study_visit_vo.timepoint = self._create_timepoint_simple_concept(
                study_visit_input=create_input
            )
            study_visit_vo.study_day = self._create_numeric_value_simple_concept(
                value=study_visit_vo.derive_study_day_number(),
                numeric_value_type=NumericValueType.STUDY_DAY,
            )
            study_visit_vo.study_duration_days = (
                self._create_numeric_value_simple_concept(
                    value=study_visit_vo.derive_study_duration_days_number(),
                    numeric_value_type=NumericValueType.STUDY_DURATION_DAYS,
                )
            )
            study_visit_vo.study_week = self._create_numeric_value_simple_concept(
                value=study_visit_vo.derive_study_week_number(),
                numeric_value_type=NumericValueType.STUDY_WEEK,
            )
            study_visit_vo.study_duration_weeks = (
                self._create_numeric_value_simple_concept(
                    value=study_visit_vo.derive_study_duration_weeks_number(),
                    numeric_value_type=NumericValueType.STUDY_DURATION_WEEKS,
                )
            )
            study_visit_vo.week_in_study = self._create_numeric_value_simple_concept(
                value=study_visit_vo.derive_week_in_study_number(),
                numeric_value_type=NumericValueType.WEEK_IN_STUDY,
            )

            if study_visit_vo.visit_class == visit_class.MANUALLY_DEFINED_VISIT:
                study_visit_vo.visit_number = create_input.visit_number
                study_visit_vo.vis_unique_number = create_input.unique_visit_number
                study_visit_vo.vis_short_name = create_input.visit_short_name
                study_visit_vo.visit_name_sc = self._create_visit_name_simple_concept(
                    visit_name=create_input.visit_name
                )
            elif (
                study_visit_vo.visit_class != visit_class.MANUALLY_DEFINED_VISIT
                and any(
                    [
                        create_input.visit_number,
                        create_input.unique_visit_number,
                        create_input.visit_short_name,
                        create_input.visit_name,
                    ]
                )
            ):
                raise ValidationException(
                    "Only Manually defined visit can specify visit_number, unique_visit_number, visit_short_name or visit_name properties."
                )
        return study_visit_vo

    def synchronize_visit_numbers(
        self, ordered_visits: list[Any], start_index_to_synchronize: int
    ):
        """
        Fixes the visit number if some visit was added in between of others or some of the visits were removed, edited.
        :param ordered_visits:
        :param start_index_to_synchronize:
        :return:
        """
        for visit in ordered_visits[start_index_to_synchronize:]:
            # Manually defined visits have explicitly specified order properties
            if visit.visit_class != VisitClass.MANUALLY_DEFINED_VISIT:
                self.assign_props_derived_from_visit_number(study_visit=visit)
                self.repo.save(visit)

    def assign_props_derived_from_visit_number(self, study_visit: StudyVisitVO):
        """
        Assigns some properties of StudyVisitVO that are derived from Visit Number.
        Visit Number property is not assigned when we create StudyVisitVO.
        It's done later as we need to derive VisitNumber from the order of given Visit in a sequence of all Study Visits.
        This is why we need to initialize some of the properties later then creation of StudyVisitVO.
        :param study_visit:
        :return:
        """
        study_visit.visit_name_sc = self._create_visit_name_simple_concept(
            visit_name=study_visit.derive_visit_name()
        )

    @db.transaction
    def create(self, study_uid: str, study_visit_input: StudyVisitCreateInput):
        study_visits = self.repo.find_all_visits_by_study_uid(study_uid)

        epoch = self._repos.study_epoch_repository.find_by_uid(
            uid=study_visit_input.study_epoch_uid, study_uid=study_uid
        )
        study_visit = self._from_input_values(study_visit_input, epoch)
        timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
        self._validate_visit(study_visit_input, study_visit, timeline, create=True)
        self.assign_props_derived_from_visit_number(study_visit=study_visit)
        added_item = self.repo.save(study_visit, create=True)

        timeline.add_visit(added_item)

        ordered_visits = timeline.ordered_study_visits
        # if added item is not last in ordered_study_visits, then we have to synchronize Visit Numbers
        if added_item.uid != ordered_visits[-1].uid:
            self.synchronize_visit_numbers(
                ordered_visits=ordered_visits,
                start_index_to_synchronize=int(added_item.visit_number),
            )
        return self._transform_all_to_response_model(added_item)

    @db.transaction
    def preview(self, study_uid: str, study_visit_input: StudyVisitCreateInput):
        study_visits = self.repo.find_all_visits_by_study_uid(study_uid)

        epoch = self._repos.study_epoch_repository.find_by_uid(
            uid=study_visit_input.study_epoch_uid, study_uid=study_uid
        )
        study_visit = self._from_input_values(study_visit_input, epoch)
        timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
        self._validate_visit(
            study_visit_input, study_visit, timeline, create=True, preview=True
        )

        study_visit.uid = "preview"
        timeline.add_visit(study_visit)

        return self._transform_all_to_response_model(study_visit)

    @db.transaction
    def edit(
        self,
        study_uid: str,
        study_visit_uid: str,
        study_visit_input: StudyVisitEditInput,
    ):
        study_visits = self.repo.find_all_visits_by_study_uid(study_uid)
        study_visit = self.repo.find_by_uid(study_uid=study_uid, uid=study_visit_uid)

        epoch = self._repos.study_epoch_repository.find_by_uid(
            uid=study_visit_input.study_epoch_uid, study_uid=study_uid
        )
        updated_visit = self._from_input_values(study_visit_input, epoch)
        update_dict = {
            k: v
            for k, v in dataclasses.asdict(updated_visit).items()
            if k not in ["uid"]
        }
        update_dict["time_unit_object"] = updated_visit.time_unit_object
        update_dict["window_unit_object"] = updated_visit.window_unit_object
        update_dict["day_unit_object"] = updated_visit.day_unit_object
        update_dict["week_unit_object"] = updated_visit.week_unit_object
        update_dict["timepoint"] = updated_visit.timepoint
        update_dict["study_day"] = updated_visit.study_day
        update_dict["study_duration_days"] = updated_visit.study_duration_days
        update_dict["study_duration_weeks"] = updated_visit.study_duration_weeks
        update_dict["week_in_study"] = updated_visit.week_in_study
        update_dict["study_week"] = updated_visit.study_week
        update_dict["visit_name_sc"] = updated_visit.visit_name_sc

        new_study_visit = dataclasses.replace(study_visit, **update_dict)
        new_study_visit.epoch_connector = epoch

        timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
        timeline.update_visit(new_study_visit)

        self._validate_visit(study_visit_input, new_study_visit, timeline, create=False)

        ordered_visits = timeline.ordered_study_visits

        # If Visit Number was edited, then we have to synchronize the Visit Numbers in the database
        if study_visit.visit_number != new_study_visit.visit_number:
            if new_study_visit.visit_number < study_visit.visit_number:
                start_index_to_sync = int(new_study_visit.visit_number) - 1
            else:
                start_index_to_sync = int(study_visit.visit_number) - 1
            self.synchronize_visit_numbers(
                ordered_visits=ordered_visits,
                start_index_to_synchronize=start_index_to_sync,
            )
        self.assign_props_derived_from_visit_number(study_visit=new_study_visit)

        self.repo.save(new_study_visit)

        return self._transform_all_to_response_model(new_study_visit)

    @db.transaction
    def delete(self, study_uid: str, study_visit_uid: str):
        study_visit = self.repo.find_by_uid(study_uid=study_uid, uid=study_visit_uid)
        if study_visit.status != StudyStatus.DRAFT:
            raise ValidationException("Cannot delete visits non DRAFT status")

        subvisits_references = self.repo.find_all_visits_referencing_study_visit(
            study_visit_uid=study_visit_uid
        )
        if subvisits_references:
            subvisit_ref_short_labels = [
                visit.short_visit_label for visit in subvisits_references
            ]
            raise BusinessLogicException(
                f"The Visit can't be deleted as other visits ({subvisit_ref_short_labels}) are referencing this Visit"
            )

        # add check if visits that we want to group are the same
        schedules_service = StudyActivityScheduleService()

        # Load aggregate
        study_activity_schedules = (
            schedules_service.get_all_schedules_for_specific_visit(
                study_uid=study_uid, study_visit_uid=study_visit.uid
            )
        )
        for study_activity_schedule in study_activity_schedules:
            self._repos.study_activity_schedule_repository.delete(
                study_uid,
                study_activity_schedule.study_activity_schedule_uid,
                self.author,
            )

        study_visit.delete()

        self.repo.save(study_visit)

        study_visits = self.repo.find_all_visits_by_study_uid(study_uid)
        timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
        ordered_visits = timeline.ordered_study_visits

        # we want to synchronize numbers if we have more than one visit
        if len(ordered_visits) > 0:
            # After removing specific visit if it was not the last visit,
            # we have to synchronize the Visit Numbers to fill in the gap
            if study_visit.uid != ordered_visits[-1].uid:
                self.synchronize_visit_numbers(
                    ordered_visits=ordered_visits,
                    start_index_to_synchronize=int(study_visit.visit_number) - 1,
                )

    @db.transaction
    def get_consecutive_groups(self, study_uid: str):
        all_visits = self.repo.find_all_visits_by_study_uid(study_uid)
        groups = [
            visit.consecutive_visit_group
            for visit in all_visits
            if visit.consecutive_visit_group is not None
        ]
        groups_set = set(groups)
        return groups_set

    @db.transaction
    def audit_trail(
        self,
        visit_uid: str,
        study_uid: str,
    ) -> list[StudyVisitVersion]:
        all_versions = self.repo.get_all_versions(visit_uid, study_uid=study_uid)
        versions = [
            self._transform_all_to_response_history_model(_).dict()
            for _ in all_versions
        ]
        data = calculate_diffs(versions, StudyVisitVersion)
        return data

    @db.transaction
    def audit_trail_all_visits(
        self,
        study_uid: str,
    ) -> list[StudyVisitVersion]:
        data = calculate_diffs_history(
            get_all_object_versions=self.repo.get_all_visit_versions,
            transform_all_to_history_model=self._transform_all_to_response_history_model,
            study_uid=study_uid,
            version_object_class=StudyVisitVersion,
        )
        return data

    @db.transaction
    def remove_visit_consecutive_group(
        self, study_uid: str, consecutive_visit_group: str
    ):
        study_visits = self.repo.find_all_visits_by_study_uid(study_uid=study_uid)
        timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
        ordered_visits = timeline.ordered_study_visits
        for visit in ordered_visits:
            if visit.consecutive_visit_group == consecutive_visit_group:
                visit.consecutive_visit_group = None
                self.repo.save(self.repo.from_neomodel_to_vo(visit))

    @db.transaction
    def assign_visit_consecutive_group(
        self,
        study_uid: str,
        visits_to_assign: list[str],
        overwrite_visit_from_template: str | None = None,
    ) -> list[StudyVisit]:
        study_visits = self.repo.find_all_visits_by_study_uid(study_uid=study_uid)
        timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
        ordered_visits = timeline.ordered_study_visits

        # Sort Visits that are about to be grouped
        visits_to_assign.sort()
        # Get StudyVisitVOs for these visits that should be assigned to consecutive visit group
        visits_to_be_assigned = self._get_visits_to_be_assigned_to_cons_group(
            visit_to_assign_uids=visits_to_assign, ordered_visits=ordered_visits
        )

        # Get visit short labels to derive the consecutive visit group name
        visits_short_labels = sorted(
            visit.visit_short_name for visit in visits_to_be_assigned
        )
        consecutive_visit_group = f"{visits_short_labels[0]}-{visits_short_labels[-1]}"
        self._validate_consecutive_group_assignment(
            study_uid=study_uid,
            visit_to_assign_uids=visits_to_assign,
            visits_to_be_assigned=visits_to_be_assigned,
            overwrite_visit_from_template=overwrite_visit_from_template,
        )
        updated_visits = []
        for visit in ordered_visits:
            if visit.uid in visits_to_assign:
                visit.consecutive_visit_group = consecutive_visit_group
                self.repo.save(self.repo.from_neomodel_to_vo(visit))
                updated_visits.append(self._transform_all_to_response_model(visit))
        return updated_visits

    def _get_visits_to_be_assigned_to_cons_group(
        self,
        visit_to_assign_uids: list[str],
        ordered_visits: list[StudyVisitVO],
    ):
        visits_to_assign = sorted(visit_to_assign_uids)
        idx_of_first_vis_in_cons_group = None
        for idx, visit in enumerate(ordered_visits):
            if visit.uid == visits_to_assign[0]:
                idx_of_first_vis_in_cons_group = idx

        # if first visit from visits_to_assign was not found in all visits for a given Study
        if idx_of_first_vis_in_cons_group is None:
            raise ValidationException(
                f"The {visits_to_assign[0]} was not found in the ordered study visits"
            )

        # get the slice of all visits that represents the visit objects that are being assigned to consecutive group
        visits_to_be_assigned = ordered_visits[
            idx_of_first_vis_in_cons_group : idx_of_first_vis_in_cons_group
            + len(visits_to_assign)
        ]
        return visits_to_be_assigned

    def _validate_consecutive_group_assignment(
        self,
        study_uid: str,
        visit_to_assign_uids: list[str],
        visits_to_be_assigned: list[StudyVisitVO],
        overwrite_visit_from_template: str | None = None,
    ):
        visit_to_overwrite_from = None
        for visit in visits_to_be_assigned:
            if visit.uid == overwrite_visit_from_template:
                visit_to_overwrite_from = visit
        # check if none of visits that we want to assign to consecutive group is not having a group already
        for visit in visits_to_be_assigned:
            if visit.consecutive_visit_group:
                if overwrite_visit_from_template:
                    # overwrite visit with props from overwrite_visit_from_template
                    self._overwrite_visit_from_template(
                        visit=visit, visit_template=visit_to_overwrite_from
                    )
                else:
                    raise ValidationException(
                        f"The following visit {visit.uid} already has consecutive group {visit.consecutive_visit_group}"
                    )

        chunk_uids = [visit.uid for visit in visits_to_be_assigned]

        # check if we don't have a gap between visits that we are trying to assign to a consecutive visit group
        for visit_to_assign, ordered_visit in zip(visit_to_assign_uids, chunk_uids):
            if visit_to_assign != ordered_visit:
                raise ValidationException(
                    "To create visits group please select consecutive visits."
                )

        # add check if visits that we want to group are the same
        schedules_service = StudyActivityScheduleService()
        if visit_to_overwrite_from:
            reference_visit = visit_to_overwrite_from
        else:
            reference_visit = visits_to_be_assigned[0]
        reference_visit_study_activities = {
            schedule.study_activity_uid
            for schedule in schedules_service.get_all_schedules_for_specific_visit(
                study_uid=study_uid, study_visit_uid=reference_visit.uid
            )
            if schedule.study_activity_uid is not None
        }
        for visit in visits_to_be_assigned:
            are_visits_the_same = reference_visit.compare_cons_group_equality(
                visit_study_activities=reference_visit_study_activities,
                other_visit=visit,
                other_visit_study_activities={
                    schedule.study_activity_uid
                    for schedule in schedules_service.get_all_schedules_for_specific_visit(
                        study_uid=study_uid, study_visit_uid=visit.uid
                    )
                    if schedule.study_activity_uid is not None
                },
            )
            if not are_visits_the_same:
                # overwrite
                if overwrite_visit_from_template:
                    self._overwrite_visit_from_template(
                        visit=visit, visit_template=visit_to_overwrite_from
                    )
                else:
                    raise ValidationException(
                        f"The following visit {reference_visit.visit_name} is not the same as {visit.visit_name}"
                    )

    def _overwrite_visit_from_template(self, visit, visit_template):
        schedules_service = StudyActivityScheduleService()

        # remove old activity schedules
        for schedule in schedules_service.get_all_schedules_for_specific_visit(
            study_uid=visit.study_uid, study_visit_uid=visit.uid
        ):
            self._repos.study_activity_schedule_repository.delete(
                study_uid=visit.study_uid,
                selection_uid=schedule.study_activity_schedule_uid,
                author=self.author,
            )

        # copy activity schedules from the visit to overwrite
        for schedule in schedules_service.get_all_schedules_for_specific_visit(
            study_uid=visit_template.study_uid, study_visit_uid=visit_template.uid
        ):
            self._repos.study_activity_schedule_repository.save(
                schedules_service._from_input_values(
                    study_uid=visit.study_uid,
                    schedule_input=StudyActivityScheduleCreateInput(
                        study_activity_uid=schedule.study_activity_uid,
                        study_visit_uid=visit.uid,
                    ),
                ),
                self.author,
            )

        # copy properties from visit_template
        visit.copy_cons_group_visit_properties(visit_template)
        self._repos.study_visit_repository.save(visit)
