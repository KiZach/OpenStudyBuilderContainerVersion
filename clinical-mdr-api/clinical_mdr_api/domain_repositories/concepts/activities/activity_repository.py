from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.config import REQUESTED_LIBRARY_NAME
from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    convert_to_datetime,
    to_relation_trees,
)
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityGrouping,
    ActivityRoot,
    ActivityValidGroup,
    ActivityValue,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.activities.activity import (
    ActivityAR,
    ActivityGroupingVO,
    ActivityVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.exceptions import BusinessLogicException
from clinical_mdr_api.models.concepts.activities.activity import Activity


def _version_to_number(version: str) -> float:
    major, minor = version.split(".")
    return 1000 * float(major) + float(minor)


def _get_display_version(versions: list[dict]) -> dict | None:
    if len(versions) == 1:
        return versions[0]
    sorted_versions = sorted(
        versions, key=lambda x: _version_to_number(x["version"]), reverse=True
    )
    for status in [
        LibraryItemStatus.FINAL,
        LibraryItemStatus.RETIRED,
        LibraryItemStatus.DRAFT,
    ]:
        latest_ver = next(
            (
                version
                for version in sorted_versions
                if version["status"] == status.value
            ),
            None,
        )
        if latest_ver:
            return latest_ver
    return None


class ActivityRepository(ConceptGenericRepository[ActivityAR]):
    root_class = ActivityRoot
    value_class = ActivityValue
    return_model = Activity
    filter_query_parameters = {}

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> ActivityAR:
        major, minor = input_dict.get("version").split(".")
        return ActivityAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=ActivityVO.from_repository_values(
                nci_concept_id=input_dict.get("nci_concept_id"),
                name=input_dict.get("name"),
                name_sentence_case=input_dict.get("name_sentence_case"),
                definition=input_dict.get("definition"),
                abbreviation=input_dict.get("abbreviation"),
                activity_groupings=[
                    ActivityGroupingVO(
                        activity_group_uid=activity_grouping.get("activity_group_uid"),
                        activity_subgroup_uid=activity_grouping.get(
                            "activity_subgroup_uid"
                        ),
                    )
                    for activity_grouping in input_dict.get("activity_groupings")
                ],
                request_rationale=input_dict.get("request_rationale"),
                is_request_final=input_dict.get("is_request_final"),
                requester_study_id=input_dict.get("requester_study_id"),
                replaced_by_activity=input_dict.get("replaced_by_activity"),
                reason_for_rejecting=input_dict.get("reason_for_rejecting"),
                contact_person=input_dict.get("contact_person"),
                is_request_rejected=input_dict.get("is_request_rejected"),
                is_data_collected=input_dict.get("is_data_collected"),
                is_multiple_selection_allowed=input_dict.get(
                    "is_multiple_selection_allowed"
                ),
                is_finalized=input_dict.get("is_finalized"),
                is_used_by_legacy_instances=input_dict.get(
                    "is_used_by_legacy_instances"
                ),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=input_dict.get("library_name"),
                is_library_editable_callback=(
                    lambda _: input_dict.get("is_library_editable")
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=input_dict.get("change_description"),
                status=LibraryItemStatus(input_dict.get("status")),
                author=input_dict.get("user_initials"),
                start_date=convert_to_datetime(value=input_dict.get("start_date")),
                end_date=convert_to_datetime(value=input_dict.get("end_date")),
                major_version=int(major),
                minor_version=int(minor),
            ),
        )

    def _create_ar(
        self,
        root: VersionRoot,
        library: Library | None,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> ActivityAR:
        requester_study_id = None
        # We are only interested in the StudyId of the Activity Requests
        if library.name == REQUESTED_LIBRARY_NAME:
            if study_activity := value.has_selected_activity.single():
                if activity := study_activity.has_study_activity.single():
                    requester_study_id = (
                        f"{activity.study_id_prefix}-{activity.study_number}"
                    )
        return ActivityAR.from_repository_values(
            uid=root.uid,
            concept_vo=ActivityVO.from_repository_values(
                nci_concept_id=value.nci_concept_id,
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                definition=value.definition,
                abbreviation=value.abbreviation,
                activity_groupings=[
                    ActivityGroupingVO(
                        activity_group_uid=activity_grouping.get("activity_group_uid"),
                        activity_subgroup_uid=activity_grouping.get(
                            "activity_subgroup_uid"
                        ),
                    )
                    for activity_grouping in _kwargs["activity_root"][
                        "activity_groupings"
                    ]
                ],
                request_rationale=value.request_rationale,
                is_request_final=value.is_request_final
                if value.is_request_final
                else False,
                requester_study_id=requester_study_id,
                replaced_by_activity=_kwargs["activity_root"]["replaced_activity_uid"],
                reason_for_rejecting=value.reason_for_rejecting,
                contact_person=value.contact_person,
                is_request_rejected=value.is_request_rejected
                if value.is_request_rejected
                else False,
                is_data_collected=value.is_data_collected
                if value.is_data_collected
                else False,
                is_multiple_selection_allowed=value.is_multiple_selection_allowed
                if value.is_multiple_selection_allowed is not None
                else True,
                is_finalized=bool(
                    value.is_request_rejected
                    or _kwargs["activity_root"]["replaced_activity_uid"]
                ),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library | None,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> ActivityAR:
        replaced_activity = value.replaced_by_activity.get_or_none()
        activity_groupings_nodes = value.has_grouping.all()
        activity_groupings = []
        activity_instances_legacy_codes = []
        for activity_grouping in activity_groupings_nodes:
            activity_instances_legacy_codes.extend(
                activity_instance_value.is_legacy_usage
                for activity_instance_value in activity_grouping.has_activity.all()
            )
            activity_valid_groups = activity_grouping.in_subgroup.all()
            for activity_valid_group in activity_valid_groups:
                activity_groupings.append(
                    {
                        "activity_group_uid": activity_valid_group.in_group.get()
                        .has_version.single()
                        .uid,
                        "activity_subgroup_uid": activity_valid_group.has_group.get()
                        .has_version.single()
                        .uid,
                    }
                )
        requester_study_id = None
        # We are only interested in the StudyId of the Activity Requests
        if library.name == REQUESTED_LIBRARY_NAME:
            if study_activity := value.has_selected_activity.single():
                if activity := study_activity.has_study_activity.single():
                    requester_study_id = (
                        f"{activity.study_id_prefix}-{activity.study_number}"
                    )
        return ActivityAR.from_repository_values(
            uid=root.uid,
            concept_vo=ActivityVO.from_repository_values(
                nci_concept_id=value.nci_concept_id,
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                definition=value.definition,
                abbreviation=value.abbreviation,
                activity_groupings=[
                    ActivityGroupingVO(
                        activity_group_uid=activity_grouping.get("activity_group_uid"),
                        activity_subgroup_uid=activity_grouping.get(
                            "activity_subgroup_uid"
                        ),
                    )
                    for activity_grouping in activity_groupings
                ],
                request_rationale=value.request_rationale,
                is_request_final=value.is_request_final
                if value.is_request_final
                else False,
                requester_study_id=requester_study_id,
                replaced_by_activity=replaced_activity.uid
                if replaced_activity
                else None,
                reason_for_rejecting=value.reason_for_rejecting,
                contact_person=value.contact_person,
                is_request_rejected=value.is_request_rejected
                if value.is_request_rejected
                else False,
                is_data_collected=value.is_data_collected
                if value.is_data_collected
                else False,
                is_multiple_selection_allowed=value.is_multiple_selection_allowed
                if value.is_multiple_selection_allowed is not None
                else True,
                is_finalized=bool(value.is_request_rejected or replaced_activity),
                is_used_by_legacy_instances=all(activity_instances_legacy_codes)
                if activity_instances_legacy_codes
                else False,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def create_query_filter_statement(
        self, library: str | None = None, **kwargs
    ) -> tuple[str, dict]:
        (
            filter_statements_from_concept,
            filter_query_parameters,
        ) = super().create_query_filter_statement(library=library)
        filter_parameters = []
        if (activity_subgroup_uid := kwargs.get("activity_subgroup_uid")) is not None:
            filter_by_activity_subgroup_uid = """
            $activity_subgroup_uid IN [(concept_value)-[:HAS_GROUPING]->(:ActivityGrouping)-[:IN_SUBGROUP]->
            (:ActivityValidGroup)<-[:HAS_GROUP]-(activity_subgroup_value:ActivitySubGroupValue)
            <-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot) | activity_subgroup_root.uid]"""
            filter_parameters.append(filter_by_activity_subgroup_uid)
            filter_query_parameters["activity_subgroup_uid"] = activity_subgroup_uid
        if kwargs.get("activity_names") is not None:
            activity_names = kwargs.get("activity_names")
            filter_by_activity_names = "concept_value.name IN $activity_names"
            filter_parameters.append(filter_by_activity_names)
            filter_query_parameters["activity_names"] = activity_names
        if kwargs.get("activity_subgroup_names") is not None:
            activity_subgroup_names = kwargs.get("activity_subgroup_names")
            filter_by_activity_subgroup_names = """
            size([(concept_value)-[:HAS_GROUPING]->(:ActivityGrouping)-[:IN_SUBGROUP]->
            (:ActivityValidGroup)<-[:HAS_GROUP]-(asgv:ActivitySubGroupValue) WHERE asgv.name IN $activity_subgroup_names | asgv.name]) > 0"""
            filter_parameters.append(filter_by_activity_subgroup_names)
            filter_query_parameters["activity_subgroup_names"] = activity_subgroup_names
        if kwargs.get("activity_group_names") is not None:
            activity_group_names = kwargs.get("activity_group_names")
            filter_by_activity_group_names = """
            size([(concept_value)-[:HAS_GROUPING]->(:ActivityGrouping)-[:IN_SUBGROUP]->
            (:ActivityValidGroup)-[:IN_GROUP]->(agv:ActivityGroupValue) WHERE agv.name IN $activity_group_names | agv.name]) > 0"""
            filter_parameters.append(filter_by_activity_group_names)
            filter_query_parameters["activity_group_names"] = activity_group_names
        extended_filter_statements = " AND ".join(filter_parameters)
        if filter_statements_from_concept != "":
            if len(extended_filter_statements) > 0:
                filter_statements_to_return = " AND ".join(
                    [filter_statements_from_concept, extended_filter_statements]
                )
            else:
                filter_statements_to_return = filter_statements_from_concept
        else:
            filter_statements_to_return = (
                "WHERE " + extended_filter_statements
                if len(extended_filter_statements) > 0
                else ""
            )
        return filter_statements_to_return, filter_query_parameters

    def _create_new_value_node(self, ar: ActivityAR) -> ActivityValue:
        value_node: ActivityValue = super()._create_new_value_node(ar=ar)
        value_node.request_rationale = ar.concept_vo.request_rationale
        value_node.is_request_final = ar.concept_vo.is_request_final
        value_node.reason_for_rejecting = ar.concept_vo.reason_for_rejecting
        value_node.contact_person = ar.concept_vo.contact_person
        value_node.is_request_rejected = ar.concept_vo.is_request_rejected
        value_node.is_data_collected = ar.concept_vo.is_data_collected
        value_node.is_multiple_selection_allowed = (
            ar.concept_vo.is_multiple_selection_allowed
        )
        value_node.save()
        for activity_grouping in ar.concept_vo.activity_groupings:
            # create ActivityGrouping node
            activity_grouping_node = ActivityGrouping(
                uid=ActivityGrouping.get_next_free_uid_and_increment_counter()
            )
            activity_grouping_node.save()

            # link ActivityValue and ActivityGrouping nodes
            value_node.has_grouping.connect(activity_grouping_node)

            # find related ActivityValidGroup node
            activity_valid_group_node = to_relation_trees(
                ActivityValidGroup.nodes.filter(
                    in_group__has_version__uid=activity_grouping.activity_group_uid,
                    has_group__has_version__uid=activity_grouping.activity_subgroup_uid,
                )
            ).distinct()
            if len(activity_valid_group_node) == 0:
                raise BusinessLogicException(
                    f"The ActivityValidGroup node wasn't found for subgroup ({activity_grouping.activity_subgroup_uid}) "
                    f"and group ({activity_grouping.activity_group_uid})"
                )
            activity_valid_group_node = activity_valid_group_node[0]

            # link ActivityGrouping and ActivityValidGroup
            activity_grouping_node.in_subgroup.connect(activity_valid_group_node)

        return value_node

    def _has_data_changed(self, ar: ActivityAR, value: ActivityValue) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)
        are_props_changed = (
            ar.concept_vo.request_rationale != value.request_rationale
            or ar.concept_vo.is_request_final != value.is_request_final
            or ar.concept_vo.reason_for_rejecting != value.reason_for_rejecting
            or ar.concept_vo.contact_person != value.contact_person
            or ar.concept_vo.is_request_rejected != value.is_request_rejected
            or ar.concept_vo.is_data_collected != value.is_data_collected
            or ar.concept_vo.is_multiple_selection_allowed
            != value.is_multiple_selection_allowed
        )

        activity_subgroup_uids = []
        activity_group_uids = []
        activity_grouping_nodes = value.has_grouping.all()
        for activity_grouping_node in activity_grouping_nodes:
            activity_valid_group_nodes = activity_grouping_node.in_subgroup.all()
            for activity_valid_group_node in activity_valid_group_nodes:
                activity_subgroup_uids.append(
                    activity_valid_group_node.has_group.get().has_version.single().uid
                )
                activity_group_uids.append(
                    activity_valid_group_node.in_group.get().has_version.single().uid
                )

        are_rels_changed = sorted(
            [
                activity_grouping.activity_group_uid
                for activity_grouping in ar.concept_vo.activity_groupings
            ]
        ) != sorted(activity_group_uids) or sorted(
            [
                activity_grouping.activity_subgroup_uid
                for activity_grouping in ar.concept_vo.activity_groupings
            ]
        ) != sorted(
            activity_subgroup_uids
        )
        return are_concept_properties_changed or are_rels_changed or are_props_changed

    def specific_alias_clause(
        self, only_specific_status: str = ObjectStatus.LATEST.name
    ) -> str:
        # concept_value property comes from the main part of the query
        # which is specified in the concept_generic_repository
        activity_subgroup_names = self.filter_query_parameters.get(
            "activity_subgroup_names"
        )
        activity_group_names = self.filter_query_parameters.get("activity_group_names")
        return f"""
        WITH *,
            concept_value.request_rationale AS request_rationale,
            coalesce(concept_value.is_request_final, false) AS is_request_final,
            coalesce(concept_value.is_request_rejected, false) AS is_request_rejected,
            concept_value.contact_person AS contact_person,
            concept_value.reason_for_rejecting AS reason_for_rejecting,
            CASE
                WHEN library_name='Requested'
                THEN head([(concept_root)-[:HAS_VERSION]->(:{self.value_class.__label__})<-[:HAS_SELECTED_ACTIVITY]->(:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(study_value:StudyValue)
                   | coalesce(study_value.study_id_prefix, "") + "-" + toString(study_value.study_number)])
                ELSE NULL
            END AS requester_study_id,
            coalesce(concept_value.is_data_collected, False) AS is_data_collected,
            coalesce(concept_value.is_multiple_selection_allowed, True) AS is_multiple_selection_allowed,
            apoc.coll.toSet([(concept_value)-[:HAS_GROUPING]->(:ActivityGrouping)-[:IN_SUBGROUP]->(activity_valid_group:ActivityValidGroup)
            {'WHERE size([(activity_valid_group)<-[:HAS_GROUP]-(activity_subgroup_value) WHERE activity_subgroup_value.name in $activity_subgroup_names | activity_subgroup_value.name]) > 0 ' if activity_subgroup_names else ''}
            {'AND' if activity_subgroup_names and activity_group_names else ''}
            {'' if activity_subgroup_names and activity_group_names else 'WHERE' if not activity_subgroup_names and activity_group_names else ''}
            {'size([(activity_valid_group)-[:IN_GROUP]-(activity_group_value) WHERE activity_group_value.name in $activity_group_names | activity_group_value.name]) > 0 ' if activity_group_names else ''}
             | {{
                 activity_subgroup_uid: head([(activity_valid_group)<-[:HAS_GROUP]-(activity_subgroup_value:ActivitySubGroupValue)
                 <-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot) | activity_subgroup_root.uid]), 
                 activity_subgroup_name: head([(activity_valid_group)<-[:HAS_GROUP]-(activity_subgroup_value:ActivitySubGroupValue)
                   | activity_subgroup_value.name]), 
                 activity_group_uid: head([(activity_valid_group)-[:IN_GROUP]-(activity_group_value:ActivityGroupValue)
                 <-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot) | activity_group_root.uid]),
                 activity_group_name: head([(activity_valid_group)-[:IN_GROUP]-(activity_group_value:ActivityGroupValue)
                   | activity_group_value.name])
             }}]) AS activity_groupings,
            head([(concept_value)-[:REPLACED_BY_ACTIVITY]->(replacing_activity_root:ActivityRoot) | replacing_activity_root.uid]) AS replaced_by_activity,
            [(concept_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-(activity_instance_value:ActivityInstanceValue) | activity_instance_value.is_legacy_usage] AS all_legacy_codes

            WITH *, 
                CASE
                WHEN NOT is_request_rejected and replaced_by_activity IS NULL THEN false
                ELSE true
                END as is_finalized,
                CASE WHEN size(all_legacy_codes) > 0
                    THEN all(is_legacy_usage IN all_legacy_codes where is_legacy_usage=true and is_legacy_usage IS NOT NULL)
                    ELSE false
                END as is_used_by_legacy_instances
        """

    def replace_request_with_sponsor_activity(
        self, activity_request_uid: str, sponsor_activity_uid: str
    ) -> None:
        replace_activity_request_with_sponsor_activity_query = """
            MATCH (:ActivityRoot {uid: $activity_request_uid})-[:LATEST]->(activity_request_value:ActivityValue)
            MATCH (replacing_activity_root:ActivityRoot {uid: $sponsor_activity_uid})
            WITH activity_request_value, replacing_activity_root
            MERGE (activity_request_value)-[:REPLACED_BY_ACTIVITY]->(replacing_activity_root)
        """
        db.cypher_query(
            replace_activity_request_with_sponsor_activity_query,
            {
                "activity_request_uid": activity_request_uid,
                "sponsor_activity_uid": sponsor_activity_uid,
            },
        )

    def final_or_replaced_retired_activity_exists(self, uid: str) -> bool:
        query = f"""
            MATCH (concept_root:{self.root_class.__label__} {{uid: $uid}})-[:LATEST_FINAL]->(concept_value)
            RETURN concept_root
            """
        result, _ = db.cypher_query(query, {"uid": uid})
        exists = len(result) > 0 and len(result[0]) > 0
        if not exists:
            query = f"""
                MATCH (concept_root:{self.root_class.__label__} {{uid: $uid}})-[:LATEST_RETIRED]->(concept_value)
                -[:REPLACED_BY_ACTIVITY]->(:ActivityRoot)
                RETURN concept_root
                """
            result, _ = db.cypher_query(query, {"uid": uid})
            exists = len(result) > 0 and len(result[0]) > 0
        return exists

    def get_activity_overview(self, uid: str, version: str | None = None) -> dict:
        if version:
            params = {"uid": uid, "version": version}
            match = """
                MATCH (activity_root:ActivityRoot {uid:$uid})
                CALL {
                        WITH activity_root
                        MATCH (activity_root)-[hv:HAS_VERSION {version:$version}]->(av:ActivityValue)
                        WITH hv, av
                        ORDER BY
                            toInteger(split(hv.version, '.')[0]) ASC,
                            toInteger(split(hv.version, '.')[1]) ASC,
                            hv.end_date ASC,
                            hv.start_date ASC
                        WITH collect(hv) as hvs, collect (av) as avs
                        RETURN last(hvs) as has_version, last(avs) as activity_value
                    }
                """
        else:
            params = {"uid": uid}
            match = """
                    MATCH (activity_root:ActivityRoot {uid:$uid})-[:LATEST]->(activity_value:ActivityValue)
                    CALL {
                        WITH activity_root, activity_value
                        MATCH (activity_root)-[hv:HAS_VERSION]-(activity_value)
                        WITH hv
                        ORDER BY
                            toInteger(split(hv.version, '.')[0]) ASC,
                            toInteger(split(hv.version, '.')[1]) ASC,
                            hv.end_date ASC,
                            hv.start_date ASC
                        WITH collect(hv) as hvs
                        RETURN last(hvs) as has_version
                    }
                    """

        query = (
            match
            + """
        WITH DISTINCT activity_root,activity_value, has_version,
            head([(library)-[:CONTAINS_CONCEPT]->(activity_root) | library.name]) AS activity_library_name,
            [(activity_root)-[versions:HAS_VERSION]->(:ActivityValue) | versions.version] as all_versions,
            apoc.coll.toSet([(activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-
            (activity_instance_value:ActivityInstanceValue)-[:ACTIVITY_INSTANCE_CLASS]->
            (activity_instance_class_root:ActivityInstanceClassRoot)-[:LATEST]->(activity_instance_class_value:ActivityInstanceClassValue)
            | {
                activity_instance_library_name: head([(library)-[:CONTAINS_CONCEPT]->
                (activity_instance_root:ActivityInstanceRoot)-[:HAS_VERSION]->(activity_instance_value) | library.name]),
                uid: head([(activity_instance_value)<-[:HAS_VERSION]-(activity_instance_root:ActivityInstanceRoot) | activity_instance_root.uid]),
                versions: [(activity_instance_value)<-[aihv:HAS_VERSION]-(activity_instance_root:ActivityInstanceRoot) | aihv { .version, .status, .start_date, .end_date }],
                name:activity_instance_value.name,
                name_sentence_case:activity_instance_value.name_sentence_case,
                abbreviation:activity_instance_value.abbreviation,
                definition:activity_instance_value.definition,
                adam_param_code:activity_instance_value.adam_param_code,
                is_required_for_activity:coalesce(activity_instance_value.is_required_for_activity, false),
                is_default_selected_for_activity:coalesce(activity_instance_value.is_default_selected_for_activity, false),
                is_data_sharing:coalesce(activity_instance_value.is_data_sharing, false),
                is_legacy_usage:coalesce(activity_instance_value.is_legacy_usage, false),
                is_derived:coalesce(activity_instance_value.is_derived, false),
                topic_code:activity_instance_value.topic_code,
                activity_instance_class: activity_instance_class_value
            }]) AS activity_instances,
            [(activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)-[:IN_SUBGROUP]->(activity_valid_group:ActivityValidGroup)
                <-[:HAS_GROUP]-(activity_subgroup_value:ActivitySubGroupValue) | {
                    activity_subgroup_value: activity_subgroup_value, 
                    activity_group_value: head([(activity_valid_group)-[:IN_GROUP]->(activity_group_value) | activity_group_value])
                }
            ] AS hierarchy
        WITH *,
            apoc.coll.sortMaps(activity_instances, '^name') as activity_instances
        RETURN
            hierarchy,
            activity_root,
            activity_value,
            activity_library_name,
            activity_instances,
            has_version,
            apoc.coll.dropDuplicateNeighbors(apoc.coll.sort(all_versions)) AS all_versions
        """
        )
        result_array, attribute_names = db.cypher_query(query=query, params=params)
        if len(result_array) != 1:
            raise exceptions.BusinessLogicException(
                f"The overview query returned broken data: {result_array}"
            )
        overview = result_array[0]
        overview_dict = {}
        for overview_prop, attribute_name in zip(overview, attribute_names):
            overview_dict[attribute_name] = overview_prop
        for item in overview_dict["activity_instances"]:
            item["version"] = _get_display_version(item["versions"])
        return overview_dict

    def get_cosmos_activity_overview(self, uid: str) -> dict:
        query = """
        MATCH (activity_root:ActivityRoot {uid:$uid})-[:LATEST]->(activity_value:ActivityValue)
        WITH DISTINCT activity_root,activity_value,
            apoc.coll.toSet([(activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-
            (activity_instance_value:ActivityInstanceValue)-[:ACTIVITY_INSTANCE_CLASS]->
            (activity_instance_class_root:ActivityInstanceClassRoot)-[:LATEST]->(activity_instance_class_value:ActivityInstanceClassValue)
            | {
                name:activity_instance_value.name,
                nci_concept_id:activity_instance_value.nci_concept_id,
                abbreviation:activity_instance_value.abbreviation,
                definition:activity_instance_value.definition,
                activity_instance_class_name: activity_instance_class_value.name
            }]) AS activity_instances,
            [(activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)-[:IN_SUBGROUP]->(activity_valid_group:ActivityValidGroup)
            <-[:HAS_GROUP]-(activity_subgroup_value:ActivitySubGroupValue) | activity_subgroup_value.name] AS activity_subgroups
        WITH activity_value,
             activity_subgroups,
             apoc.coll.sortMaps(activity_instances, '^name') as activity_instances
        OPTIONAL MATCH (activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-
              (activity_instance_value)-[:CONTAINS_ACTIVITY_ITEM]->
              (activity_item:ActivityItem)<-[:HAS_ACTIVITY_ITEM]-(activity_item_class_root:ActivityItemClassRoot)-[:LATEST]->
              (activity_item_class_value:ActivityItemClassValue)
        OPTIONAL MATCH (activity_item)-[]->(CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(CTTermAttributesRoot)-[:LATEST]->(activity_item_term_attr_value)
        OPTIONAL MATCH (activity_item)-[:HAS_UNIT_DEFINITION]->(:UnitDefinitionRoot)-[:LATEST]->(unit_def:UnitDefinitionValue)
        WITH activity_value,
             activity_item_class_value,
             activity_instances,
             activity_subgroups,
             CASE WHEN size(collect(activity_item)) > 0 THEN
               apoc.map.fromPairs([
                 ['nci_concept_id', activity_item_class_value.nci_concept_id],
                 ['name', activity_item_class_value.name],
                 ['type', head([(activity_item_class_value)-[:HAS_DATA_TYPE]->(data_type_term_root)-[:HAS_ATTRIBUTES_ROOT]->(data_type_term_attr_root)-[:LATEST]->(data_type_term_attr_value) | data_type_term_attr_value.preferred_term])],
                 ['example_set', collect(distinct(coalesce(activity_item_term_attr_value.code_submission_value, unit_def.name)))]
               ]) ELSE null
             END
             AS activity_items
        RETURN
            activity_subgroups,
            activity_value,
            activity_instances,
            collect(activity_items) AS activity_items
        """
        result_array, attribute_names = db.cypher_query(
            query=query, params={"uid": uid}
        )
        if len(result_array) != 1:
            raise exceptions.BusinessLogicException(
                f"The overview query returned broken data: {result_array}"
            )
        return {
            attribute_name: result_array[0][index]
            for index, attribute_name in enumerate(attribute_names)
        }

    def generic_match_clause_all_versions(self):
        return """
            MATCH (concept_root:ActivityRoot)-[version:HAS_VERSION]->(concept_value:ActivityValue)
                    -[:HAS_GROUPING]->(ag:ActivityGrouping)
                    -[:IN_SUBGROUP]->(avg:ActivityValidGroup)<-[:HAS_GROUP]-(subgroup_val:ActivitySubGroupValue)<-[:HAS_VERSION]-(subgroup_root:ActivitySubGroupRoot)
            WITH *
            MATCH (avg)-[:IN_GROUP]->(group_value:ActivityGroupValue)<-[:HAS_VERSION]-(group_root:ActivityGroupRoot)
        """

    def is_multiple_selection_allowed_for_activity(self, activity_uid: str) -> bool:
        query = """
            MATCH (activity_root:ActivityRoot {uid: $activity_uid})-[:LATEST_FINAL]->(activity_value)
            RETURN coalesce(activity_value.is_multiple_selection_allowed, true)
            """
        result, _ = db.cypher_query(query, {"activity_uid": activity_uid})
        is_multiple_selection_allowed_for_activity = (
            len(result) > 0 and len(result[0]) > 0
        )
        return is_multiple_selection_allowed_for_activity
