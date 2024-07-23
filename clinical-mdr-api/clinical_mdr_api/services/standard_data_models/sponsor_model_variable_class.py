from clinical_mdr_api.domain_repositories.standard_data_models.sponsor_model_variable_class_repository import (
    SponsorModelVariableClassRepository,
)
from clinical_mdr_api.domains.standard_data_models.sponsor_model_variable_class import (
    SponsorModelVariableClassAR,
    SponsorModelVariableClassVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.standard_data_models.sponsor_model_variable_class import (
    SponsorModelVariableClass,
    SponsorModelVariableClassInput,
)
from clinical_mdr_api.services.neomodel_ext_generic import NeomodelExtGenericService


class SponsorModelVariableClassService(NeomodelExtGenericService):
    repository_interface = SponsorModelVariableClassRepository
    api_model_class = SponsorModelVariableClass

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: SponsorModelVariableClassAR
    ) -> SponsorModelVariableClass:
        return SponsorModelVariableClass.from_sponsor_model_variable_class_ar(
            sponsor_model_variable_class_ar=item_ar,
        )

    def _create_aggregate_root(
        self, item_input: SponsorModelVariableClassInput, library: LibraryVO
    ) -> SponsorModelVariableClassAR:
        return SponsorModelVariableClassAR.from_input_values(
            author=self.user_initials,
            sponsor_model_variable_class_vo=SponsorModelVariableClassVO.from_repository_values(
                dataset_class_uid=item_input.dataset_class_uid,
                variable_class_uid=item_input.variable_class_uid,
                sponsor_model_name=item_input.sponsor_model_name,
                sponsor_model_version_number=item_input.sponsor_model_version_number,
                is_basic_std=item_input.is_basic_std,
                label=item_input.label,
                order=item_input.order,
                variable_type=item_input.variable_type,
                length=item_input.length,
                display_format=item_input.display_format,
                xml_datatype=item_input.xml_datatype,
                xml_codelist=item_input.xml_codelist,
                core=item_input.core,
                origin=item_input.origin,
                role=item_input.role,
                term=item_input.term,
                algorithm=item_input.algorithm,
                qualifiers=item_input.qualifiers,
                comment=item_input.comment,
                ig_comment=item_input.ig_comment,
                map_var_flag=item_input.map_var_flag,
                fixed_mapping=item_input.fixed_mapping,
                include_in_raw=item_input.include_in_raw,
                nn_internal=item_input.nn_internal,
                incl_cre_domain=item_input.incl_cre_domain,
                xml_codelist_values=item_input.xml_codelist_values,
            ),
            library=library,
        )

    def _edit_aggregate(
        self,
        item: SponsorModelVariableClassAR,
        item_edit_input: SponsorModelVariableClassInput,
    ) -> SponsorModelVariableClassAR:
        item.edit_draft(
            author=self.user_initials,
            sponsor_model_vo=SponsorModelVariableClassVO.from_repository_values(
                dataset_class_uid=item_edit_input.dataset_class_uid,
                variable_class_uid=item_edit_input.variable_class_uid,
                sponsor_model_name=item_edit_input.sponsor_model_name,
                sponsor_model_version_number=item_edit_input.sponsor_model_version_number,
                is_basic_std=item_edit_input.is_basic_std,
                label=item_edit_input.label,
                order=item_edit_input.order,
                variable_type=item_edit_input.variable_type,
                length=item_edit_input.length,
                display_format=item_edit_input.display_format,
                xml_datatype=item_edit_input.xml_datatype,
                xml_codelist=item_edit_input.xml_codelist,
                core=item_edit_input.core,
                origin=item_edit_input.origin,
                role=item_edit_input.role,
                term=item_edit_input.term,
                algorithm=item_edit_input.algorithm,
                qualifiers=item_edit_input.qualifiers,
                comment=item_edit_input.comment,
                ig_comment=item_edit_input.ig_comment,
                map_var_flag=item_edit_input.map_var_flag,
                fixed_mapping=item_edit_input.fixed_mapping,
                include_in_raw=item_edit_input.include_in_raw,
                nn_internal=item_edit_input.nn_internal,
                incl_cre_domain=item_edit_input.incl_cre_domain,
                xml_codelist_values=item_edit_input.xml_codelist_values,
            ),
        )
        return item
