from fastapi import APIRouter, Query

from clinical_mdr_api import models
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services import template_parameters as service

# Prefixed with "/template-parameters"
router = APIRouter()


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all template parameter available with samples of the available values.",
    description="The returned template parameter are ordered by\n0. name ascending",
    response_model=list[models.TemplateParameter],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_template_parameters():
    return service.get_all()


@router.get(
    "/{name}/terms",
    dependencies=[rbac.LIBRARY_READ],
    summary="Return all terms available for the given template parameter.",
    response_model=list[models.TemplateParameterTerm],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_template_parameter_terms(
    name: str = Query(..., description="Name of the template parameter")
):
    return service.get_template_parameter_terms(name)
