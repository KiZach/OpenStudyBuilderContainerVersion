from typing import cast

from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    LATEST_VERSION_ORDER_BY,
    to_relation_trees,
)
from clinical_mdr_api.domain_repositories.models.configuration import (
    CTConfigRoot,
    CTConfigValue,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCodelistRoot,
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.syntax_templates.generic_syntax_template_repository import (
    _AggregateRootType,
)
from clinical_mdr_api.domains.controlled_terminologies.configurations import (
    CTConfigAR,
    CTConfigValueVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
)
from clinical_mdr_api.models.controlled_terminologies.configuration import CTConfigOGM


class CTConfigRepository(LibraryItemRepositoryImplBase[CTConfigAR]):
    value_class = CTConfigValue
    root_class = CTConfigRoot
    user: str
    has_library = False

    def find_all(
        self,
        *,
        status: LibraryItemStatus | None = None,
        library_name: str | None = None,
        return_study_count: bool | None = False,
    ) -> list[CTConfigOGM]:
        all_configurations = [
            CTConfigOGM.from_orm(sas_node)
            for sas_node in to_relation_trees(
                self.root_class.nodes.fetch_relations("has_latest_value")
                .fetch_optional_relations(
                    "has_latest_value__has_configured_codelist",
                    "has_latest_value__has_configured_term",
                )
                .fetch_optional_single_relation_of_type(
                    {
                        "has_version": ("latest_version", LATEST_VERSION_ORDER_BY),
                    }
                )
                .order_by("uid")
            )
        ]
        return all_configurations

    def generate_uid(self) -> str:
        return self.root_class.get_next_free_uid_and_increment_counter()

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> CTConfigAR:
        ar_root = cast(CTConfigRoot, root)
        ar_value = cast(CTConfigValue, value)
        configured_codelist = ar_value.has_configured_codelist.get_or_none()
        configured_term = ar_value.has_configured_term.get_or_none()
        result = CTConfigAR.from_repository_values(
            uid=ar_root.uid,
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
            ct_config_value=CTConfigValueVO.from_repository_values(
                study_field_name=ar_value.study_field_name,
                study_field_data_type=ar_value.study_field_data_type,
                study_field_null_value_code=ar_value.study_field_null_value_code,
                configured_codelist_uid=(
                    configured_codelist.uid if configured_codelist is not None else None
                ),
                configured_term_uid=(
                    configured_term.uid if configured_term is not None else None
                ),
                study_field_grouping=ar_value.study_field_grouping,
                study_field_name_api=ar_value.study_field_name_api,
                is_dictionary_term=ar_value.is_dictionary_term,
            ),
        )
        return result

    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: VersionRoot,
        value: VersionValue,
    ) -> None:
        # method required by interface, does nothing #
        pass

    def _get_or_create_value(self, root: VersionRoot, ar: CTConfigAR) -> VersionValue:
        value = CTConfigValue(
            study_field_name=ar.value.study_field_name,
            study_field_data_type=ar.value.study_field_data_type,
            study_field_null_value_code=ar.value.study_field_null_value_code,
            study_field_grouping=ar.value.study_field_grouping,
            study_field_name_api=ar.value.study_field_name_api,
            is_dictionary_term=ar.value.is_dictionary_term,
        )
        self._db_save_node(node=value)
        if ar.value.configured_codelist_uid is not None:
            codelist_root = CTCodelistRoot.nodes.get_or_none(
                uid=ar.value.configured_codelist_uid
            )
            if codelist_root:
                value.has_configured_codelist.connect(codelist_root)
        if ar.value.configured_term_uid is not None:
            term_root = CTTermRoot.nodes.get_or_none(uid=ar.value.configured_term_uid)
            if term_root:
                value.has_configured_term.connect(term_root)
        return value

    def _is_new_version_necessary(self, ar: CTConfigAR, value: VersionValue) -> bool:
        codelist_config_value = cast(CTConfigValue, value)
        val = (
            value.study_field_name != ar.value.study_field_name
            or codelist_config_value.study_field_data_type
            != ar.value.study_field_data_type
            or codelist_config_value.study_field_null_value_code
            != ar.value.study_field_null_value_code
            or self._get_uid_or_none(
                codelist_config_value.has_configured_codelist.get_or_none()
            )
            != ar.value.configured_codelist_uid
            or self._get_uid_or_none(
                codelist_config_value.has_configured_term.get_or_none()
            )
            != ar.value.configured_term_uid
            or codelist_config_value.study_field_grouping
            != ar.value.study_field_grouping
            or codelist_config_value.study_field_name_api
            != ar.value.study_field_name_api
            or codelist_config_value.is_dictionary_term != ar.value.is_dictionary_term
        )
        return val

    def _create(self, item: CTConfigAR) -> CTConfigAR:
        relation_data: LibraryItemMetadataVO = item.item_metadata
        root = self.root_class(uid=item.uid)
        self._db_save_node(root)

        value = self._get_or_create_value(root=root, ar=item)

        (
            root,
            value,
            _,
            _,
            _,
        ) = self._db_create_and_link_nodes(
            root, value, self._library_item_metadata_vo_to_datadict(relation_data)
        )
        self._maintain_parameters(item, root, value)

        return item
