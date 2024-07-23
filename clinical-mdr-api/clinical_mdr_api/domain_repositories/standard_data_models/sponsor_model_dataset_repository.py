from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domain_repositories.models._utils import CustomNodeSet
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    Dataset,
    DatasetVariable,
    SponsorModelDatasetInstance,
    SponsorModelValue,
)
from clinical_mdr_api.domain_repositories.neomodel_ext_item_repository import (
    NeomodelExtBaseRepository,
)
from clinical_mdr_api.domain_repositories.standard_data_models.utils import (
    get_sponsor_model_info_from_dataset,
)
from clinical_mdr_api.domains.standard_data_models.sponsor_model_dataset import (
    SponsorModelDatasetAR,
    SponsorModelDatasetVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.exceptions import BusinessLogicException
from clinical_mdr_api.models.standard_data_models.sponsor_model_dataset import (
    SponsorModelDataset,
)


class SponsorModelDatasetRepository(
    NeomodelExtBaseRepository, LibraryItemRepositoryImplBase[SponsorModelDatasetAR]
):
    root_class = Dataset
    value_class = SponsorModelDatasetInstance
    return_model = SponsorModelDataset

    def get_neomodel_extension_query(self) -> CustomNodeSet:
        return Dataset.nodes.fetch_relations(
            "has_sponsor_model_instance__has_dataset",
            "has_dataset__has_library",
        ).fetch_optional_relations_and_collect(
            "has_sponsor_model_instance__has_key",
            "has_sponsor_model_instance__has_sort_key",
        )

    def _has_data_changed(
        self, ar: SponsorModelDatasetAR, value: SponsorModelDatasetInstance
    ) -> bool:
        return (
            ar.sponsor_model_dataset_vo.is_basic_std != value.is_basic_std
            or ar.sponsor_model_dataset_vo.xml_path != value.xml_path
            or ar.sponsor_model_dataset_vo.xml_title != value.xml_title
            or ar.sponsor_model_dataset_vo.structure != value.structure
            or ar.sponsor_model_dataset_vo.purpose != value.purpose
            or ar.sponsor_model_dataset_vo.source_ig != value.source_ig
            or ar.sponsor_model_dataset_vo.comment != value.comment
            or ar.sponsor_model_dataset_vo.ig_comment != value.ig_comment
            or ar.sponsor_model_dataset_vo.map_domain_flag != value.map_domain_flag
            or ar.sponsor_model_dataset_vo.suppl_qual_flag != value.suppl_qual_flag
            or ar.sponsor_model_dataset_vo.include_in_raw != value.include_in_raw
            or ar.sponsor_model_dataset_vo.gen_raw_seqno_flag
            != value.gen_raw_seqno_flag
            or ar.sponsor_model_dataset_vo.label != value.label
            or ar.sponsor_model_dataset_vo.state != value.state
            or ar.sponsor_model_dataset_vo.extended_domain != value.extended_domain
        )

    def _create(self, item: SponsorModelDatasetAR) -> SponsorModelDatasetAR:
        """
        Overrides generic LibraryItemRepository method
        """
        root = Dataset.nodes.get_or_none(uid=item.uid)

        if root is None:
            root = Dataset(uid=item.uid).save()

        instance = self._get_or_create_instance(root=root, ar=item)

        # Connect with SponsorModelValue node
        parent_node = SponsorModelValue.nodes.get_or_none(
            name=item.sponsor_model_dataset_vo.sponsor_model_name
        )
        if parent_node:
            instance.has_dataset.connect(
                parent_node,
                {"ordinal": item.sponsor_model_dataset_vo.enrich_build_order},
            )
        else:
            raise BusinessLogicException(
                f"The given Sponsor Model version {item.sponsor_model_dataset_vo.sponsor_model_name} does not exist in the database."
            )

        return item

    def _get_or_create_instance(
        self, root: Dataset, ar: SponsorModelDatasetAR
    ) -> SponsorModelDatasetInstance:
        for itm in root.has_sponsor_model_instance.all():
            if not self._has_data_changed(ar, itm):
                return itm

        new_instance = SponsorModelDatasetInstance(
            is_basic_std=ar.sponsor_model_dataset_vo.is_basic_std,
            xml_path=ar.sponsor_model_dataset_vo.xml_path,
            xml_title=ar.sponsor_model_dataset_vo.xml_title,
            structure=ar.sponsor_model_dataset_vo.structure,
            purpose=ar.sponsor_model_dataset_vo.purpose,
            source_ig=ar.sponsor_model_dataset_vo.source_ig,
            comment=ar.sponsor_model_dataset_vo.comment,
            ig_comment=ar.sponsor_model_dataset_vo.ig_comment,
            map_domain_flag=ar.sponsor_model_dataset_vo.map_domain_flag,
            suppl_qual_flag=ar.sponsor_model_dataset_vo.suppl_qual_flag,
            include_in_raw=ar.sponsor_model_dataset_vo.include_in_raw,
            gen_raw_seqno_flag=ar.sponsor_model_dataset_vo.gen_raw_seqno_flag,
            label=ar.sponsor_model_dataset_vo.label,
            state=ar.sponsor_model_dataset_vo.state,
            extended_domain=ar.sponsor_model_dataset_vo.extended_domain,
        )
        self._db_save_node(new_instance)

        # Connect with root
        root.has_sponsor_model_instance.connect(new_instance)

        # Create relations
        # Find key & sort-key variable nodes
        if ar.sponsor_model_dataset_vo.keys is not None:
            keys = DatasetVariable.nodes.filter(
                uid__in=ar.sponsor_model_dataset_vo.keys
            )
            keys_dict = {key.uid: key for key in keys}
            for index, key in enumerate(ar.sponsor_model_dataset_vo.keys):
                if key in keys_dict:
                    new_instance.has_key.connect(keys_dict[key], {"order": index})

        if ar.sponsor_model_dataset_vo.sort_keys is not None:
            sort_keys = DatasetVariable.nodes.filter(
                uid__in=ar.sponsor_model_dataset_vo.sort_keys
            )
            sort_keys_dict = {key.uid: key for key in sort_keys}
            for index, key in enumerate(ar.sponsor_model_dataset_vo.sort_keys):
                if key in sort_keys_dict:
                    new_instance.has_sort_key.connect(keys_dict[key], {"order": index})

        return new_instance

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: Dataset,
        library: Library,
        relationship: VersionRelationship,
        value: SponsorModelDatasetInstance,
        **_kwargs,
    ) -> SponsorModelDatasetAR:
        sponsor_model_name = None
        sponsor_model_version = None
        enrich_build_order = None
        # Get sponsor model-related info
        (
            sponsor_model_name,
            sponsor_model_version,
            enrich_build_order,
        ) = get_sponsor_model_info_from_dataset(value)
        return SponsorModelDatasetAR.from_repository_values(
            dataset_uid=root.uid,
            sponsor_model_dataset_vo=SponsorModelDatasetVO.from_repository_values(
                sponsor_model_name=sponsor_model_name,
                sponsor_model_version_number=sponsor_model_version,
                dataset_uid=root.uid,
                is_basic_std=value.is_basic_std,
                xml_path=value.xml_path,
                xml_title=value.xml_title,
                structure=value.structure,
                purpose=value.purpose,
                keys=None,
                sort_keys=None,
                source_ig=value.source_ig,
                comment=value.comment,
                ig_comment=value.ig_comment,
                map_domain_flag=value.map_domain_flag,
                suppl_qual_flag=value.suppl_qual_flag,
                include_in_raw=value.include_in_raw,
                gen_raw_seqno_flag=value.gen_raw_seqno_flag,
                enrich_build_order=enrich_build_order,
                label=value.label,
                state=value.state,
                extended_domain=value.extended_domain,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _maintain_parameters(
        self,
        versioned_object: SponsorModelDatasetAR,
        root: Dataset,
        value: SponsorModelDatasetInstance,
    ) -> None:
        # This method from parent repo is not needed for this repo
        # So we use pass to skip implementation
        pass
