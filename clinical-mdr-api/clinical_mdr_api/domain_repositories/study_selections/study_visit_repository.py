import datetime

from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.config import (
    GLOBAL_ANCHOR_VISIT_NAME,
    PREVIOUS_VISIT_NAME,
    STUDY_VISIT_TIMEREF_NAME,
)
from clinical_mdr_api.domain_repositories.concepts.unit_definitions.unit_definition_repository import (
    UnitDefinitionRepository,
)
from clinical_mdr_api.domain_repositories.generic_repository import (
    manage_previous_connected_study_selection_relationships,
)
from clinical_mdr_api.domain_repositories.models._utils import to_relation_trees
from clinical_mdr_api.domain_repositories.models.concepts import (
    StudyDayRoot,
    StudyDurationDaysRoot,
    StudyDurationWeeksRoot,
    StudyWeekRoot,
    TimePointRoot,
    UnitDefinitionRoot,
    VisitNameRoot,
    WeekInStudyRoot,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
)
from clinical_mdr_api.domain_repositories.models.study_epoch import StudyEpoch
from clinical_mdr_api.domain_repositories.models.study_visit import StudyVisit
from clinical_mdr_api.domain_repositories.study_selections.study_epoch_repository import (
    StudyEpochRepository,
    get_ctlist_terms_by_name,
)
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_visit import (
    NumericValue,
    StudyVisitHistoryVO,
    StudyVisitVO,
    TextValue,
    TimeUnit,
)
from clinical_mdr_api.models.study_selections.study_visit import (
    StudyVisitOGM,
    StudyVisitOGMVer,
)


def get_valid_visit_types_for_epoch_type(epoch_type_uid: str, study_uid: str):
    cypher_query = """
        MATCH (visit_type_value:CTTermNameValue)<-[:LATEST]-(:CTTermNameRoot)<-[:HAS_NAME_ROOT]-
        (visit_type_root:CTTermRoot)-[:VALID_FOR_EPOCH_TYPE]->(:CTTermRoot {uid:$epoch_type_uid})

        RETURN visit_type_root.uid, visit_type_value.name
        """
    items, _ = db.cypher_query(
        cypher_query, {"epoch_type_uid": epoch_type_uid, "study_uid": study_uid}
    )
    return {a[0]: a[1] for a in items}


def get_valid_time_references_for_study(
    study_uid: str, effective_date: datetime.datetime | None = None
):
    if not effective_date:
        time_reference_match = "MATCH (time_reference_value:CTTermNameValue)<-[:LATEST]-(time_reference_name_root)"
        visit_type_match = (
            "MATCH (visit_type_root)-[:LATEST]->(visit_type_value:CTTermNameValue)"
        )
    else:
        time_reference_match = """
        MATCH (time_reference_value:CTTermNameValue)<-[hv:HAS_VERSION]-(time_reference_name_root)
            WHERE (hv.start_date<= datetime($effective_date) < hv.end_date) OR (hv.end_date IS NULL AND (hv.start_date <= datetime($effective_date)))
        """
        visit_type_match = """
        MATCH (visit_type_root)-[hv_type:HAS_VERSION]->(visit_type_value:CTTermNameValue)
            WHERE (hv_type.start_date<= datetime($effective_date) < hv_type.end_date) OR (hv_type.end_date IS NULL AND (hv_type.start_date <= datetime($effective_date)))
        """
    cypher_query = f"""
        MATCH (time_reference_name_root:CTTermNameRoot)<-[HAS_NAME_ROOT]-
        (time_reference_root:CTTermRoot)<-[HAS_TERM]-(codelist_root:CTCodelistRoot)-[:HAS_NAME_ROOT]->
        (:CTCodelistNameRoot)-[:LATEST]->(:CTCodelistNameValue {{name:$time_reference_codelist_name}})

        {time_reference_match}
        
        MATCH (study_root:StudyRoot {{uid:$study_uid}})-[:LATEST]->(:StudyValue)-[:HAS_STUDY_VISIT]->
            (study_visit:StudyVisit)-[:HAS_VISIT_TYPE]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(visit_type_root:CTTermNameRoot) 
        
        {visit_type_match}
            
        WITH time_reference_root, time_reference_value, COLLECT(visit_type_value.name) AS visit_type_value_names 
            WHERE time_reference_value.name IN visit_type_value_names 
                OR time_reference_value.name IN [$global_anchor_visit_name, $previous_visit_name]
        RETURN time_reference_root.uid, time_reference_value.name
        """
    items, _ = db.cypher_query(
        cypher_query,
        {
            "time_reference_codelist_name": STUDY_VISIT_TIMEREF_NAME,
            "study_uid": study_uid,
            "global_anchor_visit_name": GLOBAL_ANCHOR_VISIT_NAME,
            "previous_visit_name": PREVIOUS_VISIT_NAME,
            "effective_date": effective_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            if effective_date
            else None,
        },
    )

    return {time_reference[0]: time_reference[1] for time_reference in items}


class StudyVisitRepository:
    def __init__(self, author: str):
        self.author = author
        unit_repository = UnitDefinitionRepository(self.author)
        units, _ = unit_repository.get_all_optimized()
        unit: UnitDefinitionAR
        self._day_unit = None
        self._week_unit = None
        for unit in units:
            if unit.concept_vo.name == "day":
                self._day_unit = unit
            if unit.concept_vo.name == "week":
                self._week_unit = unit

    def generate_uid(self) -> str:
        return StudyVisit.get_next_free_uid_and_increment_counter()

    def fetch_ctlist(self, code_list_name: str, effective_date=None):
        return get_ctlist_terms_by_name(code_list_name, effective_date=effective_date)

    def get_day_week_units(self):
        return (self._day_unit, self._week_unit)

    def save(self, visit: StudyVisitVO, create: bool = False):
        return self._update(visit, create)

    def count_activities(
        self, visit_uid: str, study_value_version: str | None = None
    ) -> int:
        """
        Returns the amount of activities assigned to given study visit

        :return: int
        """
        if study_value_version:
            query = """
                MATCH (:StudyRoot)-[l:HAS_VERSION{status:'RELEASED', version:$study_value_version}]-(:StudyValue)-[:HAS_STUDY_VISIT]->(svis:StudyVisit{uid:$uid})
                MATCH (svis:StudyVisit)-[:STUDY_VISIT_HAS_SCHEDULE]->(activity_schedule:StudyActivitySchedule)--(:StudyValue)-[l:HAS_VERSION{status:'RELEASED', version:$study_value_version}]-(:StudyRoot)
                RETURN count(activity_schedule)
                """
            result, _ = db.cypher_query(
                query=query,
                params={"uid": visit_uid, "study_value_version": study_value_version},
            )
        else:
            query = """
                MATCH (:StudyValue)-[:HAS_STUDY_VISIT]->(svis:StudyVisit{uid:$uid})
                MATCH (svis:StudyVisit)-[:STUDY_VISIT_HAS_SCHEDULE]->(activity_schedule:StudyActivitySchedule)
                RETURN count(activity_schedule)
                """
            result, _ = db.cypher_query(query=query, params={"uid": visit_uid})

        return result[0][0] if len(result) > 0 else 0

    def count_study_visits(self, study_uid: str) -> int:
        nodes = to_relation_trees(
            StudyVisit.nodes.filter(
                has_study_visit__latest_value__uid=study_uid  # , is_deleted=False
            )
        )
        return len(nodes)

    def from_neomodel_to_vo(
        self,
        study_visit_ogm_input: StudyVisitOGM,
        study_value_version: str | None = None,
    ):
        epoch_repository = StudyEpochRepository(author=self.author)
        study_epoch_object = epoch_repository.find_by_uid(
            uid=study_visit_ogm_input.epoch_uid,
            study_uid=study_visit_ogm_input.study_uid,
            study_value_version=study_value_version,
        )

        unit_repository = UnitDefinitionRepository(self.author)
        if study_visit_ogm_input.timepoint:
            req_time_unit_ar: UnitDefinitionAR = unit_repository.find_by_uid_2(
                study_visit_ogm_input.timepoint.time_unit_uid
            )
            req_time_unit = req_time_unit_ar.concept_vo
            time_unit_object = TimeUnit(
                name=req_time_unit.name,
                conversion_factor_to_master=req_time_unit.conversion_factor_to_master,
                from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
            )
        else:
            time_unit_object = None

        if study_visit_ogm_input.window_unit_uid is not None:
            window_time_unit_ar: UnitDefinitionAR = unit_repository.find_by_uid_2(
                study_visit_ogm_input.window_unit_uid
            )
            window_time_unit = window_time_unit_ar.concept_vo
            window_unit_object = TimeUnit(
                name=window_time_unit.name,
                conversion_factor_to_master=window_time_unit.conversion_factor_to_master,
                from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
            )
        else:
            window_unit_object = None

        if study_visit_ogm_input.study_day:
            study_day = StudyDayRoot.nodes.get(
                uid=study_visit_ogm_input.study_day.uid
            ).has_latest_value.get()
        else:
            study_day = None
        if study_visit_ogm_input.study_duration_days:
            study_duration_days = StudyDurationDaysRoot.nodes.get(
                uid=study_visit_ogm_input.study_duration_days.uid
            ).has_latest_value.get()
        else:
            study_duration_days = None
        if study_visit_ogm_input.study_week:
            study_week = StudyWeekRoot.nodes.get(
                uid=study_visit_ogm_input.study_week.uid
            ).has_latest_value.get()
        else:
            study_week = None
        if study_visit_ogm_input.study_duration_weeks:
            study_duration_weeks = StudyDurationWeeksRoot.nodes.get(
                uid=study_visit_ogm_input.study_duration_weeks.uid
            ).has_latest_value.get()
        else:
            study_duration_weeks = None
        if study_visit_ogm_input.week_in_study:
            week_in_study = WeekInStudyRoot.nodes.get(
                uid=study_visit_ogm_input.week_in_study.uid
            ).has_latest_value.get()
        else:
            week_in_study = None
        visit_name = VisitNameRoot.nodes.get(
            uid=study_visit_ogm_input.visit_name_sc.uid
        ).has_latest_value.get()
        return StudyVisitVO(
            uid=study_visit_ogm_input.uid,
            visit_number=study_visit_ogm_input.visit_number,
            visit_sublabel=study_visit_ogm_input.visit_sublabel,
            visit_sublabel_reference=study_visit_ogm_input.visit_sublabel_reference,
            visit_sublabel_uid=study_visit_ogm_input.visit_sublabel_uid,
            consecutive_visit_group=study_visit_ogm_input.consecutive_visit_group,
            show_visit=study_visit_ogm_input.show_visit,
            timepoint=study_visit_ogm_input.timepoint,
            study_day=NumericValue(
                uid=study_visit_ogm_input.study_day.uid, value=int(study_day.value)
            )
            if study_visit_ogm_input.study_day
            else None,
            study_duration_days=NumericValue(
                uid=study_visit_ogm_input.study_duration_days.uid,
                value=int(study_duration_days.value),
            )
            if study_visit_ogm_input.study_duration_days
            else None,
            study_week=NumericValue(
                uid=study_visit_ogm_input.study_week.uid, value=int(study_week.value)
            )
            if study_visit_ogm_input.study_week
            else None,
            study_duration_weeks=NumericValue(
                uid=study_visit_ogm_input.study_duration_weeks.uid,
                value=int(study_duration_weeks.value),
            )
            if study_visit_ogm_input.study_duration_weeks
            else None,
            week_in_study=NumericValue(
                uid=study_visit_ogm_input.week_in_study.uid,
                value=int(week_in_study.value),
            )
            if study_visit_ogm_input.week_in_study
            else None,
            visit_name_sc=TextValue(
                uid=study_visit_ogm_input.visit_name_sc.uid, name=visit_name.name
            ),
            time_unit_object=time_unit_object,
            window_unit_object=window_unit_object,
            visit_window_min=study_visit_ogm_input.visit_window_min,
            visit_window_max=study_visit_ogm_input.visit_window_max,
            window_unit_uid=study_visit_ogm_input.window_unit_uid,
            description=study_visit_ogm_input.description,
            start_rule=study_visit_ogm_input.start_rule,
            end_rule=study_visit_ogm_input.end_rule,
            visit_contact_mode=study_visit_ogm_input.visit_contact_mode,
            epoch_allocation=study_visit_ogm_input.epoch_allocation,
            visit_type=study_visit_ogm_input.visit_type,
            status=StudyStatus(study_visit_ogm_input.status),
            start_date=study_visit_ogm_input.start_date,
            author=study_visit_ogm_input.author,
            day_unit_object=study_visit_ogm_input.day_unit_object,
            week_unit_object=study_visit_ogm_input.week_unit_object,
            epoch_connector=study_epoch_object,
            visit_class=study_visit_ogm_input.visit_class,
            visit_subclass=study_visit_ogm_input.visit_subclass
            if study_visit_ogm_input.visit_subclass
            else None,
            is_global_anchor_visit=study_visit_ogm_input.is_global_anchor_visit,
            is_soa_milestone=study_visit_ogm_input.is_soa_milestone,
            visit_order=study_visit_ogm_input.visit_number,
            vis_unique_number=study_visit_ogm_input.vis_unique_number,
            vis_short_name=study_visit_ogm_input.vis_short_name,
        )

    def _from_neomodel_to_history_vo(self, study_visit_ogm_input: StudyVisitOGMVer):
        study_visit_vo = self.from_neomodel_to_vo(study_visit_ogm_input)
        return StudyVisitHistoryVO(
            uid=study_visit_vo.uid,
            visit_number=study_visit_vo.visit_number,
            visit_sublabel=study_visit_vo.visit_sublabel,
            visit_sublabel_reference=study_visit_vo.visit_sublabel_reference,
            visit_sublabel_uid=study_visit_vo.visit_sublabel_uid,
            consecutive_visit_group=study_visit_vo.consecutive_visit_group,
            show_visit=study_visit_vo.show_visit,
            timepoint=study_visit_vo.timepoint,
            study_day=study_visit_vo.study_day,
            study_duration_days=study_visit_vo.study_duration_days,
            study_week=study_visit_vo.study_week,
            study_duration_weeks=study_visit_vo.study_duration_weeks,
            week_in_study=study_visit_vo.week_in_study,
            visit_name_sc=study_visit_vo.visit_name_sc,
            time_unit_object=study_visit_vo.time_unit_object,
            window_unit_object=study_visit_vo.window_unit_object,
            visit_window_min=study_visit_vo.visit_window_min,
            visit_window_max=study_visit_vo.visit_window_max,
            window_unit_uid=study_visit_vo.window_unit_uid,
            description=study_visit_vo.description,
            start_rule=study_visit_vo.start_rule,
            end_rule=study_visit_vo.end_rule,
            visit_contact_mode=study_visit_vo.visit_contact_mode,
            epoch_allocation=study_visit_vo.epoch_allocation,
            visit_type=study_visit_vo.visit_type,
            status=study_visit_vo.status,
            start_date=study_visit_vo.start_date,
            author=study_visit_vo.author,
            day_unit_object=study_visit_vo.day_unit_object,
            week_unit_object=study_visit_vo.week_unit_object,
            epoch_connector=study_visit_vo.epoch_connector,
            visit_class=study_visit_vo.visit_class,
            visit_subclass=study_visit_vo.visit_subclass,
            is_global_anchor_visit=study_visit_vo.is_global_anchor_visit,
            is_soa_milestone=study_visit_vo.is_soa_milestone,
            visit_order=study_visit_vo.visit_number,
            vis_unique_number=study_visit_vo.vis_unique_number,
            vis_short_name=study_visit_vo.vis_short_name,
            # History VO params
            change_type=study_visit_ogm_input.change_type,
            end_date=study_visit_ogm_input.end_date,
        )

    def find_all_visits_by_study_uid(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[StudyVisitOGM]:
        if study_value_version:
            filters = {
                "has_study_visit__has_version|version": study_value_version,
                "study_epoch_has_study_visit__study_value__has_version|version": study_value_version,
                "has_study_visit__has_version__uid": study_uid,
                "study_epoch_has_study_visit__study_value__has_version__uid": study_uid,
            }
        else:
            filters = {
                "has_study_visit__latest_value__uid": study_uid,
                "study_epoch_has_study_visit__study_value__latest_value__uid": study_uid,
            }

        return [
            StudyVisitOGM.from_orm(sas_node)
            for sas_node in to_relation_trees(
                StudyVisit.nodes.fetch_relations(
                    "study_epoch_has_study_visit__has_epoch",
                    "has_visit_type",
                    "has_visit_contact_mode",
                    "has_visit_name__has_latest_value",
                    "has_after__audit_trail",
                    "study_epoch_has_study_visit__study_value",
                )
                .fetch_optional_relations(
                    "has_repeating_frequency",
                    "has_window_unit__has_latest_value",
                    "has_timepoint__has_latest_value__has_unit_definition__has_latest_value",
                    "has_timepoint__has_latest_value__has_time_reference",
                    "has_timepoint__has_latest_value__has_value__has_latest_value",
                    "has_study_day__has_latest_value",
                    "has_study_duration_days__has_latest_value",
                    "has_study_week__has_latest_value",
                    "has_study_duration_weeks__has_latest_value",
                    "has_week_in_study__has_latest_value",
                    "has_epoch_allocation",
                )
                .filter(**filters)
                .order_by("unique_visit_number")
            ).distinct()
        ]

    def find_all_visits_referencing_study_visit(
        self, study_visit_uid: str
    ) -> list[StudyVisit]:
        return (
            StudyVisit.nodes.filter(
                visit_sublabel_reference=study_visit_uid,
            )
            .order_by("unique_visit_number")
            .has(has_before=False, has_study_visit=True)
            .all()
        )

    def find_by_uid(
        self, study_uid: str, uid: str, study_value_version: str | None = None
    ) -> StudyVisitVO:
        if study_value_version:
            filters = {
                "uid": uid,
                "has_study_visit__has_version|version": study_value_version,
                "study_epoch_has_study_visit__study_value__has_version|version": study_value_version,
                "has_study_visit__has_version__uid": study_uid,
                "study_epoch_has_study_visit__study_value__has_version__uid": study_uid,
            }
        else:
            filters = {
                "uid": uid,
                "has_study_visit__latest_value__uid": study_uid,
                "study_epoch_has_study_visit__study_value__latest_value__uid": study_uid,
            }

        visit_node = to_relation_trees(
            StudyVisit.nodes.fetch_relations(
                "study_epoch_has_study_visit__has_epoch",
                "study_epoch_has_study_visit__study_value",
                "has_visit_type",
                "has_visit_contact_mode",
                "has_visit_name__has_latest_value",
                "has_after__audit_trail",
            )
            .fetch_optional_relations(
                "has_repeating_frequency",
                "has_window_unit__has_latest_value",
                "has_timepoint__has_latest_value__has_unit_definition__has_latest_value",
                "has_timepoint__has_latest_value__has_time_reference",
                "has_timepoint__has_latest_value__has_value__has_latest_value",
                "has_study_day__has_latest_value",
                "has_study_duration_days__has_latest_value",
                "has_study_week__has_latest_value",
                "has_study_duration_weeks__has_latest_value",
                "has_week_in_study__has_latest_value",
                "has_epoch_allocation",
            )
            .filter(**filters)
        )
        unique_visits = []
        for ith_visit_node in visit_node:
            if ith_visit_node not in unique_visits:
                unique_visits.extend([ith_visit_node])
        if len(unique_visits) > 1:
            raise exceptions.ValidationException(
                f"Found more than one StudyVisit node with uid='{uid}'."
            )
        if len(unique_visits) == 0:
            raise exceptions.ValidationException(
                f"The study visit with uid='{uid}' could not be found."
            )
        return self.from_neomodel_to_vo(
            study_visit_ogm_input=StudyVisitOGM.from_orm(unique_visits[0]),
            study_value_version=study_value_version,
        )

    def get_all_versions(self, uid: str, study_uid: str):
        return sorted(
            [
                self._from_neomodel_to_history_vo(
                    study_visit_ogm_input=StudyVisitOGMVer.from_orm(se_node)
                )
                for se_node in to_relation_trees(
                    StudyVisit.nodes.fetch_relations(
                        "study_epoch_has_study_visit__has_epoch",
                        "has_visit_type",
                        "has_visit_contact_mode",
                        "has_visit_name__has_latest_value",
                        "has_after__audit_trail",
                        "study_epoch_has_study_visit__study_value",
                    )
                    .fetch_optional_relations(
                        "has_window_unit__has_latest_value",
                        "has_timepoint__has_latest_value__has_unit_definition__has_latest_value",
                        "has_timepoint__has_latest_value__has_time_reference",
                        "has_timepoint__has_latest_value__has_value__has_latest_value",
                        "has_study_day__has_latest_value",
                        "has_study_duration_days__has_latest_value",
                        "has_study_week__has_latest_value",
                        "has_study_duration_weeks__has_latest_value",
                        "has_week_in_study__has_latest_value",
                        "has_epoch_allocation",
                        "has_before",
                    )
                    .filter(uid=uid, has_after__audit_trail__uid=study_uid)
                ).distinct()
            ],
            key=lambda item: item.start_date,
            reverse=True,
        )

    def get_all_visit_versions(self, study_uid: str):
        version_nodes = [
            self._from_neomodel_to_history_vo(
                study_visit_ogm_input=StudyVisitOGMVer.from_orm(se_node)
            )
            for se_node in to_relation_trees(
                StudyVisit.nodes.fetch_relations(
                    "study_epoch_has_study_visit__has_epoch",
                    "has_visit_type",
                    "has_visit_contact_mode",
                    "has_visit_name__has_latest_value",
                    "has_after__audit_trail",
                    "study_epoch_has_study_visit__study_value",
                )
                .fetch_optional_relations(
                    "has_repeating_frequency",
                    "has_window_unit__has_latest_value",
                    "has_timepoint__has_latest_value__has_unit_definition__has_latest_value",
                    "has_timepoint__has_latest_value__has_time_reference",
                    "has_timepoint__has_latest_value__has_value__has_latest_value",
                    "has_study_day__has_latest_value",
                    "has_study_duration_days__has_latest_value",
                    "has_study_week__has_latest_value",
                    "has_study_duration_weeks__has_latest_value",
                    "has_week_in_study__has_latest_value",
                    "has_epoch_allocation",
                    "has_before",
                )
                .filter(has_after__audit_trail__uid=study_uid)
            ).distinct()
        ]
        return version_nodes

    def manage_versioning_create(
        self, study_root: StudyRoot, study_visit: StudyVisitVO, new_item: StudyVisit
    ):
        action = Create(
            date=datetime.datetime.now(datetime.timezone.utc),
            status=study_visit.status.value,
            user_initials=study_visit.author,
        )
        action.save()
        action.has_after.connect(new_item)
        study_root.audit_trail.connect(action)

    def manage_versioning_update(
        self,
        study_root: StudyRoot,
        study_visit: StudyVisitVO,
        previous_item: StudyVisit,
        new_item: StudyVisit,
    ):
        action = Edit(
            date=datetime.datetime.now(datetime.timezone.utc),
            status=study_visit.status.value,
            user_initials=study_visit.author,
        )
        action.save()
        action.has_before.connect(previous_item)
        action.has_after.connect(new_item)
        study_root.audit_trail.connect(action)

    def manage_versioning_delete(
        self,
        study_root: StudyRoot,
        study_visit: StudyVisitVO,
        previous_item: StudyVisit,
        new_item: StudyVisit,
    ):
        action = Delete(
            date=datetime.datetime.now(datetime.timezone.utc),
            status=study_visit.status.value,
            user_initials=study_visit.author,
        )
        action.save()
        action.has_before.connect(previous_item)
        action.has_after.connect(new_item)
        study_root.audit_trail.connect(action)

    def _update(self, study_visit: StudyVisitVO, create: bool = False):
        study_root: StudyRoot = StudyRoot.nodes.get(uid=study_visit.study_uid)
        study_value: StudyValue = study_root.latest_value.get_or_none()
        if study_value is None:
            raise exceptions.ValidationException("Study does not have draft version")
        if not create:
            previous_item = study_value.has_study_visit.get(uid=study_visit.uid)

        new_visit = StudyVisit(
            uid=study_visit.uid,
            visit_number=study_visit.visit_number,
            visit_sublabel=study_visit.visit_sublabel,
            visit_sublabel_uid=study_visit.visit_sublabel_uid,
            visit_sublabel_reference=study_visit.visit_sublabel_reference,
            short_visit_label=study_visit.visit_short_name,
            unique_visit_number=study_visit.unique_visit_number,
            consecutive_visit_group=study_visit.consecutive_visit_group,
            show_visit=study_visit.show_visit,
            visit_window_min=study_visit.visit_window_min,
            visit_window_max=study_visit.visit_window_max,
            description=study_visit.description,
            start_rule=study_visit.start_rule,
            end_rule=study_visit.end_rule,
            status=study_visit.status.name,
            visit_class=study_visit.visit_class.name,
            visit_subclass=study_visit.visit_subclass.name
            if study_visit.visit_subclass
            else None,
            is_global_anchor_visit=study_visit.is_global_anchor_visit,
            is_soa_milestone=study_visit.is_soa_milestone,
        )
        if study_visit.uid:
            new_visit.uid = study_visit.uid
        new_visit.save()
        if study_visit.uid is None:
            study_visit.uid = new_visit.uid

        visit_type = CTTermRoot.nodes.get(uid=study_visit.visit_type.name)
        new_visit.has_visit_type.connect(visit_type)

        if study_visit.repeating_frequency:
            visit_repeating_frequency = CTTermRoot.nodes.get(
                uid=study_visit.repeating_frequency.name
            )
            new_visit.has_repeating_frequency.connect(visit_repeating_frequency)

        if study_visit.timepoint:
            visit_timepoint = TimePointRoot.nodes.get(uid=study_visit.timepoint.uid)
            new_visit.has_timepoint.connect(visit_timepoint)
        if study_visit.study_day:
            study_day_numeric_value = StudyDayRoot.nodes.get(
                uid=study_visit.study_day.uid
            )
            new_visit.has_study_day.connect(study_day_numeric_value)
        if study_visit.study_duration_days:
            study_duration_days = StudyDurationDaysRoot.nodes.get(
                uid=study_visit.study_duration_days.uid
            )
            new_visit.has_study_duration_days.connect(study_duration_days)
        if study_visit.study_week:
            study_week_numeric_value = StudyWeekRoot.nodes.get(
                uid=study_visit.study_week.uid
            )
            new_visit.has_study_week.connect(study_week_numeric_value)
        if study_visit.study_duration_weeks:
            study_duration_weeks = StudyDurationWeeksRoot.nodes.get(
                uid=study_visit.study_duration_weeks.uid
            )
            new_visit.has_study_duration_weeks.connect(study_duration_weeks)
        if study_visit.week_in_study:
            week_in_study = WeekInStudyRoot.nodes.get(uid=study_visit.week_in_study.uid)
            new_visit.has_week_in_study.connect(week_in_study)

        visit_name_text_value = VisitNameRoot.nodes.get(
            uid=study_visit.visit_name_sc.uid
        )
        new_visit.has_visit_name.connect(visit_name_text_value)

        if study_visit.window_unit_uid is not None:
            window_unit = UnitDefinitionRoot.nodes.get(uid=study_visit.window_unit_uid)
            new_visit.has_window_unit.connect(window_unit)
        else:
            window_unit = None
        visit_contact_mode = CTTermRoot.nodes.get(
            uid=study_visit.visit_contact_mode.name
        )
        new_visit.has_visit_contact_mode.connect(visit_contact_mode)
        if study_visit.epoch_allocation:
            epoch_allocation = CTTermRoot.nodes.get(
                uid=study_visit.epoch_allocation.name
            )
            new_visit.has_epoch_allocation.connect(epoch_allocation)

        study_epoch = (
            StudyEpoch.nodes.has(has_after=True)
            .has(has_before=False)
            .get(uid=study_visit.epoch_uid)
        )
        new_visit.study_epoch_has_study_visit.connect(study_epoch)
        if not create:
            if study_visit.is_deleted:
                self.manage_versioning_delete(
                    study_root=study_root,
                    study_visit=study_visit,
                    previous_item=previous_item,
                    new_item=new_visit,
                )
            else:
                new_visit.has_study_visit.connect(study_value)
                self.manage_versioning_update(
                    study_root=study_root,
                    study_visit=study_visit,
                    previous_item=previous_item,
                    new_item=new_visit,
                )
            exclude_study_selection_relationships = [
                StudyEpoch,
            ]
            manage_previous_connected_study_selection_relationships(
                previous_item=previous_item,
                study_value_node=study_value,
                new_item=new_visit,
                exclude_study_selection_relationships=exclude_study_selection_relationships,
            )
        else:
            new_visit.has_study_visit.connect(study_value)
            self.manage_versioning_create(
                study_root=study_root, study_visit=study_visit, new_item=new_visit
            )

        return study_visit
