from abc import ABC
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityGroupRoot,
    ActivityRoot,
    ActivitySubGroupRoot,
)
from clinical_mdr_api.domain_repositories.models.concepts import UnitDefinitionRoot
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.odm import (
    OdmFormRoot,
    OdmItemGroupRoot,
    OdmItemRoot,
    OdmVendorAttributeRoot,
    OdmVendorElementRoot,
)
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.utils import RelationType
from clinical_mdr_api.exceptions import BusinessLogicException
from clinical_mdr_api.models.concepts.odms.odm_common_models import (
    OdmElementWithParentUid,
)
from clinical_mdr_api.repositories._utils import (
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
    sb_clear_cache,
)


class OdmGenericRepository(ConceptGenericRepository[_AggregateRootType], ABC):
    def find_all(
        self,
        library: str | None = None,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        return_all_versions: bool = False,
        only_specific_status: str = ObjectStatus.LATEST.name,
        **kwargs,
    ) -> tuple[list[_AggregateRootType], int]:
        """
        Method runs a cypher query to fetch all needed data to create objects of type AggregateRootType.
        In the case of the following repository it will be some Concept aggregates.

        It uses cypher instead of neomodel as neomodel approach triggered some performance issues, because it is needed
        to traverse many relationships to fetch all needed data and each traversal is separate database call when using
        neomodel.
        :param library:
        :param sort_by:
        :param page_number:
        :param page_size:
        :param filter_by:
        :param filter_operator:
        :param total_count:
        :param return_all_versions:
        :param only_specific_status:
        :return GenericFilteringReturn[_AggregateRootType]:
        """
        match_clause = self.generic_match_clause(only_specific_status)

        filter_statements, filter_query_parameters = self.create_query_filter_statement(
            library=library, **kwargs
        )
        match_clause += filter_statements

        alias_clause = self.generic_alias_clause() + self.specific_alias_clause(
            only_specific_status
        )
        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict(elements=filter_by),
            filter_operator=filter_operator,
            total_count=total_count,
            return_model=self.return_model,
        )

        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = query.execute()
        extracted_items = self._retrieve_concepts_from_cypher_res(
            result_array, attributes_names
        )

        count_result, _ = db.cypher_query(
            query=query.count_query, params=query.parameters
        )
        total_amount = (
            count_result[0][0] if len(count_result) > 0 and total_count else 0
        )

        return extracted_items, total_amount

    @classmethod
    def _get_origin_and_relation_node(
        cls, uid: str, relation_uid: str | None, relationship_type: RelationType
    ):
        root_class_node = cls.root_class.nodes.get_or_none(uid=uid)

        relation_mapping = {
            RelationType.ACTIVITY_GROUP: (ActivityGroupRoot, "has_activity_group"),
            RelationType.ACTIVITY_SUB_GROUP: (
                ActivitySubGroupRoot,
                "has_activity_subgroup",
            ),
            RelationType.ACTIVITY: (ActivityRoot, "has_activity"),
            RelationType.ITEM_GROUP: (OdmItemGroupRoot, "item_group_ref"),
            RelationType.ITEM: (OdmItemRoot, "item_ref"),
            RelationType.FORM: (OdmFormRoot, "form_ref"),
            RelationType.TERM: (CTTermRoot, "has_codelist_term"),
            RelationType.UNIT_DEFINITION: (UnitDefinitionRoot, "has_unit_definition"),
            RelationType.VENDOR_ELEMENT: (OdmVendorElementRoot, "has_vendor_element"),
            RelationType.VENDOR_ATTRIBUTE: (
                OdmVendorAttributeRoot,
                "has_vendor_attribute",
            ),
            RelationType.VENDOR_ELEMENT_ATTRIBUTE: (
                OdmVendorAttributeRoot,
                "has_vendor_element_attribute",
            ),
        }

        if relationship_type not in relation_mapping:
            raise BusinessLogicException("Invalid relation type.")

        relation_node_cls, origin_label = relation_mapping[relationship_type]
        relation_node = relation_node_cls.nodes.get_or_none(uid=relation_uid)

        if not relation_node and relation_uid:
            raise BusinessLogicException(
                f"The object with uid ({relation_uid}) does not exist."
            )

        return getattr(root_class_node, origin_label), relation_node

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def add_relation(
        self,
        uid: str,
        relation_uid: str,
        relationship_type: RelationType,
        parameters: dict | None = None,
    ) -> None:
        origin, relation_node = self.__class__._get_origin_and_relation_node(
            uid, relation_uid, relationship_type
        )

        origin.disconnect(relation_node)

        if isinstance(parameters, dict):
            origin.connect(relation_node, parameters)
        else:
            origin.connect(relation_node)

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def remove_relation(
        self,
        uid: str,
        relation_uid: str | None,
        relationship_type: RelationType,
        disconnect_all: bool = False,
    ) -> None:
        origin, relation_node = self.__class__._get_origin_and_relation_node(
            uid, relation_uid, relationship_type
        )

        if disconnect_all:
            origin.disconnect_all()
        else:
            origin.disconnect(relation_node)

    def has_active_relationships(
        self, uid: str, relationships: list[Any], all_exist: bool = False
    ) -> bool:
        """
        Checks if the node has active relationships.

        :param uid: The uid of the node to check relationships on.
        :param relationships: A list of relationship names to check the existence of.
        :param all_exist: If True, all provided relationships must exist on the node. If False, at least one of the provided relationships must exist.
        :return: Returns True, if the relationships exist, otherwise False.
        """
        root = self.root_class.nodes.get_or_none(uid=uid)

        try:
            if not all_exist:
                for relationship in relationships:
                    if getattr(root, relationship):
                        return True

                return False
            for relationship in relationships:
                if not getattr(root, relationship):
                    return False

            return True
        except AttributeError as exc:
            raise AttributeError(f"{relationship} relationship was not found.") from exc

    def get_active_relationships(
        self, uid: str, relationships: list[Any]
    ) -> dict[str, list[str]]:
        """
        Returns a key-pair value of target node's name and a list of uids of nodes connected to source node.

        :param uid: The uid of the source node to check relationships on.
        :param relationships: A list of relationship names to check the existence of.
        :return: Returns a dict.
        """
        source_node = self.root_class.nodes.get_or_none(uid=uid)

        try:
            rs: dict[str, list[str]] = {}
            for relationship in relationships:
                rel = getattr(source_node, relationship)
                if rel:
                    for target_node in rel.all():
                        target_node_without_suffix = target_node.__label__.removesuffix(
                            "Root"
                        )
                        if target_node_without_suffix not in rs:
                            rs[target_node_without_suffix] = [target_node.uid]
                        else:
                            rs[target_node_without_suffix].append(target_node.uid)
            return rs
        except AttributeError as exc:
            raise AttributeError(f"{relationship} relationship was not found.") from exc

    def get_if_has_relationship(self, relationship: str):
        """
        Returns a list of ODM Element uid and name with their parent uids.
        """
        roots = self.root_class.nodes.has(**{relationship: True})

        rs = []
        for root in roots:
            parents = getattr(root, relationship).all()

            rs.append(
                OdmElementWithParentUid(
                    uid=root.uid,
                    name=root.has_latest_value.get_or_none().name,
                    parent_uids=[parent.uid for parent in parents],
                )
            )

        return rs
