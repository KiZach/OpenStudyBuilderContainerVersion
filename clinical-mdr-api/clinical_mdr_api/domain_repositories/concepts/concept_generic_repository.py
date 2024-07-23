from abc import ABC, abstractmethod
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.concepts.utils import (
    list_concept_wildcard_properties,
)
from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    format_generic_header_values,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameterTermRoot,
)
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase
from clinical_mdr_api.repositories._utils import (
    ComparisonOperator,
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
    sb_clear_cache,
)


class ConceptGenericRepository(LibraryItemRepositoryImplBase[_AggregateRootType], ABC):
    root_class = type
    value_class = type
    return_model = type
    filter_query_parameters = {}

    @abstractmethod
    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> _AggregateRootType:
        raise NotImplementedError

    @abstractmethod
    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library | None,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> _AggregateRootType:
        raise NotImplementedError

    @abstractmethod
    def specific_alias_clause(
        self, only_specific_status: str = ObjectStatus.LATEST.name
    ) -> str:
        """
        Methods is overridden in the ConceptGenericRepository subclasses
        and it contains matches and traversals specific for domain object represented by subclass repository.
        :return str:
        """

    def specific_header_match_clause(self) -> str | None:
        return None

    def _create_new_value_node(self, ar: _AggregateRootType) -> VersionValue:
        return self.value_class(
            nci_concept_id=getattr(ar.concept_vo, "nci_concept_id", None),
            name=ar.concept_vo.name,
            name_sentence_case=ar.concept_vo.name_sentence_case,
            definition=ar.concept_vo.definition,
            abbreviation=ar.concept_vo.abbreviation,
            external_id=getattr(ar.concept_vo, "external_id", None),
        )

    def _has_data_changed(self, ar: _AggregateRootType, value: VersionValue) -> bool:
        return (
            ar.concept_vo.name != value.name
            or getattr(ar.concept_vo, "nci_concept_id", None)
            != getattr(value, "nci_concept_id", None)
            or ar.concept_vo.name_sentence_case != value.name_sentence_case
            or ar.concept_vo.definition != value.definition
            or ar.concept_vo.abbreviation != value.abbreviation
            or getattr(ar.concept_vo, "external_id", None)
            != getattr(value, "external_id", None)
        )

    def generate_uid(self) -> str:
        return self.root_class.get_next_free_uid_and_increment_counter()

    def generic_match_clause(
        self, only_specific_status: str = ObjectStatus.LATEST.name
    ):
        concept_label = self.root_class.__label__
        concept_value_label = self.value_class.__label__
        return f"""CYPHER runtime=slotted MATCH (concept_root:{concept_label})-[:{only_specific_status}]->(concept_value:{concept_value_label})"""

    def generic_alias_clause(self):
        return """
            DISTINCT concept_root, concept_value,
            head([(library)-[:CONTAINS_CONCEPT]->(concept_root) | library]) AS library
            CALL {
                WITH concept_root, concept_value
                MATCH (concept_root)-[hv:HAS_VERSION]-(concept_value)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.end_date ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS version_rel
            }
            WITH
                concept_root,
                concept_root.uid AS uid,
                concept_value as concept_value,
                library.name AS library_name,
                library.is_editable AS is_library_editable,
                version_rel
            WITH
                uid,
                concept_root,
                concept_value.nci_concept_id AS nci_concept_id,
                concept_value.name AS name,
                concept_value.name_sentence_case AS name_sentence_case,
                concept_value.external_id AS external_id,
                concept_value.definition AS definition,
                concept_value.abbreviation AS abbreviation,
                CASE WHEN concept_value:TemplateParameterTermValue THEN true ELSE false END AS template_parameter,
                library_name,
                is_library_editable,
                version_rel.start_date AS start_date,
                version_rel.end_date AS end_date,
                version_rel.status AS status,
                version_rel.version AS version,
                version_rel.change_description AS change_description,
                version_rel.user_initials AS user_initials,
                concept_value
        """

    def generic_alias_clause_all_versions(self):
        return """
            DISTINCT concept_root, concept_value,
            head([(library)-[:CONTAINS_CONCEPT]->(concept_root) | library]) AS library
            CALL {
                WITH concept_root, concept_value
                MATCH (concept_root)-[hv:HAS_VERSION]-(concept_value)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.end_date ASC,
                    hv.start_date ASC
                RETURN hv AS version_rel
            }
            WITH
                concept_root,
                concept_root.uid AS uid,
                concept_value as concept_value,
                library.name AS library_name,
                library.is_editable AS is_library_editable,
                version_rel
            WITH
                uid,
                concept_root,
                concept_value.nci_concept_id AS nci_concept_id,
                concept_value.name AS name,
                concept_value.name_sentence_case AS name_sentence_case,
                concept_value.external_id AS external_id,
                concept_value.definition AS definition,
                concept_value.abbreviation AS abbreviation,
                CASE WHEN concept_value:TemplateParameterTermValue THEN true ELSE false END AS template_parameter,
                library_name,
                is_library_editable,
                version_rel.start_date AS start_date,
                version_rel.end_date AS end_date,
                version_rel.status AS status,
                version_rel.version AS version,
                version_rel.change_description AS change_description,
                version_rel.user_initials AS user_initials,
                concept_value
        """

    def generic_match_clause_all_versions(self):
        return self.generic_match_clause()

    def create_query_filter_statement(
        self, library: str | None = None, **kwargs
    ) -> tuple[str, dict]:
        # pylint: disable=unused-argument
        filter_parameters = []
        filter_query_parameters = {}
        if library:
            filter_by_library_name = """
            head([(library:Library)-[:CONTAINS_CONCEPT]->(concept_root) | library.name])=$library_name"""
            filter_parameters.append(filter_by_library_name)
            filter_query_parameters["library_name"] = library
        filter_statements = " AND ".join(filter_parameters)
        filter_statements = (
            "WHERE " + filter_statements if len(filter_statements) > 0 else ""
        )
        return filter_statements, filter_query_parameters

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
        :return GenericFilteringReturn[_AggregateRootType]:
        """
        match_clause = (
            self.generic_match_clause()
            if not return_all_versions
            else self.generic_match_clause_all_versions()
        )

        filter_statements, filter_query_parameters = self.create_query_filter_statement(
            library=library, **kwargs
        )
        self.filter_query_parameters = filter_query_parameters
        match_clause += filter_statements

        alias_clause = (
            self.generic_alias_clause()
            if not return_all_versions
            else self.generic_alias_clause_all_versions()
        ) + self.specific_alias_clause()
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

    def _retrieve_concepts_from_cypher_res(
        self, result_array, attribute_names
    ) -> list[_AggregateRootType]:
        """
        Method maps the result of the cypher query into real aggregate objects.
        :param result_array:
        :param attribute_names:
        :return Iterable[_AggregateRootType]:
        """
        concept_ars = []
        for concept in result_array:
            concept_dictionary = {}
            for concept_property, attribute_name in zip(concept, attribute_names):
                concept_dictionary[attribute_name] = concept_property
            concept_ars.append(
                self._create_aggregate_root_instance_from_cypher_result(
                    concept_dictionary
                )
            )

        return concept_ars

    def get_distinct_headers(
        self,
        field_name: str,
        search_string: str | None = "",
        library: str | None = None,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        result_count: int = 10,
        **kwargs,
    ) -> list[Any]:
        # pylint: disable=unused-argument
        """
        Method runs a cypher query to fetch possible values for a given field_name, with a limit of result_count.
        It uses generic filtering capability, on top of filtering the field_name with provided search_string.

        :param field_name: Field name for which to return possible values
        :param search_string
        :param library:
        :param filter_by:
        :param filter_operator: Same as for generic filtering
        :param result_count: Max number of values to return. Default 10
        :return list[Any]:
        """
        # Match clause
        match_clause = self.generic_match_clause()
        if self.specific_header_match_clause():
            match_clause += self.specific_header_match_clause()

        filter_statements, filter_query_parameters = self.create_query_filter_statement(
            library=library, **kwargs
        )
        match_clause += filter_statements

        # Aliases clause
        alias_clause = self.generic_alias_clause() + self.specific_alias_clause()

        # Add header field name to filter_by, to filter with a CONTAINS pattern
        if search_string != "":
            if filter_by is None:
                filter_by = {}
            filter_by[field_name] = {
                "v": [search_string],
                "op": ComparisonOperator.CONTAINS,
            }

        # Use Cypher query class to use reusable helper methods
        query = CypherQueryBuilder(
            filter_by=FilterDict(elements=filter_by),
            filter_operator=filter_operator,
            match_clause=match_clause,
            alias_clause=alias_clause,
            return_model=self.return_model,
            wildcard_properties_list=list_concept_wildcard_properties(
                self.return_model
            ),
        )

        query.parameters.update(filter_query_parameters)

        query.full_query = query.build_header_query(
            header_alias=field_name, result_count=result_count
        )
        result_array, _ = query.execute()

        return (
            format_generic_header_values(result_array[0][0])
            if len(result_array) > 0
            else []
        )

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def save(self, item: _AggregateRootType) -> None:
        if item.uid is not None and item.repository_closure_data is None:
            self._create(item)
        elif item.uid is not None and not item.is_deleted:
            self._update(item)
        elif item.is_deleted:
            assert item.uid is not None
            self._soft_delete(item.uid)

    def _soft_delete(self, uid: str) -> None:
        label = self.root_class.__label__
        db.cypher_query(
            f"""
            MATCH (otr:{label} {{uid: $uid}})-[latest_draft:LATEST_DRAFT|LATEST_RETIRED]->(otv)
            WHERE NOT (otr)-[:HAS_VERSION {{version:'Final'}}]->()
            SET otr:Deleted{label}
            WITH otr
            REMOVE otr:{label}
            WITH otr
            MATCH (otr)-[v:HAS_VERSION]->()
            WHERE v.end_date IS NULL
            SET v.end_date = datetime(apoc.date.toISO8601(datetime().epochSeconds, 's'))
            """,
            {"uid": uid},
        )

    def final_concept_exists(self, uid: str) -> bool:
        query = f"""
            MATCH (concept_root:{self.root_class.__label__} {{uid: $uid}})-[:LATEST_FINAL]->(concept_value)
            RETURN concept_root
            """
        result, _ = db.cypher_query(query, {"uid": uid})
        return len(result) > 0 and len(result[0]) > 0

    def latest_concept_in_library_exists_by_name(
        self, library_name: str, concept_name: str
    ) -> bool:
        query = f"""
            MATCH (l:Library {{name: $library_name}})-[:CONTAINS_CONCEPT]->
                    (concept_root:{self.root_class.__label__})-[:LATEST]->
                    (concept_value:{self.value_class.__label__}{{name: $concept_name}})
            RETURN concept_root
            """
        result, _ = db.cypher_query(
            query, {"concept_name": concept_name, "library_name": library_name}
        )
        return len(result) > 0 and len(result[0]) > 0

    def _is_new_version_necessary(self, ar: ConceptARBase, value: VersionValue) -> bool:
        return self._has_data_changed(ar, value)

    def _get_or_create_value(
        self, root: VersionRoot, ar: ConceptARBase
    ) -> VersionValue:
        for itm in root.has_version.all():
            if not self._has_data_changed(ar, itm):
                return itm
        latest_draft = root.latest_draft.get_or_none()
        if latest_draft and not self._has_data_changed(ar, latest_draft):
            return latest_draft
        latest_final = root.latest_final.get_or_none()
        if latest_final and not self._has_data_changed(ar, latest_final):
            return latest_final
        latest_retired = root.latest_retired.get_or_none()
        if latest_retired and not self._has_data_changed(ar, latest_retired):
            return latest_retired
        new_value = self._create_new_value_node(ar=ar)
        self._db_save_node(new_value)
        return new_value

    @classmethod
    def is_concept_node_a_tp(cls, concept_node: VersionValue) -> bool:
        labels = concept_node.labels()
        for label in labels:
            if "TemplateParameterTermValue" in label:
                return True
        return False

    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: VersionRoot,
        value: VersionValue,
    ) -> None:
        if versioned_object.concept_vo.is_template_parameter:
            # neomodel can't add custom label to already existing node, we have to manage that by executing cypher query
            template_parameter_name = self.root_class.__name__.removesuffix("Root")
            # we want to initiate a Comparator TemplateParameter type with the same template parameter terms as we do
            # for Compound TemplateParameter
            if template_parameter_name == "Compound":
                template_parameter_names = [template_parameter_name, "Comparator"]
            else:
                template_parameter_names = [template_parameter_name]
            for template_param_name in template_parameter_names:
                query = """
                    MATCH (template_parameter:TemplateParameter {name:$template_parameter_name})
                    MATCH (concept_root:ConceptRoot {uid: $uid})-[:LATEST]->(concept_value)
                    SET concept_root:TemplateParameterTermRoot
                    SET concept_value:TemplateParameterTermValue
                    MERGE (template_parameter)-[:HAS_PARAMETER_TERM]->(concept_root)
                """
                db.cypher_query(
                    query,
                    {
                        "uid": versioned_object.uid,
                        "template_parameter_name": template_param_name,
                    },
                )
                TemplateParameterTermRoot.generate_node_uids_if_not_present()
