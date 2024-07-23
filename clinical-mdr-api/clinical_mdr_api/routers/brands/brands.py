from fastapi import APIRouter, Body, Path, Response, status

from clinical_mdr_api import models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.brands.brand import BrandService

# Prefixed with "/brands"
router = APIRouter()

BrandUID = Path(None, description="The unique id of brand")
Service = BrandService


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all brands.",
    response_model=list[models.Brand],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_brands() -> list[models.Brand]:
    return Service().get_all_brands()


@router.get(
    "/{uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the brand identified by the specified 'uid'.",
    response_model=models.Brand,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_brand(
    uid: str = BrandUID,
) -> models.Brand:
    return Service().get_brand(uid)


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates a new brand.",
    response_model=models.Brand,
    status_code=201,
    responses={
        201: {"description": "Created - The brand was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Some application/business rules forbid to process the request. Expect more detailed"
            " information in response body.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def create(
    brand_create_input: models.BrandCreateInput = Body(
        description="Related parameters of the brand that shall be created."
    ),
) -> models.Brand:
    return Service().create(brand_create_input)


@router.delete(
    "/{uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Deletes the brand identified by 'uid'.",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The item was successfully deleted."},
        500: _generic_descriptions.ERROR_500,
    },
)
def delete(uid: str = BrandUID) -> None:
    Service().delete(uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
