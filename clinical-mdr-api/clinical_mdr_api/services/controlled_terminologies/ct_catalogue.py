from datetime import datetime

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.domains._utils import normalize_string
from clinical_mdr_api.domains.controlled_terminologies.ct_catalogue import CTCatalogueAR
from clinical_mdr_api.models import CTCatalogueChanges
from clinical_mdr_api.oauth.user import user
from clinical_mdr_api.repositories.ct_catalogues import (
    CatalogueComparisonType,
    get_ct_catalogues_changes,
)
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore


class CTCatalogueService:
    _repos: MetaRepository

    def __init__(self):
        self.user_initials = user().id()
        self._repos = MetaRepository(self.user_initials)

    def _close_all_repos(self) -> None:
        self._repos.close()

    @classmethod
    def _models_ct_catalogue_from_ct_catalogue_ar(
        cls, ct_catalogue_ar: CTCatalogueAR
    ) -> models.CTCatalogue:
        return models.CTCatalogue(
            name=ct_catalogue_ar.name, library_name=ct_catalogue_ar.library_name
        )

    def get_all_ct_catalogues(
        self, library_name: str | None
    ) -> list[models.CTCatalogue]:
        if (
            library_name is not None
            and not self._repos.library_repository.library_exists(
                normalize_string(library_name)
            )
        ):
            raise exceptions.BusinessLogicException(
                f"There is no library identified by provided library name ({library_name})"
            )
        try:
            all_ct_catalogues = self._repos.ct_catalogue_repository.find_all(
                library_name=library_name
            )
            return [
                self._models_ct_catalogue_from_ct_catalogue_ar(ct_catalogue_ar)
                for ct_catalogue_ar in all_ct_catalogues
            ]
        finally:
            self._close_all_repos()

    def get_ct_catalogues_changes(
        self,
        library_name: str | None,
        catalogue_name: str | None,
        comparison_type: str,
        start_datetime: datetime,
        end_datetime: datetime,
    ) -> CTCatalogueChanges:
        try:
            if end_datetime < start_datetime:
                raise exceptions.BusinessLogicException(
                    f"End datetime ({end_datetime}) can't be older than "
                    f"start datetime ({start_datetime})"
                )

            if (
                library_name is not None
                and not self._repos.library_repository.library_exists(
                    normalize_string(library_name)
                )
            ):
                raise exceptions.BusinessLogicException(
                    f"There is no library identified by provided library name ({library_name})"
                )

            if (
                catalogue_name is not None
                and not self._repos.ct_catalogue_repository.catalogue_exists(
                    normalize_string(catalogue_name)
                )
            ):
                raise exceptions.BusinessLogicException(
                    f"There is no catalogue identified by provided catalogue name ({catalogue_name})"
                )

            comparison_type = comparison_type.lower()
            if comparison_type == "attributes":
                comp_type = CatalogueComparisonType.ATTRIBUTES_COMPARISON
            elif comparison_type == "sponsor":
                comp_type = CatalogueComparisonType.SPONSOR_COMPARISON
            else:
                raise exceptions.BusinessLogicException(
                    f"The following type ({comparison_type}) is not valid catalogue comparison type."
                )

            result = get_ct_catalogues_changes(
                library_name=library_name,
                catalogue_name=catalogue_name,
                comparison_type=comp_type,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
            )

            return CTCatalogueChanges.from_repository_output(
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                query_output=result,
            )
        finally:
            self._close_all_repos()
