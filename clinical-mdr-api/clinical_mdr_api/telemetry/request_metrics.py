import contextlib
import logging
import time
from functools import wraps
from typing import Mapping

import neomodel
import opencensus.trace
from pydantic import BaseModel, Field
from starlette_context import context

from clinical_mdr_api import config
from clinical_mdr_api.telemetry import trace_block

log = logging.getLogger(__name__)


class RequestMetrics(BaseModel):
    """Per-request metrics"""

    cypher_count: int = Field(
        0, alias="cypher.count", title="Number of cypher.query events"
    )
    cypher_times: float = Field(
        0,
        alias="cypher.times",
        title="Cumulative walltime (in seconds) cypher.query events took",
    )
    cypher_slowest_time: float = Field(
        0,
        alias="cypher.slowest.time",
        title="Walltime (in seconds) the slowest cypher.query events took",
    )
    cypher_slowest_query: str | None = Field(
        None,
        alias="cypher.slowest.query",
        title="Slowest (by walltime) cypher.query string",
    )
    cypher_slowest_query_params: dict | None = Field(
        None,
        alias="cypher.slowest.query.params",
        title="Parameters of the slowest cypher query",
    )


def init_request_metrics():
    """Initialize request metrics object in request context"""

    if context.exists():
        context["request_metrics"] = RequestMetrics()


def include_request_metrics(span: opencensus.trace.Span):
    """Adds request metrics to tracing Span"""

    if metrics := get_request_metrics():
        for key, val in metrics.dict(by_alias=True, exclude_none=True).items():
            span.add_attribute(key, val)


def get_request_metrics() -> RequestMetrics | None:
    """Gets request metrics object from request context"""

    if context.exists():
        return context.get("request_metrics")

    return None


@contextlib.contextmanager
def cypher_tracing(query: str, params: Mapping):
    """cypher query tracing and metrics to Opencensus"""

    # update request metrics
    if metrics := get_request_metrics():
        metrics.cypher_count += 1
        start_time = time.time()

    with trace_block("neomodel.query") as span:
        span.add_attribute("cypher.query", query)
        span.add_attribute("cypher.params", params)

        # run the query (or any wrapped code) as a distinct operation (logical tracing block == Span)
        yield

    # update cypher query metrics of the request
    if metrics:
        delta_time = time.time() - start_time
        metrics.cypher_times += delta_time

        # find the slowest query of the request
        if delta_time > metrics.cypher_slowest_time:
            metrics.cypher_slowest_time = delta_time

            # also record query text and parameters if slower than the threshold
            if delta_time > config.SLOW_QUERY_TIME_SECS:
                metrics.cypher_slowest_query = query
                metrics.cypher_slowest_query_params = params


def patch_neomodel_database():
    """Monkey-patch neomodel.core.db singleton to trace Cypher queries"""

    def wrap(func):
        @wraps(func)
        def _run_cypher_query(
            self,
            session,
            query,
            params,
            handle_unique,
            retry_on_session_expire,
            resolve_objects,
        ):
            with cypher_tracing(query, params):
                return func(
                    self,
                    session=session,
                    query=query,
                    params=params,
                    handle_unique=handle_unique,
                    retry_on_session_expire=retry_on_session_expire,
                    resolve_objects=resolve_objects,
                )

        return _run_cypher_query

    log.info("Patching neomodel.util.Database")

    neomodel.util.Database._run_cypher_query = wrap(
        neomodel.util.Database._run_cypher_query
    )
