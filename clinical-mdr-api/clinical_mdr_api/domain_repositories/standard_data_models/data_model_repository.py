from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    DataModelRoot,
    DataModelValue,
)
from clinical_mdr_api.domain_repositories.standard_data_models.standard_data_model_repository import (
    StandardDataModelRepository,
)
from clinical_mdr_api.models.standard_data_models.data_model import DataModel


class DataModelRepository(StandardDataModelRepository):
    root_class = DataModelRoot
    value_class = DataModelValue
    return_model = DataModel

    def specific_alias_clause(self) -> str:
        return """
        WITH *,
            standard_value.version_number AS version_number,
            [(standard_value)<-[:IMPLEMENTS]-(implementation_guide_value:DataModelIGValue)<-[:HAS_VERSION]-
            (implementation_guide_root:DataModelIGRoot) | 
                {uid:implementation_guide_root.uid, name:implementation_guide_value.name}] AS implementation_guides
        """
