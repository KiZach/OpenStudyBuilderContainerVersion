import json
import re
from copy import copy
from datetime import datetime
from typing import Any, Callable, Generic, Iterable, Self, Type, TypeVar

from pydantic import BaseModel as PydanticBaseModel
from pydantic import conint
from pydantic.generics import GenericModel
from starlette.responses import Response

from clinical_mdr_api.config import STUDY_TIME_UNIT_SUBSET
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.libraries.parameter_term import ParameterTermEntryVO

EXCLUDE_PROPERTY_ATTRIBUTES_FROM_SCHEMA = {
    "remove_from_wildcard",
    "source",
    "exclude_from_orm",
    "is_json",
}


def capitalize_first_letter_if_template_parameter(
    name: str,
    template_plain_name: str,
    parameters: list[ParameterTermEntryVO] | None = None,
) -> str:
    """
    Capitalizes the first letter of `name` if the letter is part of a template parameter which is not a Unit Definition.

    Args:
        name (str): The input string that may have its first letter capitalized.
        template_plain_name (str): The plain name of the template used to determine if capitalization is needed.

    Returns:
        str: `name` with the first letter capitalized if the letter is part of a template parameter which is not a Unit Definition.
        Otherwise, it returns `name` without any changes.
    """
    if (
        template_plain_name.startswith("[")
        and parameters
        and not parameters[0].parameters[0].uid.startswith("UnitDefinition_")
    ):
        idx = name.find("[")
        first_letter = idx + 1
        second_letter = idx + 2

        return (
            name[:first_letter]
            + name[first_letter:second_letter].upper()
            + name[second_letter:]
        )
    return name


def from_duration_object_to_value_and_unit(
    duration: str,
    find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
):
    duration_code = duration[-1].lower()
    # cut off the first 'P' and last unit letter
    duration_value = int(duration[1:-1])

    all_study_time_units, _ = find_all_study_time_units(subset=STUDY_TIME_UNIT_SUBSET)
    # We are using a callback here and this function returns objects as an item list, hence we need to unwrap i
    found_unit = None
    # find unit extracted from iso duration string (duration_code) and find it in the set of all age units
    for unit in all_study_time_units:
        if unit.name[0].lower() == duration_code:
            found_unit = unit
            break
    return duration_value, found_unit


def get_latest_on_datetime_str():
    return f"LATEST on {datetime.utcnow().isoformat()}"


class BaseModel(PydanticBaseModel):
    @classmethod
    def from_orm(cls, obj):
        """
        We override this method to allow flattening on nested models.

        It is now possible to declare a source property on a Field()
        call to specify the location where this method should get a
        field's value from.
        """

        def _extract_part_from_node(node_to_extract, path, extract_from_relationship):
            """
            Traverse specified path in the node_to_extract.
            The possible paths for the traversal are stored in the node _relations dictionary.
            """
            if extract_from_relationship:
                path += "_relationship"
            if not hasattr(node_to_extract, "_relations"):
                return None
            if path not in node_to_extract._relations.keys():
                # it means that the field is Optional and None was set to be a default value
                if field.field_info.default is None:
                    return None
                raise RuntimeError(
                    f"{path} is not present in node relations (did you forget to fetch it?)"
                )
            return node_to_extract._relations[path]

        ret = []
        for name, field in cls.__fields__.items():
            source = field.field_info.extra.get("source")
            if field.field_info.extra.get("exclude_from_orm"):
                continue
            if not source:
                if issubclass(field.type_, BaseModel):
                    # get out of recursion
                    if field.type_ is cls:
                        continue
                    # added copy to not override properties in main obj
                    value = field.type_.from_orm(copy(obj))
                    # if some value of nested model is initialized then set the whole nested object
                    if isinstance(value, list):
                        if value:
                            setattr(obj, name, value)
                        else:
                            setattr(obj, name, [])
                    else:
                        if any(value.dict().values()):
                            setattr(obj, name, value)
                        # if all values of nested model are None set the whole object to None
                        else:
                            setattr(obj, name, None)
                # Quick fix to provide default None value to fields that allow it
                # Not the best place to do this...
                elif field.field_info.default is Ellipsis and not hasattr(obj, name):
                    setattr(obj, name, None)
                continue
            if "." in source or "|" in source:
                orig_source = source
                # split by . that implicates property on node or | that indicates property on the relationship
                parts = re.split(r"[.|]", source)
                source = parts[-1]
                last_traversal = parts[-2]
                node = obj
                parts = parts[:-1]
                for _, part in enumerate(parts):
                    extract_from_relationship = False
                    if part == last_traversal and "|" in orig_source:
                        extract_from_relationship = True
                    # if node is a list of nodes we want to extract property/relationship
                    # from all nodes in list of nodes
                    if isinstance(node, list):
                        return_node = []
                        for item in node:
                            extracted = _extract_part_from_node(
                                node_to_extract=item,
                                path=part,
                                extract_from_relationship=extract_from_relationship,
                            )
                            return_node.extend(extracted)
                        node = return_node
                    else:
                        node = _extract_part_from_node(
                            node_to_extract=node,
                            path=part,
                            extract_from_relationship=extract_from_relationship,
                        )
                    if node is None:
                        break
            else:
                node = obj
            if node is not None:
                # if node is a list we want to
                # extract property from each element of list and return list of property values
                if isinstance(node, list):
                    value = [getattr(n, source) for n in node]
                else:
                    value = getattr(node, source)
            else:
                value = None
            if issubclass(field.type_, BaseModel):
                value = field.type_.from_orm(node._relations[source])
            # if obtained value is a list and field type is not List
            # it means that we are building some list[BaseModel] but its fields are not of list type

            if isinstance(value, list) and not field.sub_fields:
                # if ret array is not instantiated
                # it means that the first property out of the whole list [BaseModel] is being instantiated
                if not ret:
                    for val in value:
                        temp_obj = copy(obj)
                        setattr(temp_obj, name, val)
                        ret.append(temp_obj)
                # if ret exists it means that some properties out of whole list [BaseModel] are already instantiated
                else:
                    for val, item in zip(value, ret):
                        setattr(item, name, val)
            else:
                setattr(obj, name, value)
        # Nothing to return and the value returned by the query
        # is an empty list => return an empty list
        if not ret and isinstance(value, list):
            return []
        # Returning single BaseModel
        if not ret and not isinstance(value, list):
            return super().from_orm(obj)
        # if ret exists it means that the list of BaseModels is being returned
        objs_to_return = []
        for item in ret:
            objs_to_return.append(super().from_orm(item))
        return objs_to_return

    class Config:
        # Configuration applies to all our models #

        @staticmethod
        def schema_extra(schema: dict[str, Any], _: Type) -> None:
            """Exclude some custom internal attributes of Fields (properties) from the schema definitions"""
            for prop in schema.get("properties", {}).values():
                for attr in EXCLUDE_PROPERTY_ATTRIBUTES_FROM_SCHEMA:
                    prop.pop(attr, None)


def snake_to_camel(name):
    name = "".join(word.title() for word in name.split("_"))
    name = f"{name[0].lower()}{name[1:]}"
    return name


def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def snake_case_data(datadict, privates=False):
    return_value = {}
    for key, value in datadict.items():
        if privates:
            new_key = f"_{camel_to_snake(key)}"
        else:
            new_key = camel_to_snake(key)
        return_value[new_key] = value
    return return_value


def camel_case_data(datadict):
    return_value = {}
    for key, value in datadict.items():
        return_value[snake_to_camel(key)] = value
    return return_value


def is_attribute_in_model(attribute: str, model: BaseModel) -> bool:
    """
    Checks if given string is an attribute defined in a model (in the Pydantic sense).
    This works for the model's own attributes and inherited attributes.
    """
    return attribute in model.__fields__.keys()


T = TypeVar("T")


class CustomPage(GenericModel, Generic[T]):
    """
    A generic class used as a return type for paginated queries.

    Attributes:
        items (list[T]): The items returned by the query.
        total (int): The total number of items that match the query.
        page (int): The number of the current page.
        size (int): The maximum number of items per page.
    """

    items: list[T]
    total: conint(ge=0)
    page: conint(ge=0)
    size: conint(ge=0)

    @classmethod
    def create(cls, items: list[T], total: int, page: int, size: int) -> Self:
        return cls(total=total, items=items, page=page, size=size)


class GenericFilteringReturn(GenericModel, Generic[T]):
    """
    A generic class used as a return type for filtered queries.

    Attributes:
        items (list[T]): The items returned by the query.
        total (int): The total number of items that match the query.
    """

    items: list[T]
    total: conint(ge=0)

    @classmethod
    def create(cls, items: list[T], total: int) -> Self:
        return cls(items=items, total=total)


class PrettyJSONResponse(Response):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=4,
            separators=(", ", ": "),
        ).encode("utf-8")
