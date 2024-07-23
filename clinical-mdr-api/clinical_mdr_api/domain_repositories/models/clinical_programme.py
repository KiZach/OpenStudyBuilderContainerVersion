from neomodel import StringProperty

from clinical_mdr_api.domain_repositories.models.generic import ClinicalMdrNodeWithUID


class ClinicalProgramme(ClinicalMdrNodeWithUID):
    name = StringProperty()
