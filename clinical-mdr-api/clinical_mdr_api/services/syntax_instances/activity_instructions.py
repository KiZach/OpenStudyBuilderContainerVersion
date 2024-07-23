from clinical_mdr_api import models
from clinical_mdr_api.domain_repositories.syntax_instances.activity_instruction_repository import (
    ActivityInstructionRepository,
)
from clinical_mdr_api.domain_repositories.syntax_templates.activity_instruction_template_repository import (
    ActivityInstructionTemplateRepository,
)
from clinical_mdr_api.domains.syntax_instances.activity_instruction import (
    ActivityInstructionAR,
)
from clinical_mdr_api.services.syntax_instances.generic_syntax_instance_service import (
    GenericSyntaxInstanceService,
    _AggregateRootType,
)


class ActivityInstructionService(
    GenericSyntaxInstanceService[ActivityInstructionAR | _AggregateRootType]
):
    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActivityInstructionAR
    ) -> models.ActivityInstruction:
        return models.ActivityInstruction.from_activity_instruction_ar(item_ar)

    aggregate_class = ActivityInstructionAR
    repository_interface = ActivityInstructionRepository
    template_repository_interface = ActivityInstructionTemplateRepository
    template_uid_property = "activity_instruction_template_uid"
    version_class = models.ActivityInstructionVersion
