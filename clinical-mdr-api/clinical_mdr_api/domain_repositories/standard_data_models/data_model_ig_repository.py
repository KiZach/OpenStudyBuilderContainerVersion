from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    DataModelIGRoot,
    DataModelIGValue,
)
from clinical_mdr_api.domain_repositories.standard_data_models.standard_data_model_repository import (
    StandardDataModelRepository,
)
from clinical_mdr_api.models.standard_data_models.data_model_ig import DataModelIG


class DataModelIGRepository(StandardDataModelRepository):
    root_class = DataModelIGRoot
    value_class = DataModelIGValue
    return_model = DataModelIG

    def specific_alias_clause(self) -> str:
        return """
        WITH *,
            standard_value.version_number AS version_number,
            head([(standard_value)-[:IMPLEMENTS]->(implemented_data_model_value:DataModelValue)<-[:HAS_VERSION]-
            (implemented_data_model_root:DataModelRoot) | 
                {uid:implemented_data_model_root.uid, name:implemented_data_model_value.name}]) AS implemented_data_model
        """
