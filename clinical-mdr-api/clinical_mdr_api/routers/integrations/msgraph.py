"""MS Graph API integrations router"""

from fastapi import APIRouter, Query
from pydantic import constr

from clinical_mdr_api.models.integrations import msgraph as msgraph_model
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.integrations import msgraph

# Prefixed with "/integrations/ms-graph"
router = APIRouter()


@router.get(
    "/users",
    dependencies=[rbac.ANY],
    summary="List users of the relevant AD groups",
    description="Lists all users whose name, initials or email match the optional `search` parameter (regex)"
    " and who are members of relevant AD groups.",
    status_code=200,
    response_model=list[msgraph_model.GraphUser],
    response_model_by_alias=False,
    response_model_exclude_none=True,
    responses={
        500: _generic_descriptions.ERROR_500,
    },
)
async def get_users(
    search: constr(strip_whitespace=True, min_length=2, max_length=255)
    | None = Query(
        None,
        title="Filter users by name or initials",
    ),
):
    if msgraph.service:
        return await msgraph.service.search_all_group_direct_member_users(search)
    return []
