import datetime
from dataclasses import dataclass

from neomodel import db

from clinical_mdr_api.domain_repositories._utils.helpers import unpack_list_of_lists
from clinical_mdr_api.domain_repositories.generic_repository import (
    manage_previous_connected_study_selection_relationships,
)
from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityRoot,
    ActivityValue,
)
from clinical_mdr_api.domain_repositories.models.study import StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import StudyAction
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyActivity,
    StudyActivityGroup,
    StudyActivitySubGroup,
    StudySelection,
    StudySoAGroup,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_base_repository import (
    StudySelectionActivityBaseRepository,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity import (
    StudySelectionActivityAR,
    StudySelectionActivityVO,
)


@dataclass
class SelectionHistory:
    """Class for selection history items"""

    study_selection_uid: str
    study_activity_subgroup_uid: str
    activity_subgroup_uid: str
    study_activity_group_uid: str
    activity_group_uid: str
    activity_uid: str
    soa_group_term_uid: str
    study_soa_group_uid: str
    user_initials: str
    change_type: str
    start_date: datetime.datetime
    show_activity_group_in_protocol_flowchart: bool | None
    show_activity_subgroup_in_protocol_flowchart: bool | None
    show_activity_in_protocol_flowchart: bool | None
    show_soa_group_in_protocol_flowchart: bool | None
    activity_order: int | None
    end_date: datetime.datetime | None
    activity_version: str | None


class StudySelectionActivityRepository(
    StudySelectionActivityBaseRepository[StudySelectionActivityAR]
):
    _aggregate_root_type = StudySelectionActivityAR

    def _create_value_object_from_repository(
        self, selection: dict, acv: bool
    ) -> StudySelectionActivityVO:
        return StudySelectionActivityVO.from_input_values(
            study_selection_uid=selection["study_selection_uid"],
            study_activity_subgroup_uid=selection.get(
                "study_activity_subgroup", {}
            ).get("selection_uid")
            if selection.get("study_activity_subgroup")
            else None,
            activity_subgroup_uid=selection.get("study_activity_subgroup", {}).get(
                "activity_subgroup_uid"
            )
            if selection.get("study_activity_subgroup")
            else None,
            activity_subgroup_name=selection.get("study_activity_subgroup", {}).get(
                "activity_subgroup_name"
            )
            if selection.get("study_activity_subgroup")
            else None,
            study_activity_group_uid=selection.get("study_activity_group", {}).get(
                "selection_uid"
            )
            if selection.get("study_activity_group")
            else None,
            activity_group_uid=selection.get("study_activity_group", {}).get(
                "activity_group_uid"
            )
            if selection.get("study_activity_group")
            else None,
            activity_group_name=selection.get("study_activity_group", {}).get(
                "activity_group_name"
            )
            if selection.get("study_activity_group")
            else None,
            study_uid=selection["study_uid"],
            activity_uid=selection["activity_uid"],
            activity_name=selection["activity_name"],
            activity_version=selection["activity_version"],
            activity_library_name=selection["activity_library_name"],
            soa_group_term_uid=selection["soa_group_term_uid"],
            study_soa_group_uid=selection["study_soa_group_uid"],
            activity_order=selection["activity_order"],
            show_activity_in_protocol_flowchart=selection[
                "show_activity_in_protocol_flowchart"
            ],
            show_activity_group_in_protocol_flowchart=selection.get(
                "study_activity_group", {}
            ).get("show_activity_group_in_protocol_flowchart")
            if selection.get("study_activity_group")
            else None,
            show_activity_subgroup_in_protocol_flowchart=selection.get(
                "study_activity_subgroup", {}
            ).get("show_activity_subgroup_in_protocol_flowchart")
            if selection.get("study_activity_subgroup")
            else None,
            show_soa_group_in_protocol_flowchart=selection[
                "show_soa_group_in_protocol_flowchart"
            ],
            start_date=convert_to_datetime(value=selection["start_date"]),
            user_initials=selection["user_initials"],
            accepted_version=acv,
        )

    def _additional_match(self) -> str:
        return """
            WITH sr, sv
            MATCH (sv)-[:HAS_STUDY_ACTIVITY]->(sa:StudyActivity)-[:HAS_SELECTED_ACTIVITY]->(av:ActivityValue)<-[ver:HAS_VERSION]-(ar:ActivityRoot)
            MATCH (sa)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(soa_group:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->(elr:CTTermRoot)<-[:HAS_TERM]-(:CTCodelistRoot)
            -[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[:LATEST_FINAL]->(:CTCodelistNameValue {name: "Flowchart Group"})
            MATCH (ar)<-[:CONTAINS_CONCEPT]-(lib:Library)
        """

    def _filter_clause(self, query_parameters: dict, **kwargs) -> str:
        # Filter on Activity, ActivityGroup or ActivityGroupNames if provided as a specific filter
        # This improves performance vs full service level filter
        activity_names = kwargs.get("activity_names")
        activity_group_names = kwargs.get("activity_group_names")
        activity_subgroup_names = kwargs.get("activity_subgroup_names")
        filter_query = ""
        if (
            activity_names is not None
            or activity_group_names is not None
            or activity_subgroup_names is not None
        ):
            filter_query += " WHERE "
            filter_list = []
            if activity_names is not None:
                filter_list.append("av.name IN $activity_names")
                query_parameters["activity_names"] = activity_names
            if activity_subgroup_names is not None:
                filter_list.append(
                    "size([(sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(sas:StudyActivitySubGroup)-"
                    "[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)"
                    "WHERE activity_subgroup_value.name IN $activity_subgroup_names | activity_subgroup_value.name]) > 0"
                )
                query_parameters["activity_subgroup_names"] = activity_subgroup_names
            if activity_group_names is not None:
                filter_list.append(
                    "size([(sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(sas:StudyActivityGroup)-"
                    "[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue)"
                    "WHERE activity_group_value.name IN $activity_group_names | activity_group_value.name]) > 0"
                )
                query_parameters["activity_group_names"] = activity_group_names

            filter_query += " AND ".join(filter_list)
        return filter_query

    def _return_clause(self) -> str:
        return """RETURN DISTINCT
                sr.uid AS study_uid,
                sa.order AS activity_order,
                sa.uid AS study_selection_uid,
                head([(sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_selection)
                -[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)<-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot) | 
                    {
                        selection_uid: study_activity_subgroup_selection.uid, 
                        activity_subgroup_uid:activity_subgroup_root.uid,
                        activity_subgroup_name:activity_subgroup_value.name,
                        show_activity_subgroup_in_protocol_flowchart:study_activity_subgroup_selection.show_activity_subgroup_in_protocol_flowchart
                    }]) AS study_activity_subgroup,
                head([(sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group_selection)
                    -[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot) | 
                    {
                        selection_uid: study_activity_group_selection.uid, 
                        activity_group_uid: activity_group_root.uid,
                        activity_group_name:activity_group_value.name,
                        show_activity_group_in_protocol_flowchart: study_activity_group_selection.show_activity_group_in_protocol_flowchart
                    }]) AS study_activity_group,
                sa.show_activity_in_protocol_flowchart AS show_activity_in_protocol_flowchart,
                coalesce(soa_group.show_soa_group_in_protocol_flowchart, false) AS show_soa_group_in_protocol_flowchart,
                elr.uid AS soa_group_term_uid,
                soa_group.uid AS study_soa_group_uid,
                sa.accepted_version AS accepted_version,
                ar.uid AS activity_uid,
                av.name AS activity_name,
                sac.date AS start_date,
                sac.user_initials AS user_initials,
                hv_ver.version AS activity_version,
                lib.name as activity_library_name"""

    def get_selection_history(
        self, selection: dict, change_type: str, end_date: datetime
    ):
        return SelectionHistory(
            study_selection_uid=selection["study_selection_uid"],
            study_activity_subgroup_uid=selection.get(
                "study_activity_subgroup", {}
            ).get("selection_uid")
            if selection.get("study_activity_subgroup")
            else None,
            activity_subgroup_uid=selection.get("study_activity_subgroup", {}).get(
                "activity_subgroup_uid"
            )
            if selection.get("study_activity_subgroup")
            else None,
            study_activity_group_uid=selection.get("study_activity_group", {}).get(
                "selection_uid"
            )
            if selection.get("study_activity_group")
            else None,
            activity_group_uid=selection.get("study_activity_group", {}).get(
                "activity_group_uid"
            )
            if selection.get("study_activity_group")
            else None,
            activity_uid=selection["activity_uid"],
            activity_order=selection["activity_order"],
            activity_version=selection["activity_version"],
            soa_group_term_uid=selection["soa_group_term_uid"],
            study_soa_group_uid=selection["study_soa_group_uid"],
            user_initials=selection["user_initials"],
            change_type=change_type,
            start_date=convert_to_datetime(value=selection["start_date"]),
            show_activity_in_protocol_flowchart=selection[
                "show_activity_in_protocol_flowchart"
            ],
            show_activity_group_in_protocol_flowchart=selection.get(
                "study_activity_group", {}
            ).get("show_activity_group_in_protocol_flowchart")
            if selection.get("study_activity_group")
            else None,
            show_activity_subgroup_in_protocol_flowchart=selection.get(
                "study_activity_subgroup", {}
            ).get("show_activity_subgroup_in_protocol_flowchart")
            if selection.get("study_activity_subgroup")
            else None,
            show_soa_group_in_protocol_flowchart=selection[
                "show_soa_group_in_protocol_flowchart"
            ],
            end_date=end_date,
        )

    def get_audit_trail_query(self, study_selection_uid: str):
        if study_selection_uid:
            audit_trail_cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(sa:StudyActivity { uid: $study_selection_uid})
            WITH sa
            MATCH (sa)-[:AFTER|BEFORE*0..]-(all_sa:StudyActivity)
            WITH distinct(all_sa)
            """
        else:
            audit_trail_cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sa:StudyActivity)
            WITH DISTINCT all_sa
            """
        audit_trail_cypher += """
                    MATCH (all_sa)-[:HAS_SELECTED_ACTIVITY]->(av:ActivityValue)

                    CALL {
                      WITH av
                      MATCH (av) <-[ver]-(ar:ActivityRoot)
                      WHERE ver.status = "Final"
                      RETURN ver as ver, ar as ar
                      ORDER BY ver.start_date DESC
                      LIMIT 1
                    }

                    WITH DISTINCT all_sa, ar, ver
                    OPTIONAL MATCH (all_sa)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(soa_group:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->(fgr:CTTermRoot)
                    WITH DISTINCT all_sa, ar, ver, fgr, soa_group
                    ORDER BY all_sa.order ASC
                    MATCH (all_sa)<-[:AFTER]-(asa:StudyAction)
                    OPTIONAL MATCH (all_sa)<-[:BEFORE]-(bsa:StudyAction)
                    WITH all_sa, ar, asa, bsa, ver, fgr, soa_group
                    ORDER BY all_sa.uid, asa.date DESC
                    RETURN
                        all_sa.order AS activity_order,
                        all_sa.uid AS study_selection_uid,
                        head([(all_sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_selection)
                            -[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(:ActivitySubGroupValue)<-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot) | 
                            {
                                selection_uid: study_activity_subgroup_selection.uid, 
                                activity_subgroup_uid:activity_subgroup_root.uid,
                                show_activity_subgroup_in_protocol_flowchart:study_activity_subgroup_selection.show_activity_subgroup_in_protocol_flowchart
                            }]) AS study_activity_subgroup,
                        head([(all_sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group_selection)
                            -[:HAS_SELECTED_ACTIVITY_GROUP]->(:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot) | 
                            {
                                selection_uid: study_activity_group_selection.uid, 
                                activity_group_uid: activity_group_root.uid,
                                show_activity_group_in_protocol_flowchart:study_activity_group_selection.show_activity_group_in_protocol_flowchart
                            }]) AS study_activity_group,
                        all_sa.show_activity_in_protocol_flowchart AS show_activity_in_protocol_flowchart,
                        coalesce(soa_group.show_soa_group_in_protocol_flowchart, false) AS show_soa_group_in_protocol_flowchart,
                        ar.uid AS activity_uid,
                        fgr.uid AS soa_group_term_uid,
                        soa_group.uid AS study_soa_group_uid,
                        asa.date AS start_date,
                        asa.user_initials AS user_initials,
                        labels(asa) AS change_type,
                        bsa.date AS end_date,
                        ver.version AS activity_version
                    """
        return audit_trail_cypher

    def get_study_selection_node_from_latest_study_value(
        self, study_value: StudyValue, study_selection: StudySelection
    ):
        return study_value.has_study_activity.get(
            uid=study_selection.study_selection_uid
        )

    def _add_new_selection(
        self,
        latest_study_value_node: StudyValue,
        order: int,
        selection: StudySelectionActivityVO,
        audit_node: StudyAction,
        last_study_selection_node: StudyActivity,
        for_deletion: bool = False,
    ):
        # find the activity value
        activity_root_node: ActivityRoot = ActivityRoot.nodes.get(
            uid=selection.activity_uid
        )
        latest_activity_value_node: ActivityValue = (
            activity_root_node.get_value_for_version(selection.activity_version)
        )
        # Create new activity selection
        study_activity_selection_node = StudyActivity(
            order=order,
            show_activity_in_protocol_flowchart=selection.show_activity_in_protocol_flowchart,
        )
        study_activity_selection_node.uid = selection.study_selection_uid
        study_activity_selection_node.accepted_version = selection.accepted_version
        study_activity_selection_node.save()
        if not for_deletion:
            # Connect new node with study value
            latest_study_value_node.has_study_activity.connect(
                study_activity_selection_node
            )
        # Connect new node with audit trail
        audit_node.has_after.connect(study_activity_selection_node)
        # Connect new node with Activity value
        study_activity_selection_node.has_selected_activity.connect(
            latest_activity_value_node
        )
        # Connect StudyActivity with StudySoAGroup node
        study_soa_group_node = StudySoAGroup.nodes.has(has_before=False).get(
            uid=selection.study_soa_group_uid
        )
        study_activity_selection_node.has_soa_group_selection.connect(
            study_soa_group_node
        )

        if selection.study_activity_subgroup_uid:
            # Connect StudyActivity with StudyActivitySubGroup node
            study_activity_subgroup = StudyActivitySubGroup.nodes.has(
                has_before=False
            ).get(uid=selection.study_activity_subgroup_uid)
            study_activity_selection_node.study_activity_has_study_activity_subgroup.connect(
                study_activity_subgroup
            )

        if selection.study_activity_group_uid:
            # Connect StudyActivity with StudyActivityGroup node
            study_activity_group = StudyActivityGroup.nodes.has(has_before=False).get(
                uid=selection.study_activity_group_uid
            )
            study_activity_selection_node.study_activity_has_study_activity_group.connect(
                study_activity_group
            )
        if last_study_selection_node:
            manage_previous_connected_study_selection_relationships(
                previous_item=last_study_selection_node,
                study_value_node=latest_study_value_node,
                new_item=study_activity_selection_node,
                exclude_study_selection_relationships=[
                    StudySoAGroup,
                    StudyActivitySubGroup,
                    StudyActivityGroup,
                ],
            )

    def generate_uid(self) -> str:
        return StudyActivity.get_next_free_uid_and_increment_counter()

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass

    def get_all_study_activities_for_study_activity_subgroup(
        self, study_activity_subgroup_uid: str
    ) -> list[StudyActivity]:
        query = """
            MATCH (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup)
            WHERE NOT (study_activity)<-[:BEFORE]-() AND NOT (study_activity)<-[]-(:Delete)
                AND study_activity_subgroup.uid=$study_activity_subgroup_uid 
            RETURN study_activity
        """
        study_activities, _ = db.cypher_query(
            query,
            params={"study_activity_subgroup_uid": study_activity_subgroup_uid},
            resolve_objects=True,
        )
        if len(study_activities) > 0:
            return unpack_list_of_lists(study_activities)
        return []

    def get_all_study_activities_for_study_activity_group(
        self, study_activity_group_uid: str
    ) -> list[StudyActivity]:
        query = """
            MATCH (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup)
            WHERE NOT (study_activity)<-[:BEFORE]-() AND NOT (study_activity)<-[]-(:Delete)
                AND study_activity_group.uid=$study_activity_group_uid 
            RETURN study_activity
        """
        study_activities, _ = db.cypher_query(
            query,
            params={"study_activity_group_uid": study_activity_group_uid},
            resolve_objects=True,
        )
        if len(study_activities) > 0:
            return unpack_list_of_lists(study_activities)
        return []

    def get_all_study_activities_for_study_soa_group(
        self, study_soa_group_uid: str
    ) -> list[StudyActivity]:
        query = """
            MATCH (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)
            WHERE NOT (study_activity)<-[:BEFORE]-() AND NOT (study_activity)<-[]-(:Delete)
                AND study_soa_group.uid=$study_soa_group_uid 
            RETURN study_activity
        """
        study_activities, _ = db.cypher_query(
            query,
            params={"study_soa_group_uid": study_soa_group_uid},
            resolve_objects=True,
        )
        if len(study_activities) > 0:
            return unpack_list_of_lists(study_activities)
        return []
