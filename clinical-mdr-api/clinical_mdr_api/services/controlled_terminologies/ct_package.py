from datetime import date

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.models import (
    CTPackage,
    CTPackageChanges,
    CTPackageChangesSpecificCodelist,
    CTPackageDates,
)
from clinical_mdr_api.oauth.user import user
from clinical_mdr_api.repositories.ct_packages import (
    get_ct_packages_changes,
    get_ct_packages_codelist_changes,
)
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore
from clinical_mdr_api.services._utils import normalize_string


class CTPackageService:
    _repos: MetaRepository

    def __init__(self):
        self.user_initials = user().id()
        self._repos = MetaRepository(self.user_initials)

    def _close_all_repos(self) -> None:
        self._repos.close()

    def get_all_ct_packages(
        self,
        catalogue_name: str | None,
        standards_only: bool = True,
        sponsor_only: bool = False,
    ) -> list[models.CTPackage]:
        try:
            if (
                catalogue_name is not None
                and not self._repos.ct_catalogue_repository.catalogue_exists(
                    normalize_string(catalogue_name)
                )
            ):
                raise exceptions.BusinessLogicException(
                    f"There is no catalogue identified by provided catalogue name ({catalogue_name})"
                )

            if standards_only and sponsor_only:
                standards_only = False

            all_ct_packages = self._repos.ct_package_repository.find_all(
                catalogue_name=catalogue_name,
                standards_only=standards_only,
                sponsor_only=sponsor_only,
            )
            return [
                CTPackage.from_ct_package_ar(ct_package_ar)
                for ct_package_ar in all_ct_packages
            ]
        finally:
            self._close_all_repos()

    def get_all_effective_dates(self, catalogue_name: str) -> models.CTPackageDates:
        try:
            if not self._repos.ct_catalogue_repository.catalogue_exists(
                normalize_string(catalogue_name)
            ):
                raise exceptions.BusinessLogicException(
                    f"There is no catalogue identified by provided catalogue name ({catalogue_name})"
                )

            all_ct_packages = self._repos.ct_package_repository.find_all(
                catalogue_name=catalogue_name
            )
            all_effective_dates = [
                package.effective_date for package in all_ct_packages
            ]
            return CTPackageDates.from_repository_output(
                catalogue_name=catalogue_name, effective_dates=all_effective_dates
            )
        finally:
            self._close_all_repos()

    def create_sponsor_ct_package(
        self, extends_package: str, effective_date: date
    ) -> models.CTPackage:
        try:
            sponsor_package_ar = (
                self._repos.ct_package_repository.create_sponsor_package(
                    extends_package=extends_package,
                    effective_date=effective_date,
                    user_initials=self.user_initials,
                )
            )
            return CTPackage.from_ct_package_ar(sponsor_package_ar)
        finally:
            self._close_all_repos()

    def get_ct_packages_changes(
        self, catalogue_name: str, old_package_date: date, new_package_date: date
    ) -> CTPackageChanges:
        try:
            old_package, new_package = self.validate_input_and_get_packages(
                catalogue_name=catalogue_name,
                old_package_date=old_package_date,
                new_package_date=new_package_date,
            )

            result = get_ct_packages_changes(
                old_package_name=old_package.name,
                new_package_name=new_package.name,
            )

            return CTPackageChanges.from_repository_output(
                old_package_name=old_package.name,
                new_package_name=new_package.name,
                query_output=result,
            )
        finally:
            self._close_all_repos()

    def get_ct_package_by_uid(
        self,
        ct_package_uid: str,
    ) -> CTPackage:
        try:
            return self._repos.ct_package_repository.find_by_uid(uid=ct_package_uid)
        finally:
            self._close_all_repos()

    def get_ct_packages_codelist_changes(
        self,
        catalogue_name: str,
        old_package_date: date,
        new_package_date: date,
        codelist_uid: str,
    ) -> CTPackageChanges:
        try:
            old_package, new_package = self.validate_input_and_get_packages(
                catalogue_name=catalogue_name,
                old_package_date=old_package_date,
                new_package_date=new_package_date,
                codelist_uid=codelist_uid,
            )

            result = get_ct_packages_codelist_changes(
                old_package_name=old_package.name,
                new_package_name=new_package.name,
                codelist_uid=codelist_uid,
            )

            return CTPackageChangesSpecificCodelist.from_repository_output(
                old_package_name=old_package.name,
                new_package_name=new_package.name,
                query_output=result,
            )
        finally:
            self._close_all_repos()

    def validate_input_and_get_packages(
        self,
        catalogue_name: str,
        old_package_date: date,
        new_package_date: date,
        codelist_uid: str | None = None,
    ):
        if new_package_date < old_package_date:
            raise exceptions.BusinessLogicException(
                "New package can't be older than old package"
            )

        if not self._repos.ct_catalogue_repository.catalogue_exists(
            normalize_string(catalogue_name)
        ):
            raise exceptions.BusinessLogicException(
                f"There is no catalogue identified by provided catalogue name ({catalogue_name})"
            )

        old_package = self._repos.ct_package_repository.find_by_catalogue_and_date(
            catalogue_name=catalogue_name, package_date=old_package_date
        )
        if old_package is None:
            raise exceptions.BusinessLogicException(
                f"There is no package with the following date ({old_package_date}) for the following catalogue"
                f" ({catalogue_name})"
            )

        new_package = self._repos.ct_package_repository.find_by_catalogue_and_date(
            catalogue_name=catalogue_name, package_date=new_package_date
        )
        if new_package is None:
            raise exceptions.BusinessLogicException(
                f"There is no package with the following date ({new_package_date}) for the following catalogue"
                f" ({catalogue_name})"
            )
        if (
            codelist_uid is not None
            and not self._repos.ct_codelist_attribute_repository.codelist_exists(
                normalize_string(codelist_uid)
            )
        ):
            raise exceptions.BusinessLogicException(
                f"There is no CTCodelistRoot identified by provided codelist uid ({codelist_uid})"
            )

        return old_package, new_package
