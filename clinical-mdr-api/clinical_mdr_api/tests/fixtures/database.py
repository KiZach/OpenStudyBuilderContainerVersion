# pylint: disable=unused-argument,redefined-outer-name

import logging
import time
from urllib.parse import urljoin

import neo4j.exceptions
import pytest
from neomodel import config as neoconfig
from neomodel.core import db

from clinical_mdr_api import config

__all__ = ["temp_database", "base_data"]

from clinical_mdr_api.tests.integration.utils.data_library import inject_base_data

log = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def temp_database(request) -> str:
    """module fixture to run tests with a temporary database, name derived from test module name"""

    # this import results to cypher queries which I don't want to run on the default database
    from clinical_mdr_api.routers.admin import clear_caches

    db_name = request.module.__name__.rsplit(".", 1)[-1].replace("_", "-")
    log.info(
        "%s fixture: using temporary database: %s",
        request.fixturename,
        db_name,
    )

    log.debug(
        "%s fixture: create or replace database: %s",
        request.fixturename,
        db_name,
    )
    db.cypher_query("CREATE OR REPLACE DATABASE $db", {"db": db_name})

    log.debug(
        "%s fixture: altering database configuration to: %s",
        request.fixturename,
        db_name,
    )
    full_dsn = urljoin(config.settings.neo4j_dsn, f"/{db_name}")
    neoconfig.DATABASE_URL = full_dsn

    try_cnt = 1
    db_available = False
    while try_cnt < 10 and not db_available:
        try:
            # Database creation can take a couple of seconds
            # db.set_connection will return a ClientError if the database isn't ready
            # This allows for retrying after a small pause
            db.set_connection(full_dsn)

            try_cnt = try_cnt + 1
            db.cypher_query(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Counter) REQUIRE (c.counterId) IS NODE KEY"
            )
            db_available = True

        except (
            neo4j.exceptions.ClientError,
            neo4j.exceptions.DatabaseUnavailable,
        ) as exc:
            log.debug(
                "%s fixture: database '%s' not available, %s, pausing for 2 seconds",
                request.fixturename,
                db_name,
                exc.code,
            )
            time.sleep(2)

    if not db_available:
        log.info(
            "%s fixture: database '%s' not available, given up after %s tries",
            request.fixturename,
            db_name,
            try_cnt,
        )
        raise RuntimeError(f"db {db_name} is not available")

    # clear cached data after switching databases
    clear_caches()

    yield db_name

    config.settings = config.Settings()
    log.debug(
        "%s fixture: reset to database configuration: %s",
        request.fixturename,
        config.settings.neo4j_dsn or config.settings.neo4j_database,
    )
    neoconfig.DATABASE_URL = config.settings.neo4j_dsn
    db.set_connection(config.settings.neo4j_dsn)

    # clear cached data after switching databases
    clear_caches()

    # Drop test database if pytest was not called with --keep-db command-line option
    if not request.config.getoption("--keep-db"):
        log.debug(
            "%s fixture: drop database: %s",
            request.fixturename,
            db_name,
        )
        db.cypher_query("DROP DATABASE $db IF EXISTS", {"db": db_name})


@pytest.fixture(scope="module")
def base_data(request, temp_database):
    """injects generic base data into a temporary database"""

    log.info("%s: injecting base data: inject_base_data()", request.fixturename)
    inject_base_data()
