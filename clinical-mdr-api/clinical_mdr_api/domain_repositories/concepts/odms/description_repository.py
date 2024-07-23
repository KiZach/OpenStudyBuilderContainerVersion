from typing import Any

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
    OdmDescriptionRoot,
    OdmDescriptionValue,
)
from clinical_mdr_api.domains.concepts.odms.description import (
    OdmDescriptionAR,
    OdmDescriptionVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models import OdmDescription


class DescriptionRepository(OdmGenericRepository[OdmDescriptionAR]):
    root_class = OdmDescriptionRoot
    value_class = OdmDescriptionValue
    return_model = OdmDescription

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library | None,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> OdmDescriptionAR:
        return OdmDescriptionAR.from_repository_values(
            uid=root.uid,
            concept_vo=OdmDescriptionVO.from_repository_values(
                name=value.name,
                language=value.language,
                description=value.description,
                instruction=value.instruction,
                sponsor_instruction=value.sponsor_instruction,
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
        odm_description_ar = OdmDescriptionAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=OdmDescriptionVO.from_repository_values(
                name=input_dict.get("name"),
                language=input_dict.get("language"),
                description=input_dict.get("description"),
                instruction=input_dict.get("instruction"),
                sponsor_instruction=input_dict.get("sponsor_instruction"),
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

        return odm_description_ar

    def specific_alias_clause(self, _: list[Any] | None = None) -> str:
        return """
        WITH *,
        concept_value.language AS language,
        concept_value.description AS description,
        concept_value.instruction AS instruction,
        concept_value.sponsor_instruction AS sponsor_instruction
        """

    def _create_new_value_node(self, ar: OdmDescriptionAR) -> OdmDescriptionValue:
        value_node = super()._create_new_value_node(ar=ar)
        value_node.save()

        value_node.language = ar.concept_vo.language
        value_node.description = ar.concept_vo.description
        value_node.instruction = ar.concept_vo.instruction
        value_node.sponsor_instruction = ar.concept_vo.sponsor_instruction

        return value_node

    def _has_data_changed(
        self, ar: OdmDescriptionAR, value: OdmDescriptionValue
    ) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)

        return (
            are_concept_properties_changed
            or ar.concept_vo.language != value.language
            or ar.concept_vo.description != value.description
            or ar.concept_vo.instruction != value.instruction
            or ar.concept_vo.sponsor_instruction != value.sponsor_instruction
        )
