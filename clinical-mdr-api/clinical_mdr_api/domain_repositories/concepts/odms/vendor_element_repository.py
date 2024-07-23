from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.concepts.odms.odm_generic_repository import (
    OdmGenericRepository,
)
from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.odm import (
    OdmFormRoot,
    OdmItemGroupRoot,
    OdmItemRoot,
    OdmVendorElementRoot,
    OdmVendorElementValue,
    OdmVendorNamespaceRoot,
)
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domains.concepts.odms.vendor_element import (
    OdmVendorElementAR,
    OdmVendorElementRelationVO,
    OdmVendorElementVO,
)
from clinical_mdr_api.domains.concepts.utils import RelationType
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.exceptions import BusinessLogicException
from clinical_mdr_api.models import OdmVendorElement


class VendorElementRepository(OdmGenericRepository[OdmVendorElementAR]):
    root_class = OdmVendorElementRoot
    value_class = OdmVendorElementValue
    return_model = OdmVendorElement

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library | None,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> OdmVendorElementAR:
        vendor_namespace = root.belongs_to_vendor_namespace.get_or_none()
        return OdmVendorElementAR.from_repository_values(
            uid=root.uid,
            concept_vo=OdmVendorElementVO.from_repository_values(
                name=value.name,
                vendor_namespace_uid=vendor_namespace.uid if vendor_namespace else None,
                vendor_attribute_uids=[
                    vendor_attribute.uid
                    for vendor_attribute in root.has_vendor_attribute.all()
                ],
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> _AggregateRootType:
        major, minor = input_dict.get("version").split(".")
        odm_vendor_element_ar = OdmVendorElementAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=OdmVendorElementVO.from_repository_values(
                name=input_dict.get("name"),
                vendor_namespace_uid=input_dict.get("vendor_namespace_uid"),
                vendor_attribute_uids=input_dict.get("vendor_attribute_uids"),
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
                end_date=None,
                major_version=int(major),
                minor_version=int(minor),
            ),
        )

        return odm_vendor_element_ar

    def specific_alias_clause(
        self, only_specific_status: str = ObjectStatus.LATEST.name
    ) -> str:
        return f"""
        WITH *,

        head([(concept_value)<-[:{only_specific_status}]-(:OdmVendorElementRoot)<-[:HAS_VENDOR_ELEMENT]-(vnr:OdmVendorNamespaceRoot)-[:LATEST]->(vnv:OdmVendorNamespaceValue) | {{uid: vnr.uid, name: vnv.name, prefix: vnv.prefix, url: vnv.url}}]) AS vendor_namespace,
        [(concept_value)<-[:{only_specific_status}]-(:OdmVendorElementRoot)-[:HAS_VENDOR_ATTRIBUTE]->(var:OdmVendorAttributeRoot)-[:LATEST]->(vav:OdmVendorAttributeValue) | {{uid: var.uid, name: vav.name}}] AS vendor_attributes

        WITH *,
        vendor_namespace.uid AS vendor_namespace_uid,
        apoc.coll.toSet([vendor_attribute in vendor_attributes | vendor_attribute.uid]) AS vendor_attribute_uids
        """

    def _get_or_create_value(
        self, root: VersionRoot, ar: ConceptARBase
    ) -> VersionValue:
        new_value = super()._get_or_create_value(root, ar)

        root.belongs_to_vendor_namespace.disconnect_all()

        if ar.concept_vo.vendor_namespace_uid is not None:
            vendor_namespace = OdmVendorNamespaceRoot.nodes.get_or_none(
                uid=ar.concept_vo.vendor_namespace_uid
            )
            root.belongs_to_vendor_namespace.connect(vendor_namespace)

        return new_value

    def _has_data_changed(
        self, ar: OdmVendorElementAR, value: OdmVendorElementValue
    ) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)

        root = OdmVendorElementRoot.nodes.get_or_none(uid=ar.uid)

        vendor_namespace_uid = (
            vendor_namespace.uid
            if (vendor_namespace := root.belongs_to_vendor_namespace.get_or_none())
            else None
        )

        are_rels_changed = ar.concept_vo.vendor_namespace_uid != vendor_namespace_uid

        return are_concept_properties_changed or are_rels_changed

    def find_by_uid_with_odm_element_relation(
        self, uid: str, odm_element_uid: str, odm_element_type: RelationType
    ):
        vendor_element_root = self.root_class.nodes.get_or_none(uid=uid)
        vendor_element_value = vendor_element_root.has_latest_value.get_or_none()

        if odm_element_type == RelationType.FORM:
            odm_element_root = OdmFormRoot.nodes.get_or_none(uid=odm_element_uid)
            rel = vendor_element_root.belongs_to_form.relationship(odm_element_root)
        elif odm_element_type == RelationType.ITEM_GROUP:
            odm_element_root = OdmItemGroupRoot.nodes.get_or_none(uid=odm_element_uid)
            rel = vendor_element_root.belongs_to_item_group.relationship(
                odm_element_root
            )
        elif odm_element_type == RelationType.ITEM:
            odm_element_root = OdmItemRoot.nodes.get_or_none(uid=odm_element_uid)
            rel = vendor_element_root.belongs_to_item.relationship(odm_element_root)
        else:
            raise BusinessLogicException("Invalid ODM element type.")

        return OdmVendorElementRelationVO.from_repository_values(
            uid=uid,
            name=vendor_element_value.name,
            value=rel.value,
        )
