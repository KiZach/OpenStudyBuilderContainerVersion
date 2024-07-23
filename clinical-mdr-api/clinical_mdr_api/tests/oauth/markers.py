import pytest

from clinical_mdr_api.oauth import config

if_oauth_enabled = pytest.mark.skipif(
    not config.OAUTH_ENABLED, reason="Authentication is disabled"
)
