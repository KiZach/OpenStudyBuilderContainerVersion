from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    CustomNodeSet,
    to_relation_trees,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    DatasetClass,
    SponsorModelDatasetClassInstance,
    SponsorModelVariableClassInstance,
    VariableClass,
)
from clinical_mdr_api.domain_repositories.neomodel_ext_item_repository import (
    NeomodelExtBaseRepository,
)
from clinical_mdr_api.domain_repositories.standard_data_models.utils import (
    get_sponsor_model_info_from_dataset_class,
)
from clinical_mdr_api.domains.standard_data_models.sponsor_model_variable_class import (
    SponsorModelVariableClassAR,
    SponsorModelVariableClassVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.exceptions import BusinessLogicException
from clinical_mdr_api.models.standard_data_models.sponsor_model_variable_class import (
    SponsorModelVariableClass,
)


class SponsorModelVariableClassRepository(
    NeomodelExtBaseRepository,
    LibraryItemRepositoryImplBase[SponsorModelVariableClassAR],
):
    root_class = VariableClass
    value_class = SponsorModelVariableClassInstance
    return_model = SponsorModelVariableClass

    def get_neomodel_extension_query(self) -> CustomNodeSet:
        return VariableClass.nodes.fetch_relations(
            "has_sponsor_model_instance__has_variable_class",
            "has_variable_class__has_library",
        )

    def _has_data_changed(
        self,
        ar: SponsorModelVariableClassAR,
        value: SponsorModelVariableClassInstance,
    ) -> bool:
        return (
            ar.sponsor_model_variable_class_vo.is_basic_std != value.is_basic_std
            or ar.sponsor_model_variable_class_vo.label != value.label
            or ar.sponsor_model_variable_class_vo.variable_type != value.variable_type
            or ar.sponsor_model_variable_class_vo.length != value.length
            or ar.sponsor_model_variable_class_vo.display_format != value.display_format
            or ar.sponsor_model_variable_class_vo.xml_datatype != value.xml_datatype
            or ar.sponsor_model_variable_class_vo.xml_codelist != value.xml_codelist
            or ar.sponsor_model_variable_class_vo.core != value.core
            or ar.sponsor_model_variable_class_vo.origin != value.origin
            or ar.sponsor_model_variable_class_vo.role != value.role
            or ar.sponsor_model_variable_class_vo.term != value.term
            or ar.sponsor_model_variable_class_vo.algorithm != value.algorithm
            or ar.sponsor_model_variable_class_vo.qualifiers != value.qualifiers
            or ar.sponsor_model_variable_class_vo.comment != value.comment
            or ar.sponsor_model_variable_class_vo.ig_comment != value.ig_comment
            or ar.sponsor_model_variable_class_vo.map_var_flag != value.map_var_flag
            or ar.sponsor_model_variable_class_vo.fixed_mapping != value.fixed_mapping
            or ar.sponsor_model_variable_class_vo.include_in_raw != value.include_in_raw
            or ar.sponsor_model_variable_class_vo.nn_internal != value.nn_internal
            or ar.sponsor_model_variable_class_vo.incl_cre_domain
            != value.incl_cre_domain
            or ar.sponsor_model_variable_class_vo.xml_codelist_values
            != value.xml_codelist_values
        )

    def _create(self, item: SponsorModelVariableClassAR) -> SponsorModelVariableClassAR:
        """
        Overrides generic LibraryItemRepository method
        """
        root = VariableClass.nodes.get_or_none(uid=item.uid)

        if root is None:
            root = VariableClass(uid=item.uid).save()

        instance = self._get_or_create_instance(root=root, ar=item)

        # Connect with SponsorModelDatasetClassInstance
        parent_dataset_class_instance = to_relation_trees(
            SponsorModelDatasetClassInstance.nodes.filter(
                is_instance_of__uid=item.sponsor_model_variable_class_vo.dataset_class_uid,
                has_dataset_class__name=item.sponsor_model_variable_class_vo.sponsor_model_name,
            )
        )
        if parent_dataset_class_instance:
            instance.has_variable_class.connect(
                parent_dataset_class_instance[0],
                {
                    "ordinal": item.sponsor_model_variable_class_vo.order,
                    "version_number": item.sponsor_model_variable_class_vo.sponsor_model_version_number,
                },
            )
        else:
            raise BusinessLogicException(
                f"The DatasetClass {item.sponsor_model_variable_class_vo.dataset_class_uid} is not instantiated in this version of the sponsor model."
            )

        return item

    def _get_or_create_instance(
        self, root: VariableClass, ar: SponsorModelVariableClassAR
    ) -> SponsorModelVariableClassInstance:
        for itm in root.has_sponsor_model_instance.all():
            if not self._has_data_changed(ar, itm):
                return itm

        new_instance = SponsorModelVariableClassInstance(
            is_basic_std=ar.sponsor_model_variable_class_vo.is_basic_std,
            label=ar.sponsor_model_variable_class_vo.label,
            order=ar.sponsor_model_variable_class_vo.order,
            variable_type=ar.sponsor_model_variable_class_vo.variable_type,
            length=ar.sponsor_model_variable_class_vo.length,
            display_format=ar.sponsor_model_variable_class_vo.display_format,
            xml_datatype=ar.sponsor_model_variable_class_vo.xml_datatype,
            xml_codelist=ar.sponsor_model_variable_class_vo.xml_codelist,
            core=ar.sponsor_model_variable_class_vo.core,
            origin=ar.sponsor_model_variable_class_vo.origin,
            role=ar.sponsor_model_variable_class_vo.role,
            term=ar.sponsor_model_variable_class_vo.term,
            algorithm=ar.sponsor_model_variable_class_vo.algorithm,
            qualifiers=ar.sponsor_model_variable_class_vo.qualifiers,
            comment=ar.sponsor_model_variable_class_vo.comment,
            ig_comment=ar.sponsor_model_variable_class_vo.ig_comment,
            map_var_flag=ar.sponsor_model_variable_class_vo.map_var_flag,
            fixed_mapping=ar.sponsor_model_variable_class_vo.fixed_mapping,
            include_in_raw=ar.sponsor_model_variable_class_vo.include_in_raw,
            nn_internal=ar.sponsor_model_variable_class_vo.nn_internal,
            incl_cre_domain=ar.sponsor_model_variable_class_vo.incl_cre_domain,
            xml_codelist_values=ar.sponsor_model_variable_class_vo.xml_codelist_values,
        )
        self._db_save_node(new_instance)

        # Connect with root
        root.has_sponsor_model_instance.connect(new_instance)

        return new_instance

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VariableClass,
        library: Library,
        relationship: VersionRelationship,
        value: SponsorModelVariableClassInstance,
        **_kwargs,
    ) -> SponsorModelVariableClassAR:
        # Get parent class-related info
        dataset_class_value: SponsorModelDatasetClassInstance = (
            value.has_variable_class.get_or_none()
        )
        dataset_class_uid = None
        sponsor_model_name = None
        sponsor_model_version = None
        ordinal = None
        if dataset_class_value is not None:
            # Get parent class uid
            dataset_class: DatasetClass = (
                dataset_class_value.has_sponsor_model_instance.single()
            )
            if dataset_class is not None:
                dataset_class_uid = dataset_class.uid

            # Get order in parent class
            dataset_class_rel = value.has_variable_class.relationship(
                dataset_class_value
            )
            if dataset_class_rel is not None:
                ordinal = dataset_class_rel.ordinal

            # Get sponsor model-related info
            (
                sponsor_model_name,
                sponsor_model_version,
            ) = get_sponsor_model_info_from_dataset_class(dataset_class_value)
        return SponsorModelVariableClassAR.from_repository_values(
            variable_class_uid=root.uid,
            sponsor_model_variable_class_vo=SponsorModelVariableClassVO.from_repository_values(
                dataset_class_uid=dataset_class_uid,
                variable_class_uid=root.uid,
                sponsor_model_name=sponsor_model_name,
                sponsor_model_version_number=sponsor_model_version,
                is_basic_std=value.is_basic_std,
                label=value.label,
                order=ordinal,
                variable_type=value.variable_type,
                length=value.length,
                display_format=value.display_format,
                xml_datatype=value.xml_datatype,
                xml_codelist=value.xml_codelist,
                core=value.core,
                origin=value.origin,
                role=value.role,
                term=value.term,
                algorithm=value.algorithm,
                qualifiers=value.qualifiers,
                comment=value.comment,
                ig_comment=value.ig_comment,
                map_var_flag=value.map_var_flag,
                fixed_mapping=value.fixed_mapping,
                include_in_raw=value.include_in_raw,
                nn_internal=value.nn_internal,
                incl_cre_domain=value.incl_cre_domain,
                xml_codelist_values=value.xml_codelist_values,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _maintain_parameters(
        self,
        versioned_object: SponsorModelVariableClassAR,
        root: VariableClass,
        value: SponsorModelVariableClassInstance,
    ) -> None:
        # This method from parent repo is not needed for this repo
        # So we use pass to skip implementation
        pass
