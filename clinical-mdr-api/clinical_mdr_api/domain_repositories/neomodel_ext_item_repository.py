from abc import abstractmethod
from typing import Any, TypeVar

from clinical_mdr_api.domain_repositories.models._utils import (
    CustomNodeSet,
    to_relation_trees,
)
from clinical_mdr_api.repositories._utils import (
    ComparisonOperator,
    FilterOperator,
    get_field,
    get_field_path,
    get_order_by_clause,
    merge_q_query_filters,
    transform_filters_into_neomodel,
    validate_page_number_and_page_size,
)

# pylint: disable=invalid-name
_StandardsReturnType = TypeVar("_StandardsReturnType")


class NeomodelExtBaseRepository:
    root_class = type
    return_model = type

    @abstractmethod
    def get_neomodel_extension_query(self) -> CustomNodeSet:
        """
        Method creates a specific neomodel extension query that
        fetches all required relationships to build an object of type
        return_model.

        :return CustomNodeSet:
        """

        raise NotImplementedError

    def find_all(
        self,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
    ) -> tuple[list[_StandardsReturnType], int]:
        q_filters = transform_filters_into_neomodel(
            filter_by=filter_by, model=self.return_model
        )
        q_filters = merge_q_query_filters(q_filters, filter_operator=filter_operator)
        sort_paths = get_order_by_clause(sort_by=sort_by, model=self.return_model)
        page_number = validate_page_number_and_page_size(
            page_number=page_number, page_size=page_size
        )
        start: int = page_number * page_size
        end: int = start + page_size
        nodes = to_relation_trees(
            self.get_neomodel_extension_query()
            .order_by(sort_paths[0] if len(sort_paths) > 0 else "uid")
            .filter(*q_filters)[start:end]
        )
        all_data_model = [
            self.return_model.from_orm(activity_node) for activity_node in nodes
        ]
        if total_count:
            len_query = self.root_class.nodes.filter(*q_filters)
            all_nodes = len(len_query)
        return all_data_model, all_nodes if total_count else 0

    def find_by_uid(self, uid: str) -> _StandardsReturnType | None:
        return to_relation_trees(self.get_neomodel_extension_query().filter(uid=uid))

    def get_distinct_headers(
        self,
        field_name: str,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        result_count: int = 10,
    ) -> list[Any]:
        """
        Fetches possible values for a given field_name, with a limit of result_count.
        It uses generic filtering capability, on top of filtering the field_name with provided search_string.

        Args:
            field_name (str): The name of the field for which to return possible values.
            search_string (str | None, optional): A string to filter the field with. Defaults to "".
            filter_by (dict | None, optional): A dictionary of filters. Defaults to None.
            filter_operator (FilterOperator | None, optional): The operator to use for the filters. Defaults to FilterOperator.AND.
            result_count (int, optional): The maximum number of values to return. Defaults to 10.

        Returns:
        A `sequence` of possible values for the given field_name.
        """
        # Add header field name to filter_by, to filter with a CONTAINS pattern
        if search_string != "":
            if filter_by is None:
                filter_by = {}
            filter_by[field_name] = {
                "v": [search_string],
                "op": ComparisonOperator.CONTAINS,
            }
        q_filters = transform_filters_into_neomodel(
            filter_by=filter_by, model=self.return_model
        )
        q_filters = merge_q_query_filters(q_filters, filter_operator=filter_operator)
        field = get_field(prop=field_name, model=self.return_model)
        field_path = get_field_path(prop=field_name, field=field)

        values = (
            self.root_class.nodes.collect_values(field_path)
            .filter(*q_filters)[:result_count]
            .all()
        )
        return values
