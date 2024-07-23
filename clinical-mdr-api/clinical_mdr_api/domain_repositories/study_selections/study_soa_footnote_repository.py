import datetime

from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain_repositories._utils.helpers import db_result_to_list
from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
)
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyActivityGroup,
    StudyActivitySubGroup,
    StudySoAFootnote,
    StudySoAGroup,
)
from clinical_mdr_api.domain_repositories.models.syntax import (
    FootnoteRoot,
    FootnoteTemplateRoot,
    FootnoteTemplateValue,
    FootnoteValue,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_soa_footnote import (
    ReferencedItemVO,
    SoAItemType,
    StudySoAFootnoteVO,
    StudySoAFootnoteVOHistory,
)
from clinical_mdr_api.exceptions import ValidationException


class StudySoAFootnoteRepository:
    def generate_soa_footnote_uid(self) -> str:
        return StudySoAFootnote.get_next_free_uid_and_increment_counter()

    def where_query(self):
        return (
            "WHERE NOT (sf)<-[:BEFORE]-(:StudyAction) AND NOT (sf)<-[:AFTER]-(:Delete)"
        )

    def with_query(self):
        return """
            WITH DISTINCT sr, sf, sa,
            [(sf)-[:REFERENCES_STUDY_ACTIVITY]->(study_activity:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(sv) | 
                {
                    uid:study_activity.uid, 
                    name:head([(study_activity)-[:HAS_SELECTED_ACTIVITY]->(activity_value:ActivityValue) | activity_value.name])
                }] AS referenced_study_activities,
            [(sf)-[:REFERENCES_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup)
                <-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]-(:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(sv) | 
                {
                    uid:study_activity_subgroup.uid, 
                    name:head([(study_activity_subgroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue) | activity_subgroup_value.name])
                }] AS referenced_study_activity_subgroups,
            [(sf)-[:REFERENCES_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup)
                <-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]-(:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(sv) | 
                {
                    uid:study_activity_group.uid, 
                    name:head([(study_activity_group)-[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue) | activity_group_value.name])
                }] AS referenced_study_activity_groups,
            [(sf)-[:REFERENCES_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)<-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]-(:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(sv) |
                {
                    uid:study_soa_group.uid, 
                    name:head([(study_soa_group)-[:HAS_FLOWCHART_GROUP]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-
                        [:LATEST]->(term_name_value:CTTermNameValue) | term_name_value.name])
                }] AS referenced_study_soa_groups,
            [(sf)-[:REFERENCES_STUDY_EPOCH]->(study_epoch:StudyEpoch)<-[:HAS_STUDY_EPOCH]-(sv) | 
                {
                    uid:study_epoch.uid, 
                    name:head([(study_epoch)-[:HAS_EPOCH]-(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(term_value:CTTermNameValue) | term_value.name])
                }] AS referenced_study_epochs,
            [(sf)-[:REFERENCES_STUDY_VISIT]->(study_visit:StudyVisit)<-[:HAS_STUDY_VISIT]-(sv) | 
                {
                    uid:study_visit.uid, 
                    name:study_visit.short_visit_label
                }] AS referenced_study_visits,
            [(sf)-[:REFERENCES_STUDY_ACTIVITY_SCHEDULE]->(study_activity_schedule:StudyActivitySchedule)<-[:HAS_STUDY_ACTIVITY_SCHEDULE]-(sv) | 
                {
                    uid:study_activity_schedule.uid, 
                    name:head([(activity_value:ActivityValue)<-[:HAS_SELECTED_ACTIVITY]-(:StudyActivity)-[STUDY_ACTIVITY_HAS_SCHEDULE]->
                        (study_activity_schedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(study_visit:StudyVisit)<-[:HAS_STUDY_VISIT]-(sv) 
                        | activity_value.name + ' ' + study_visit.short_visit_label])
                }] AS referenced_study_activity_schedules,
            head([(sf)<-[:BEFORE]-(before_action:StudyAction) | before_action.date]) AS end_date
            CALL {
                WITH sf
                OPTIONAL MATCH (sf)-[:HAS_SELECTED_FOOTNOTE]->(:FootnoteValue)<-[ver:HAS_VERSION]-(fr:FootnoteRoot)
                WHERE ver.status = "Final"
                RETURN {uid:fr.uid, version: ver.version} as footnote
                ORDER BY ver.start_date DESC
                LIMIT 1
            }
            CALL{
                WITH sf
                OPTIONAL MATCH (sf)-[:HAS_SELECTED_FOOTNOTE_TEMPLATE]->(:FootnoteTemplateValue)<-[ver:HAS_VERSION]-(ftv:FootnoteTemplateRoot)
                WHERE ver.status = "Final"
                RETURN {uid:ftv.uid, version: ver.version} as footnote_template
                ORDER BY ver.start_date DESC
                LIMIT 1
            }
            RETURN DISTINCT
                sr.uid AS study_uid,
                sf.uid AS uid,
                sf.footnote_number AS footnote_number,
                sf.accepted_version as accepted_version,
                footnote.uid as footnote_uid, 
                footnote.version as footnote_version,
                footnote_template.uid as footnote_template_uid, 
                footnote_template.version as footnote_template_version,
                sa.date AS modified_date,
                end_date,
                sa.user_initials AS user_initials,
                sa.status AS status,
                labels(sa) AS change_type,
                apoc.coll.toSet(referenced_study_activities) AS referenced_study_activities,
                apoc.coll.toSet(referenced_study_activity_subgroups) AS referenced_study_activity_subgroups,
                apoc.coll.toSet(referenced_study_activity_groups) AS referenced_study_activity_groups,
                apoc.coll.toSet(referenced_study_soa_groups) AS referenced_study_soa_groups,
                apoc.coll.toSet(referenced_study_epochs) AS referenced_study_epochs,
                apoc.coll.toSet(referenced_study_visits) AS referenced_study_visits,
                apoc.coll.toSet(referenced_study_activity_schedules) AS referenced_study_activity_schedules
            """

    def order_by_footnote_number(self):
        return " ORDER BY footnote_number"

    def order_by_date(self):
        return "ORDER BY modified_date DESC"

    def get_referenced_items_from_selection(self, selection: dict):
        referenced_items = []
        selected_study_activities = selection.get("referenced_study_activities")
        for activity in selected_study_activities:
            referenced_items.append(
                ReferencedItemVO(
                    item_uid=activity.get("uid"),
                    item_type=SoAItemType.STUDY_ACTIVITY,
                    item_name=activity.get("name"),
                )
            )
        selected_study_activity_subgroups = selection.get(
            "referenced_study_activity_subgroups"
        )
        for activity_subgroup in selected_study_activity_subgroups:
            referenced_items.append(
                ReferencedItemVO(
                    item_uid=activity_subgroup.get("uid"),
                    item_type=SoAItemType.STUDY_ACTIVITY_SUBGROUP,
                    item_name=activity_subgroup.get("name"),
                )
            )
        selected_study_activity_groups = selection.get(
            "referenced_study_activity_groups"
        )
        for activity_group in selected_study_activity_groups:
            referenced_items.append(
                ReferencedItemVO(
                    item_uid=activity_group.get("uid"),
                    item_type=SoAItemType.STUDY_ACTIVITY_GROUP,
                    item_name=activity_group.get("name"),
                )
            )
        selected_study_soa_groups = selection.get("referenced_study_soa_groups")
        for soa_group in selected_study_soa_groups:
            referenced_items.append(
                ReferencedItemVO(
                    item_uid=soa_group.get("uid"),
                    item_type=SoAItemType.STUDY_SOA_GROUP,
                    item_name=soa_group.get("name"),
                )
            )
        selected_study_epochs = selection.get("referenced_study_epochs")
        for study_epoch in selected_study_epochs:
            referenced_items.append(
                ReferencedItemVO(
                    item_uid=study_epoch.get("uid"),
                    item_type=SoAItemType.STUDY_EPOCH,
                    item_name=study_epoch.get("name"),
                )
            )
        selected_study_visits = selection.get("referenced_study_visits")
        for study_visit in selected_study_visits:
            referenced_items.append(
                ReferencedItemVO(
                    item_uid=study_visit.get("uid"),
                    item_type=SoAItemType.STUDY_VISIT,
                    item_name=study_visit.get("name"),
                )
            )
        selected_study_activity_schedules = selection.get(
            "referenced_study_activity_schedules"
        )
        for sas in selected_study_activity_schedules:
            referenced_items.append(
                ReferencedItemVO(
                    item_uid=sas.get("uid"),
                    item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
                    item_name=sas.get("name"),
                )
            )
        return referenced_items

    def create_vo_from_db_output(self, selection: dict) -> StudySoAFootnoteVO:
        referenced_items = self.get_referenced_items_from_selection(selection=selection)

        selection_vo = StudySoAFootnoteVO.from_repository_values(
            study_uid=selection.get("study_uid"),
            footnote_uid=selection.get("footnote_uid"),
            footnote_version=selection.get("footnote_version"),
            footnote_template_uid=selection.get("footnote_template_uid"),
            footnote_template_version=selection.get("footnote_template_version"),
            referenced_items=referenced_items,
            footnote_number=selection.get("footnote_number"),
            uid=selection.get("uid"),
            modified=convert_to_datetime(value=selection.get("modified_date")),
            author=selection.get("user_initials"),
            status=StudyStatus(selection.get("status")),
            accepted_version=selection.get("accepted_version"),
        )
        return selection_vo

    def create_vo_history_from_db_output(
        self, selection: dict
    ) -> StudySoAFootnoteVOHistory:
        referenced_items = self.get_referenced_items_from_selection(selection=selection)
        change_type = None
        for action in selection["change_type"]:
            if "StudyAction" not in action:
                change_type = action
        selection_vo = StudySoAFootnoteVOHistory(
            study_uid=selection.get("study_uid"),
            footnote_uid=selection.get("footnote_uid"),
            footnote_version=selection.get("footnote_version"),
            footnote_template_uid=selection.get("footnote_template_uid"),
            footnote_template_version=selection.get("footnote_template_version"),
            referenced_items=referenced_items,
            footnote_number=selection.get("footnote_number"),
            uid=selection.get("uid"),
            start_date=convert_to_datetime(value=selection.get("modified_date")),
            end_date=convert_to_datetime(value=selection.get("end_date"))
            if selection.get("end_date")
            else None,
            change_type=change_type,
            author=selection.get("user_initials"),
            status=StudyStatus(selection.get("status")),
            accepted_version=selection.get("accepted_version"),
        )
        return selection_vo

    def find_all_footnotes(
        self,
        study_uids: str | list[str] | None = None,
        study_value_version: str | None = None,
    ) -> list[StudySoAFootnoteVO]:
        query_parameters = {}
        if study_uids:
            if isinstance(study_uids, str):
                study_uid_statement = "{uid: $uids}"
            else:
                study_uid_statement = "WHERE sr.uid IN $uids"
            if study_value_version:
                query = (
                    f"MATCH (sr:StudyRoot {study_uid_statement})-[l:HAS_VERSION{{status:'RELEASED', version:$study_value_version}}]->(sv:StudyValue)"
                    "-[:HAS_STUDY_FOOTNOTE]->(sf:StudySoAFootnote)<-[:AFTER]-(sa:StudyAction)"
                )
                query_parameters["study_value_version"] = study_value_version
                query_parameters["uids"] = study_uids
            else:
                query = (
                    f"MATCH (sr:StudyRoot {study_uid_statement})-[l:LATEST]->(sv:StudyValue)-[:HAS_STUDY_FOOTNOTE]->"
                    "(sf:StudySoAFootnote)<-[:AFTER]-(sa:StudyAction)"
                )
                query_parameters["uids"] = study_uids
        else:
            if study_value_version:
                query = (
                    "MATCH (sr:StudyRoot)-[l:HAS_VERSION{status:'RELEASED', version:$study_value_version}]->(sv:StudyValue)"
                    "-[:HAS_STUDY_FOOTNOTE]->(sf:StudySoAFootnote)<-[:AFTER]-(sa:StudyAction)"
                )
                query_parameters["study_value_version"] = study_value_version
            else:
                query = (
                    "MATCH (sr:StudyRoot)-[l:LATEST]->(sv:StudyValue)-[:HAS_STUDY_FOOTNOTE]->(sf:StudySoAFootnote)"
                    "<-[:AFTER]-(sa:StudyAction)"
                )

        if not study_value_version:
            query += self.where_query()
        query += self.with_query()
        query += self.order_by_footnote_number()
        all_study_soa_footnotes = db.cypher_query(query, query_parameters)
        all_selections = []
        for selection in db_result_to_list(all_study_soa_footnotes):
            selection_vo = self.create_vo_from_db_output(selection=selection)
            all_selections.append(selection_vo)
        return all_selections

    def find_by_uid(
        self, uid: str, study_value_version: str | None = None
    ) -> StudySoAFootnoteVO:
        query_parameters = {}
        query_parameters["uid"] = uid
        if study_value_version:
            query = (
                "MATCH (sr:StudyRoot)-[l:HAS_VERSION{status:'RELEASED', version:$study_value_version}]->(sv:StudyValue)-[:HAS_STUDY_FOOTNOTE]->"
                "(sf:StudySoAFootnote {uid:$uid})<-[:AFTER]-(sa:StudyAction)"
            )
            query_parameters["study_value_version"] = study_value_version
        else:
            query = (
                "MATCH (sr:StudyRoot)-[l:LATEST]->(sv:StudyValue)-[:HAS_STUDY_FOOTNOTE]->"
                "(sf:StudySoAFootnote {uid:$uid})<-[:AFTER]-(sa:StudyAction)"
            )
        if not study_value_version:
            query += self.where_query()
        query += self.with_query()
        query += self.order_by_footnote_number()

        db_ret = db.cypher_query(query, query_parameters)

        soa_footnote = db_result_to_list(db_ret)
        if len(soa_footnote) == 0:
            raise exceptions.NotFoundException(
                f"StudySoAFootnote with uid {uid} does not exist."
            )
        if len(soa_footnote) > 1:
            raise exceptions.ValidationException(
                f"Returned more than one StudySoAFootnote with uid {uid}"
            )

        selection_vo = self.create_vo_from_db_output(selection=soa_footnote[0])
        return selection_vo

    def save(self, soa_footnote_vo: StudySoAFootnoteVO, create: bool = True):
        study_root = StudyRoot.nodes.get(uid=soa_footnote_vo.study_uid)
        study_value = study_root.latest_value.get_or_none()
        if study_value is None:
            raise ValidationException(
                f"Study ({soa_footnote_vo.study_uid}) doesn't exist"
            )
        soa_footnote_node = StudySoAFootnote(
            uid=soa_footnote_vo.uid,
            footnote_number=soa_footnote_vo.footnote_number,
            accepted_version=soa_footnote_vo.accepted_version,
        )
        soa_footnote_node.save()

        # link to selected footnote if there's no specific version
        if soa_footnote_vo.footnote_uid and not soa_footnote_vo.footnote_version:
            selected_footnote = FootnoteRoot.nodes.get(
                uid=soa_footnote_vo.footnote_uid
            ).has_latest_value.get()
            soa_footnote_node.has_footnote.connect(selected_footnote)
        # link to selected footnote with specified version
        elif soa_footnote_vo.footnote_uid and soa_footnote_vo.footnote_version:
            selected_footnote = (
                FootnoteValue.nodes.fetch_relations("has_version")
                .filter(
                    **{
                        "has_version__uid": soa_footnote_vo.footnote_uid,
                        "has_version|version": soa_footnote_vo.footnote_version,
                    }
                )
                .get_or_none()[1]
            )
            soa_footnote_node.has_footnote.connect(selected_footnote)
        # link to selected footnote template if there's no specific version specified
        elif (
            soa_footnote_vo.footnote_template_uid
            and not soa_footnote_vo.footnote_template_version
        ):
            selected_footnote_template = FootnoteTemplateRoot.nodes.get(
                uid=soa_footnote_vo.footnote_template_uid
            ).has_latest_value.get()
            soa_footnote_node.has_footnote_template.connect(selected_footnote_template)
        # link to selected footnote template with specified version
        elif (
            soa_footnote_vo.footnote_template_uid
            and soa_footnote_vo.footnote_template_version
        ):
            selected_footnote_template = (
                FootnoteTemplateValue.nodes.fetch_relations("has_version")
                .filter(
                    **{
                        "has_version__uid": soa_footnote_vo.footnote_template_uid,
                        "has_version|version": soa_footnote_vo.footnote_template_version,
                    }
                )
                .get_or_none()[1]
            )
            soa_footnote_node.has_footnote_template.connect(selected_footnote_template)
        not_found_items = []
        # link to referenced items by a footnote
        for referenced_item in soa_footnote_vo.referenced_items:
            # Activity
            if referenced_item.item_type.value == SoAItemType.STUDY_ACTIVITY.value:
                study_activity_referenced_node = (
                    study_value.has_study_activity.get_or_none(
                        uid=referenced_item.item_uid
                    )
                )
                if study_activity_referenced_node:
                    soa_footnote_node.references_study_activity.connect(
                        study_activity_referenced_node
                    )
                else:
                    not_found_items.append(referenced_item)
            # ActivitySubGroup
            if (
                referenced_item.item_type.value
                == SoAItemType.STUDY_ACTIVITY_SUBGROUP.value
            ):
                study_activity_subgroup_referenced_node = (
                    StudyActivitySubGroup.nodes.has(has_before=False).get_or_none(
                        uid=referenced_item.item_uid
                    )
                )
                if study_activity_subgroup_referenced_node:
                    soa_footnote_node.references_study_activity_subgroup.connect(
                        study_activity_subgroup_referenced_node
                    )
                else:
                    not_found_items.append(referenced_item)
            # Activity Group
            if (
                referenced_item.item_type.value
                == SoAItemType.STUDY_ACTIVITY_GROUP.value
            ):
                study_activity_group_referenced_node = StudyActivityGroup.nodes.has(
                    has_before=False
                ).get_or_none(uid=referenced_item.item_uid)
                if study_activity_group_referenced_node:
                    soa_footnote_node.references_study_activity_group.connect(
                        study_activity_group_referenced_node
                    )
                else:
                    not_found_items.append(referenced_item)
            # SoA Group
            if referenced_item.item_type.value == SoAItemType.STUDY_SOA_GROUP.value:
                study_soa_group_referenced_node = StudySoAGroup.nodes.has(
                    has_before=False
                ).get_or_none(uid=referenced_item.item_uid)
                if study_soa_group_referenced_node:
                    soa_footnote_node.references_study_soa_group.connect(
                        study_soa_group_referenced_node
                    )
                else:
                    not_found_items.append(referenced_item)
            # StudyActivitySchedule
            if (
                referenced_item.item_type.value
                == SoAItemType.STUDY_ACTIVITY_SCHEDULE.value
            ):
                sas_referenced_node = (
                    study_value.has_study_activity_schedule.get_or_none(
                        uid=referenced_item.item_uid
                    )
                )
                if sas_referenced_node:
                    soa_footnote_node.references_study_activity_schedule.connect(
                        sas_referenced_node
                    )
                else:
                    not_found_items.append(referenced_item)
            # StudyVisit
            if referenced_item.item_type.value == SoAItemType.STUDY_VISIT.value:
                study_visit_referenced_node = study_value.has_study_visit.get_or_none(
                    uid=referenced_item.item_uid
                )
                if study_visit_referenced_node:
                    soa_footnote_node.references_study_visit.connect(
                        study_visit_referenced_node
                    )
                else:
                    not_found_items.append(referenced_item)
            # StudyEpoch
            if referenced_item.item_type.value == SoAItemType.STUDY_EPOCH.value:
                study_epoch_referenced_node = study_value.has_study_epoch.get_or_none(
                    uid=referenced_item.item_uid
                )
                if study_epoch_referenced_node:
                    soa_footnote_node.references_study_epoch.connect(
                        study_epoch_referenced_node
                    )
                else:
                    not_found_items.append(referenced_item)
        if not_found_items:
            raise ValidationException(
                f"The following referenced nodes were not found "
                f"{[not_found_item.item_name if not_found_item.item_name else not_found_item.item_uid for not_found_item in not_found_items]}"
            )
        if create:
            self.manage_versioning_create(
                study_root=study_root,
                study_soa_footnote_vo=soa_footnote_vo,
                new_node=soa_footnote_node,
            )
            soa_footnote_node.study_value.connect(study_value)
        else:
            previous_item = StudySoAFootnote.nodes.filter(uid=soa_footnote_vo.uid).has(
                study_value=True, has_before=False
            )[0]
            if soa_footnote_vo.is_deleted:
                self.manage_versioning_delete(
                    study_root=study_root,
                    study_soa_footnote_vo=soa_footnote_vo,
                    previous_node=previous_item,
                    new_node=soa_footnote_node,
                )
            else:
                self.manage_versioning_update(
                    study_root=study_root,
                    study_soa_footnote_vo=soa_footnote_vo,
                    previous_node=previous_item,
                    new_node=soa_footnote_node,
                )
                soa_footnote_node.study_value.connect(study_value)
            # disconnect old StudyValue node to only keep StudyValue connection to the Latest value of StudySoAFootnote
            previous_item.study_value.disconnect(study_value)

    def get_all_versions_for_specific_visit(
        self, uid: str, study_uid: str
    ) -> list[StudySoAFootnoteVOHistory]:
        query_parameters = {}
        query = """
                MATCH (sr:StudyRoot {uid: $study_uid})-[:AUDIT_TRAIL]->(sa:StudyAction)-[:AFTER]->(sf:StudySoAFootnote {uid:$uid})
                """

        query_parameters["study_uid"] = study_uid
        query_parameters["uid"] = uid
        query += self.with_query()
        query += self.order_by_date()
        all_study_soa_footnotes = db.cypher_query(query, query_parameters)
        all_selections = []
        for selection in db_result_to_list(all_study_soa_footnotes):
            selection_vo = self.create_vo_history_from_db_output(selection=selection)
            all_selections.append(selection_vo)
        return all_selections

    def get_all_versions(self, study_uid: str) -> list[StudySoAFootnoteVOHistory]:
        query_parameters = {}
        query = """
                MATCH (sr:StudyRoot {uid: $study_uid})-[:AUDIT_TRAIL]->(sa:StudyAction)-[:AFTER]->(sf:StudySoAFootnote)
                """

        query_parameters["study_uid"] = study_uid
        query += self.with_query()
        query += self.order_by_date()
        all_study_soa_footnotes = db.cypher_query(query, query_parameters)
        all_selections = []
        for selection in db_result_to_list(all_study_soa_footnotes):
            selection_vo = self.create_vo_history_from_db_output(selection=selection)
            all_selections.append(selection_vo)
        return all_selections

    def manage_versioning_create(
        self,
        study_root: StudyRoot,
        study_soa_footnote_vo: StudySoAFootnoteVO,
        new_node: StudySoAFootnote,
    ):
        action = Create(
            date=datetime.datetime.now(datetime.timezone.utc),
            status=study_soa_footnote_vo.status.value,
            user_initials=study_soa_footnote_vo.author,
        )
        action.save()
        action.has_after.connect(new_node)
        study_root.audit_trail.connect(action)

    def manage_versioning_update(
        self,
        study_root: StudyRoot,
        study_soa_footnote_vo: StudySoAFootnoteVO,
        previous_node: StudySoAFootnote,
        new_node: StudySoAFootnote,
    ):
        action = Edit(
            date=datetime.datetime.now(datetime.timezone.utc),
            status=study_soa_footnote_vo.status.value,
            user_initials=study_soa_footnote_vo.author,
        )
        action.save()
        action.has_before.connect(previous_node)
        action.has_after.connect(new_node)
        study_root.audit_trail.connect(action)

    def manage_versioning_delete(
        self,
        study_root: StudyRoot,
        study_soa_footnote_vo: StudySoAFootnoteVO,
        previous_node: StudySoAFootnote,
        new_node: StudySoAFootnote,
    ):
        action = Delete(
            date=datetime.datetime.now(datetime.timezone.utc),
            status=study_soa_footnote_vo.status.value,
            user_initials=study_soa_footnote_vo.author,
        )
        action.save()
        action.has_before.connect(previous_node)
        action.has_after.connect(new_node)
        study_root.audit_trail.connect(action)
