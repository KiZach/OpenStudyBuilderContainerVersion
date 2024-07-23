from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain_repositories.concepts.odms.vendor_attribute_repository import (
    VendorAttributeRepository,
)
from clinical_mdr_api.domains.concepts.odms.vendor_attribute import (
    OdmVendorAttributeAR,
    OdmVendorAttributeVO,
)
from clinical_mdr_api.models.concepts.odms.odm_vendor_attribute import (
    OdmVendorAttribute,
    OdmVendorAttributePatchInput,
    OdmVendorAttributePostInput,
    OdmVendorAttributeVersion,
)
from clinical_mdr_api.services.concepts.odms.odm_generic_service import (
    OdmGenericService,
)


class OdmVendorAttributeService(OdmGenericService[OdmVendorAttributeAR]):
    aggregate_class = OdmVendorAttributeAR
    version_class = OdmVendorAttributeVersion
    repository_interface = VendorAttributeRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmVendorAttributeAR
    ) -> OdmVendorAttribute:
        return OdmVendorAttribute.from_odm_vendor_attribute_ar(
            odm_vendor_attribute_ar=item_ar,
            find_odm_vendor_namespace_by_uid=self._repos.odm_vendor_namespace_repository.find_by_uid_2,
            find_odm_vendor_element_by_uid=self._repos.odm_vendor_element_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, concept_input: OdmVendorAttributePostInput, library
    ) -> OdmVendorAttributeAR:
        return OdmVendorAttributeAR.from_input_values(
            author=self.user_initials,
            concept_vo=OdmVendorAttributeVO.from_repository_values(
                name=concept_input.name,
                compatible_types=[
                    compatible_type.value
                    for compatible_type in concept_input.compatible_types
                ],
                data_type=concept_input.data_type,
                value_regex=concept_input.value_regex,
                vendor_namespace_uid=concept_input.vendor_namespace_uid,
                vendor_element_uid=concept_input.vendor_element_uid,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            find_odm_vendor_namespace_callback=self._repos.odm_vendor_namespace_repository.find_by_uid_2,
            find_odm_vendor_element_callback=self._repos.odm_vendor_element_repository.find_by_uid_2,
            find_odm_vendor_attribute_callback=self._repos.odm_vendor_attribute_repository.find_all,
        )

    def _edit_aggregate(
        self,
        item: OdmVendorAttributeAR,
        concept_edit_input: OdmVendorAttributePatchInput,
    ) -> OdmVendorAttributeAR:
        item.edit_draft(
            author=self.user_initials,
            change_description=concept_edit_input.change_description,
            concept_vo=OdmVendorAttributeVO.from_repository_values(
                name=concept_edit_input.name,
                compatible_types=[
                    compatible_type.value
                    for compatible_type in concept_edit_input.compatible_types
                ],
                data_type=concept_edit_input.data_type,
                value_regex=concept_edit_input.value_regex,
                vendor_namespace_uid=item.concept_vo.vendor_namespace_uid,
                vendor_element_uid=item.concept_vo.vendor_element_uid,
            ),
        )
        return item

    @db.transaction
    def get_active_relationships(self, uid: str):
        if not self._repos.odm_vendor_attribute_repository.exists_by("uid", uid, True):
            raise exceptions.NotFoundException(
                f"ODM Vendor Attribute identified by uid ({uid}) does not exist."
            )

        return self._repos.odm_vendor_attribute_repository.get_active_relationships(
            uid, ["belongs_to_vendor_namespace", "belongs_to_vendor_element"]
        )
