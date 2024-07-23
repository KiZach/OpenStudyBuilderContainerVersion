import re
from abc import ABC

from clinical_mdr_api.domain_repositories.concepts.odms.form_repository import (
    FormRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.item_group_repository import (
    ItemGroupRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.item_repository import (
    ItemRepository,
)
from clinical_mdr_api.domains.concepts.odms.form import OdmFormAR
from clinical_mdr_api.domains.concepts.odms.item import OdmItemAR
from clinical_mdr_api.domains.concepts.odms.item_group import OdmItemGroupAR
from clinical_mdr_api.domains.concepts.odms.vendor_attribute import OdmVendorAttributeAR
from clinical_mdr_api.domains.concepts.utils import RelationType, VendorCompatibleType
from clinical_mdr_api.exceptions import BusinessLogicException
from clinical_mdr_api.models.concepts.odms.odm_common_models import (
    OdmVendorElementRelationPostInput,
    OdmVendorRelationPostInput,
    OdmVendorsPostInput,
)
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
    _AggregateRootType,
)


class OdmGenericService(ConceptGenericService[_AggregateRootType], ABC):
    OBJECT_IS_INACTIVE = "The object is inactive"

    def fail_if_non_present_vendor_elements_are_used_by_current_odm_element_attributes(
        self,
        attribute_uids: list[str],
        input_elements: list[OdmVendorElementRelationPostInput],
    ):
        """
        Raises an error if any ODM vendor element that is not present in the input is used by any of the given ODM element attributes.

        Args:
            attribute_uids (list[str]): The uids of the ODM element attributes.
            input_elements (list[OdmVendorElementRelationPostInput]): The input ODM vendor elements.

        Returns:
            None

        Raises:
            BusinessLogicException: If an ODM vendor element is used by any of the given ODM element attributes and is not present in the input.
        """
        (
            odm_vendor_attribute_ars,
            _,
        ) = self._repos.odm_vendor_attribute_repository.find_all(
            filter_by={"uid": {"v": attribute_uids, "op": "eq"}}
        )

        odm_vendor_attribute_element_uids = {
            odm_vendor_attribute_ar.concept_vo.vendor_element_uid
            for odm_vendor_attribute_ar in odm_vendor_attribute_ars
        }

        if not odm_vendor_attribute_element_uids.issubset(
            {input_element.uid for input_element in input_elements}
        ):
            raise BusinessLogicException(
                "Cannot remove an ODM Vendor Element whose attributes are connected to this ODM element."
            )

    def fail_if_these_attributes_cannot_be_added(
        self,
        input_attributes: list[OdmVendorRelationPostInput],
        element_uids: list[str] | None = None,
        compatible_type: VendorCompatibleType | None = None,
    ):
        """
        Raises an error if any of the given ODM vendor attributes cannot be added as vendor attributes or vendor element attributes.

        Args:
            input_attributes (list[OdmVendorRelationPostInput]): The input ODM vendor attributes.
            element_uids (list[str] | None, optional): The uids of the vendor elements to which the attributes can be added.
            compatible_type (VendorCompatibleType | None, optional): The vendor compatible type of the attributes.

        Returns:
            None

        Raises:
            BusinessLogicException: If any of the given ODM vendor attributes cannot be added as vendor attributes or vendor element attributes.
        """
        odm_vendor_attribute_ars = self._get_odm_vendor_attributes(input_attributes)
        vendor_attribute_patterns = {
            odm_vendor_attribute_ar.uid: odm_vendor_attribute_ar.concept_vo.value_regex
            for odm_vendor_attribute_ar in odm_vendor_attribute_ars
        }

        self.attribute_values_matches_their_regex(
            input_attributes, vendor_attribute_patterns
        )

        for odm_vendor_attribute_ar in odm_vendor_attribute_ars:
            if odm_vendor_attribute_ar:
                if (
                    element_uids
                    and odm_vendor_attribute_ar.concept_vo.vendor_element_uid
                    not in element_uids
                ):
                    raise BusinessLogicException(
                        f"ODM Vendor Attribute identified by ({odm_vendor_attribute_ar.uid}) cannot not be added as an Vendor Element Attribute."
                    )

                if (
                    not element_uids
                    and not odm_vendor_attribute_ar.concept_vo.vendor_namespace_uid
                ):
                    raise BusinessLogicException(
                        f"ODM Vendor Attribute identified by ({odm_vendor_attribute_ar.uid}) cannot not be added as an Vendor Attribute."
                    )

        self.is_vendor_compatible(odm_vendor_attribute_ars, compatible_type)

    def can_connect_vendor_attributes(
        self, attributes: list[OdmVendorRelationPostInput]
    ):
        errors = []
        for attribute in attributes:
            attr = self._repos.odm_vendor_attribute_repository.find_by_uid_2(
                attribute.uid
            )

            if not attr or not attr.concept_vo.vendor_namespace_uid:
                errors.append(attribute.uid)

        if errors:
            raise BusinessLogicException(
                f"ODM Vendor Attributes with the following UIDs don't exist or aren't connected to an ODM Vendor Namespace. UIDs: {errors}"
            )

        return True

    def attribute_values_matches_their_regex(
        self,
        input_attributes: list[OdmVendorRelationPostInput],
        attribute_patterns: dict,
    ):
        """
        Determines whether the values of the given ODM vendor attributes match their regex patterns.

        Args:
            input_attributes (list[OdmVendorRelationPostInput]): The input ODM vendor attributes.
            attribute_patterns (dict): The regex patterns for the ODM vendor attributes.

        Returns:
            bool: True if the values of the ODM vendor attributes match their regex patterns, False otherwise.

        Raises:
            BusinessLogicException: If the values of any of the ODM vendor attributes don't match their regex patterns.
        """
        errors = {}
        for input_attribute in input_attributes:
            if (
                input_attribute.value
                and attribute_patterns.get(input_attribute.uid)
                and not bool(
                    re.match(
                        attribute_patterns[input_attribute.uid], input_attribute.value
                    )
                )
            ):
                errors[input_attribute.uid] = attribute_patterns[input_attribute.uid]
        if errors:
            raise BusinessLogicException(
                f"Provided values for following attributes don't match their regex pattern:\n\n{errors}"
            )

        return True

    def get_regex_patterns_of_attributes(
        self, attribute_uids: list[str]
    ) -> dict[str, str | None]:
        """
        Returns a dictionary where the key is the attribute uid and the value is the regex pattern of the specified ODM vendor attributes.

        Args:
            attribute_uids (list[str]): The uids of the ODM vendor attributes.

        Returns:
            dict[str, str | None]: A dictionary of regex patterns for the specified ODM vendor attributes.
        """
        attributes, _ = self._repos.odm_vendor_attribute_repository.find_all(
            filter_by={"uid": {"v": attribute_uids, "op": "eq"}}
        )

        return {
            attribute.uid: attribute.concept_vo.value_regex for attribute in attributes
        }

    def is_vendor_compatible(
        self,
        odm_vendor_attributes: list[OdmVendorRelationPostInput]
        | list[OdmVendorAttributeAR],
        compatible_type: VendorCompatibleType | None = None,
    ):
        """
        Determines whether the given ODM vendor attributes are compatible with the specified vendor compatible type.

        Args:
            odm_vendor_attributes (list[OdmVendorRelationPostInput] | list[OdmVendorAttributeAR]): The ODM vendor attributes.
            compatible_type (VendorCompatibleType | None, optional): The vendor compatible type to check for compatibility.

        Returns:
            bool: True if the given ODM vendor attributes are compatible with the specified vendor compatible type.

        Raises:
            BusinessLogicException: If any of the given ODM vendor attributes are not compatible with the specified vendor compatible type.
        """
        errors = {}

        if all(
            isinstance(odm_vendor_attribute, OdmVendorRelationPostInput)
            for odm_vendor_attribute in odm_vendor_attributes
        ):
            odm_vendor_attributes = self._get_odm_vendor_attributes(
                odm_vendor_attributes
            )

        for odm_vendor_attribute in odm_vendor_attributes:
            if (
                compatible_type
                and compatible_type.value
                not in odm_vendor_attribute.concept_vo.compatible_types
            ):
                errors[
                    odm_vendor_attribute.uid
                ] = odm_vendor_attribute.concept_vo.compatible_types
        if errors:
            raise BusinessLogicException(
                f"Trying to add non-compatible ODM Vendor:\n\n{errors}"
            )

        return True

    def _get_odm_vendor_attributes(
        self, input_attributes: list[OdmVendorRelationPostInput]
    ):
        return self._repos.odm_vendor_attribute_repository.find_all(
            filter_by={
                "uid": {
                    "v": [input_attribute.uid for input_attribute in input_attributes],
                    "op": "eq",
                }
            }
        )[0]

    def pre_management(
        self,
        uid: str,
        odm_vendors_post_input: OdmVendorsPostInput,
        odm_ar: OdmFormAR | OdmItemGroupAR | OdmItemAR,
        repo: FormRepository | ItemGroupRepository | ItemRepository,
    ):
        """
        Prepares the given ODM Vendors by adding and removing vendor element and vendor element attribute relations.

        Args:
            uid (str): The uid of the ODM form, item group, or item.
            odm_vendors_post_input (OdmVendorsPostInput): The ODM vendors.
            odm_ar (OdmFormAR | OdmItemGroupAR | OdmItemAR): The ODM form, item group, or item.
            repo (FormRepository | ItemGroupRepository | ItemRepository): The repository for the ODM form, item group, or item.

        Returns:
            None
        """
        removed_vendor_attribute_uids = set(
            odm_ar.concept_vo.vendor_element_attribute_uids
        ) - {
            element_attribute.uid
            for element_attribute in odm_vendors_post_input.element_attributes
        }
        for removed_vendor_attribute_uid in removed_vendor_attribute_uids:
            repo.remove_relation(
                uid=uid,
                relation_uid=removed_vendor_attribute_uid,
                relationship_type=RelationType.VENDOR_ELEMENT_ATTRIBUTE,
            )

        new_vendor_element_uids = {
            element.uid for element in odm_vendors_post_input.elements
        } - set(odm_ar.concept_vo.vendor_element_uids)
        for element in odm_vendors_post_input.elements:
            if element.uid in new_vendor_element_uids:
                repo.add_relation(
                    uid=uid,
                    relation_uid=element.uid,
                    relationship_type=RelationType.VENDOR_ELEMENT,
                    parameters={
                        "value": element.value,
                    },
                )
