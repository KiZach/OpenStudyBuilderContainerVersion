import datetime
import re
from typing import Any

import neo4j
from neomodel import (
    AliasProperty,
    StructuredRel,
    match,
    match_q,
    properties,
    relationship_manager,
)
from neomodel.core import db

from clinical_mdr_api import exceptions

LATEST_VERSION_ORDER_BY = """
    toInteger(split({rel}.version, '.')[0]) ASC,
    toInteger(split({rel}.version, '.')[1]) ASC,
    {rel}.end_date ASC,
    {rel}.start_date ASC
    """

path_split_regex = re.compile(r"__|\|")


def convert_to_tz_aware_datetime(value: datetime.datetime):
    """
    Converts a datetime object to a timezone-aware datetime object with UTC timezone.

    Args:
        value (datetime.datetime): The datetime object to convert.

    Returns:
        datetime.datetime: The timezone-aware datetime object with UTC timezone.
    """
    return value.astimezone(tz=datetime.timezone.utc)


def convert_to_datetime(value: neo4j.time.DateTime) -> datetime.datetime | None:
    """
    Converts a DateTime object from the database to a Python datetime object.

    Args:
        value (neo4j.time.DateTime): The DateTime object to convert.

    Returns:
        datetime.datetime: The Python datetime object.
    """
    return value.to_native() if value is not None else None


def format_generic_header_values(values: list[Any]):
    """
    Formats a list of values to match the expected format for generic headers.

    Args:
        values (list[Any]): The list of values to format.

    Returns:
        list: The formatted list of values, with any DateTime objects converted to Python datetime objects.
    """
    if len(values) > 0 and isinstance(values[0], neo4j.time.DateTime):
        return [convert_to_datetime(_val) for _val in values]
    return values


def _initialize_filter_args_variables(cls, key):
    current_class = cls
    current_rel_model = None
    leaf_prop = None
    operator = "="
    is_rel_property = "|" in key
    prop = key

    return current_class, current_rel_model, leaf_prop, operator, is_rel_property, prop


def _process_filter_key(cls, key):
    (
        current_class,
        current_rel_model,
        leaf_prop,
        operator,
        is_rel_property,
        prop,
    ) = _initialize_filter_args_variables(cls, key)

    for part in re.split(path_split_regex, key):
        defined_props = current_class.defined_properties(rels=True)
        # update defined props dictionary with relationship properties if
        # we are filtering by property
        if is_rel_property and current_rel_model:
            defined_props.update(current_rel_model.defined_properties(rels=True))
        if part in defined_props:
            if isinstance(
                defined_props[part], relationship_manager.RelationshipDefinition
            ):
                defined_props[part].lookup_node_class()
                current_class = defined_props[part].definition["node_class"]
                current_rel_model = defined_props[part].definition["model"]
        elif part in match.OPERATOR_TABLE:
            operator = match.OPERATOR_TABLE[part]
            prop, _ = prop.rsplit("__", 1)
            continue
        else:
            raise exceptions.ValidationException(
                f"No such property {part} on {cls.__name__}"
            )
        leaf_prop = part

    if is_rel_property and current_rel_model:
        property_obj = getattr(current_rel_model, leaf_prop)
    else:
        property_obj = getattr(current_class, leaf_prop)

    return property_obj, operator, prop


def _handle_special_operators(property_obj, key, value, operator, prop):
    if operator == match._SPECIAL_OPERATOR_IN:
        if not isinstance(value, tuple) and not isinstance(value, list):
            raise exceptions.ValidationException(
                f"Value must be a tuple or list for IN operation {key}={value}"
            )
        deflated_value = [property_obj.deflate(v) for v in value]
    elif operator == match._SPECIAL_OPERATOR_ISNULL:
        if not isinstance(value, bool):
            raise exceptions.ValidationException(
                f"Value must be a bool for isnull operation on {key}"
            )
        operator = "IS NULL" if value else "IS NOT NULL"
        deflated_value = None
    elif operator in match._REGEX_OPERATOR_TABLE.values():
        deflated_value = property_obj.deflate(value)
        if not isinstance(deflated_value, str):
            raise exceptions.ValidationException(f"Must be a string value for {key}")
        if operator in match._STRING_REGEX_OPERATOR_TABLE.values():
            deflated_value = re.escape(deflated_value)
        deflated_value = operator.format(deflated_value)
        operator = match._SPECIAL_OPERATOR_REGEX
    else:
        deflated_value = property_obj.deflate(value)

    return deflated_value, operator, prop


def _deflate_value(cls, property_obj, key, value, operator, prop):
    if isinstance(property_obj, properties.AliasProperty):
        prop = property_obj.aliased_to()
        deflated_value = getattr(cls, prop).deflate(value)
    else:
        # handle special operators
        deflated_value, operator, prop = _handle_special_operators(
            property_obj, key, value, operator, prop
        )

    return deflated_value, operator, prop


def process_filter_args(cls, kwargs):
    """
    loop through properties in filter parameters check they match class definition
    deflate them and convert into something easy to generate cypher from
    """
    output = {}

    for key, value in kwargs.items():
        property_obj, operator, prop = _process_filter_key(cls, key)
        deflated_value, operator, prop = _deflate_value(
            cls, property_obj, key, value, operator, prop
        )

        # map property to correct property name in the database
        db_property = prop

        output[db_property] = (operator, deflated_value)
    return output


# pylint: disable=unused-argument
def _rel_helper(
    left_hand_stmt: str,
    right_hand_stmt: str,
    relationship_variable: str | None = None,
    relationship_type: str | None = None,
    direction: int = 0,
    relationship_properties: dict | None = None,
) -> str:
    """
    Helper function that generates a Cypher relationship statement.

    Args:
        left_hand_stmt (str): The left hand statement.
        right_hand_stmt (str): The right statement.
        relationship_variable (str | None, optional): The name of the relationship variable. Defaults to None
        relationship_type (str | None, optional): The name of the relationship type. Defaults to None
        direction (int, optional): The direction of the relationship. OUTGOING=1, INCOMING=-1 and EITHER=0. Defaults to 0.
        relationship_properties (dict | None, optional): A dictionary of relationship properties to match. Defaults to None

    Returns:
        str: The Cypher statement with two nodes and their relationship.

    Example:
        >>> _rel_helper(
        ...    left_hand_stmt="odm:OdmItemRoot",
        ...    right_hand_stmt="term:CTTermRoot",
        ...    relationship_variable="rel",
        ...    relationship_type="HAS_CODELIST_TERM",
        ...    direction=1,
        ...    relationship_properties={"mandatory": True}
        ... )
        "(odm:OdmItemRoot)-[rel:`HAS_CODELIST_TERM` {mandatory: True}]->(term:CTTermRoot)"
    """
    if direction == match.OUTGOING:
        relationship_stmt = "-{0}->"
    elif direction == match.INCOMING:
        relationship_stmt = "<-{0}-"
    else:
        relationship_stmt = "-{0}-"

    rel_props = ""

    if relationship_properties:
        key_val_pairs = ", ".join(
            [f"{key}: {value}" for key, value in relationship_properties.items()]
        )
        rel_props = f"{{{key_val_pairs}}}"

    if relationship_type is None:
        relationship_stmt = relationship_stmt.format("")
    # all("*" wildcard) relationship_type
    elif relationship_type == "*":
        relationship_stmt = relationship_stmt.format("[*]")
    else:
        # explicit relationship_type
        relationship_stmt = relationship_stmt.format(
            f"[{relationship_variable if relationship_variable else ''}:`{relationship_type}` {rel_props}]"
        )

    # Make sure not to add parenthesis when they are already present
    # (was not part of the original function)
    if left_hand_stmt[-1] != ")":
        left_hand_stmt = f"({left_hand_stmt})"
    if right_hand_stmt[-1] != ")":
        right_hand_stmt = f"({right_hand_stmt})"

    return f"{left_hand_stmt}{relationship_stmt}{right_hand_stmt}"


class CustomQueryAST(match.QueryAST):
    relation_selectors: dict | None = None
    relation_tree_map: dict | None = None
    return_set: list | None = None
    collect: list | None = None
    distinct: list | None = None

    def __init__(
        self,
        match: list | None = None,  # pylint: disable=redefined-outer-name
        optional_match: list | None = None,
        where: list | None = None,
        with_clause: str | None = None,
        return_clause: str | None = None,
        order_by: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
        result_class: type | None = None,
        lookup: str | None = None,
        additional_return: list | None = None,
        relation_selectors: dict | None = None,
        relation_tree_map: dict | None = None,
        return_set: list | None = None,
        collect: list | None = None,
        distinct: list | None = None,
    ):
        super().__init__(
            match=match,
            optional_match=optional_match,
            where=where,
            with_clause=with_clause,
            return_clause=return_clause,
            order_by=order_by,
            skip=skip,
            limit=limit,
            result_class=result_class,
            lookup=lookup,
            additional_return=additional_return,
        )
        self.relation_selectors: dict = relation_selectors if relation_selectors else {}
        self.relation_tree_map: dict = relation_tree_map if relation_tree_map else {}
        self.return_set: list[Any] = return_set if return_set else []
        self.collect: list[Any] = collect if collect else []
        self.distinct: list[Any] = distinct if distinct else []


class CustomQueryBuilder(match.QueryBuilder):
    def __init__(self, node_set):
        super().__init__(node_set=node_set)
        self._ast = CustomQueryAST()

    def build_ast(self):
        # This is where we deal with required additional relations to
        # fetch, it is not part of the original method.
        for rel_name in self.node_set._relations_to_fetch:
            self.build_traversal_from_path(
                rel_name, self.node_set.source, include_rel_in_return=True
            )
        for rel_name in self.node_set._relations_to_fetch_and_collect:
            self.build_traversal_from_path(
                rel_name,
                self.node_set.source,
                include_nodes_in_return=False,
                collect_variables=True,
            )
        for rel_name in self.node_set._optional_relations_to_fetch:
            self.build_traversal_from_path(
                rel_name,
                self.node_set.source,
                optional_traversal=True,
                include_rel_in_return=True,
            )
        for rel_name in self.node_set._optional_relations_to_fetch_and_collect:
            self.build_traversal_from_path(
                rel_name,
                self.node_set.source,
                include_nodes_in_return=False,
                optional_traversal=True,
                collect_variables=True,
            )
        for relation, data in self.node_set._optional_relation_to_fetch_single.items():
            new_name, sort_clause = data
            (
                root_alias,
                target_label,
                reltype,
                direction,
            ) = self.build_relationship_to_select(
                relation, self.node_set.source, data[0]
            )
            self._add_to_select(
                root_alias, new_name, sort_clause, target_label, reltype, direction
            )
        self.build_source(self.node_set)
        self.build_distinct_clause()

        if hasattr(self.node_set, "skip"):
            self._ast.skip = self.node_set.skip
        if hasattr(self.node_set, "limit"):
            self._ast.limit = self.node_set.limit

        return self

    def build_distinct_clause(self):
        for rel_name in self.node_set._values_to_collect:
            if "__" in rel_name:
                path, prop = rel_name.rsplit("__", 1)
                variable = self.build_traversal_from_path(
                    path,
                    self.node_set.source,
                    optional_traversal=True,
                    include_nodes_in_return=False,
                )
            else:
                variable = self.node_set.source.__label__.lower()
                prop = rel_name
            # clear the return section that is autogenerated by
            self._ast.return_clause = None

            self._add_to_distinct_set(f" DISTINCT {variable}.{prop} AS {variable}")
            self._add_to_return_set(variable)

    def _add_to_return_set(self, name):
        if name not in self._ast.return_set and name != self._ast.return_clause:
            self._ast.return_set.append(name)

    def _add_to_collect_set(self, name):
        if name not in self._ast.collect and name != self._ast.collect:
            self._ast.collect.append(name)

    def _add_to_distinct_set(self, name):
        if name not in self._ast.distinct and name != self._ast.distinct:
            self._ast.distinct.append(name)

    def _add_to_select(
        self, root_alias, variable_name, sort_clause, target_label, rel_type, direction
    ):
        data = {
            "root_alias": root_alias,
            "sort_clause": sort_clause,
            "target_label": target_label,
            "type": rel_type,
            "direction": direction,
            "filter_clause": [],
        }
        self._add_to_return_set(variable_name)
        self._ast.relation_selectors[variable_name] = data

    def build_relationship_to_select(
        self,
        relationship: str,
        source_class,
        new_variable_name,
    ):
        rel = getattr(source_class, relationship)
        lhs_name = source_class.__label__.lower()
        relation_tree_map = self._ast.relation_tree_map
        if new_variable_name not in relation_tree_map:
            relation_tree_map[new_variable_name] = {
                "target": rel.definition["node_class"],
                "children": {},
                "variable_name": new_variable_name,
                "rel_variable_name": new_variable_name,
            }
        direction = (rel.definition["direction"],)
        relation_type = (rel.definition["relation_type"],)
        return (
            lhs_name,
            rel.definition["node_class"].__label__,
            relation_type,
            direction,
        )

    def _parse_right_hand_statement(
        self,
        relationship,
        splitted_path: list[str],
        part: str,
        path_to_the_part: str,
        collect_variables: bool,
        include_nodes_in_return: bool,
    ):
        # if the part is the first part of traversal we don't want double underscore in the beginning
        path_to_the_part += f"{'' if part == splitted_path[0] else '__'}{part}"
        # build source
        if "node_class" not in relationship.definition:
            relationship.lookup_node_class()
        rhs_label = relationship.definition["node_class"].__label__
        rhs_name = f"{rhs_label.lower()}_{path_to_the_part}"

        if collect_variables:
            rhs_name += "_collected"
            self._add_to_collect_set(rhs_name)
        elif include_nodes_in_return:
            self._add_to_return_set(rhs_name)

        # derive rhs_ident after the rhs_name is potentially updated with _collected
        rhs_ident = f"{rhs_name}:{rhs_label}"

        return path_to_the_part, relationship, rhs_ident, rhs_name

    def _parse_left_hand_statement(
        self, src_class, stmt: str, include_nodes_in_return: bool
    ):
        if not stmt:
            lhs_label = src_class.__label__
            lhs_name = lhs_label.lower()
            lhs_ident = f"{lhs_name}:{lhs_label}"
            if include_nodes_in_return:
                self._add_to_return_set(lhs_name)
            # We remove the item generated by build_label() to avoid a useless MATCH statement
            if f"({lhs_ident})" in self._ast.match:
                self._ast.match.remove(f"({lhs_ident})")
        else:
            lhs_ident = stmt

        return lhs_ident

    # The ignored pylint rule is because neomodel's relation argument is here overriden with path
    # This is because we only partially merged this extension back into neomodel
    def build_traversal_from_path(
        self,
        path: str,
        source_class,
        include_nodes_in_return=True,
        include_rel_in_return=False,
        optional_traversal=False,
        is_rel_filtering=False,
        collect_variables=False,
    ):  # pylint: disable=arguments-renamed
        src_class = source_class
        stmt = ""
        relation_tree_map = self._ast.relation_tree_map
        splitted_path = re.split(path_split_regex, path)
        path_to_the_part = ""
        for part in splitted_path:
            relationship = getattr(src_class, part)

            (
                path_to_the_part,
                relationship,
                rhs_ident,
                rhs_name,
            ) = self._parse_right_hand_statement(
                relationship,
                splitted_path,
                part,
                path_to_the_part,
                collect_variables,
                include_nodes_in_return,
            )

            lhs_ident = self._parse_left_hand_statement(
                src_class, stmt, include_nodes_in_return
            )

            rel_ident = self.create_ident()
            if is_rel_filtering:
                rhs_name = rel_ident

            if part not in relation_tree_map:
                relation_tree_map[part] = {
                    "target": relationship.definition["node_class"],
                    "children": {},
                    "variable_name": rhs_name,
                    "rel_variable_name": rel_ident,
                }

            # add relationship variable to the return set
            if collect_variables:
                self._add_to_collect_set(rel_ident)
            if include_rel_in_return:
                self._add_to_return_set(rel_ident)
            stmt = _rel_helper(
                left_hand_stmt=lhs_ident,
                right_hand_stmt=rhs_ident,
                relationship_variable=rel_ident,
                direction=relationship.definition["direction"],
                relationship_type=relationship.definition["relation_type"],
            )
            src_class = relationship.definition["node_class"]
            relation_tree_map = relation_tree_map[part]["children"]
        if not optional_traversal:
            self._ast.match.append(stmt)
        else:
            self._ast.optional_match.append(stmt)
        return rhs_name

    def _build_lookup_clause(self) -> str:
        if self._ast.lookup:
            return self._ast.lookup
        return ""

    def _build_match_clause(self) -> str:
        # Instead of using only one MATCH statement for every relation
        # to follow, we use one MATCH per relation (to avoid cartesian
        # product issues...). This part will need some refinement!
        if self._ast.match:
            return " MATCH " + " MATCH ".join(i for i in self._ast.match)
        return ""

    def _build_optional_match_clause(self) -> str:
        if self._ast.optional_match:
            return " OPTIONAL MATCH " + " OPTIONAL MATCH ".join(
                i for i in self._ast.optional_match
            )
        return ""

    def _build_where_clause(self) -> str:
        if self._ast.where:
            return " WHERE " + " AND ".join(self._ast.where)
        return ""

    def _build_with_clause(self) -> str:
        if self._ast.with_clause:
            return " WITH " + self._ast.with_clause
        return ""

    def _build_distinct_clause(self) -> str:
        if self._ast.distinct:
            if self._ast.with_clause:
                query = ", "
            else:
                query = " WITH "
            query += ", ".join(self._ast.distinct)
            return query
        return ""

    def _build_query_relationships(self) -> str:
        output = ""
        for varname, data in self._ast.relation_selectors.items():
            root_alias = data["root_alias"]
            target_label = data["target_label"]
            order_by = data["sort_clause"].format(rel="r")
            direction = data["direction"]
            filter_clause = data["filter_clause"]
            reltypes = ":".join(data["type"])
            if direction == match.OUTGOING:
                rel_stmt = f"-[r:{reltypes}]->"
            elif direction == match.INCOMING:
                rel_stmt = f"<-[r:{reltypes}]-"
            else:
                rel_stmt = f"-[r:{reltypes}]-"
            filter_clause = [f"{varname}.{filter}" for filter in filter_clause]
            where_stmt = ""
            if len(filter_clause) > 0:
                where_stmt += "WHERE "
                where_stmt += " AND ".join(filter_clause)
            proc = """
            CALL {{
                WITH {0}
                MATCH ({0}){1}(:{2})
                WITH r
                ORDER BY {3}
                WITH collect(r) as rs
                WITH last(rs) as {4}
                {5}
                RETURN {4}
            }}
            """
            output += proc.format(
                root_alias, rel_stmt, target_label, order_by, varname, where_stmt
            )

        return output

    def _build_return_clause(self) -> str:
        query = ""
        if self._ast.return_clause:
            query += self._ast.return_clause
        if self._ast.return_set:
            if self._ast.return_clause:
                query += ", "
            query += ", ".join(self._ast.return_set)
        return query

    def _build_collect_clause(self) -> str:
        if self._ast.collect:
            query = ""
            if self._ast.return_set or self._ast.return_clause:
                query += ", "
            query += ", ".join(
                f"collect(DISTINCT {c}) as {c}" for c in self._ast.collect
            )
            return query
        return ""

    def _build_order_by_clause(self) -> str:
        if self._ast.order_by:
            return " ORDER BY " + ", ".join(self._ast.order_by)
        return ""

    def _build_skip_clause(self) -> str:
        if self._ast.skip:
            return f" SKIP {self._ast.skip}"
        return ""

    def _build_limit_clause(self) -> str:
        if self._ast.limit:
            return f" LIMIT {self._ast.limit}"
        return ""

    def build_query(self):
        query = self._build_lookup_clause()
        query += self._build_match_clause()
        query += self._build_optional_match_clause()
        query += " WITH * "

        query += self._build_where_clause()
        query += self._build_with_clause()
        query += self._build_distinct_clause()

        query += self._build_query_relationships()

        query += " RETURN DISTINCT "
        query += self._build_return_clause()
        query += self._build_collect_clause()
        query += self._build_order_by_clause()
        query += self._build_skip_clause()
        query += self._build_limit_clause()

        return query

    def build_label(self, ident, cls):
        """
        match nodes by a label
        """
        ident_w_label = ident + ":" + cls.__label__
        if not self._ast.return_set or ident not in self._ast.return_set:
            self._ast.match.append(f"({ident_w_label})")
            self._ast.return_clause = ident
            self._ast.result_class = cls
        return ident

    def _parse_path(self, source_class, prop):
        is_rel_filter = "|" in prop
        ident = self.lookup_query_variable(prop)
        if is_rel_filter:
            path, prop = prop.rsplit("|", 1)
        else:
            path, prop = prop.rsplit("__", 1)
        if not ident:
            optional_traversal = False
            if is_rel_filter:
                optional_traversal = True
            ident = self.build_traversal_from_path(
                path,
                source_class,
                include_nodes_in_return=True,
                optional_traversal=optional_traversal,
                is_rel_filtering=is_rel_filter,
            )

        return ident, path, prop

    def _finalize_filter_statement(self, operator, ident, prop, val) -> str:
        if operator in match._UNARY_OPERATORS:
            # unary operators do not have a parameter
            statement = f"{ident}.{prop} {operator}"
        else:
            place_holder = self._register_place_holder(ident + "_" + prop)
            statement = f"{ident}.{prop} {operator} ${place_holder}"
            self._query_params[place_holder] = val

        return statement

    def _set_relationship_filters(self, path, prop, val) -> None:
        for key, data in self.node_set._optional_relation_to_fetch_single.items():
            new_name, _ = data
            if key == path:
                self._ast.relation_selectors[new_name]["filter_clause"].append(
                    f"{prop}='{val}'"
                )

    def _build_filter_statements(self, ident, filters, target, source_class):
        for prop, op_and_val in filters.items():
            path = None
            if "__" in prop or "|" in prop:
                ident, path, prop = self._parse_path(source_class, prop)
            operator, val = op_and_val

            self._set_relationship_filters(path, prop, val)
            statement = self._finalize_filter_statement(operator, ident, prop, val)
            target.append(statement)

    def _parse_q_filters(self, ident, q, source_class):
        target = []
        for child in q.children:
            if isinstance(child, match_q.QBase):
                q_childs = self._parse_q_filters(ident, child, source_class)
                if child.connector == match_q.Q.OR:
                    q_childs = "(" + q_childs + ")"
                target.append(q_childs)
            else:
                kwargs = {child[0]: child[1]}

                filters = process_filter_args(source_class, kwargs)
                self._build_filter_statements(ident, filters, target, source_class)
        ret = f" {q.connector} ".join(target)
        if q.negated:
            ret = f"NOT ({ret})"
        return ret

    def _execute(self, lazy=False, dict_output=False):
        """
        Override of the original method.
        Mostly a copy/paste except we change the results format.
        """
        if lazy:
            # inject id() into return or return_set
            if self._ast.return_clause:
                self._ast.return_clause = (
                    f"{db.get_id_method()}({self._ast.return_clause})"
                )
            else:
                self._ast.return_set = [
                    f"{db.get_id_method()}({item})" for item in self._ast.return_set
                ]
        query = self.build_query()

        results, prop_names = db.cypher_query(
            query, self._query_params, resolve_objects=True
        )

        if dict_output:
            result_dict = []
            for item in results:
                result_dict.append(dict(zip(prop_names, item)))
            return result_dict
        if results and len(results[0]) == 1:
            return [n[0] for n in results]
        return results

    def _count(self):
        # we need to count the variable of the node_set.source type
        main_variable = self.node_set.source.__label__.lower()
        self._ast.return_clause = f"count(DISTINCT {main_variable})"
        self._ast.return_set = None
        # drop order_by, results in an invalid query
        self._ast.order_by = None
        query = self.build_query()
        results, _ = db.cypher_query(query, self._query_params)
        if len(results) > 0 and len(results[0]) > 0:
            return int(results[0][0])
        return 0

    def build_order_by(self, ident, source):
        if "?" in source.order_by_elements:
            self._ast.with_clause = f"{ident}, rand() as r"
            self._ast.order_by = "r"
        else:
            order_by = []
            for elm in source.order_by_elements:
                is_rel_property = "|" in elm
                if "__" not in elm and not is_rel_property:
                    order_by.append(f"{ident}.{elm}")
                else:
                    prop = (
                        elm.split("__")[-1]
                        if not is_rel_property
                        else elm.split("|")[-1]
                    )
                    order_by_clause = self.lookup_query_variable(elm)
                    order_by.append(f"{order_by_clause}.{prop}")
            self._ast.order_by = order_by

    def lookup_query_variable(self, prop):
        relation_tree_map = self._ast.relation_tree_map
        if not relation_tree_map:
            return None
        is_rel_property = "|" in prop
        traversals = re.split(path_split_regex, prop)
        if len(traversals) == 0:
            raise exceptions.ValidationException("Can only lookup traversal variables")
        if traversals[0] not in relation_tree_map:
            return None
        relation_tree_map = relation_tree_map[traversals[0]]
        variable_to_return = None
        last_property = traversals[-1]
        for part in traversals[1:]:
            if part in relation_tree_map["children"]:
                relation_tree_map = relation_tree_map["children"][part]
            elif part == last_property:
                # if last part of prop is the last traversal
                # we are safe to lookup the variable from the query
                if is_rel_property:
                    variable_to_return = f"{relation_tree_map['rel_variable_name']}"
                else:
                    variable_to_return = f"{relation_tree_map['variable_name']}"
            else:
                break
        return variable_to_return


class CustomNodeSet(match.NodeSet):
    query_cls = CustomQueryBuilder

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._relations_to_fetch = []
        self._relations_to_fetch_and_collect = []
        self._optional_relations_to_fetch = []
        self._optional_relations_to_fetch_and_collect = []
        self._values_to_collect = []
        self.order_by_elements = []
        self._optional_relation_to_fetch_single = {}

    def all(self, lazy=False, dict_output=False):
        """
        Return all nodes belonging to the set
        :param lazy: False by default, specify True to get nodes with id only without the parameters.
        :param dict_output: False by default, specify True to get nodes with the corresponding query variable names
        :return: list of nodes
        :rtype: list
        """
        return self.query_cls(self).build_ast()._execute(lazy, dict_output=dict_output)

    def fetch_relations(self, *relation_names):
        """Custom method to specify a set of extra relations to return."""
        self._relations_to_fetch = relation_names
        return self

    def fetch_optional_relations(self, *relation_names):
        """Custom method to specify a set of extra optional relations to return."""
        self._optional_relations_to_fetch = relation_names
        return self

    def fetch_optional_relations_and_collect(self, *relation_names):
        """Custom method to specify a set of extra optional relations to return in collection."""
        self._optional_relations_to_fetch_and_collect = relation_names
        return self

    def collect_values(self, *relations_names):
        """Custom method to specify a set of extra optional relations to return in collection.
        The collection will be the only variable returned"""
        self._values_to_collect = relations_names
        return self

    def fetch_optional_single_relation_of_type(self, relation_data):
        """Custom method to specify an optional relation to return.
        Use this to fetch a single relationship when several may exist for the type.
        The input parameter is a dict:
        {
            $relationship$: ($output_variable_name$, $sort_statement$),
        }
        The method will get all relationships of the given type, sort them according to the sort statement,
        and return the last one in the sorted result as output_variable_name.
        The sort statement is a string with a placeholder, {rel}, where the relationship alias will be inserted.
        For example, the statement "{rel}.amount" will get expanded to "SORT BY r5.amount",
        where the alias "r5" is autogenerated.
        Full example:
        {
            "knows": ("oldest_friendship", "{rel}.since DESC"),
            "hnows": ("newest_friendship", "{rel}.since ASC"),
        }
        Here nodes represent persons, that are connected by KNOWS relationships.
        The KNOWS relationship has a property "since".
        We select the oldest and newest friendships by sorting on "since" in descending and ascending order.
        """
        self._optional_relation_to_fetch_single.update(relation_data)
        return self

    def _update_order_by_elements(self, props):
        for prop in props:
            prop = prop.strip()
            if prop.startswith("-"):
                prop = prop[1:]
                desc = True
            else:
                desc = False

            if prop in self.source_class.defined_properties(rels=False):
                property_obj = getattr(self.source_class, prop)
                if isinstance(property_obj, AliasProperty):
                    prop = property_obj.aliased_to()

            self.order_by_elements.append(prop + (" DESC" if desc else ""))

    def order_by(self, *props):
        """
        Order by properties. Prepend with minus to do descending. Pass None to
        remove ordering.
        """
        should_remove = len(props) == 1 and props[0] is None
        if not hasattr(self, "order_by_elements") or should_remove:
            self.order_by_elements = []
            if should_remove:
                return self
        if "?" in props:
            self.order_by_elements.append("?")
        else:
            self._update_order_by_elements(props)
        return self


def _update_root_node_relations(
    root_node, node, name, nodeset, other_nodes, relation_children
):
    if isinstance(node, list):
        if len(node) > 0 and isinstance(node[0], StructuredRel):
            name += "_relationship"
        root_node._relations[name] = []
        for item in node:
            root_node._relations[name].append(
                _to_relation_tree(nodeset, item, other_nodes, relation_children)
            )
    else:
        root_node._relations[name] = _to_relation_tree(
            nodeset, node, other_nodes, relation_children
        )

    return root_node, name


def _to_relation_tree(nodeset, root_node, other_nodes, relation_tree_map):
    """Recursive method to build root_node's relation tree from relation_tree_map."""
    root_node._relations = {}
    for name, relation_def in relation_tree_map.items():
        for var_name, node in other_nodes.items():
            if (
                var_name
                in [
                    relation_def["variable_name"],
                    relation_def["rel_variable_name"],
                ]
                and node is not None
            ):
                if isinstance(node, StructuredRel):
                    name += "_relationship"
                root_node, name = _update_root_node_relations(
                    root_node,
                    node,
                    name,
                    nodeset,
                    other_nodes,
                    relation_def["children"],
                )
    return root_node


def to_relation_trees(nodeset):
    """
    Convert every result contained in this node set to a relation tree.

    By default, we receive results from neomodel as a list of
    nodes without the hierarchy. This method tries to rebuild this
    hierarchy without overidding anything in the node, that's why
    we use a dedicated property to store node's relations.

    NOTE: there is still an issue with this method, it won't work
    properly if two nodes of the same type are returned because it
    will mix them. This is mostly because we don't have a simple
    way to identify which node corresponds to which relation...

    """
    results = ListDistinct([])
    qbuilder = nodeset.query_cls(nodeset).build_ast()
    all_nodes = qbuilder._execute(dict_output=True)
    other_nodes = {}
    root_node = None
    relation_tree_map = qbuilder._ast.relation_tree_map
    for result_dict in all_nodes:
        for name, node in result_dict.items():
            if node.__class__ is nodeset.source and "_" not in name:
                root_node = node
            else:
                if isinstance(node, list) and isinstance(node[0], list):
                    other_nodes[name] = node[0]
                else:
                    other_nodes[name] = node
        results.append(
            _to_relation_tree(nodeset, root_node, other_nodes, relation_tree_map)
        )
    return results


def classproperty(func) -> "classproperty.ClassPropertyFunction":
    class ClassPropertyFunction:
        def __init__(self, getter):
            self.getter = getter

        def __get__(self, obj, class_type):
            return self.getter(class_type)

    return ClassPropertyFunction(func)


class ListDistinct(list):
    def distinct(self):
        uniques = []
        for ith in self:
            if ith not in uniques:
                uniques.extend([ith])
        return uniques
