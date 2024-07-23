from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityGroupRoot,
    ActivitySubGroupRoot,
    ActivitySubGroupValue,
    ActivityValidGroup,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
    ActivitySubGroupVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.activities.activity_sub_group import (
    ActivitySubGroup,
)


class ActivitySubGroupRepository(ConceptGenericRepository[ActivitySubGroupAR]):
    root_class = ActivitySubGroupRoot
    value_class = ActivitySubGroupValue
    return_model = ActivitySubGroup

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> ActivitySubGroupAR:
        major, minor = input_dict.get("version").split(".")
        return ActivitySubGroupAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=ActivitySubGroupVO.from_repository_values(
                name=input_dict.get("name"),
                name_sentence_case=input_dict.get("name_sentence_case"),
                definition=input_dict.get("definition"),
                abbreviation=input_dict.get("abbreviation"),
                activity_groups=[
                    activity_group["uid"]
                    for activity_group in input_dict.get("activity_groups")
                ],
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
    ) -> ActivitySubGroupAR:
        return ActivitySubGroupAR.from_repository_values(
            uid=root.uid,
            concept_vo=ActivitySubGroupVO.from_repository_values(
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                definition=value.definition,
                abbreviation=value.abbreviation,
                activity_groups=_kwargs["activity_subgroups_root"][
                    "activity_groups_uids"
                ],
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
    ) -> ActivitySubGroupAR:
        activity_valid_groups = value.has_group.all()
        activity_groups_uid = []
        for activity_valid_group in activity_valid_groups:
            activity_group_uid = (
                activity_valid_group.in_group.get().has_version.single().uid
            )
            activity_groups_uid.append(activity_group_uid)

        return ActivitySubGroupAR.from_repository_values(
            uid=root.uid,
            concept_vo=ActivitySubGroupVO.from_repository_values(
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                definition=value.definition,
                abbreviation=value.abbreviation,
                activity_groups=activity_groups_uid,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def specific_alias_clause(
        self, only_specific_status: str = ObjectStatus.LATEST.name
    ) -> str:
        # concept_value property comes from the main part of the query
        # which is specified in the activity_generic_repository_impl
        return """
        WITH *,
            apoc.coll.toSet([(concept_value)-[:HAS_GROUP]->(:ActivityValidGroup)-[:IN_GROUP]-(activity_group_value:ActivityGroupValue)
            <-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot) | {uid:activity_group_root.uid, name:activity_group_value.name}]) AS activity_groups
        """

    def create_query_filter_statement(
        self, library: str | None = None, **kwargs
    ) -> tuple[str, dict]:
        (
            filter_statements_from_concept,
            filter_query_parameters,
        ) = super().create_query_filter_statement(library=library)
        filter_parameters = []
        if kwargs.get("activity_group_uid") is not None:
            activity_group_uid = kwargs.get("activity_group_uid")
            filter_by_activity_group_uid = """
            $activity_group_uid IN 
            [(concept_value)-[:HAS_GROUP]->(:ActivityValidGroup)-[:IN_GROUP]->(:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root) 
                | activity_group_root.uid]"""
            filter_parameters.append(filter_by_activity_group_uid)
            filter_query_parameters["activity_group_uid"] = activity_group_uid
        if kwargs.get("activity_group_names") is not None:
            activity_group_names = kwargs.get("activity_group_names")
            filter_by_activity_group_names = """
            size([(concept_value)-[:HAS_GROUP]->(:ActivityValidGroup)-[:IN_GROUP]->(v:ActivityGroupValue) 
            WHERE v.name IN $activity_group_names | v.name]) > 0"""
            filter_parameters.append(filter_by_activity_group_names)
            filter_query_parameters["activity_group_names"] = activity_group_names
        if kwargs.get("activity_names") is not None:
            activity_names = kwargs.get("activity_names")
            filter_by_activity_names = """
            size([(concept_value)-[:HAS_GROUP]-(:ActivityValidGroup)<-[:IN_SUBGROUP]-(:ActivityGrouping)<-[:HAS_GROUPING]-(v:ActivityValue) 
            WHERE v.name IN $activity_names | v.name]) > 0"""
            filter_parameters.append(filter_by_activity_names)
            filter_query_parameters["activity_names"] = activity_names
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

    def _create_new_value_node(self, ar: ActivitySubGroupAR) -> VersionValue:
        value_node: ActivitySubGroupValue = super()._create_new_value_node(ar=ar)
        value_node.save()
        for activity_group in ar.concept_vo.activity_groups:
            # find related ActivityGroup nodes
            group_root = ActivityGroupRoot.nodes.get_or_none(uid=activity_group)
            group_value = group_root.has_latest_value.get_or_none()

            # Create ActivityValidGroup node
            activity_valid_group = ActivityValidGroup(
                uid=ActivityValidGroup.get_next_free_uid_and_increment_counter()
            )
            activity_valid_group.save()

            # connect ActivityValidGroup and ActivityGroupValue nodes
            activity_valid_group.in_group.connect(group_value)

            # connect ActivitySubGroupValue and ActivityValidGroup nodes
            value_node.has_group.connect(activity_valid_group)

        return value_node

    def _has_data_changed(
        self, ar: ActivitySubGroupAR, value: ActivitySubGroupValue
    ) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)

        activity_valid_groups = value.has_group.all()
        activity_groups_uid = []
        for activity_valid_group in activity_valid_groups:
            activity_group_uid = (
                activity_valid_group.in_group.get().has_version.single().uid
            )
            activity_groups_uid.append(activity_group_uid)
        are_rels_changed = sorted(ar.concept_vo.activity_groups) != sorted(
            activity_groups_uid
        )

        return are_concept_properties_changed or are_rels_changed

    def generic_match_clause_all_versions(self):
        return """
            MATCH (concept_root:ActivitySubGroupRoot)-[version:HAS_VERSION]->(concept_value:ActivitySubGroupValue)
                    -[:HAS_GROUP]->(avg:ActivityValidGroup)-[:IN_GROUP]->(agv:ActivityGroupValue)<-[:HAS_VERSION]-(agr:ActivityGroupRoot)
            """
