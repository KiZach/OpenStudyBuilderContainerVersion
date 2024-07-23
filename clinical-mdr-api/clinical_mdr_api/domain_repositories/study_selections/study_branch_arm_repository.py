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
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
    StudyAction,
)
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyArm,
    StudyBranchArm,
)
from clinical_mdr_api.domains.study_selections.study_selection_branch_arm import (
    StudySelectionBranchArmAR,
    StudySelectionBranchArmVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import VersioningException


@dataclass
class SelectionHistoryBranchArm:
    """Class for selection history items"""

    study_selection_uid: str
    study_uid: str | None
    branch_arm_name: str | None
    branch_arm_short_name: str | None
    branch_arm_code: str | None
    branch_arm_description: str | None
    branch_arm_colour_code: str | None
    branch_arm_randomization_group: str | None
    branch_arm_number_of_subjects: int | None
    arm_root: str | None
    # Study selection Versioning
    start_date: datetime.datetime
    user_initials: str | None
    change_type: str
    end_date: datetime.datetime | None
    order: int
    status: str | None
    accepted_version: bool | None


class StudySelectionBranchArmRepository:
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

    def _retrieves_all_data(
        self,
        study_uid: str | None = None,
        project_name: str | None = None,
        project_number: str | None = None,
        study_value_version: str | None = None,
    ) -> tuple[StudySelectionBranchArmVO]:
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
            MATCH (sv)-[:HAS_STUDY_BRANCH_ARM]->(sba:StudyBranchArm)
            WITH DISTINCT sr, sba 

        """
        if study_value_version:
            query += """
                OPTIONAL MATCH (sba)<-[:STUDY_ARM_HAS_BRANCH_ARM]-(ar:StudyArm)<-[:HAS_STUDY_ARM]-(:StudyValue)<-[l:HAS_VERSION{status:'RELEASED', version:$study_value_version}]-(:StudyRoot)
            """
        else:
            query += """
            
                OPTIONAL MATCH (:StudyValue)--(ar:StudyArm)-[:STUDY_ARM_HAS_BRANCH_ARM]->(sba)
        
             """

        query += """
            MATCH (sba)<-[:AFTER]-(sa:StudyAction)

            RETURN DISTINCT 
                sr.uid AS study_uid,
                sba.uid AS study_selection_uid,
                sba.name AS branch_arm_name,
                sba.short_name AS branch_arm_short_name,
                sba.branch_arm_code AS branch_arm_code,
                sba.description AS branch_arm_description,
                sba.colour_code AS branch_arm_colour_code,
                sba.order AS order,
                sba.accepted_version AS accepted_version,
                sba.number_of_subjects AS number_of_subjects,
                sba.randomization_group AS randomization_group,
                ar.uid AS arm_root_uid,
                sba.text AS text,
                sa.date AS start_date,
                sa.user_initials AS user_initials
                ORDER BY order
            """

        all_branch_arm_selections = db.cypher_query(query, query_parameters)
        all_selections = []

        for selection in helpers.db_result_to_list(all_branch_arm_selections):
            acv = selection.get("accepted_version", False)
            if acv is None:
                acv = False
            selection_vo = StudySelectionBranchArmVO.from_input_values(
                user_initials=selection["user_initials"],
                study_uid=selection["study_uid"],
                name=selection["branch_arm_name"],
                short_name=selection["branch_arm_short_name"],
                code=selection["branch_arm_code"],
                description=selection["branch_arm_description"],
                colour_code=selection["branch_arm_colour_code"],
                study_selection_uid=selection["study_selection_uid"],
                arm_root_uid=selection["arm_root_uid"],
                number_of_subjects=selection["number_of_subjects"],
                randomization_group=selection["randomization_group"],
                start_date=convert_to_datetime(value=selection["start_date"]),
                accepted_version=selection["accepted_version"],
            )
            all_selections.append(selection_vo)
        return tuple(all_selections)

    def _retrieves_all_data_within_arm(
        self,
        study_arm_uid: str | None = None,
        study_uid: str | None = None,
        project_name: str | None = None,
        project_number: str | None = None,
        study_value_version: str | None = None,
    ) -> tuple[StudySelectionBranchArmVO]:
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
            MATCH (sv)-[:HAS_STUDY_ARM]->(ar:StudyArm{ uid: $uid})
            WITH DISTINCT sr, sv, ar 
            MATCH (ar)<-[:AFTER]-(:StudyAction)"""
        query_parameters["uid"] = study_arm_uid

        query += """
            WITH sr, sv, ar
            MATCH (sv)-[:HAS_STUDY_BRANCH_ARM]->(sba:StudyBranchArm)<-[:STUDY_ARM_HAS_BRANCH_ARM]-(ar)
            WITH DISTINCT sr, sba, ar
            
            MATCH (sba)<-[:AFTER]-(sa:StudyAction)

            RETURN DISTINCT 
                sr.uid AS study_uid,
                sba.uid AS study_selection_uid,
                sba.name AS branch_arm_name,
                sba.short_name AS branch_arm_short_name,
                sba.branch_arm_code AS branch_arm_code,
                sba.description AS branch_arm_description,
                sba.colour_code AS branch_arm_colour_code,
                sba.order AS order,
                sba.accepted_version AS accepted_version,
                sba.number_of_subjects AS number_of_subjects,
                sba.randomization_group AS randomization_group,
                ar.uid AS arm_root_uid,
                sba.text AS text,
                sa.date AS start_date,
                sa.user_initials AS user_initials
                ORDER BY order
            """

        all_branch_arm_selections = db.cypher_query(query, query_parameters)
        all_selections = []

        for selection in helpers.db_result_to_list(all_branch_arm_selections):
            acv = selection.get("accepted_version", False)
            if acv is None:
                acv = False
            selection_vo = StudySelectionBranchArmVO.from_input_values(
                user_initials=selection["user_initials"],
                study_uid=selection["study_uid"],
                name=selection["branch_arm_name"],
                short_name=selection["branch_arm_short_name"],
                code=selection["branch_arm_code"],
                description=selection["branch_arm_description"],
                colour_code=selection["branch_arm_colour_code"],
                study_selection_uid=selection["study_selection_uid"],
                arm_root_uid=selection["arm_root_uid"],
                number_of_subjects=selection["number_of_subjects"],
                randomization_group=selection["randomization_group"],
                start_date=convert_to_datetime(value=selection["start_date"]),
                accepted_version=selection["accepted_version"],
            )
            all_selections.append(selection_vo)
        return tuple(all_selections)

    def find_by_study(
        self,
        study_uid: str,
        for_update: bool = False,
        study_value_version: str | None = None,
    ) -> StudySelectionBranchArmAR | None:
        """
        Finds all the selected study branch arms for a given study
        :param study_uid:
        :param for_update:
        :return:
        """
        if for_update:
            self._acquire_write_lock_study_value(study_uid)
        all_selections = self._retrieves_all_data(
            study_uid, study_value_version=study_value_version
        )
        selection_aggregate = StudySelectionBranchArmAR.from_repository_values(
            study_uid=study_uid,
            study_branch_arms_selection=all_selections,
        )
        if for_update:
            selection_aggregate.repository_closure_data = all_selections
        return selection_aggregate

    def find_by_arm(
        self,
        study_uid: str,
        study_arm_uid: str,
        for_update: bool = False,
        study_value_version: str | None = None,
    ) -> StudySelectionBranchArmAR | None:
        """
        Finds all the selected study branch arms for a given study_arm
        :param study_uid:
        :param study_arm_uid:
        :param for_update:
        :return:
        """
        if for_update:
            self._acquire_write_lock_study_value(study_uid)
        all_selections = self._retrieves_all_data_within_arm(
            study_arm_uid, study_value_version=study_value_version
        )
        selection_aggregate = StudySelectionBranchArmAR.from_repository_values(
            study_uid=study_uid, study_branch_arms_selection=all_selections
        )
        if for_update:
            selection_aggregate.repository_closure_data = all_selections
        return selection_aggregate

    def find_by_arm_nested_info(
        self,
        study_uid: str,
        study_arm_uid: str,
        user_initials: str,
        study_value_version: str | None = None,
    ) -> tuple[StudySelectionBranchArmVO, int] | None:
        """
        Return StudySelectionBranchArmVO's connected to the specified StudyArmUid
        :param study_uid: str
        :param study_arm_uid: str
        :param user_initials: str
        :return: Return a list of tuples of StudySelectionBranchArmVO and ordering
        """
        if study_value_version:
            filters = {
                "uid": study_arm_uid,
                "study_value__has_version|version": str(study_value_version),
                "has_branch_arm__study_value__has_version|version": str(
                    study_value_version
                ),
                "study_value__has_version__uid": study_uid,
                "has_branch_arm__study_value__has_version__uid": study_uid,
            }
        else:
            filters = {
                "uid": study_arm_uid,
                "study_value__latest_value__uid": study_uid,
                "has_branch_arm__study_value__latest_value__uid": study_uid,
            }
        sa_nodes = (
            StudyArm.nodes.fetch_relations("has_branch_arm__study_value__has_version")
            .filter(**filters)
            .order_by("order")
            .all()
        )
        sba_nodes_non_unique = [i_sa_nodes[0] for i_sa_nodes in sa_nodes]
        sba_nodes = []
        for ith in sba_nodes_non_unique:
            if ith not in sba_nodes:
                sba_nodes.append(ith)
        sba_nodes.sort(key=lambda sba_node: sba_node.order)
        # Tuple for the StudySelectionBranchArmVO and the order
        study_branch_arms: list[tuple[StudySelectionBranchArmVO, int]] = []
        if sba_nodes:
            for i_sdc_node in sba_nodes:
                study_branch_arms.append(
                    (
                        StudySelectionBranchArmVO.from_input_values(
                            user_initials=user_initials,
                            study_uid=study_uid,
                            study_selection_uid=i_sdc_node.uid,
                            name=i_sdc_node.name,
                            short_name=i_sdc_node.short_name,
                            code=i_sdc_node.branch_arm_code,
                            description=i_sdc_node.description,
                            colour_code=i_sdc_node.colour_code,
                            randomization_group=i_sdc_node.randomization_group,
                            number_of_subjects=i_sdc_node.number_of_subjects,
                            arm_root_uid=None,
                            start_date=i_sdc_node.has_after.single().date,
                            end_date=None,
                            status=None,
                            change_type=None,
                            accepted_version=None,
                        ),
                        i_sdc_node.order,
                    )
                )
            return study_branch_arms
        return None

    def _get_audit_node(
        self, study_selection: StudySelectionBranchArmAR, study_selection_uid: str
    ):
        all_current_ids = []
        for item in study_selection.study_branch_arms_selection:
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

    def branch_arm_specific_exists_by_uid(
        self, study_uid: str, branch_arm_uid: str
    ) -> bool:
        """
        Returns True if StudyBranchArm with specified uid exists.
        :return:
        """
        sdc_node = to_relation_trees(
            StudyBranchArm.nodes.fetch_relations("has_after").filter(
                study_value__latest_value__uid=study_uid, uid=branch_arm_uid
            )
        )
        return len(sdc_node) > 0

    def get_branch_arms_connected_to_arm(self, study_uid: str, study_arm_uid: str):
        sdc_nodes = (
            StudyArm.nodes.fetch_relations("has_branch_arm__study_value__latest_value")
            .filter(uid=study_arm_uid, study_value__latest_value__uid=study_uid)
            .order_by("order")
            .all()
        )
        return sorted(
            [i_th[0] for i_th in sdc_nodes],
            key=lambda branch_arm: branch_arm.order,
            reverse=False,
        )

    def branch_arm_specific_has_connected_cell(
        self, study_uid: str, branch_arm_uid: str
    ) -> bool:
        """
        Returns True if StudyBranchArm with specified uid has connected at least one StudyDesignCell.
        :return:
        """
        sdc_node = to_relation_trees(
            StudyBranchArm.nodes.fetch_relations(
                "has_design_cell__study_value", "has_after"
            ).filter(study_value__latest_value__uid=study_uid, uid=branch_arm_uid)
        )
        return len(sdc_node) > 0

    def branch_arm_specific_is_last_on_arm_root(
        self, study_uid: str, arm_root_uid: str, branch_arm_uid: str
    ) -> bool:
        """
        Returns True if Study Branch Arm with specified uid has connected is the last Study Branch Arm on its Study Arm root
        :return:
        """
        sdc_node = to_relation_trees(
            StudyBranchArm.nodes.fetch_relations("arm_root", "has_after")
            .filter(
                study_value__latest_value__uid=study_uid, arm_root__uid=arm_root_uid
            )
            .exclude(uid=branch_arm_uid)
        )
        return len(sdc_node) == 0

    def save(self, study_selection: StudySelectionBranchArmAR, author: str) -> None:
        """
        Persist the set of selected study amrs from the aggregate to the database
        :param study_selection:
        :param author:
        """
        assert study_selection.repository_closure_data is not None

        # getting the latest study value node
        study_root_node = StudyRoot.nodes.get(uid=study_selection.study_uid)
        latest_study_value_node = study_root_node.latest_value.single()

        if study_root_node.latest_locked.get_or_none() == latest_study_value_node:
            raise VersioningException(
                "You cannot add or reorder a study selection when the study is in a locked state."
            )

        # group closure by parent arm
        closure_group_by_root = {}
        for selected_object in study_selection.repository_closure_data:
            if selected_object.arm_root_uid not in closure_group_by_root:
                closure_group_by_root[selected_object.arm_root_uid] = []
            closure_group_by_root[selected_object.arm_root_uid].append(selected_object)
        # group branch arm by root
        branch_arm_group_by_root = {}
        for selected_object in study_selection.study_branch_arms_selection:
            if selected_object.arm_root_uid not in branch_arm_group_by_root:
                branch_arm_group_by_root[selected_object.arm_root_uid] = []
            branch_arm_group_by_root[selected_object.arm_root_uid].append(
                selected_object
            )

        # process new/changed/deleted elements for each parent arm
        selections_to_remove = {}
        selections_to_add = {}

        # first, check for deleted elements
        for arm_root, branch_arm_list in closure_group_by_root.items():
            # check if object is removed from the selection list - delete has been called
            # two options to detect object is removed : list for given criteria type is empty or smaller than the list in the closure
            if (arm_root not in branch_arm_group_by_root) or len(branch_arm_list) > len(
                branch_arm_group_by_root[arm_root]
            ):
                # remove the last item from old list, as there will no longer be any study criteria with that high order
                selections_to_remove[arm_root] = [
                    (len(branch_arm_list), branch_arm_list[-1])
                ]

        # then, check for new/changed elements
        for arm_root, branch_arm_list in branch_arm_group_by_root.items():
            for order, selected_object in enumerate(branch_arm_list, start=1):
                if arm_root in closure_group_by_root:
                    _closure_data = closure_group_by_root[arm_root]
                    # check whether something new is added
                    if len(_closure_data) > order - 1:
                        # check if anything has changed
                        if selected_object is not _closure_data[order - 1]:
                            # update the selection by removing the old if the old exists, and adding new selection
                            if arm_root in selections_to_remove:
                                selections_to_remove[arm_root].append(
                                    (order, _closure_data[order - 1])
                                )
                            else:
                                selections_to_remove[arm_root] = [
                                    (order, _closure_data[order - 1])
                                ]
                            if arm_root in selections_to_add:
                                selections_to_add[arm_root].append(
                                    (order, selected_object)
                                )
                            else:
                                selections_to_add[arm_root] = [(order, selected_object)]
                    else:
                        # else something new has been added
                        if arm_root in selections_to_add:
                            selections_to_add[arm_root].append((order, selected_object))
                        else:
                            selections_to_add[arm_root] = [(order, selected_object)]
                else:
                    selections_to_add[arm_root] = [(1, branch_arm_list[0])]

        # audit trail nodes dictionary, holds the new nodes created for the audit trail
        audit_trail_nodes = {}
        last_nodes = {}

        # loop through and remove selections
        for arm_root, branch_arm_list in selections_to_remove.items():
            for selection in branch_arm_list:
                order = selection[0]
                selected_object = selection[1]
                # traverse --> study_value__study_branch__uid
                last_study_selection_node = (
                    latest_study_value_node.has_study_branch_arm.get(
                        uid=selected_object.study_selection_uid
                    )
                )
                # detect if the action should be create, delete or edit, then create audit node of the that StucyAction type
                audit_node = self._get_audit_node(
                    study_selection, selected_object.study_selection_uid
                )
                # create the before node to the last_study_selection_node and audit trial to study_root
                audit_node = self._set_before_audit_info(
                    audit_node=audit_node,
                    study_selection_node=last_study_selection_node,
                    study_root_node=study_root_node,
                    author=author,
                )

                audit_trail_nodes[selected_object.study_selection_uid] = audit_node
                last_nodes[
                    selected_object.study_selection_uid
                ] = last_study_selection_node
                if isinstance(audit_node, Delete):
                    self._add_new_selection(
                        latest_study_value_node,
                        order,
                        selected_object,
                        audit_node,
                        True,
                        before_node=last_study_selection_node,
                    )

        # loop through and add selections
        for arm_root, branch_arm_list in selections_to_add.items():
            for selection in branch_arm_list:
                order = selection[0]
                selected_object = selection[1]
                last_study_selection_node = None
                if selected_object.study_selection_uid in audit_trail_nodes:
                    audit_node = audit_trail_nodes[selected_object.study_selection_uid]
                    last_study_selection_node = last_nodes[
                        selected_object.study_selection_uid
                    ]
                else:
                    audit_node = Create()
                    audit_node.user_initials = selected_object.user_initials
                    audit_node.date = selected_object.start_date
                    audit_node.save()
                    study_root_node.audit_trail.connect(audit_node)
                self._add_new_selection(
                    latest_study_value_node,
                    order,
                    selected_object,
                    audit_node,
                    False,
                    before_node=last_study_selection_node,
                )

    @staticmethod
    def _set_before_audit_info(
        audit_node: StudyAction,
        study_selection_node: StudyBranchArm,
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
    def branch_arm_arm_update_conflict(
        branch_arm_vo: StudySelectionBranchArmVO,
    ) -> bool:
        """
        Return True if a BranchArm with a specific StudyArm root has connected StudyDesignCells
        To consider:
            - select StudyDesignCell that is connected to a StudyValue
        """
        branch_arm_with_connected_design_cell_with_diff_arm_root = (
            StudyBranchArm.nodes.has(has_design_cell=True)
            .filter(
                # If it matches a branch_arm with a different arm_root, then it would
                # mean that it is trying to change its arm_root, even though it's having design_cells connected to the BranchArm.
                arm_root__uid__ne=branch_arm_vo.arm_root_uid,
                study_value__latest_value__uid=branch_arm_vo.study_uid,
                has_design_cell__study_value__latest_value__uid=branch_arm_vo.study_uid,
            )
            .get_or_none(uid=branch_arm_vo.study_selection_uid)
        )
        return branch_arm_with_connected_design_cell_with_diff_arm_root is not None

    @staticmethod
    def branch_arm_exists_by(
        db_property: str, value: str, branch_arm_vo: StudySelectionBranchArmVO
    ) -> StudyBranchArm:
        kwarg_value = getattr(branch_arm_vo, value)
        branch_arm_node = (
            StudyBranchArm.nodes.has(study_value=True)
            .filter(
                uid__ne=branch_arm_vo.study_selection_uid,
                study_value__latest_value__uid=branch_arm_vo.study_uid,
            )
            .get_or_none(**{db_property: kwarg_value})
        )
        return branch_arm_node

    @staticmethod
    def _add_new_selection(
        latest_study_value_node: StudyValue,
        order: int,
        selection: StudySelectionBranchArmVO,
        audit_node: StudyAction,
        for_deletion: bool = False,
        before_node: StudyBranchArm | None = None,
    ):
        """
        Add new BranchArm Selection
        StudyBranchArm Possible Outbound Relationships:
            - StudyDesignCell - optional
            - StudyArm - mandatory
            - StudyCohort - optional
        """
        # Create new arm selection
        study_branch_arm_selection_node = StudyBranchArm(order=order).save()
        study_branch_arm_selection_node.uid = selection.study_selection_uid
        study_branch_arm_selection_node.accepted_version = selection.accepted_version
        study_branch_arm_selection_node.name = selection.name
        study_branch_arm_selection_node.short_name = selection.short_name
        study_branch_arm_selection_node.branch_arm_code = selection.code
        study_branch_arm_selection_node.description = selection.description
        study_branch_arm_selection_node.colour_code = selection.colour_code
        study_branch_arm_selection_node.randomization_group = (
            selection.randomization_group
        )
        study_branch_arm_selection_node.number_of_subjects = (
            selection.number_of_subjects
        )
        study_branch_arm_selection_node.save()

        # Connect new node with study value
        if not for_deletion:
            # Connect new node with study value
            latest_study_value_node.has_study_branch_arm.connect(
                study_branch_arm_selection_node
            )
        # Connect new node with audit trail
        audit_node.has_after.connect(study_branch_arm_selection_node)

        if before_node is not None:
            manage_previous_connected_study_selection_relationships(
                previous_item=before_node,
                study_value_node=latest_study_value_node,
                new_item=study_branch_arm_selection_node,
                exclude_study_selection_relationships=[StudyArm],
            )

        # check if arm root is set
        if selection.arm_root_uid:
            # find the objective
            study_arm_root = latest_study_value_node.has_study_arm.get(
                uid=selection.arm_root_uid
            )
            # connect to node
            # pylint: disable=no-member
            study_branch_arm_selection_node.arm_root.connect(study_arm_root)

    def generate_uid(self) -> str:
        return StudyBranchArm.get_next_free_uid_and_increment_counter()

    def _get_selection_with_history(
        self, study_uid: str, study_selection_uid: str | None = None
    ):
        """
        returns the audit trail for study branch arm either for a specific selection or for all study branch arm for the study
        """
        if study_selection_uid:
            cypher = """
                    MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(sa:StudyBranchArm { uid: $study_selection_uid})
                    WITH sa
                    MATCH (sa)-[:AFTER|BEFORE*0..]-(all_sba:StudyBranchArm)
                    WITH distinct(all_sba)
                    """
        else:
            cypher = """
                    MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sba:StudyBranchArm)
                    WITH DISTINCT all_sba
                    """
        specific_branch_arm_selections_audit_trail = db.cypher_query(
            cypher
            + """
            WITH DISTINCT all_sba
            OPTIONAL MATCH (at:StudyArm)-[:STUDY_ARM_HAS_BRANCH_ARM]->(all_sba)
            WITH DISTINCT all_sba, at
            ORDER BY all_sba.order ASC
            MATCH (all_sba)<-[:AFTER]-(asa:StudyAction)
            OPTIONAL MATCH (all_sba)<-[:BEFORE]-(bsa:StudyAction)
            WITH all_sba, asa, bsa, at
            ORDER BY all_sba.uid, asa.date DESC
            RETURN
                all_sba.uid AS study_selection_uid,
                all_sba.name AS branch_arm_name,
                all_sba.short_name AS branch_arm_short_name,
                all_sba.branch_arm_code AS branch_arm_code,
                all_sba.description AS branch_arm_description,
                all_sba.colour_code AS branch_arm_colour_code,
                all_sba.order AS order,
                all_sba.accepted_version AS accepted_version,
                all_sba.number_of_subjects AS number_of_subjects,
                all_sba.randomization_group AS randomization_group,
                at.uid AS arm_root_uid,
                all_sba.text AS text,
                asa.date AS start_date,
                asa.user_initials AS user_initials,
                labels(asa) AS change_type,
                bsa.date AS end_date
            """,
            {"study_uid": study_uid, "study_selection_uid": study_selection_uid},
        )
        result = []
        for res in helpers.db_result_to_list(
            specific_branch_arm_selections_audit_trail
        ):
            for action in res["change_type"]:
                if "StudyAction" not in action:
                    change_type = action
            end_date = (
                convert_to_datetime(value=res["end_date"]) if res["end_date"] else None
            )
            result.append(
                SelectionHistoryBranchArm(
                    study_selection_uid=res["study_selection_uid"],
                    study_uid=study_uid,
                    branch_arm_name=res["branch_arm_name"],
                    branch_arm_short_name=res["branch_arm_short_name"],
                    branch_arm_code=res["branch_arm_code"],
                    branch_arm_description=res["branch_arm_description"],
                    branch_arm_colour_code=res["branch_arm_colour_code"],
                    branch_arm_randomization_group=res["randomization_group"],
                    branch_arm_number_of_subjects=res["number_of_subjects"],
                    arm_root=res["arm_root_uid"],
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
    ) -> list[SelectionHistoryBranchArm]:
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
