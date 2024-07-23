from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    DatasetClass,
    DatasetClassInstance,
)
from clinical_mdr_api.domain_repositories.standard_data_models.standard_data_model_repository import (
    StandardDataModelRepository,
)
from clinical_mdr_api.models.standard_data_models.dataset_class import (
    DatasetClass as DatasetClassAPIModel,
)


class DatasetClassRepository(StandardDataModelRepository):
    root_class = DatasetClass
    value_class = DatasetClassInstance
    return_model = DatasetClassAPIModel

    # pylint: disable=unused-argument
    def generic_match_clause(
        self, versioning_relationship: str, uid: str | None = None
    ):
        standard_data_model_label = self.root_class.__label__
        standard_data_model_value_label = self.value_class.__label__
        uid_filter = ""
        if uid:
            uid_filter = f"{{uid: '{uid}'}}"
        return f"""MATCH (standard_root:{standard_data_model_label} {uid_filter})-[:HAS_INSTANCE]->
                (standard_value:{standard_data_model_value_label})"""

    def specific_alias_clause(self) -> str:
        return """
        WITH *,
            standard_value.label AS label,
            standard_value.title AS title,
            head([(standard_root)<-[:HAS_DATASET_CLASS]-(catalogue:DataModelCatalogue) | catalogue.name]) AS catalogue_name,
            head([(standard_value)-[:HAS_PARENT_CLASS]->(parent_class:DatasetClassInstance) | parent_class.label]) AS parent_class,
            [(standard_value)<-[has_dataset_class:HAS_DATASET_CLASS]-(data_model_value:DataModelValue) | {
                data_model_name: data_model_value.name,
                ordinal:has_dataset_class.ordinal
            }
            ] AS data_models
        """
