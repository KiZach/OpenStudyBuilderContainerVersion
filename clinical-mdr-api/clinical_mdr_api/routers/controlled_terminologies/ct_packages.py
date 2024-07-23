"""CTPackage router."""

from datetime import date

from fastapi import APIRouter, Body, Path, Query

from clinical_mdr_api import models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.controlled_terminologies.ct_package import (
    CTPackageService,
)

# Prefixed with "/ct"
router = APIRouter()

CTCodelistUid = Path(None, description="The unique id of the CTCodelist")


@router.get(
    "/packages",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all controlled terminology packages.",
    response_model=list[models.CTPackage],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_packages(
    catalogue_name: str
    | None = Query(
        None,
        description="If specified, only packages from given catalogue are returned.",
    ),
    standards_only: bool
    | None = Query(
        True,
        description="If set to True, only standard packages are returned. Defaults to True",
    ),
    sponsor_only: bool
    | None = Query(
        False,
        description="If set to True, only sponsor packages are returned.",
    ),
):
    ct_package_service = CTPackageService()

    return ct_package_service.get_all_ct_packages(
        catalogue_name=catalogue_name,
        standards_only=standards_only,
        sponsor_only=sponsor_only,
    )


@router.get(
    "/packages/changes",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns changes between codelists and terms inside two different packages.",
    response_model=models.CTPackageChanges,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_packages_changes_between_codelists_and_terms(
    catalogue_name: str,
    old_package_date: date = Query(
        ...,
        description="The date for the old package, for instance '2020-03-27'"
        "\n_the possible dates for given catalogue_name can be retrieved by the /ct/packages/dates endpoint",
    ),
    new_package_date: date = Query(
        ...,
        description="The datetime for the new package, for instance '2020-06-26'"
        "\n_the possible dates for given catalogue_name can be retrieved by the /ct/packages/dates endpoint",
    ),
):
    ct_package_service = CTPackageService()
    return ct_package_service.get_ct_packages_changes(
        catalogue_name=catalogue_name,
        old_package_date=old_package_date,
        new_package_date=new_package_date,
    )


@router.get(
    "/packages/{codelist_uid}/changes",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns changes from given codelist and all associated terms inside two different packages.",
    response_model=models.CTPackageChangesSpecificCodelist,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_packages_changes_between_codelist_and_all_associated_terms(
    catalogue_name: str,
    codelist_uid: str = CTCodelistUid,
    old_package_date: date = Query(
        ...,
        description="The date for the old package, for instance '2020-03-27'"
        "\n_the possible dates for given catalogue_name can be retrieved by the /ct/packages/dates endpoint",
    ),
    new_package_date: date = Query(
        ...,
        description="The date for the new package, for instance '2020-06-26'"
        "\n_the possible dates for given catalogue_name can be retrieved by the /ct/packages/dates endpoint",
    ),
):
    ct_package_service = CTPackageService()
    return ct_package_service.get_ct_packages_codelist_changes(
        catalogue_name=catalogue_name,
        old_package_date=old_package_date,
        new_package_date=new_package_date,
        codelist_uid=codelist_uid,
    )


@router.get(
    "/packages/dates",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all effective dates for packages in a given catalogue.",
    response_model=models.CTPackageDates,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_package_dates(catalogue_name: str):
    ct_package_service = CTPackageService()
    return ct_package_service.get_all_effective_dates(catalogue_name=catalogue_name)


@router.post(
    "/packages/sponsor",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates a sponsor CT package, in the context of a study.",
    response_model=models.CTPackage,
    status_code=201,
    responses={
        201: {"description": "Created - The sponsor package was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Cannot create two CT Sponsor Packages with the same date.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Entity not found - Reasons include: \n"
            "- The parent package does not exist.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def create(
    extends_package: str = Body(
        ...,
        description="The name of the parent package that the sponsor package extends.",
    ),
    effective_date: date = Body(
        ...,
        description="The effective date of the package, for instance '2020-09-27'",
    ),
):
    ct_package_service = CTPackageService()
    return ct_package_service.create_sponsor_ct_package(extends_package, effective_date)
