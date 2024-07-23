from time import time
from xml.dom import minicompat, minidom

from fastapi import UploadFile
from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain_repositories.concepts.odms.odm_generic_repository import (
    OdmGenericRepository,
)
from clinical_mdr_api.domains._utils import get_iso_lang_data
from clinical_mdr_api.domains.concepts.utils import (
    ENG_LANGUAGE,
    RelationType,
    VendorCompatibleType,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryVO,
    VersioningException,
)
from clinical_mdr_api.models import (
    OdmConditionPostInput,
    OdmDescriptionPostInput,
    OdmFormalExpressionPostInput,
    OdmFormItemGroupPostInput,
    OdmFormPostInput,
    OdmItemGroupItemPostInput,
    OdmItemGroupPostInput,
    OdmItemPostInput,
    OdmItemTermRelationshipInput,
    OdmItemUnitDefinitionRelationshipInput,
    OdmStudyEventFormPostInput,
    OdmStudyEventPostInput,
    OdmVendorAttributePostInput,
)
from clinical_mdr_api.models.concepts.odms.odm_common_models import (
    OdmRefVendorPostInput,
    OdmVendorElementRelationPostInput,
    OdmVendorRelationPostInput,
)
from clinical_mdr_api.models.concepts.odms.odm_condition import OdmCondition
from clinical_mdr_api.models.concepts.odms.odm_form import OdmForm
from clinical_mdr_api.models.concepts.odms.odm_item import OdmItem
from clinical_mdr_api.models.concepts.odms.odm_item_group import OdmItemGroup
from clinical_mdr_api.models.concepts.odms.odm_method import (
    OdmMethod,
    OdmMethodPostInput,
)
from clinical_mdr_api.models.concepts.odms.odm_study_event import OdmStudyEvent
from clinical_mdr_api.models.concepts.odms.odm_vendor_attribute import (
    OdmVendorAttribute,
)
from clinical_mdr_api.models.concepts.odms.odm_vendor_element import (
    OdmVendorElement,
    OdmVendorElementPostInput,
)
from clinical_mdr_api.models.concepts.odms.odm_vendor_namespace import (
    OdmVendorNamespace,
    OdmVendorNamespacePostInput,
)
from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionModel,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term_attributes import (
    CTTermAttributes,
)
from clinical_mdr_api.oauth.user import user
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import is_library_editable, normalize_string
from clinical_mdr_api.services.concepts.odms.odm_conditions import OdmConditionService
from clinical_mdr_api.services.concepts.odms.odm_descriptions import (
    OdmDescriptionService,
)
from clinical_mdr_api.services.concepts.odms.odm_formal_expressions import (
    OdmFormalExpressionService,
)
from clinical_mdr_api.services.concepts.odms.odm_forms import OdmFormService
from clinical_mdr_api.services.concepts.odms.odm_item_groups import OdmItemGroupService
from clinical_mdr_api.services.concepts.odms.odm_items import OdmItemService
from clinical_mdr_api.services.concepts.odms.odm_methods import OdmMethodService
from clinical_mdr_api.services.concepts.odms.odm_study_events import (
    OdmStudyEventService,
)
from clinical_mdr_api.services.concepts.odms.odm_vendor_attributes import (
    OdmVendorAttributeService,
)
from clinical_mdr_api.services.concepts.odms.odm_vendor_elements import (
    OdmVendorElementService,
)
from clinical_mdr_api.services.concepts.odms.odm_vendor_namespaces import (
    OdmVendorNamespaceService,
)
from clinical_mdr_api.services.concepts.unit_definitions.unit_definition import (
    UnitDefinitionService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesService,
)
from clinical_mdr_api.services.utils.odm_xml_mapper import map_xml
from clinical_mdr_api.utils import strtobool


class OdmXmlImporterService:
    _repos: MetaRepository
    odm_vendor_namespace_service: OdmVendorNamespaceService
    odm_vendor_attribute_service: OdmVendorAttributeService
    odm_vendor_element_service: OdmVendorElementService
    odm_study_event_service: OdmStudyEventService
    odm_form_service: OdmFormService
    odm_item_group_service: OdmItemGroupService
    odm_item_service: OdmItemService
    odm_condition_service: OdmConditionService
    odm_method_service: OdmMethodService
    odm_formal_expression_service: OdmFormalExpressionService
    odm_description_service: OdmDescriptionService
    unit_definition_service: UnitDefinitionService
    ct_term_attributes_service: CTTermAttributesService

    xml_document: minidom.Document
    form_defs: minicompat.NodeList
    item_group_defs: minicompat.NodeList
    item_defs: minicompat.NodeList
    condition_defs: minicompat.NodeList
    method_defs: minicompat.NodeList
    codelists: minicompat.NodeList
    measurement_units: minicompat.NodeList

    namespace_prefixes: dict[str, str]

    db_vendor_namespaces: list[OdmVendorNamespace]
    db_vendor_attributes: list[OdmVendorAttribute]
    db_vendor_elements: list[OdmVendorElement]
    db_study_events: list[OdmStudyEvent]
    db_forms: list[OdmForm]
    db_item_groups: list[OdmItemGroup]
    db_items: list[OdmItem]
    db_conditions: list[OdmCondition]
    db_methods: list[OdmMethod]
    db_ct_term_attributes: list[CTTermAttributes]
    db_unit_definitions: list[UnitDefinitionModel]
    unit_definition_uids_by: dict[str, str]
    measurement_unit_names_by_oid: dict[str, str]

    mapper_file: UploadFile | None = None

    OSB_PREFIX = "osb"
    EXCLUDED_OSB_VENDOR_ATTRIBUTES = [
        "version",
        "lang",
        "instruction",
        "sponsorInstruction",
    ]
    EXCLUDED_OSB_VENDOR_ELEMENTS = ["DomainColor"]
    OSB_INSTRUCTION = f"{OSB_PREFIX}:instruction"
    OSB_SPONSOR_INSTRUCTION = f"{OSB_PREFIX}:sponsorInstruction"

    def __init__(self, xml_file: UploadFile, mapper_file: UploadFile | None):
        if xml_file.content_type not in ["application/xml", "text/xml"]:
            raise exceptions.BusinessLogicException("Only XML format is supported.")

        self._repos = MetaRepository()
        self.odm_vendor_namespace_service = OdmVendorNamespaceService()
        self.odm_vendor_attribute_service = OdmVendorAttributeService()
        self.odm_vendor_element_service = OdmVendorElementService()
        self.odm_study_event_service = OdmStudyEventService()
        self.odm_form_service = OdmFormService()
        self.odm_item_group_service = OdmItemGroupService()
        self.odm_item_service = OdmItemService()
        self.odm_condition_service = OdmConditionService()
        self.odm_method_service = OdmMethodService()
        self.odm_formal_expression_service = OdmFormalExpressionService()
        self.odm_description_service = OdmDescriptionService()
        self.ct_term_attributes_service = CTTermAttributesService()

        self.namespace_prefixes = {}
        self.db_vendor_namespaces = []
        self.db_vendor_attributes = []
        self.db_vendor_elements = []
        self.db_study_events = []
        self.db_forms = []
        self.db_item_groups = []
        self.db_items = []
        self.db_conditions = []
        self.db_methods = []
        self.db_ct_term_attributes = []
        self.db_unit_definitions = []
        self.unit_definition_uids_by = {}
        self.measurement_unit_names_by_oid = {}

        self.mapper_file = mapper_file

        self.xml_document = minidom.parseString(xml_file.file.read())

        map_xml(self.xml_document, mapper_file)

        self._set_def_elements()

    @db.transaction
    def store_odm_xml(self):
        self._set_vendor_namespaces()
        self._create_missing_vendor_namespaces()
        self._set_vendor_attributes()
        self._set_vendor_elements()
        if not self.db_unit_definitions:
            self._set_unit_definitions()
        self._set_unit_definition_uids_by()
        self._set_measurement_unit_names_by_oid()
        self._set_ct_term_attributes()
        self._create_methods_with_relations()
        self._create_conditions_with_relations()
        self._create_items_with_relations()
        self._create_item_groups_with_relations()
        self._create_forms_with_relations()
        self._create_study_event_with_relations()

        return {
            "vendor_namespaces": self._get_newly_created_vendor_namespaces(),
            "vendor_attributes": self._get_newly_created_vendor_attributes(),
            "vendor_elements": self._get_newly_created_vendor_elements(),
            "study_events": self._get_newly_created_study_events(),
            "forms": self._get_newly_created_forms(),
            "item_groups": self._get_newly_created_item_groups(),
            "items": self._get_newly_created_items(),
            "conditions": self._get_newly_created_conditions(),
            "methods": self._get_newly_created_methods(),
        }

    def _set_def_elements(self):
        self.measurement_units = self.xml_document.getElementsByTagName(
            "MeasurementUnit"
        )
        self.form_defs = self.xml_document.getElementsByTagName("FormDef")
        self.item_group_defs = self.xml_document.getElementsByTagName("ItemGroupDef")
        self.item_defs = self.xml_document.getElementsByTagName("ItemDef")
        self.condition_defs = self.xml_document.getElementsByTagName("ConditionDef")
        self.method_defs = self.xml_document.getElementsByTagName("MethodDef")
        self.codelists = self.xml_document.getElementsByTagName("CodeList")

    def _set_vendor_namespaces(self):
        odm_element = self.xml_document.getElementsByTagName("ODM")[0]
        for attribute in odm_element.attributes.values():
            if attribute.prefix and attribute.localName != "odm":
                self.namespace_prefixes[attribute.localName] = attribute.nodeValue

        rs, _ = self._repos.odm_vendor_namespace_repository.find_all(
            filter_by={
                "prefix": {"v": list(self.namespace_prefixes.keys()), "op": "eq"}
            },
        )

        rs.sort(key=lambda elm: elm.name)

        self.db_vendor_namespaces = [
            self.odm_vendor_namespace_service._transform_aggregate_root_to_pydantic_model(
                concept_ar
            )
            for concept_ar in rs
        ]

    def _set_vendor_attributes(self):
        vendor_attribute_uids = [
            vendor_attribute.uid
            for db_vendor_namespace in self.db_vendor_namespaces
            for vendor_attribute in db_vendor_namespace.vendor_attributes
        ]

        rs, _ = self._repos.odm_vendor_attribute_repository.find_all(
            filter_by={"uid": {"v": vendor_attribute_uids, "op": "eq"}},
        )

        rs.sort(key=lambda elm: elm.name)

        self.db_vendor_attributes = [
            self.odm_vendor_attribute_service._transform_aggregate_root_to_pydantic_model(
                concept_ar
            )
            for concept_ar in rs
        ]

    def _set_vendor_elements(self):
        vendor_element_uids = [
            vendor_element.uid
            for db_vendor_namespace in self.db_vendor_namespaces
            for vendor_element in db_vendor_namespace.vendor_elements
        ]

        rs, _ = self._repos.odm_vendor_element_repository.find_all(
            filter_by={"uid": {"v": vendor_element_uids, "op": "eq"}},
        )

        rs.sort(key=lambda elm: elm.name)

        self.db_vendor_elements = [
            self.odm_vendor_element_service._transform_aggregate_root_to_pydantic_model(
                concept_ar
            )
            for concept_ar in rs
        ]

    def _create_missing_vendor_namespaces(self):
        missing_prefixes = sorted(
            list(
                set(self.namespace_prefixes.keys())
                - {
                    db_vendor_namespace.prefix
                    for db_vendor_namespace in self.db_vendor_namespaces
                }
            )
        )

        new_vendor_namespaces = []
        for missing_prefix in missing_prefixes:
            rs = self._create(
                self._repos.odm_vendor_namespace_repository,
                self.odm_vendor_namespace_service,
                new_vendor_namespaces,
                OdmVendorNamespacePostInput(
                    name=missing_prefix.upper(),
                    prefix=missing_prefix,
                    url=self.namespace_prefixes[missing_prefix],
                ),
            )

            self._approve(
                self._repos.odm_vendor_namespace_repository,
                self.odm_vendor_namespace_service,
                rs,
            )

        self.db_vendor_namespaces.extend(new_vendor_namespaces)

    def _create_missing_vendors(self, def_element: minidom.Element):
        self._create_missing_vendor_attributes(def_element.attributes.values())
        self._create_missing_vendor_elements(def_element.childNodes)
        self._create_missing_vendor_element_attributes(def_element.childNodes)

    def _create_missing_vendor_attributes(self, elm_attributes):
        new_vendor_attributes = []

        for elm_attribute in elm_attributes:
            if not isinstance(elm_attribute, minidom.Attr) or not elm_attribute.prefix:
                continue

            if not self._vendor_attribute_exists(
                elm_attribute.prefix, elm_attribute.localName
            ):
                rs = self._create(
                    self._repos.odm_vendor_attribute_repository,
                    self.odm_vendor_attribute_service,
                    new_vendor_attributes,
                    OdmVendorAttributePostInput(
                        name=elm_attribute.localName,
                        compatible_types=[elm_attribute.ownerElement.localName],
                        vendor_namespace_uid=next(
                            db_vendor_namespace.uid
                            for db_vendor_namespace in self.db_vendor_namespaces
                            if db_vendor_namespace.prefix == elm_attribute.prefix
                        ),
                    ),
                )

                self._approve(
                    self._repos.odm_vendor_attribute_repository,
                    self.odm_vendor_attribute_service,
                    rs,
                )

        self.db_vendor_attributes.extend(new_vendor_attributes)

    def _create_missing_vendor_elements(self, elements: minicompat.NodeList):
        new_vendor_elements = []

        for element in elements:
            if not isinstance(element, minidom.Element) or not element.prefix:
                continue

            if not self.vendor_element_exists(element.prefix, element.localName):
                rs = self._create(
                    self._repos.odm_vendor_element_repository,
                    self.odm_vendor_element_service,
                    new_vendor_elements,
                    OdmVendorElementPostInput(
                        name=element.localName,
                        vendor_namespace_uid=next(
                            db_vendor_namespace.uid
                            for db_vendor_namespace in self.db_vendor_namespaces
                            if db_vendor_namespace.prefix == element.prefix
                        ),
                    ),
                )

                self._approve(
                    self._repos.odm_vendor_element_repository,
                    self.odm_vendor_element_service,
                    rs,
                )

        self.db_vendor_elements.extend(new_vendor_elements)

    def _create_missing_vendor_element_attributes(self, elements: minicompat.NodeList):
        for element in elements:
            if not isinstance(element, minidom.Element) or not element.prefix:
                continue

            new_vendor_element_attributes = []
            for element_attribute in element.attributes.values():
                if (
                    not isinstance(element_attribute, minidom.Attr)
                    or not element_attribute.prefix
                ):
                    continue

                if not self._vendor_element_attribtue_exists(
                    element_attribute.prefix, element_attribute.localName
                ):
                    rs = self._create(
                        self._repos.odm_vendor_attribute_repository,
                        self.odm_vendor_attribute_service,
                        new_vendor_element_attributes,
                        OdmVendorAttributePostInput(
                            name=element_attribute.localName,
                            vendor_element_uid=next(
                                db_vendor_element.uid
                                for db_vendor_element in self.db_vendor_elements
                                if db_vendor_element.vendor_namespace.prefix
                                == element_attribute.prefix
                                and db_vendor_element.name == element.localName
                            ),
                        ),
                    )

                    self._approve(
                        self._repos.odm_vendor_attribute_repository,
                        self.odm_vendor_attribute_service,
                        rs,
                    )

            self.db_vendor_attributes.extend(new_vendor_element_attributes)

    def _create_relationships_with_vendors(
        self,
        uid: str,
        def_element: minidom.Element,
        repo: OdmGenericRepository,
        compatible_type: VendorCompatibleType | None = None,
    ):
        self._create_relationship_with_vendor_attributes(
            uid, def_element.attributes.values(), repo, compatible_type
        )
        self._create_relationship_with_vendor_elements(
            uid, def_element.childNodes, repo
        )
        self._create_relationship_with_vendor_element_attributes(
            uid, def_element.childNodes, repo
        )

    def _create_relationship_with_vendor_attributes(
        self,
        uid: str,
        elm_attributes,
        repository: OdmGenericRepository,
        compatible_type: VendorCompatibleType | None = None,
    ):
        odm_vendor_relations: list[OdmVendorRelationPostInput] = []
        for elm_attribute in elm_attributes:
            if (
                not isinstance(elm_attribute, minidom.Attr)
                or not elm_attribute.prefix
                or (
                    elm_attribute.prefix == self.OSB_PREFIX
                    and elm_attribute.localName in self.EXCLUDED_OSB_VENDOR_ATTRIBUTES
                )
            ):
                continue

            vendor_attribute_uid = next(
                db_vendor_attribute.uid
                for db_vendor_attribute in self.db_vendor_attributes
                if elm_attribute.localName == db_vendor_attribute.name
                and (
                    db_vendor_attribute.vendor_namespace
                    and elm_attribute.prefix
                    == db_vendor_attribute.vendor_namespace.prefix
                )
            )

            odm_vendor_relations.append(
                OdmVendorRelationPostInput(
                    uid=vendor_attribute_uid, value=elm_attribute.nodeValue
                )
            )

            vendor_attribute_patterns = (
                self.odm_vendor_attribute_service.get_regex_patterns_of_attributes(
                    [
                        odm_vendor_relation.uid
                        for odm_vendor_relation in odm_vendor_relations
                    ]
                )
            )
            self.odm_vendor_attribute_service.attribute_values_matches_their_regex(
                odm_vendor_relations, vendor_attribute_patterns
            )
            self.odm_vendor_attribute_service.is_vendor_compatible(
                odm_vendor_relations, compatible_type
            )

        for odm_vendor_relation in odm_vendor_relations:
            repository.add_relation(
                uid=uid,
                relation_uid=odm_vendor_relation.uid,
                relationship_type=RelationType.VENDOR_ATTRIBUTE,
                parameters={"value": odm_vendor_relation.value},
            )

    def _create_relationship_with_vendor_elements(
        self,
        uid: str,
        child_elements: minicompat.NodeList,
        repository: OdmGenericRepository,
    ):
        odm_vendor_relations: list[OdmVendorElementRelationPostInput] = []
        for child_element in child_elements:
            if (
                not isinstance(child_element, minidom.Element)
                or not child_element.prefix
                or (
                    child_element.prefix == self.OSB_PREFIX
                    and child_element.localName in self.EXCLUDED_OSB_VENDOR_ELEMENTS
                )
            ):
                continue

            vendor_element_uid = next(
                db_vendor_element.uid
                for db_vendor_element in self.db_vendor_elements
                if child_element.localName == db_vendor_element.name
                and (
                    db_vendor_element.vendor_namespace
                    and child_element.prefix
                    == db_vendor_element.vendor_namespace.prefix
                )
            )

            odm_vendor_relations.append(
                OdmVendorElementRelationPostInput(
                    uid=vendor_element_uid,
                    value=child_element.firstChild.nodeValue
                    if child_element.firstChild
                    else "",
                )
            )

        for odm_vendor_relation in odm_vendor_relations:
            repository.add_relation(
                uid=uid,
                relation_uid=odm_vendor_relation.uid,
                relationship_type=RelationType.VENDOR_ELEMENT,
                parameters={"value": odm_vendor_relation.value},
            )

    def _create_relationship_with_vendor_element_attributes(
        self,
        uid: str,
        child_elements: minicompat.NodeList,
        repository: OdmGenericRepository,
    ):
        for child_element in child_elements:
            if (
                not isinstance(child_element, minidom.Element)
                or not child_element.prefix
                or (
                    child_element.prefix == self.OSB_PREFIX
                    and child_element.localName in self.EXCLUDED_OSB_VENDOR_ATTRIBUTES
                )
            ):
                continue

            odm_vendor_relations: list[OdmVendorRelationPostInput] = []
            for child_element_attribute in child_element.attributes.values():
                if (
                    not isinstance(child_element_attribute, minidom.Attr)
                    or not child_element_attribute.prefix
                    or (
                        child_element_attribute.prefix == self.OSB_PREFIX
                        and child_element_attribute.localName
                        in self.EXCLUDED_OSB_VENDOR_ATTRIBUTES
                    )
                ):
                    continue

                vendor_element_attribute_uid = next(
                    db_vendor_attribute.uid
                    for db_vendor_attribute in self.db_vendor_attributes
                    if child_element_attribute.localName == db_vendor_attribute.name
                    and (
                        db_vendor_attribute.vendor_element
                        and child_element_attribute.prefix
                        == next(
                            (
                                db_vendor_element.vendor_namespace.prefix
                                for db_vendor_element in self.db_vendor_elements
                                if db_vendor_element.uid
                                == db_vendor_attribute.vendor_element.uid
                            ),
                            None,
                        )
                    )
                )

                odm_vendor_relations.append(
                    OdmVendorRelationPostInput(
                        uid=vendor_element_attribute_uid,
                        value=child_element_attribute.nodeValue,
                    )
                )

            for odm_vendor_relation in odm_vendor_relations:
                repository.add_relation(
                    uid=uid,
                    relation_uid=odm_vendor_relation.uid,
                    relationship_type=RelationType.VENDOR_ELEMENT_ATTRIBUTE,
                    parameters={"value": odm_vendor_relation.value},
                )

    def _vendor_attribute_exists(self, prefix, vendor_attribute_name):
        if (
            prefix == self.OSB_PREFIX
            and vendor_attribute_name in self.EXCLUDED_OSB_VENDOR_ATTRIBUTES
        ):
            return True

        for db_vendor_attribute in self.db_vendor_attributes:
            if vendor_attribute_name == db_vendor_attribute.name and (
                db_vendor_attribute.vendor_namespace
                and prefix == db_vendor_attribute.vendor_namespace.prefix
            ):
                return True
        return False

    def vendor_element_exists(self, prefix, vendor_element_name):
        if (
            prefix == self.OSB_PREFIX
            and vendor_element_name in self.EXCLUDED_OSB_VENDOR_ELEMENTS
        ):
            return True

        for db_vendor_element in self.db_vendor_elements:
            if vendor_element_name == db_vendor_element.name and (
                db_vendor_element.vendor_namespace
                and prefix == db_vendor_element.vendor_namespace.prefix
            ):
                return True
        return False

    def _vendor_element_attribtue_exists(self, prefix, vendor_attribute_name):
        if (
            prefix == self.OSB_PREFIX
            and vendor_attribute_name in self.EXCLUDED_OSB_VENDOR_ATTRIBUTES
        ):
            return True

        for db_vendor_attribute in self.db_vendor_attributes:
            if vendor_attribute_name == db_vendor_attribute.name and (
                db_vendor_attribute.vendor_element
                and prefix
                == next(
                    (
                        db_vendor_element.vendor_namespace.prefix
                        for db_vendor_element in self.db_vendor_elements
                        if db_vendor_element.uid
                        == db_vendor_attribute.vendor_element.uid
                    ),
                    None,
                )
            ):
                return True
        return False

    def _set_unit_definitions(self):
        measurement_unit_oids = {
            measurement_unit.getAttribute("OID")
            for measurement_unit in self.measurement_units
        }

        rs, _ = self._repos.unit_definition_repository.find_all(
            filter_by={"name": {"v": measurement_unit_oids, "op": "eq"}},
        )

        rs_names = {item.name for item in rs}

        non_existent_measurement_unit_oids = measurement_unit_oids - rs_names

        if non_existent_measurement_unit_oids:
            raise exceptions.BusinessLogicException(
                f"MeasurementUnits identified by following OIDs {non_existent_measurement_unit_oids} don't match any Unit Definition."
            )

        self.db_unit_definitions = [
            UnitDefinitionModel.from_unit_definition_ar(
                unit_definition_ar,
                find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
                find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
            )
            for unit_definition_ar in rs
        ]

    def _set_unit_definition_uids_by(self):
        self.unit_definition_uids_by = {
            db_unit_definition.ucum.term_uid: db_unit_definition.uid
            for db_unit_definition in self.db_unit_definitions
            if db_unit_definition.ucum
        }

    def _set_measurement_unit_names_by_oid(self):
        self.measurement_unit_names_by_oid = {
            measurement_unit.getAttribute("OID"): measurement_unit.getAttribute("Name")
            for measurement_unit in self.measurement_units
        }

    def _set_ct_term_attributes(self):
        rs = self._repos.ct_term_attributes_repository.find_all(
            filter_by={
                "nci_preferred_name": {
                    "v": [
                        domain.split(":", 1)[-1]
                        for item_group_def in self.item_group_defs
                        for domain in item_group_def.getAttribute("Domain").split("|")
                        if domain
                    ],
                    "op": "eq",
                }
            }
        )

        self.db_ct_term_attributes = [
            self.ct_term_attributes_service._transform_aggregate_root_to_pydantic_model(
                ct_codelist_ar
            )
            for ct_codelist_ar in rs.items
        ]

    def _create_formal_expressions(self, target):
        new_formal_expressions = []
        for formal_expression in target.getElementsByTagName("FormalExpression"):
            rs = self._create(
                self._repos.odm_formal_expression_repository,
                self.odm_formal_expression_service,
                new_formal_expressions,
                OdmFormalExpressionPostInput(
                    context=formal_expression.getAttribute("Context"),
                    expression=formal_expression.firstChild.nodeValue,
                ),
            )

            self._approve(
                self._repos.odm_formal_expression_repository,
                self.odm_formal_expression_service,
                rs,
            )

        return new_formal_expressions

    def _create_conditions_with_relations(self):
        for condition_def in self.condition_defs:
            descriptions = self._extract_descriptions(condition_def)

            rs = self._create(
                self._repos.odm_condition_repository,
                self.odm_condition_service,
                self.db_conditions,
                OdmConditionPostInput(
                    oid=condition_def.getAttribute("OID"),
                    name=condition_def.getAttribute("Name"),
                    formal_expressions=[
                        formal_expression.uid
                        for formal_expression in self._create_formal_expressions(
                            condition_def
                        )
                    ],
                    descriptions=[
                        self._create_description(
                            name=description["name"],
                            lang=description["lang"],
                            description=description["description"],
                        ).uid
                        for description in descriptions
                    ],
                    alias_uids=[],
                ),
            )
            self._approve(
                self._repos.odm_condition_repository, self.odm_condition_service, rs
            )

    def _create_methods_with_relations(self):
        for method_def in self.method_defs:
            descriptions = self._extract_descriptions(method_def)

            rs = self._create(
                self._repos.odm_method_repository,
                self.odm_method_service,
                self.db_methods,
                OdmMethodPostInput(
                    oid=method_def.getAttribute("OID"),
                    name=method_def.getAttribute("Name"),
                    method_type=method_def.getAttribute("Name"),
                    formal_expressions=[
                        formal_expression.uid
                        for formal_expression in self._create_formal_expressions(
                            method_def
                        )
                    ],
                    descriptions=[
                        self._create_description(
                            name=description["name"],
                            lang=description["lang"],
                            description=description["description"],
                        ).uid
                        for description in descriptions
                    ],
                    alias_uids=[],
                ),
            )
            self._approve(
                self._repos.odm_method_repository, self.odm_method_service, rs
            )

    def _create_items_with_relations(self):
        for item_def in self.item_defs:
            self._create_missing_vendors(item_def)

            (
                odm_item_post_input,
                terms,
                unit_definitions,
            ) = self._get_odm_item_post_input(item_def)

            rs = self._create(
                self._repos.odm_item_repository,
                self.odm_item_service,
                self.db_items,
                odm_item_post_input,
            )

            if terms:
                self.odm_item_service._manage_terms(rs.uid, terms)
            self.odm_item_service._manage_unit_definitions(rs.uid, unit_definitions)

            self._create_relationships_with_vendors(
                rs.uid,
                item_def,
                self._repos.odm_item_repository,
                VendorCompatibleType.ITEM_DEF,
            )
            self._approve(self._repos.odm_item_repository, self.odm_item_service, rs)

    def _create_item_groups_with_relations(self):
        for item_group_def in self.item_group_defs:
            self._create_missing_vendors(item_group_def)

            rs = self._create(
                self._repos.odm_item_group_repository,
                self.odm_item_group_service,
                self.db_item_groups,
                self._get_odm_item_group_post_input(item_group_def),
            )

            self._create_relationships_with_vendors(
                rs.uid,
                item_group_def,
                self._repos.odm_item_group_repository,
                VendorCompatibleType.ITEM_GROUP_DEF,
            )

            odm_item_group_items: list[OdmItemGroupItemPostInput] = []
            for item_ref in item_group_def.getElementsByTagName("ItemRef"):
                self._create_missing_vendor_attributes(item_ref.attributes.values())

                odm_item_group_items.append(
                    OdmItemGroupItemPostInput(
                        uid=next(
                            (
                                db_item.uid
                                for db_item in self.db_items
                                if db_item.oid == item_ref.getAttribute("ItemOID")
                            ),
                            None,
                        ),
                        order_number=item_ref.getAttribute("OrderNumber"),
                        mandatory=item_ref.getAttribute("Mandatory"),
                        key_sequence="None",
                        method_oid=item_ref.getAttribute("MethodOID") or None,
                        imputation_method_oid="None",
                        role="None",
                        role_codelist_oid="None",
                        collection_exception_condition_oid=item_ref.getAttribute(
                            "CollectionExceptionConditionOID"
                        ),
                        vendor=OdmRefVendorPostInput(
                            attributes=self._get_list_of_attributes(
                                item_ref.attributes.items()
                            )
                        ),
                    )
                )

            self.odm_item_group_service.non_transactional_add_items(
                rs.uid, odm_item_group_items
            )

            self._approve(
                self._repos.odm_item_group_repository, self.odm_item_group_service, rs
            )

    def _create_forms_with_relations(self):
        for form_def in self.form_defs:
            self._create_missing_vendors(form_def)

            rs = self._create(
                self._repos.odm_form_repository,
                self.odm_form_service,
                self.db_forms,
                self._get_odm_form_post_input(form_def),
            )

            self._create_relationships_with_vendors(
                rs.uid,
                form_def,
                self._repos.odm_form_repository,
                VendorCompatibleType.FORM_DEF,
            )
            odm_form_item_groups: list[OdmFormItemGroupPostInput] = []
            for item_group_ref in form_def.getElementsByTagName("ItemGroupRef"):
                self._create_missing_vendor_attributes(
                    item_group_ref.attributes.values()
                )

                odm_form_item_groups.append(
                    OdmFormItemGroupPostInput(
                        uid=next(
                            (
                                db_item_group.uid
                                for db_item_group in self.db_item_groups
                                if db_item_group.oid
                                == item_group_ref.getAttribute("ItemGroupOID")
                            ),
                            None,
                        ),
                        order_number=item_group_ref.getAttribute("OrderNumber"),
                        mandatory=item_group_ref.getAttribute("Mandatory"),
                        collection_exception_condition_oid=item_group_ref.getAttribute(
                            "CollectionExceptionConditionOID"
                        ),
                        vendor=OdmRefVendorPostInput(
                            attributes=self._get_list_of_attributes(
                                item_group_ref.attributes.items()
                            )
                        ),
                    )
                )

            self.odm_form_service.non_transactional_add_item_groups(
                rs.uid, odm_form_item_groups
            )

            self._approve(self._repos.odm_form_repository, self.odm_form_service, rs)

    def _create_study_event_with_relations(self):
        if self.xml_document.getElementsByTagName("StudyName"):
            study_name = self.xml_document.getElementsByTagName("StudyName")[
                0
            ].firstChild.nodeValue
        else:
            study_name = f"@{int(time() * 1_000)}"

        rs = self._create(
            self._repos.odm_study_event_repository,
            self.odm_study_event_service,
            self.db_study_events,
            OdmStudyEventPostInput(oid=study_name, name=study_name),
        )

        odm_study_event_forms = []
        for db_form in self.db_forms:
            odm_study_event_forms.append(
                OdmStudyEventFormPostInput(
                    uid=db_form.uid,
                    order_number=999999,
                    mandatory="yes",
                    locked="No",
                )
            )

        for odm_study_event_form in odm_study_event_forms:
            self._repos.odm_study_event_repository.add_relation(
                uid=rs.uid,
                relation_uid=odm_study_event_form.uid,
                relationship_type=RelationType.FORM,
                parameters={
                    "order_number": odm_study_event_form.order_number,
                    "mandatory": strtobool(odm_study_event_form.mandatory),
                    "locked": strtobool(odm_study_event_form.locked),
                    "collection_exception_condition_oid": odm_study_event_form.collection_exception_condition_oid,
                },
            )

        self._approve(
            self._repos.odm_study_event_repository, self.odm_study_event_service, rs
        )

    def _create_description(
        self,
        name: str | minidom.Text,
        lang: str = ENG_LANGUAGE,
        description: str | None = None,
        instruction: str | None = None,
        sponsor_instruction: str | None = None,
    ):
        if isinstance(name, minidom.Text):
            name = name.nodeValue

        if not description:
            description = "Please update this description"

        if not instruction:
            instruction = "Please update this instruction"

        if not sponsor_instruction:
            sponsor_instruction = "Please update this sponsor instruction"

        concept_input = OdmDescriptionPostInput(
            name=name,
            language=lang,
            description=description,
            instruction=instruction if lang == ENG_LANGUAGE else None,
            sponsor_instruction=sponsor_instruction if lang == ENG_LANGUAGE else None,
        )

        library_vo = self._get_library(concept_input)

        concept_ar = self.odm_description_service._create_aggregate_root(
            concept_input=concept_input, library=library_vo
        )
        self._repos.odm_description_repository.save(concept_ar)
        self._approve(
            self._repos.odm_description_repository,
            self.odm_description_service,
            concept_ar,
        )
        return self.odm_description_service._transform_aggregate_root_to_pydantic_model(
            concept_ar
        )

    def _extract_descriptions(self, elm):
        description_element = elm.getElementsByTagName("Description")
        question_element = elm.getElementsByTagName("Question")
        descriptions = []
        description_langs = []

        if description_element:
            for translated_text in description_element[0].getElementsByTagName(
                "TranslatedText"
            ):
                lang = translated_text.getAttribute("xml:lang")
                desc = translated_text.firstChild.nodeValue

                descriptions.append(
                    {
                        "lang": lang,
                        "name": desc,
                        "description": desc,
                    }
                )
                description_langs.append(lang)

        if question_element:
            for translated_text in question_element[0].getElementsByTagName(
                "TranslatedText"
            ):
                lang = translated_text.getAttribute("xml:lang")
                name = translated_text.firstChild

                if lang not in description_langs:
                    descriptions.append(
                        {
                            "lang": lang,
                            "name": name,
                            "description": None,
                        }
                    )
                else:
                    for description in descriptions:
                        if lang == description["lang"]:
                            description["name"] = name
                            break

        for description in descriptions:
            description["lang"] = get_iso_lang_data(
                description["lang"], "639-1", "639-2/B"
            ).upper()

        if elm.tagName in {"ConditionDef", "MethodDef"} and not any(
            description["lang"] == ENG_LANGUAGE for description in descriptions
        ):
            raise exceptions.ValidationException(
                f"An English OdmDescription must be provided for {elm.tagName} identified by OID ({elm.getAttribute('OID')})."
            )

        return descriptions

    def _get_newly_created_vendor_namespaces(self):
        rs, _ = self._repos.odm_vendor_namespace_repository.find_all(
            filter_by={
                "uid": {
                    "v": [
                        vendor_namespace.uid
                        for vendor_namespace in self.db_vendor_namespaces
                    ],
                    "op": "eq",
                }
            },
        )

        rs.sort(key=lambda elm: elm.name)

        return [
            self.odm_vendor_namespace_service._transform_aggregate_root_to_pydantic_model(
                concept_ar
            )
            for concept_ar in rs
        ]

    def _get_newly_created_vendor_attributes(self):
        rs, _ = self._repos.odm_vendor_attribute_repository.find_all(
            filter_by={
                "uid": {
                    "v": [
                        vendor_attribute.uid
                        for vendor_attribute in self.db_vendor_attributes
                    ],
                    "op": "eq",
                }
            },
        )

        rs.sort(key=lambda elm: elm.name)

        return [
            self.odm_vendor_attribute_service._transform_aggregate_root_to_pydantic_model(
                concept_ar
            )
            for concept_ar in rs
        ]

    def _get_newly_created_vendor_elements(self):
        rs, _ = self._repos.odm_vendor_element_repository.find_all(
            filter_by={
                "uid": {
                    "v": [
                        vendor_element.uid for vendor_element in self.db_vendor_elements
                    ],
                    "op": "eq",
                }
            },
        )

        rs.sort(key=lambda elm: elm.name)

        return [
            self.odm_vendor_element_service._transform_aggregate_root_to_pydantic_model(
                concept_ar
            )
            for concept_ar in rs
        ]

    def _get_newly_created_study_events(self):
        rs, _ = self._repos.odm_study_event_repository.find_all(
            filter_by={
                "uid": {
                    "v": [study_event.uid for study_event in self.db_study_events],
                    "op": "eq",
                }
            },
        )

        rs.sort(key=lambda elm: elm.name)

        return [
            self.odm_study_event_service._transform_aggregate_root_to_pydantic_model(
                concept_ar
            )
            for concept_ar in rs
        ]

    def _get_newly_created_forms(self):
        rs, _ = self._repos.odm_form_repository.find_all(
            filter_by={
                "uid": {
                    "v": [form.uid for form in self.db_forms],
                    "op": "eq",
                }
            },
        )

        rs.sort(key=lambda elm: elm.name)

        return [
            self.odm_form_service._transform_aggregate_root_to_pydantic_model(
                concept_ar
            )
            for concept_ar in rs
        ]

    def _get_newly_created_item_groups(self):
        rs, _ = self._repos.odm_item_group_repository.find_all(
            filter_by={
                "uid": {
                    "v": [item_group.uid for item_group in self.db_item_groups],
                    "op": "eq",
                }
            }
        )

        rs.sort(key=lambda elm: elm.name)

        return [
            self.odm_item_group_service._transform_aggregate_root_to_pydantic_model(
                concept_ar
            )
            for concept_ar in rs
        ]

    def _get_newly_created_conditions(self):
        rs, _ = self._repos.odm_condition_repository.find_all(
            filter_by={
                "uid": {
                    "v": [condition.uid for condition in self.db_conditions],
                    "op": "eq",
                }
            }
        )

        rs.sort(key=lambda elm: elm.name)

        return [
            self.odm_condition_service._transform_aggregate_root_to_pydantic_model(
                concept_ar
            )
            for concept_ar in rs
        ]

    def _get_newly_created_methods(self):
        rs, _ = self._repos.odm_method_repository.find_all(
            filter_by={
                "uid": {
                    "v": [method.uid for method in self.db_methods],
                    "op": "eq",
                }
            }
        )

        rs.sort(key=lambda elm: elm.name)

        return [
            self.odm_method_service._transform_aggregate_root_to_pydantic_model(
                concept_ar
            )
            for concept_ar in rs
        ]

    def _get_newly_created_items(self):
        rs, _ = self._repos.odm_item_repository.find_all(
            filter_by={
                "uid": {
                    "v": [item.uid for item in self.db_items],
                    "op": "eq",
                }
            }
        )

        rs.sort(key=lambda elm: elm.name)

        return [
            self.odm_item_service._transform_aggregate_root_to_pydantic_model(
                concept_ar
            )
            for concept_ar in rs
        ]

    def _get_library(self, concept_input):
        if not self._repos.library_repository.library_exists(
            normalize_string(concept_input.library_name)
        ):
            raise exceptions.BusinessLogicException(
                f"There is no library identified by provided library name ({concept_input.library_name})"
            )

        return LibraryVO.from_input_values_2(
            library_name=concept_input.library_name,
            is_library_editable_callback=is_library_editable,
        )

    def _get_odm_item_post_input(self, item_def):
        descriptions = self._extract_descriptions(item_def)

        item_unit_definitions = self._get_item_unit_definition_inputs(item_def)

        codelist = next(
            (
                codelist
                for codelist in self.codelists
                if item_def.getElementsByTagName("CodeListRef")
                and codelist.getAttribute("OID")
                == item_def.getElementsByTagName("CodeListRef")[0].getAttribute(
                    "CodeListOID"
                )
            ),
            None,
        )

        input_terms = []
        if codelist:
            input_terms = [
                OdmItemTermRelationshipInput(
                    uid=codelist_item.getAttribute("osb:OID"),
                    mandatory=codelist_item.getAttribute("osb:mandatory")
                    if codelist_item.getAttribute("osb:mandatory") != ""
                    else True,
                    order=codelist_item.getAttribute("OrderNumber"),
                    display_text=codelist_item.getElementsByTagName("TranslatedText")[
                        0
                    ].firstChild.nodeValue,
                )
                for codelist_item in codelist.getElementsByTagName("CodeListItem")
            ]

        return (
            OdmItemPostInput(
                oid=item_def.getAttribute("OID"),
                name=item_def.getAttribute("Name"),
                prompt=item_def.getAttribute("Prompt"),
                datatype=item_def.getAttribute("DataType"),
                length=item_def.getAttribute("Length"),
                sas_field_name=item_def.getAttribute("SASFieldName"),
                sds_var_name=item_def.getAttribute("SDSVarName"),
                origin=item_def.getAttribute("Origin"),
                descriptions=[
                    self._create_description(
                        name=description["name"],
                        lang=description["lang"],
                        description=description["description"],
                        instruction=item_def.getAttribute(self.OSB_INSTRUCTION),
                        sponsor_instruction=item_def.getAttribute(
                            self.OSB_SPONSOR_INSTRUCTION
                        ),
                    ).uid
                    for description in descriptions
                ],
                alias_uids=[],
                unit_definitions=item_unit_definitions,
                codelist_uid=codelist.getAttribute("Name") if codelist else None,
                terms=input_terms,
            ),
            input_terms,
            item_unit_definitions,
        )

    def _get_odm_item_group_post_input(self, item_group_def):
        descriptions = self._extract_descriptions(item_group_def)

        return OdmItemGroupPostInput(
            oid=item_group_def.getAttribute("OID"),
            name=item_group_def.getAttribute("Name"),
            origin=item_group_def.getAttribute("Origin"),
            repeating=item_group_def.getAttribute("Repeating"),
            is_reference_data="no",  # missing in odm
            purpose=item_group_def.getAttribute("Purpose"),
            sas_dataset_name=item_group_def.getAttribute("SASDatasetName"),
            descriptions=[
                self._create_description(
                    name=description["name"],
                    lang=description["lang"],
                    description=description["description"],
                    instruction=item_group_def.getAttribute(self.OSB_INSTRUCTION),
                    sponsor_instruction=item_group_def.getAttribute(
                        self.OSB_SPONSOR_INSTRUCTION
                    ),
                ).uid
                for description in descriptions
            ],
            alias_uids=[],
            sdtm_domain_uids=[
                db_ct_term_attribute.term_uid
                for db_ct_term_attribute in self.db_ct_term_attributes
                for domain in item_group_def.getAttribute("Domain").split("|")
                if domain
                and domain.split(":", 1)[-1] == db_ct_term_attribute.nci_preferred_name
            ],
        )

    def _get_odm_form_post_input(self, form_def):
        descriptions = self._extract_descriptions(form_def)

        return OdmFormPostInput(
            oid=form_def.getAttribute("OID"),
            name=form_def.getAttribute("Name"),
            sdtm_version="",
            repeating=form_def.getAttribute("Repeating"),
            descriptions=[
                self._create_description(
                    name=description["name"],
                    lang=description["lang"],
                    description=description["description"],
                    instruction=form_def.getAttribute(self.OSB_INSTRUCTION),
                    sponsor_instruction=form_def.getAttribute(
                        self.OSB_SPONSOR_INSTRUCTION
                    ),
                ).uid
                for description in descriptions
            ],
            alias_uids=[],
        )

    def _get_item_unit_definition_inputs(self, item_def):
        try:
            return [
                OdmItemUnitDefinitionRelationshipInput(
                    uid=self.unit_definition_uids_by[
                        self.measurement_unit_names_by_oid[
                            measurement_unit_ref.getAttribute("MeasurementUnitOID")
                        ]
                    ]
                )
                for measurement_unit_ref in item_def.getElementsByTagName(
                    "MeasurementUnitRef"
                )
            ]
        except KeyError as exc:
            raise exceptions.BusinessLogicException(
                f"MeasurementUnit with OID ({exc}) was not provided."
            )

    def _get_list_of_attributes(self, attributes):
        rs = []
        for name, value in attributes:
            if ":" in name:
                prefix, local_name = name.split(":")

                vendor_attribute_uid = next(
                    db_vendor_attribute.uid
                    for db_vendor_attribute in self.db_vendor_attributes
                    if local_name == db_vendor_attribute.name
                    and (
                        db_vendor_attribute.vendor_namespace
                        and prefix == db_vendor_attribute.vendor_namespace.prefix
                    )
                )
                rs.append(
                    OdmVendorRelationPostInput(uid=vendor_attribute_uid, value=value)
                )
        return rs

    def _create(self, repository, service, save_to, concept_input):
        library_vo = self._get_library(concept_input)

        concept_ar = service._create_aggregate_root(
            concept_input=concept_input, library=library_vo
        )
        repository.save(concept_ar)
        item = service._transform_aggregate_root_to_pydantic_model(concept_ar)
        save_to.append(item)
        return item

    def _approve(self, repository, service, item):
        try:
            appr = service._find_by_uid_or_raise_not_found(item.uid, for_update=True)
            appr.approve(author=user().id())
            repository.save(appr)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)
