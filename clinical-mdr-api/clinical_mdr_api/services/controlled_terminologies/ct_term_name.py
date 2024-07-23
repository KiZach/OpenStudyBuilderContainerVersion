from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_name_repository import (
    CTTermNameRepository,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import (
    CTTermNameAR,
    CTTermNameVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import VersioningException
from clinical_mdr_api.models import CTTermName, CTTermNameVersion
from clinical_mdr_api.models.utils import BaseModel
from clinical_mdr_api.services.controlled_terminologies.ct_term_generic_service import (
    CTTermGenericService,
)


class CTTermNameService(CTTermGenericService[CTTermNameAR]):
    aggregate_class = CTTermNameAR
    repository_interface = CTTermNameRepository
    version_class = CTTermNameVersion

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: CTTermNameAR
    ) -> CTTermName:
        return CTTermName.from_ct_term_ar(item_ar)

    @db.transaction
    def edit_draft(self, term_uid: str, term_input: BaseModel) -> BaseModel:
        try:
            item = self._find_by_uid_or_raise_not_found(term_uid, for_update=True)

            item.edit_draft(
                author=self.user_initials,
                change_description=term_input.change_description,
                ct_term_vo=CTTermNameVO.from_input_values(
                    codelists=item.ct_term_vo.codelists,
                    catalogue_name=item.ct_term_vo.catalogue_name,
                    name=self.get_input_or_previous_property(
                        term_input.sponsor_preferred_name, item.ct_term_vo.name
                    ),
                    name_sentence_case=self.get_input_or_previous_property(
                        term_input.sponsor_preferred_name_sentence_case,
                        item.ct_term_vo.name_sentence_case,
                    ),
                    # passing always True callbacks, as we can't change catalogue
                    # in scope of CTTermName or CTTermAttributes, it can be only changed via CTTermRoot
                    codelist_exists_callback=lambda _: True,
                    catalogue_exists_callback=lambda _: True,
                ),
                term_exists_by_name_in_codelists_callback=self._repos.ct_term_name_repository.term_specific_exists_by_name_in_codelists,
            )
            self.repository.save(item)
            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)
