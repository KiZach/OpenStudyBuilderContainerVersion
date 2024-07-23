from neomodel import db  # type: ignore

from clinical_mdr_api import models
from clinical_mdr_api.domains.clinical_programmes.clinical_programme import (
    ClinicalProgrammeAR,
)
from clinical_mdr_api.models import ClinicalProgrammeInput
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore
from clinical_mdr_api.services._utils import service_level_generic_filtering


def _models_clinical_programme_from_clinical_programme_ar(
    clinical_programme_ar: ClinicalProgrammeAR,
) -> models.ClinicalProgramme:
    return models.ClinicalProgramme(
        uid=clinical_programme_ar.uid, name=clinical_programme_ar.name
    )


def get_all_clinical_programmes(
    sort_by: dict | None = None,
    page_number: int = 1,
    page_size: int = 10,
    filter_by: dict | None = None,
    filter_operator: FilterOperator | None = FilterOperator.AND,
    total_count: bool = False,
) -> GenericFilteringReturn[models.ClinicalProgramme]:
    repos = MetaRepository()
    try:
        all_clinical_programmes = repos.clinical_programme_repository.find_all()
        repos.clinical_programme_repository.close()
        items = [
            _models_clinical_programme_from_clinical_programme_ar(clinical_programme)
            for clinical_programme in all_clinical_programmes
        ]
        filtered_items = service_level_generic_filtering(
            items=items,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )
        return GenericFilteringReturn.create(filtered_items.items, filtered_items.total)
    finally:
        repos.close()


@db.transaction
def create(
    clinical_programme_create_input: ClinicalProgrammeInput,
) -> models.ClinicalProgramme:
    repos = MetaRepository()
    try:
        clinical_programme_ar = ClinicalProgrammeAR.from_input_values(
            name=clinical_programme_create_input.name,
            generate_uid_callback=repos.clinical_programme_repository.generate_uid,
        )
        repos.clinical_programme_repository.save(clinical_programme_ar)
        return _models_clinical_programme_from_clinical_programme_ar(
            clinical_programme_ar
        )
    finally:
        repos.close()
