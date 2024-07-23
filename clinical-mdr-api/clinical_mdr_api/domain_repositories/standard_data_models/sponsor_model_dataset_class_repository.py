from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domain_repositories.models._utils import CustomNodeSet
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    DatasetClass,
    SponsorModelDatasetClassInstance,
    SponsorModelValue,
)
from clinical_mdr_api.domain_repositories.neomodel_ext_item_repository import (
    NeomodelExtBaseRepository,
)
from clinical_mdr_api.domain_repositories.standard_data_models.utils import (
    get_sponsor_model_info_from_dataset_class,
)
from clinical_mdr_api.domains.standard_data_models.sponsor_model_dataset_class import (
    SponsorModelDatasetClassAR,
    SponsorModelDatasetClassVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.exceptions import BusinessLogicException
from clinical_mdr_api.models.standard_data_models.sponsor_model_dataset_class import (
    SponsorModelDatasetClass,
)


class SponsorModelDatasetClassRepository(
    NeomodelExtBaseRepository, LibraryItemRepositoryImplBase[SponsorModelDatasetClassAR]
):
    root_class = DatasetClass
    value_class = SponsorModelDatasetClassInstance
    return_model = SponsorModelDatasetClass

    def get_neomodel_extension_query(self) -> CustomNodeSet:
        return DatasetClass.nodes.fetch_relations(
            "has_sponsor_model_instance__has_dataset_class",
            "has_dataset_class__has_library",
        )

    def _has_data_changed(
        self, ar: SponsorModelDatasetClassAR, value: SponsorModelDatasetClassInstance
    ) -> bool:
        return (
            ar.sponsor_model_dataset_class_vo.is_basic_std != value.is_basic_std
            or ar.sponsor_model_dataset_class_vo.xml_path != value.xml_path
            or ar.sponsor_model_dataset_class_vo.xml_title != value.xml_title
            or ar.sponsor_model_dataset_class_vo.structure != value.structure
            or ar.sponsor_model_dataset_class_vo.purpose != value.purpose
            or ar.sponsor_model_dataset_class_vo.comment != value.comment
            or ar.sponsor_model_dataset_class_vo.label != value.label
        )

    def _create(self, item: SponsorModelDatasetClassAR) -> SponsorModelDatasetClassAR:
        """
        Overrides generic LibraryItemRepository method
        """
        root = DatasetClass.nodes.get_or_none(uid=item.uid)

        if root is None:
            root = DatasetClass(uid=item.uid).save()

        instance = self._get_or_create_instance(root=root, ar=item)

        # Connect with SponsorModelValue node
        parent_node = SponsorModelValue.nodes.get_or_none(
            name=item.sponsor_model_dataset_class_vo.sponsor_model_name
        )
        if parent_node:
            instance.has_dataset_class.connect(parent_node)
        else:
            raise BusinessLogicException(
                f"The given Sponsor Model version {item.sponsor_model_dataset_class_vo.sponsor_model_name} does not exist in the database."
            )

        return item

    def _get_or_create_instance(
        self, root: DatasetClass, ar: SponsorModelDatasetClassAR
    ) -> SponsorModelDatasetClassInstance:
        for itm in root.has_sponsor_model_instance.all():
            if not self._has_data_changed(ar, itm):
                return itm

        new_instance = SponsorModelDatasetClassInstance(
            is_basic_std=ar.sponsor_model_dataset_class_vo.is_basic_std,
            xml_path=ar.sponsor_model_dataset_class_vo.xml_path,
            xml_title=ar.sponsor_model_dataset_class_vo.xml_title,
            structure=ar.sponsor_model_dataset_class_vo.structure,
            purpose=ar.sponsor_model_dataset_class_vo.purpose,
            comment=ar.sponsor_model_dataset_class_vo.comment,
            label=ar.sponsor_model_dataset_class_vo.label,
        )
        self._db_save_node(new_instance)

        # Connect with root
        root.has_sponsor_model_instance.connect(new_instance)

        return new_instance

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: DatasetClass,
        library: Library,
        relationship: VersionRelationship,
        value: SponsorModelDatasetClassInstance,
        **_kwargs,
    ) -> SponsorModelDatasetClassAR:
        (
            sponsor_model_name,
            sponsor_model_version,
        ) = get_sponsor_model_info_from_dataset_class(value)
        return SponsorModelDatasetClassAR.from_repository_values(
            dataset_class_uid=root.uid,
            sponsor_model_dataset_class_vo=SponsorModelDatasetClassVO.from_repository_values(
                sponsor_model_name=sponsor_model_name,
                sponsor_model_version_number=sponsor_model_version,
                dataset_class_uid=root.uid,
                is_basic_std=value.is_basic_std,
                xml_path=value.xml_path,
                xml_title=value.xml_title,
                structure=value.structure,
                purpose=value.purpose,
                comment=value.comment,
                label=value.label,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _maintain_parameters(
        self,
        versioned_object: SponsorModelDatasetClassAR,
        root: DatasetClass,
        value: SponsorModelDatasetClassInstance,
    ) -> None:
        # This method from parent repo is not needed for this repo
        # So we use pass to skip implementation
        pass
