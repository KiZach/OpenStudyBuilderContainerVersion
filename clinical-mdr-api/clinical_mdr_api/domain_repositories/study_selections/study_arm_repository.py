import datetime
from dataclasses import dataclass

from neomodel import db

from clinical_mdr_api.domain_repositories._utils import helpers
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
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
    StudyAction,
)
from clinical_mdr_api.domain_repositories.models.study_selections import StudyArm
from clinical_mdr_api.domains.study_selections.study_selection_arm import (
    StudySelectionArmAR,
    StudySelectionArmVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import VersioningException


@dataclass
class SelectionHistoryArm:
    """Class for selection history items"""

    study_selection_uid: str
    study_uid: str | None
    arm_name: str
    arm_short_name: str
    arm_code: str | None
    arm_description: str | None
    arm_colour: str | None
    arm_randomization_group: str | None
    arm_number_of_subjects: int | None
    arm_type: str | None
    # Study selection Versioning
    start_date: datetime.datetime
    user_initials: str | None
    change_type: str
    end_date: datetime.datetime | None
    order: int
    status: str | None
    accepted_version: bool | None


class StudySelectionArmRepository:
    @staticmethod
    def _acquire_write_lock_study_value(uid: str) -> None:
        db.cypher_query(
            """
             MATCH (sr:StudyRoot {uid: $uid})
             REMOVE sr.__WRITE_LOCK__
             RETURN true
            """,
            {"uid": uid},
        )

    def arm_specific_has_connected_cell(self, study_uid: str, arm_uid: str) -> bool:
        """
        Returns True if StudyArm with specified uid has connected at least one StudyDesignCell.
        :return:
        """

        sdc_node = to_relation_trees(
            StudyArm.nodes.fetch_relations("has_design_cell", "has_after").filter(
                study_value__latest_value__uid=study_uid,
                uid=arm_uid,
                has_design_cell__study_value__latest_value__uid=study_uid,
            )
        )
        return len(sdc_node) > 0

    def arm_specific_has_connected_branch_arms(
        self, study_uid: str, arm_uid: str
    ) -> bool:
        """
        Returns True if StudyArm with specified uid has connected at least one StudyBranchArm.
        :return:
        """

        sdc_node = to_relation_trees(
            StudyArm.nodes.fetch_relations("has_branch_arm", "has_after").filter(
                study_value__latest_value__uid=study_uid, uid=arm_uid
            )
        )
        return len(sdc_node) > 0

    def _retrieves_all_data(
        self,
        study_uid: str | None = None,
        project_name: str | None = None,
        project_number: str | None = None,
        study_value_version: str | None = None,
    ) -> tuple[StudySelectionArmVO]:
        query = ""
        query_parameters = {}
        if study_value_version:
            if study_uid:
                query = "MATCH (sr:StudyRoot { uid: $uid})-[l:HAS_VERSION{status:'RELEASED', version:$study_value_version}]->(sv:StudyValue)"
                query_parameters["study_value_version"] = study_value_version
                query_parameters["uid"] = study_uid
            else:
                query = "MATCH (sr:StudyRoot)-[l:HAS_VERSION{status:'RELEASED', version:$study_value_version}]->(sv:StudyValue)"
                query_parameters["study_value_version"] = study_value_version
        else:
            if study_uid:
                query = "MATCH (sr:StudyRoot { uid: $uid})-[l:LATEST]->(sv:StudyValue)"
                query_parameters["uid"] = study_uid
            else:
                query = "MATCH (sr:StudyRoot)-[l:LATEST]->(sv:StudyValue)"

        if project_name is not None or project_number is not None:
            query += (
                "-[:HAS_PROJECT]->(:StudyProjectField)<-[:HAS_FIELD]-(proj:Project)"
            )
            filter_list = []
            if project_name is not None:
                filter_list.append("proj.name=$project_name")
                query_parameters["project_name"] = project_name
            if project_number is not None:
                filter_list.append("proj.project_number=$project_number")
                query_parameters["project_number"] = project_number
            query += " WHERE "
            query += " AND ".join(filter_list)

        query += """
            WITH sr, sv
            MATCH (sv)-[:HAS_STUDY_ARM]->(sar:StudyArm)
            WITH DISTINCT sr, sar 
            
            OPTIONAL MATCH (sar)-[:HAS_ARM_TYPE]->(elr:CTTermRoot)
            
            MATCH (sar)<-[:AFTER]-(sa:StudyAction)

            RETURN DISTINCT 
                sr.uid AS study_uid,
                sar.uid AS study_selection_uid,
                sar.name AS arm_name,
                sar.short_name AS arm_short_name,
                sar.arm_code AS arm_code,
                sar.description AS arm_description,
                sar.arm_colour AS arm_colour,
                sar.order AS order,
                sar.accepted_version AS accepted_version,
                sar.number_of_subjects AS number_of_subjects,
                sar.randomization_group AS randomization_group,
                elr.uid AS arm_type_uid,
                sar.text AS text,
                sa.date AS start_date,
                sa.user_initials AS user_initials
                ORDER BY order
            """

        all_arm_selections = db.cypher_query(query, query_parameters)
        all_selections = []

        for selection in helpers.db_result_to_list(all_arm_selections):
            acv = selection.get("accepted_version", False)
            if acv is None:
                acv = False
            selection_vo = StudySelectionArmVO.from_input_values(
                user_initials=selection["user_initials"],
                study_uid=selection["study_uid"],
                name=selection["arm_name"],
                short_name=selection["arm_short_name"],
                code=selection["arm_code"],
                description=selection["arm_description"],
                arm_colour=selection["arm_colour"],
                study_selection_uid=selection["study_selection_uid"],
                arm_type_uid=selection["arm_type_uid"],
                number_of_subjects=selection["number_of_subjects"],
                randomization_group=selection["randomization_group"],
                start_date=convert_to_datetime(value=selection["start_date"]),
                accepted_version=selection["accepted_version"],
            )
            all_selections.append(selection_vo)
        return tuple(all_selections)

    def find_all(
        self,
        project_name: str | None = None,
        project_number: str | None = None,
    ) -> list[StudySelectionArmAR]:
        """
        Finds all the selected study endpoints for all studies, and create the aggregate
        :return: List of StudySelectionArmAR, potentially empty
        """
        all_selections = self._retrieves_all_data(
            project_name=project_name,
            project_number=project_number,
        )
        # Create a dictionary, with study_uid as key, and list of selections as value
        selection_aggregate_dict = {}
        selection_aggregates = []
        for selection in all_selections:
            if selection.study_uid in selection_aggregate_dict:
                selection_aggregate_dict[selection.study_uid].append(selection)
            else:
                selection_aggregate_dict[selection.study_uid] = [selection]
        # Then, create the list of VO from the dictionary
        for study_uid, selections in selection_aggregate_dict.items():
            selection_aggregates.append(
                StudySelectionArmAR.from_repository_values(
                    study_uid=study_uid, study_arms_selection=selections
                )
            )
        return selection_aggregates

    def find_by_study(
        self,
        study_uid: str,
        for_update: bool = False,
        study_value_version: str | None = None,
    ) -> StudySelectionArmAR | None:
        """
        Finds all the selected study arms for a given study
        :param study_uid:
        :param for_update:
        :return:
        """
        if for_update:
            self._acquire_write_lock_study_value(study_uid)
        all_selections = self._retrieves_all_data(
            study_uid, study_value_version=study_value_version
        )
        selection_aggregate = StudySelectionArmAR.from_repository_values(
            study_uid=study_uid, study_arms_selection=all_selections
        )
        if for_update:
            selection_aggregate.repository_closure_data = all_selections
        return selection_aggregate

    def _get_audit_node(
        self, study_selection: StudySelectionArmAR, study_selection_uid: str
    ):
        all_current_ids = []
        for item in study_selection.study_arms_selection:
            all_current_ids.append(item.study_selection_uid)
        all_closure_ids = []
        for item in study_selection.repository_closure_data:
            all_closure_ids.append(item.study_selection_uid)
        # if uid is in current data
        if study_selection_uid in all_current_ids:
            # if uid is in closure data
            if study_selection_uid in all_closure_ids:
                return Edit()
            return Create()
        return Delete()

    def save(self, study_selection: StudySelectionArmAR, author: str) -> None:
        """
        Persist the set of selected study amrs from the aggregate to the database
        :param study_selection:
        :param author:
        """
        assert study_selection.repository_closure_data is not None

        # get the closure_data
        closure_data = study_selection.repository_closure_data
        closure_data_length = len(closure_data)

        # getting the latest study value node
        study_root_node = StudyRoot.nodes.get(uid=study_selection.study_uid)
        latest_study_value_node = study_root_node.latest_value.single()

        if study_root_node.latest_locked.get_or_none() == latest_study_value_node:
            raise VersioningException(
                "You cannot add or reorder a study selection when the study is in a locked state."
            )

        selections_to_remove = []
        selections_to_add = []

        # check if object is removed from the selection list - delete have been called
        if len(closure_data) > len(study_selection.study_arms_selection):
            # remove the last item from old list, as there will no longer be any study objective with that high order
            selections_to_remove.append((len(closure_data), closure_data[-1]))

        # loop through new data - start=1 as order starts at 1 not at 0 and find what needs to be removed and added
        for order, selection in enumerate(
            study_selection.study_arms_selection, start=1
        ):
            # check whether something new is added
            if closure_data_length > order - 1:
                # check if anything has changed
                if selection is not closure_data[order - 1]:
                    # update the selection by removing the old if the old exists, and adding new selection
                    selections_to_remove.append((order, closure_data[order - 1]))
                    selections_to_add.append((order, selection))
            else:
                # else something new have been added
                selections_to_add.append((order, selection))

        # audit trail nodes dictionary, holds the new nodes created for the audit trail
        audit_trail_nodes = {}
        # dictonary of last nodes to traverse to their old connections
        last_nodes = {}
        # loop through and remove selections
        for order, selection in selections_to_remove:
            # traverse --> study_value__study_arm__uid
            last_study_selection_node = latest_study_value_node.has_study_arm.get(
                uid=selection.study_selection_uid
            )
            # detect if the action should be create, delete or edit, then create audit node of the that StudyAction type
            audit_node = self._get_audit_node(
                study_selection, selection.study_selection_uid
            )
            # create the before node to the last_study_selection_node and audit trial to study_root
            audit_node = self._set_before_audit_info(
                audit_node=audit_node,
                study_selection_node=last_study_selection_node,
                study_root_node=study_root_node,
                author=author,
            )
            # storage of the removed node audit trail to after put the "after" relationship to the new one
            audit_trail_nodes[selection.study_selection_uid] = audit_node
            # storage of the removed node to after get its connections
            last_nodes[selection.study_selection_uid] = last_study_selection_node
            if isinstance(audit_node, Delete):
                self._add_new_selection(
                    latest_study_value_node,
                    order,
                    selection,
                    audit_node,
                    for_deletion=True,
                    before_node=last_study_selection_node,
                )

        # loop through and add selections
        for order, selection in selections_to_add:
            # create last_study_selection_node None as the new study_selection could not have an audit trial node
            last_study_selection_node = None
            # if the study selection already has an audit trail node
            if selection.study_selection_uid in audit_trail_nodes:
                # extract the audit_trail_node
                audit_node = audit_trail_nodes[selection.study_selection_uid]
                # extract the last "AFTER" selection that now is "BEFORE"
                last_study_selection_node = last_nodes[selection.study_selection_uid]
            else:
                # if the audi_node doesn't exists, then create a new one
                audit_node = Create()
                audit_node.user_initials = selection.user_initials
                audit_node.date = selection.start_date
                audit_node.save()
                study_root_node.audit_trail.connect(audit_node)
            self._add_new_selection(
                latest_study_value_node,
                order,
                selection,
                audit_node,
                for_deletion=False,
                before_node=last_study_selection_node,
            )

    @staticmethod
    def _set_before_audit_info(
        audit_node: StudyAction,
        study_selection_node: StudyArm,
        study_root_node: StudyRoot,
        author: str,
    ) -> StudyAction:
        audit_node.user_initials = author
        audit_node.date = datetime.datetime.now(datetime.timezone.utc)
        audit_node.save()

        audit_node.has_before.connect(study_selection_node)
        study_root_node.audit_trail.connect(audit_node)
        return audit_node

    @staticmethod
    def arm_exists_by(
        db_property: str, value: str, arm_vo: StudySelectionArmVO
    ) -> StudyArm:
        kwarg_value = getattr(arm_vo, value)
        arm_node = (
            StudyArm.nodes.has(study_value=True)
            .filter(
                uid__ne=arm_vo.study_selection_uid,
                study_value__latest_value__uid=arm_vo.study_uid,
            )
            .get_or_none(**{db_property: kwarg_value})
        )
        return arm_node

    @staticmethod
    def _add_new_selection(
        latest_study_value_node: StudyValue,
        order: int,
        selection: StudySelectionArmVO,
        audit_node: StudyAction,
        for_deletion: bool = False,
        before_node: StudyArm | None = None,
    ):
        # Create new arm selection
        study_arm_selection_node: StudyArm = StudyArm(order=order).save()
        study_arm_selection_node.uid = selection.study_selection_uid
        study_arm_selection_node.accepted_version = selection.accepted_version
        study_arm_selection_node.name = selection.name
        study_arm_selection_node.short_name = selection.short_name
        study_arm_selection_node.arm_code = selection.code
        study_arm_selection_node.description = selection.description
        study_arm_selection_node.arm_colour = selection.arm_colour
        study_arm_selection_node.randomization_group = selection.randomization_group
        study_arm_selection_node.number_of_subjects = selection.number_of_subjects
        study_arm_selection_node.save()

        # Connect new node with study value
        if not for_deletion:
            # Connect new node with study value
            latest_study_value_node.has_study_arm.connect(study_arm_selection_node)
        # Connect new node with audit trail
        audit_node.has_after.connect(study_arm_selection_node)

        if before_node is not None:
            manage_previous_connected_study_selection_relationships(
                previous_item=before_node,
                study_value_node=latest_study_value_node,
                new_item=study_arm_selection_node,
                exclude_study_selection_relationships=[],
            )

        # check if arm type is set
        if selection.arm_type_uid:
            # find the CTTermRoot (but be sure that it is the actual one!!)
            study_arm_type = CTTermRoot.nodes.get(uid=selection.arm_type_uid)
            # connect to node
            # pylint: disable=no-member
            study_arm_selection_node.arm_type.connect(study_arm_type)

    def generate_uid(self) -> str:
        return StudyArm.get_next_free_uid_and_increment_counter()

    def arm_specific_exists_by_uid(self, uid: str) -> bool:
        """
        Returns True if StudyArm with specified uid exists.
        :return:
        """
        query = """
            MATCH (study_arm:StudyArm {uid: $uid})
            RETURN study_arm
            """
        result, _ = db.cypher_query(query, {"uid": uid})
        return len(result) > 0

    def _get_selection_with_history(
        self, study_uid: str, study_selection_uid: str | None = None
    ):
        """
        returns the audit trail for study arm either for a specific selection or for all study arm for the study
        """
        if study_selection_uid:
            cypher = """
                    MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(sa:StudyArm { uid: $study_selection_uid})
                    WITH sa
                    MATCH (sa)-[:AFTER|BEFORE*0..]-(all_sa:StudyArm)
                    WITH distinct(all_sa)
                    """
        else:
            cypher = """
                    MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sa:StudyArm)
                    WITH DISTINCT all_sa
                    """
        specific_arm_selections_audit_trail = db.cypher_query(
            cypher
            + """
            WITH DISTINCT all_sa
            OPTIONAL MATCH (all_sa)-[:HAS_ARM_TYPE]->(at:CTTermRoot)
            WITH DISTINCT all_sa, at
            ORDER BY all_sa.order ASC
            MATCH (all_sa)<-[:AFTER]-(asa:StudyAction)
            OPTIONAL MATCH (all_sa)<-[:BEFORE]-(bsa:StudyAction)
            WITH all_sa, asa, bsa, at
            ORDER BY all_sa.uid, asa.date DESC
            RETURN
                all_sa.uid AS study_selection_uid,
                all_sa.name AS arm_name,
                all_sa.short_name AS arm_short_name,
                all_sa.arm_code AS arm_code,
                all_sa.description AS arm_description,
                all_sa.arm_colour AS arm_colour,
                all_sa.order AS order,
                all_sa.accepted_version AS accepted_version,
                all_sa.number_of_subjects AS number_of_subjects,
                all_sa.randomization_group AS randomization_group,
                at.uid AS arm_type_uid,
                all_sa.text AS text,
                asa.date AS start_date,
                asa.user_initials AS user_initials,
                labels(asa) AS change_type,
                bsa.date AS end_date
            """,
            {"study_uid": study_uid, "study_selection_uid": study_selection_uid},
        )
        result = []
        for res in helpers.db_result_to_list(specific_arm_selections_audit_trail):
            for action in res["change_type"]:
                if "StudyAction" not in action:
                    change_type = action
            end_date = (
                convert_to_datetime(value=res["end_date"]) if res["end_date"] else None
            )
            result.append(
                SelectionHistoryArm(
                    study_selection_uid=res["study_selection_uid"],
                    study_uid=study_uid,
                    arm_name=res["arm_name"],
                    arm_short_name=res["arm_short_name"],
                    arm_code=res["arm_code"],
                    arm_description=res["arm_description"],
                    arm_colour=res["arm_colour"],
                    arm_randomization_group=res["randomization_group"],
                    arm_number_of_subjects=res["number_of_subjects"],
                    arm_type=res["arm_type_uid"],
                    start_date=convert_to_datetime(value=res["start_date"]),
                    user_initials=res["user_initials"],
                    change_type=change_type,
                    end_date=end_date,
                    accepted_version=res["accepted_version"],
                    status=None,
                    order=res["order"],
                )
            )
        return result

    def find_selection_history(
        self, study_uid: str, study_selection_uid: str | None = None
    ) -> list[SelectionHistoryArm]:
        """
        Simple method to return all versions of a study objectives for a study.
        Optionally a specific selection uid is given to see only the response for a specific selection.
        """
        if study_selection_uid:
            return self._get_selection_with_history(
                study_uid=study_uid, study_selection_uid=study_selection_uid
            )
        return self._get_selection_with_history(study_uid=study_uid)

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass
