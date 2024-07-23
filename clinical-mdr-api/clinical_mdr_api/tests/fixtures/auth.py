import logging

import pytest

from clinical_mdr_api.oauth.config import OAUTH_ENABLED
from clinical_mdr_api.oauth.dependencies import (
    dummy_access_token_claims,
    dummy_auth_object,
)

__all__ = ["mock_auth_context"]

log = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=not OAUTH_ENABLED)
def mock_auth_context(request):
    """Mock starlette context with dummy user data"""

    from starlette_context import context, request_cycle_context

    mocked_store = {"auth": dummy_auth_object(dummy_access_token_claims())}

    log.info(
        "%s fixture: mocking context with dummy auth user",
        request.fixturename,
    )

    with request_cycle_context(mocked_store):
        yield context
