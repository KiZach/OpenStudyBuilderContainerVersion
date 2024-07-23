from neomodel import RelationshipDefinition

from clinical_mdr_api.config import (
    SPONSOR_MODEL_PREFIX,
    SPONSOR_MODEL_VERSION_NUMBER_PREFIX,
)
from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    LATEST_VERSION_ORDER_BY,
    CustomNodeSet,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    DataModelIGRoot,
    SponsorModelValue,
)
from clinical_mdr_api.domain_repositories.neomodel_ext_item_repository import (
    NeomodelExtBaseRepository,
)
from clinical_mdr_api.domains.standard_data_models.sponsor_model import (
    SponsorModelAR,
    SponsorModelMetadataVO,
    SponsorModelVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.exceptions import BusinessLogicException
from clinical_mdr_api.models.standard_data_models.sponsor_model import SponsorModel


class SponsorModelRepository(
    NeomodelExtBaseRepository, LibraryItemRepositoryImplBase[SponsorModelAR]
):
    root_class = DataModelIGRoot
    value_class = SponsorModelValue
    return_model = SponsorModel

    def get_neomodel_extension_query(self) -> CustomNodeSet:
        return DataModelIGRoot.nodes.fetch_relations(
            "has_library",
            "has_latest_sponsor_model_value__extends_version",
        ).fetch_optional_single_relation_of_type(
            {
                "has_sponsor_model_version": (
                    "latest_version",
                    LATEST_VERSION_ORDER_BY,
                ),
            }
        )

    def generate_name(self, ig_uid: str, ig_version_number: str, version_number: str):
        name = "_".join(
            [
                str.lower(ig_uid),
                SPONSOR_MODEL_PREFIX,
                ig_version_number,
                f"{SPONSOR_MODEL_VERSION_NUMBER_PREFIX}{version_number}",
            ]
        )
        return name

    def _has_data_changed(self, ar: SponsorModelAR, value: SponsorModelValue) -> bool:
        return ar.sponsor_model_vo.name != value.name

    def _create(self, item: SponsorModelAR) -> SponsorModelAR:
        """
        Overrides generic LibraryItemRepository method
        """
        relation_data: SponsorModelMetadataVO = item.item_metadata
        root = DataModelIGRoot.nodes.get_or_none(uid=item.uid)

        if root is None:
            raise BusinessLogicException(
                f"The target Implementation Guide {item.uid} does not exist in the database."
            )

        value = self._get_or_create_value(root=root, ar=item)

        (
            root,
            value,
            _,
            _,
            _,
        ) = self._db_create_and_link_nodes(
            root=root,
            value=value,
            rel_properties=self._library_item_metadata_vo_to_datadict(relation_data),
            save_root=False,
        )

        return item

    def _get_version_relation_keys(
        self, root_node: DataModelIGRoot
    ) -> tuple[
        RelationshipDefinition,
        RelationshipDefinition,
        RelationshipDefinition,
        RelationshipDefinition,
        RelationshipDefinition,
    ]:
        return (
            root_node.has_sponsor_model_version,
            root_node.has_latest_sponsor_model_value,
            root_node.latest_sponsor_model_draft,
            root_node.latest_sponsor_model_final,
            root_node.latest_sponsor_model_retired,
        )

    @staticmethod
    def _library_item_metadata_vo_from_relation(
        relationship: VersionRelationship,
    ) -> SponsorModelMetadataVO:
        major = relationship.version
        return SponsorModelMetadataVO.from_repository_values(
            change_description=relationship.change_description,
            status=LibraryItemStatus(relationship.status),
            author=relationship.user_initials,
            start_date=relationship.start_date,
            end_date=relationship.end_date,
            major_version=int(major),
            minor_version=0,
        )

    def _get_or_create_value(
        self, root: DataModelIGRoot, ar: SponsorModelAR
    ) -> SponsorModelValue:
        for itm in root.has_sponsor_model_version.all():
            if not self._has_data_changed(ar, itm):
                return itm

        new_value = SponsorModelValue(
            name=ar.sponsor_model_vo.name,
        )
        self._db_save_node(new_value)

        ig_versions = root.has_version.filter(
            version_number=ar.sponsor_model_vo.ig_version_number
        )
        if ig_versions is None or len(ig_versions) == 0:
            raise BusinessLogicException(
                f"The target version {ar.sponsor_model_vo.ig_version_number}"
                f" for the Implementation Guide {ar.sponsor_model_vo.ig_uid} does not exist in the database."
            )

        new_value.extends_version.connect(ig_versions[0])

        return new_value

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: DataModelIGRoot,
        library: Library,
        relationship: VersionRelationship,
        value: SponsorModelValue,
        **_kwargs,
    ) -> SponsorModelAR:
        return SponsorModelAR.from_repository_values(
            ig_uid=root.uid,
            sponsor_model_vo=SponsorModelVO.from_repository_values(
                ig_uid=root.uid,
                ig_version_number=relationship.version,
                name=value.name,
                version_number=None,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _maintain_parameters(
        self,
        versioned_object: SponsorModelAR,
        root: DataModelIGRoot,
        value: SponsorModelValue,
    ) -> None:
        # This method from parent repo is not needed for this repo
        # So we use pass to skip implementation
        pass
