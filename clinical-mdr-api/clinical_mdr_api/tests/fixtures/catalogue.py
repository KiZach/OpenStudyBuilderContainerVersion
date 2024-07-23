"""Catalogue related fixtures"""

# pylint: disable=unused-import,redefined-outer-name,unused-argument

import logging

import pytest

from clinical_mdr_api.tests.fixtures.database import temp_database
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

__all__ = ["ct_catalogue"]

log = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def ct_catalogue(request, temp_database) -> str:
    """fixture injects a catalogue and returns its name"""
    catalogue_name = "catalogue"
    log.info("%s fixture: creating catalogue: %s", request.fixturename, catalogue_name)
    TestUtils.create_ct_catalogue(catalogue_name=catalogue_name)
    return catalogue_name
