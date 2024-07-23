import datetime
from dataclasses import dataclass

from neomodel import db

from clinical_mdr_api.domain_repositories.generic_repository import (
    manage_previous_connected_study_selection_relationships,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    convert_to_datetime,
    to_relation_trees,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.study import StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import StudyAction
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyActivity,
    StudySelection,
    StudySoAGroup,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_base_repository import (
    StudySelectionActivityBaseRepository,
)
from clinical_mdr_api.domains.study_selections.study_soa_group_selection import (
    StudySoAGroupAR,
    StudySoAGroupVO,
)


@dataclass
class SelectionHistory:
    """Class for selection history items"""

    study_selection_uid: str
    soa_group_term_uid: str
    show_soa_group_in_protocol_flowchart: bool
    user_initials: str | None
    change_type: str
    start_date: datetime.datetime
    end_date: datetime.datetime | None


class StudySoAGroupRepository(StudySelectionActivityBaseRepository[StudySoAGroupAR]):
    _aggregate_root_type = StudySoAGroupAR

    def is_repository_based_on_ordered_selection(self):
        return False

    def _create_value_object_from_repository(
        self, selection: dict, acv: bool
    ) -> StudySoAGroupVO:
        return StudySoAGroupVO.from_input_values(
            study_selection_uid=selection["study_selection_uid"],
            soa_group_term_uid=selection["soa_group_term_uid"],
            show_soa_group_in_protocol_flowchart=selection[
                "show_soa_group_in_protocol_flowchart"
            ],
            study_uid=selection["study_uid"],
            start_date=convert_to_datetime(value=selection["start_date"]),
            user_initials=selection["user_initials"],
            accepted_version=acv,
        )

    def _versioning_query(self) -> str:
        return ""

    def _additional_match(self) -> str:
        return """
            WITH sr, sv
            MATCH (sv)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->
                (sa:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->(elr:CTTermRoot)<-[:HAS_TERM]-(:CTCodelistRoot)
                -[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[:LATEST_FINAL]->(:CTCodelistNameValue {name: "Flowchart Group"})
        """

    def _filter_clause(self, query_parameters: dict, **kwargs) -> str:
        return ""

    def _order_by_query(self):
        return """
            WITH DISTINCT *
            ORDER BY study_activity.order ASC
            MATCH (sa)<-[:AFTER]-(sac:StudyAction)
        """

    def _return_clause(self) -> str:
        return """RETURN DISTINCT
                sr.uid AS study_uid,
                sa.uid AS study_selection_uid,
                sa.show_soa_group_in_protocol_flowchart AS show_soa_group_in_protocol_flowchart,
                elr.uid AS soa_group_term_uid,
                sa.accepted_version AS accepted_version,
                sac.date AS start_date,
                sac.user_initials AS user_initials"""

    def get_selection_history(
        self, selection: dict, change_type: str, end_date: datetime
    ):
        return SelectionHistory(
            study_selection_uid=selection["study_selection_uid"],
            user_initials=selection["user_initials"],
            soa_group_term_uid=selection["soa_group_term_uid"],
            show_soa_group_in_protocol_flowchart=selection[
                "show_soa_group_in_protocol_flowchart"
            ],
            change_type=change_type,
            start_date=convert_to_datetime(value=selection["start_date"]),
            end_date=end_date,
        )

    def get_audit_trail_query(self, study_selection_uid: str):
        if study_selection_uid:
            audit_trail_cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(sa:StudySoAGroup {uid: $study_selection_uid})
                <-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]-(study_activity:StudyActivity)
            WITH sa, study_activity
            MATCH (sa)-[:AFTER|BEFORE*0..]-(all_sa:StudySoAGroup)
            WITH distinct(all_sa), study_activity
            """
        else:
            audit_trail_cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudySoAGroup)-[:BEFORE|AFTER]->(all_sa:StudySoAGroup)
                <-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]-(study_activity:StudyActivity)
            WITH DISTINCT all_sa, study_activity
            """
        audit_trail_cypher += """

                    WITH DISTINCT all_sa, study_activity
                    OPTIONAL MATCH (all_sa)-[:HAS_FLOWCHART_GROUP]->(fgr:CTTermRoot)
                    WITH DISTINCT all_sa, fgr, study_activity
                    ORDER BY study_activity.order ASC
                    MATCH (all_sa)<-[:AFTER]-(asa:StudyAction)
                    OPTIONAL MATCH (all_sa)<-[:BEFORE]-(bsa:StudyAction)
                    WITH all_sa, asa, bsa, fgr
                    ORDER BY all_sa.uid, asa.date DESC
                    RETURN
                        all_sa.uid AS study_selection_uid,
                        all_sa.show_soa_group_in_protocol_flowchart AS show_soa_group_in_protocol_flowchart,
                        fgr.uid AS soa_group_term_uid,
                        asa.date AS start_date,
                        asa.user_initials AS user_initials,
                        labels(asa) AS change_type,
                        bsa.date AS end_date
                    """
        return audit_trail_cypher

    def get_study_selection_node_from_latest_study_value(
        self, study_value: StudyValue, study_selection: StudySelection
    ):
        return StudySoAGroup.nodes.has(has_before=False).get(
            uid=study_selection.study_selection_uid
        )

    def _add_new_selection(
        self,
        latest_study_value_node: StudyValue,
        order: int,
        selection: StudySoAGroupVO,
        audit_node: StudyAction,
        last_study_selection_node: StudySoAGroup,
        for_deletion: bool = False,
    ):
        # Create new activity selection
        study_soa_group_node = StudySoAGroup(
            show_soa_group_in_protocol_flowchart=selection.show_soa_group_in_protocol_flowchart
        )
        study_soa_group_node.uid = selection.study_selection_uid
        study_soa_group_node.accepted_version = selection.accepted_version
        study_soa_group_node.save()

        # Connect new node with audit trail
        audit_node.study_selection_metadata_has_after.connect(study_soa_group_node)
        # Set flowchart group
        ct_term_root = CTTermRoot.nodes.get(uid=selection.soa_group_term_uid)
        study_soa_group_node.has_flowchart_group.connect(ct_term_root)
        if last_study_selection_node:
            manage_previous_connected_study_selection_relationships(
                previous_item=last_study_selection_node,
                study_value_node=latest_study_value_node,
                new_item=study_soa_group_node,
                exclude_study_selection_relationships=[StudyActivity],
            )

    def generate_uid(self) -> str:
        return StudySoAGroup.get_next_free_uid_and_increment_counter()

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass

    def get_all_study_soa_groups_for_study_activity(
        self, study_uid: str, study_activity_uid
    ) -> list[StudySoAGroup]:
        query = """
            MATCH (study_soa_group:StudySoAGroup)<-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]-(study_activity:StudyActivity)
                <-[:HAS_STUDY_ACTIVITY]-(study_value:StudyValue)<-[:LATEST]-(study_root:StudyRoot)
            WITH study_root, study_soa_group, collect(study_activity.uid) as all_sa_using_soa_group
            WHERE NOT (study_soa_group)<-[:BEFORE]-() 
                AND study_root.uid=$study_uid 
                AND all_sa_using_soa_group=[$study_activity_uid]
            RETURN study_soa_group
        """
        study_soa_groups, _ = db.cypher_query(
            query,
            params={"study_uid": study_uid, "study_activity_uid": study_activity_uid},
            resolve_objects=True,
        )
        if len(study_soa_groups) > 0:
            return study_soa_groups[0]
        return []

    def find_study_soa_group_in_a_study(
        self, study_uid: str, soa_group_term_uid: str
    ) -> StudySoAGroup | None:
        study_soa_groups = to_relation_trees(
            StudySoAGroup.nodes.filter(
                has_soa_group_selection__has_study_activity__latest_value__uid=study_uid,
                has_flowchart_group__uid=soa_group_term_uid,
            ).has(has_before=False)
        ).distinct()
        return study_soa_groups[0] if len(study_soa_groups) > 0 else None
