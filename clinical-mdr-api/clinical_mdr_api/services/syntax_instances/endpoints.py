from clinical_mdr_api.domain_repositories.syntax_instances.endpoint_repository import (
    EndpointRepository,
)
from clinical_mdr_api.domain_repositories.syntax_templates.endpoint_template_repository import (
    EndpointTemplateRepository,
)
from clinical_mdr_api.domains.syntax_instances.endpoint import EndpointAR
from clinical_mdr_api.models.syntax_instances.endpoint import Endpoint, EndpointVersion
from clinical_mdr_api.services.syntax_instances.generic_syntax_instance_service import (
    GenericSyntaxInstanceService,
    _AggregateRootType,
)


class EndpointService(GenericSyntaxInstanceService[EndpointAR | _AggregateRootType]):
    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: EndpointAR
    ) -> Endpoint:
        return Endpoint.from_endpoint_ar(item_ar)

    aggregate_class = EndpointAR
    repository_interface = EndpointRepository
    template_repository_interface = EndpointTemplateRepository
    version_class = EndpointVersion
    template_uid_property = "endpoint_template_uid"
