import abc
from datetime import datetime
from typing import TypeVar

from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityGroupRoot,
    ActivityRoot,
    ActivitySubGroupRoot,
)
from clinical_mdr_api.domain_repositories.models.concepts import (
    NumericValue,
    NumericValueRoot,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.dictionary import DictionaryTermRoot
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.syntax import (
    SyntaxTemplateRoot,
    SyntaxTemplateValue,
)
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    ParameterTemplateRoot,
    TemplateParameterComplexRoot,
    TemplateParameterComplexValue,
    TemplateParameterTermRoot,
)
from clinical_mdr_api.domains.libraries.parameter_term import (
    ComplexParameterTerm,
    NumericParameterTermVO,
    ParameterTermEntryVO,
    SimpleParameterTermVO,
)
from clinical_mdr_api.domains.syntax_templates.template import (
    InstantiationCountsVO,
    TemplateAggregateRootBase,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemStatus,
)
from clinical_mdr_api.exceptions import NotFoundException
from clinical_mdr_api.repositories._utils import FilterOperator

_AggregateRootType = TypeVar("_AggregateRootType", bound=LibraryItemAggregateRootBase)


class GenericSyntaxRepository(
    LibraryItemRepositoryImplBase[_AggregateRootType], abc.ABC
):
    def find_by_uid_2(
        self,
        uid: str,
        *,
        version: str | None = None,
        status: LibraryItemStatus | None = None,
        at_specific_date: datetime | None = None,
        for_update: bool = False,
        return_study_count: bool | None = False,
        return_instantiation_counts: bool = False,
    ):
        "Use find_by_uid instead"

    def find_all(
        self,
        *,
        status: LibraryItemStatus | None = None,
        library_name: str | None = None,
        return_study_count: bool | None = False,
    ):
        "Use get_all instead"

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        study_count: int = 0,
        counts: InstantiationCountsVO | None = None,
    ) -> _AggregateRootType:
        "Use _create_ar instead"

    @abc.abstractmethod
    def _create_ar(
        self,
        root: SyntaxTemplateRoot,
        library: Library,
        relationship: VersionRelationship,
        value: SyntaxTemplateValue,
        study_count: int = 0,
        **kwargs,
    ) -> TemplateAggregateRootBase:
        raise NotImplementedError

    def find_by_uid(
        self,
        uid: str,
        for_update=False,
        *,
        library_name: str | None = None,
        status: LibraryItemStatus | None = None,
        version: str | None = None,
        return_study_count: bool | None = False,
        for_audit_trail: bool = False,
    ) -> _AggregateRootType | list[_AggregateRootType]:
        return self.find_by_uid_optimized(
            uid=uid,
            for_update=for_update,
            library_name=library_name,
            status=status,
            version=version,
            return_study_count=return_study_count,
            for_audit_trail=for_audit_trail,
        )

    def get_all(
        self,
        *,
        status: LibraryItemStatus | None = None,
        library_name: str | None = None,
        return_study_count: bool | None = False,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        for_audit_trail: bool = False,
    ) -> tuple[list, int]:
        return self.get_all_optimized(
            status=status,
            library_name=library_name,
            return_study_count=return_study_count,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=filter_by,
            filter_operator=filter_operator,
            total_count=total_count,
            for_audit_trail=for_audit_trail,
        )

    def get_headers(
        self,
        *,
        field_name: str,
        status: LibraryItemStatus | None = None,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        result_count: int = 10,
    ):
        return self.get_headers_optimized(
            field_name=field_name,
            status=status,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            result_count=result_count,
        )

    def _maintain_complex_parameter(self, parameter_config: ComplexParameterTerm):
        complex_value = TemplateParameterComplexValue.nodes.get_or_none(
            name=parameter_config.value
        )
        if complex_value is None:
            root: TemplateParameterComplexRoot = TemplateParameterComplexRoot(
                is_active_parameter=True
            )
            root.save()
            complex_value = TemplateParameterComplexValue(name=parameter_config.value)
            complex_value.save()
            root.latest_final.connect(complex_value)
            root.has_latest_value.connect(complex_value)
            parameter_root = ParameterTemplateRoot.get(uid=parameter_config.uid)
            root.has_complex_value.connect(parameter_root)
            template_root = ParameterTemplateRoot.nodes.get(uid=parameter_config.uid)
            template_parameter = template_root.has_definition.get()
            root.has_parameter_term.connect(template_parameter)
        else:
            root_uid = complex_value.get_root_uid_by_latest()
            root = TemplateParameterComplexRoot.nodes.get(uid=root_uid)
        for i, param in enumerate(parameter_config.parameters):
            param_uid = param.uid
            if isinstance(param, NumericParameterTermVO):
                numeric_value = NumericValue.nodes.get_or_none(name=param.value)
                if not numeric_value:
                    numeric_value_root = NumericValueRoot(
                        uid="NumericValue_" + str(param.value)
                    )
                    numeric_value_root.save()
                    numeric_value = NumericValue(name=param.value)
                    numeric_value.save()
                    numeric_value_root.latest_final.connect(numeric_value, {})
                    numeric_value_root.has_latest_value.connect(numeric_value)
                    numeric_value_root = numeric_value_root.uid
                else:
                    numeric_value_root = numeric_value.get_root_uid_by_latest()
                param_uid = numeric_value_root
            tptr = TemplateParameterTermRoot.nodes.get(uid=param_uid)
            complex_value.uses_parameter.connect(tptr, {"position": i + 1})
        return root.element_id

    def _parse_parameter_terms(
        self, instance_parameters
    ) -> dict[int, list[ParameterTermEntryVO]]:
        # Note that this method is used both by templates for default values and instances for values
        # Hence the checks we have to make on the existence of the set_number property
        parameter_strings = []
        # First, parse results from the database
        for position_parameters in instance_parameters:
            position, param_name, param_terms, _ = position_parameters
            if len(param_terms) == 0:
                # If we find an empty (NA) parameter term, temporary save a none object that will be replaced later
                parameter_strings.append(
                    {
                        "set_number": 0,
                        "position": position,
                        "index": None,
                        "definition": None,
                        "template": None,
                        "parameter_uid": None,
                        "parameter_term": None,
                        "parameter_name": param_name,
                    }
                )

            for parameter in param_terms:
                parameter_strings.append(
                    {
                        "set_number": (
                            parameter["set_number"] if "set_number" in parameter else 0
                        ),
                        "position": parameter["position"],
                        "index": parameter["index"],
                        "parameter_name": parameter["parameter_name"],
                        "parameter_term": parameter["parameter_term"],
                        "parameter_uid": parameter["parameter_uid"],
                        "definition": parameter["definition"],
                        "template": parameter["template"],
                    }
                )

        # Then, start building the nested dictionary to group parameter terms in a list
        data_dict = {}
        # Create the first two levels, like
        # set_number
        # --> position
        for param in parameter_strings:
            if param["set_number"] not in data_dict:
                data_dict[param["set_number"]] = {}
            data_dict[param["set_number"]][param["position"]] = {
                "parameter_name": param["parameter_name"],
                "definition": param["definition"],
                "template": param["template"],
                "parameter_uids": [],
                "conjunction": next(
                    filter(
                        lambda x, param=param: x[0] == param["position"]
                        and (
                            len(x[2]) == 0
                            or (
                                "set_number" in x[2][0]
                                and x[2][0]["set_number"] == param["set_number"]
                            )
                        ),
                        instance_parameters,
                    )
                )[3],
            }

        # Then, unwind to create the third level, like:
        # set_number
        # --> position
        # -----> [parameter_uids]
        for param in parameter_strings:
            data_dict[param["set_number"]][param["position"]]["parameter_uids"].append(
                {
                    "index": param["index"],
                    "parameter_uid": param["parameter_uid"],
                    "parameter_name": param["parameter_name"],
                    "parameter_term": param["parameter_term"],
                }
            )

        # Finally, convert the nested dictionary to a list of ParameterTermEntryVO objects, grouped by value set
        return_dict = {}
        for set_number, term_set in data_dict.items():
            term_set = [x[1] for x in sorted(term_set.items(), key=lambda x: x[0])]
            parameter_list = []
            for item in term_set:
                term_list = []
                if item.get("definition"):
                    tpcr = TemplateParameterComplexRoot.nodes.get(
                        uid=item["parameter_uids"][0]["parameter_uid"]
                    )
                    defr: ParameterTemplateRoot = tpcr.has_complex_value.get()
                    tpcv: TemplateParameterComplexValue = tpcr.latest_final.get()
                    items = tpcv.get_all()
                    cpx_params = []
                    param_terms = []
                    for itemp in items:
                        param_terms.append(
                            {
                                "position": itemp[2],
                                "value": itemp[3],
                                "vv": itemp[4],
                                "item": itemp[1],
                            }
                        )
                    param_terms.sort(key=lambda x: x["position"])
                    for param in param_terms:
                        if param["value"] is not None:
                            simple_template_parameter_term_vo = NumericParameterTermVO(
                                uid=param["item"], value=param["value"]
                            )
                        else:
                            simple_template_parameter_term_vo = SimpleParameterTermVO(
                                uid=param["item"], value=param["vv"]
                            )
                        cpx_params.append(simple_template_parameter_term_vo)
                    parameter_list.append(
                        ComplexParameterTerm(
                            uid=defr.uid,
                            parameter_template=item["template"],
                            parameters=cpx_params,
                        )
                    )
                else:
                    for value in sorted(
                        item["parameter_uids"],
                        key=lambda x: x["index"] or 0,
                    ):
                        if value["parameter_uid"]:
                            simple_parameter_term_vo = (
                                self._parameter_from_repository_values(value)
                            )
                            term_list.append(simple_parameter_term_vo)
                    pve = ParameterTermEntryVO.from_repository_values(
                        parameters=term_list,
                        parameter_name=item["parameter_name"],
                        conjunction=item.get("conjunction", ""),
                    )
                    parameter_list.append(pve)
            return_dict[set_number] = parameter_list
        return return_dict

    def _parameter_from_repository_values(self, value):
        simple_parameter_term_vo = SimpleParameterTermVO.from_repository_values(
            uid=value["parameter_uid"], value=value["parameter_term"]
        )
        return simple_parameter_term_vo

    def get_template_type_uid(self, syntax_node: SyntaxTemplateRoot) -> str:
        """
        Get the UID of the type associated with a given Syntax Template.

        Args:
            syntax_node (SyntaxTemplateRoot): Syntax Template Root to get the type for.

        Returns:
            str: The UID of the type associated with the given Syntax Template.

        Raises:
            NotFoundException: If a Syntax Template does not exist.
        """

        if not syntax_node:
            raise NotFoundException("The requested Syntax Template does not exist.")

        ct_term = syntax_node.has_type.get_or_none()

        return ct_term.uid if ct_term else None

    def _get_indication(self, uid: str) -> DictionaryTermRoot:
        # Finds indication in database based on root node uid
        return DictionaryTermRoot.nodes.get(uid=uid)

    def _get_category(self, uid: str) -> CTTermRoot:
        # Finds category in database based on root node uid
        return CTTermRoot.nodes.get(uid=uid)

    def _get_activity(self, uid: str) -> ActivityRoot:
        # Finds activity in database based on root node uid
        return ActivityRoot.nodes.get(uid=uid)

    def _get_activity_group(self, uid: str) -> ActivityGroupRoot:
        # Finds activity group in database based on root node uid
        return ActivityGroupRoot.nodes.get(uid=uid)

    def _get_activity_subgroup(self, uid: str) -> ActivitySubGroupRoot:
        # Finds activity sub group in database based on root node uid
        return ActivitySubGroupRoot.nodes.get(uid=uid)

    def _get_template_type(self, uid: str) -> CTTermRoot:
        # Finds template type in database based on root node uid
        return CTTermRoot.nodes.get(uid=uid)

    def patch_indications(self, uid: str, indication_uids: list[str] | None) -> None:
        root = self.root_class.nodes.get(uid=uid)
        root.has_indication.disconnect_all()
        for indication in indication_uids or []:
            indication = self._get_indication(indication)
            root.has_indication.connect(indication)

    def patch_categories(self, uid: str, category_uids: list[str] | None) -> None:
        root = self.root_class.nodes.get(uid=uid)
        root.has_category.disconnect_all()
        for category in category_uids or []:
            category = self._get_category(category)
            root.has_category.connect(category)

    def patch_subcategories(
        self, uid: str, sub_category_uids: list[str] | None
    ) -> None:
        root = self.root_class.nodes.get(uid=uid)
        root.has_subcategory.disconnect_all()
        for sub_category in sub_category_uids or []:
            sub_category = self._get_category(sub_category)
            root.has_subcategory.connect(sub_category)

    def patch_activities(self, uid: str, activity_uids: list[str] | None) -> None:
        root = self.root_class.nodes.get(uid=uid)
        root.has_activity.disconnect_all()
        for activity in activity_uids or []:
            activity = self._get_activity(activity)
            root.has_activity.connect(activity)

    def patch_activity_groups(
        self, uid: str, activity_group_uids: list[str] | None
    ) -> None:
        root = self.root_class.nodes.get(uid=uid)
        root.has_activity_group.disconnect_all()
        for group in activity_group_uids or []:
            group = self._get_activity_group(group)
            root.has_activity_group.connect(group)

    def patch_activity_subgroups(
        self, uid: str, activity_subgroup_uids: list[str] | None
    ) -> None:
        root = self.root_class.nodes.get(uid=uid)
        root.has_activity_subgroup.disconnect_all()
        for group in activity_subgroup_uids or []:
            sub_group = self._get_activity_subgroup(group)
            root.has_activity_subgroup.connect(sub_group)

    def patch_is_confirmatory_testing(
        self, uid: str, is_confirmatory_testing: bool
    ) -> None:
        root = self.root_class.nodes.get(uid=uid)
        root.is_confirmatory_testing = is_confirmatory_testing

        self._db_save_node(root)

    def _create(self, item: _AggregateRootType):
        item = super()._create(item)
        root = None
        if item.uid:
            root = self.root_class.nodes.get(uid=item.uid)
            root.sequence_id = item.sequence_id
            self._db_save_node(root)

        return root, item
