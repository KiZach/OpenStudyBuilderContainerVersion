from neomodel import BooleanProperty, StringProperty

from clinical_mdr_api.domain_repositories.models.generic import ClinicalMdrNodeWithUID


class Brand(ClinicalMdrNodeWithUID):
    name = StringProperty()
    is_deleted = BooleanProperty(default=False)
