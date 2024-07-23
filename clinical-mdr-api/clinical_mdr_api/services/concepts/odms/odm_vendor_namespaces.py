from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain_repositories.concepts.odms.vendor_namespace_repository import (
    VendorNamespaceRepository,
)
from clinical_mdr_api.domains.concepts.odms.vendor_namespace import (
    OdmVendorNamespaceAR,
    OdmVendorNamespaceVO,
)
from clinical_mdr_api.models.concepts.odms.odm_vendor_namespace import (
    OdmVendorNamespace,
    OdmVendorNamespacePatchInput,
    OdmVendorNamespacePostInput,
    OdmVendorNamespaceVersion,
)
from clinical_mdr_api.services.concepts.odms.odm_generic_service import (
    OdmGenericService,
)


class OdmVendorNamespaceService(OdmGenericService[OdmVendorNamespaceAR]):
    aggregate_class = OdmVendorNamespaceAR
    version_class = OdmVendorNamespaceVersion
    repository_interface = VendorNamespaceRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmVendorNamespaceAR
    ) -> OdmVendorNamespace:
        return OdmVendorNamespace.from_odm_vendor_namespace_ar(
            odm_vendor_namespace_ar=item_ar,
            find_odm_vendor_element_by_uid=self._repos.odm_vendor_element_repository.find_by_uid_2,
            find_odm_vendor_attribute_by_uid=self._repos.odm_vendor_attribute_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, concept_input: OdmVendorNamespacePostInput, library
    ) -> OdmVendorNamespaceAR:
        return OdmVendorNamespaceAR.from_input_values(
            author=self.user_initials,
            concept_vo=OdmVendorNamespaceVO.from_repository_values(
                name=concept_input.name,
                prefix=concept_input.prefix,
                url=concept_input.url,
                vendor_element_uids=[],
                vendor_attribute_uids=[],
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            concept_exists_by_callback=self._repos.odm_vendor_namespace_repository.exists_by,
        )

    def _edit_aggregate(
        self,
        item: OdmVendorNamespaceAR,
        concept_edit_input: OdmVendorNamespacePatchInput,
    ) -> OdmVendorNamespaceAR:
        item.edit_draft(
            author=self.user_initials,
            change_description=concept_edit_input.change_description,
            concept_vo=OdmVendorNamespaceVO.from_repository_values(
                name=concept_edit_input.name,
                prefix=concept_edit_input.prefix,
                url=concept_edit_input.url,
                vendor_element_uids=[],
                vendor_attribute_uids=[],
            ),
            concept_exists_by_callback=self._repos.odm_vendor_namespace_repository.exists_by,
        )
        return item

    def soft_delete(self, uid: str) -> None:
        if not self._repos.odm_vendor_namespace_repository.exists_by("uid", uid, True):
            raise exceptions.NotFoundException(
                f"ODM Vendor Namespace identified by uid ({uid}) does not exist."
            )

        if self._repos.odm_vendor_namespace_repository.has_active_relationships(
            uid, ["has_vendor_element", "has_vendor_attribute"]
        ):
            raise exceptions.BusinessLogicException(
                "This ODM Vendor Namespace is in use."
            )

        return super().soft_delete(uid)

    @db.transaction
    def get_active_relationships(self, uid: str):
        if not self._repos.odm_vendor_namespace_repository.exists_by("uid", uid, True):
            raise exceptions.NotFoundException(
                f"ODM Vendor Namespace identified by uid ({uid}) does not exist."
            )

        return self._repos.odm_vendor_namespace_repository.get_active_relationships(
            uid, ["has_vendor_element", "has_vendor_attribute"]
        )
