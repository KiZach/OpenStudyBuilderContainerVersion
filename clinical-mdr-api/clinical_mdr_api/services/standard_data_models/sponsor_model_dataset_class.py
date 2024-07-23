from clinical_mdr_api.domain_repositories.standard_data_models.sponsor_model_dataset_class_repository import (
    SponsorModelDatasetClassRepository,
)
from clinical_mdr_api.domains.standard_data_models.sponsor_model_dataset_class import (
    SponsorModelDatasetClassAR,
    SponsorModelDatasetClassVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.standard_data_models.sponsor_model_dataset_class import (
    SponsorModelDatasetClass,
    SponsorModelDatasetClassInput,
)
from clinical_mdr_api.services.neomodel_ext_generic import NeomodelExtGenericService


class SponsorModelDatasetClassService(NeomodelExtGenericService):
    repository_interface = SponsorModelDatasetClassRepository
    api_model_class = SponsorModelDatasetClass

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: SponsorModelDatasetClassAR
    ) -> SponsorModelDatasetClass:
        return SponsorModelDatasetClass.from_sponsor_model_dataset_class_ar(
            sponsor_model_dataset_class_ar=item_ar,
        )

    def _create_aggregate_root(
        self, item_input: SponsorModelDatasetClassInput, library: LibraryVO
    ) -> SponsorModelDatasetClassAR:
        return SponsorModelDatasetClassAR.from_input_values(
            author=self.user_initials,
            sponsor_model_dataset_class_vo=SponsorModelDatasetClassVO.from_repository_values(
                sponsor_model_name=item_input.sponsor_model_name,
                sponsor_model_version_number=item_input.sponsor_model_version_number,
                dataset_class_uid=item_input.dataset_class_uid,
                is_basic_std=item_input.is_basic_std,
                xml_path=item_input.xml_path,
                xml_title=item_input.xml_title,
                structure=item_input.structure,
                purpose=item_input.purpose,
                comment=item_input.comment,
                label=item_input.label,
            ),
            library=library,
        )

    def _edit_aggregate(
        self,
        item: SponsorModelDatasetClassAR,
        item_edit_input: SponsorModelDatasetClassInput,
    ) -> SponsorModelDatasetClassAR:
        item.edit_draft(
            author=self.user_initials,
            sponsor_model_vo=SponsorModelDatasetClassVO.from_repository_values(
                sponsor_model_name=item_edit_input.sponsor_model_name,
                sponsor_model_version_number=item_edit_input.sponsor_model_version_number,
                dataset_class_uid=item_edit_input.dataset_class_uid,
                is_basic_std=item_edit_input.is_basic_std,
                xml_path=item_edit_input.xml_path,
                xml_title=item_edit_input.xml_title,
                structure=item_edit_input.structure,
                purpose=item_edit_input.purpose,
                comment=item_edit_input.comment,
                label=item_edit_input.label,
            ),
        )
        return item
