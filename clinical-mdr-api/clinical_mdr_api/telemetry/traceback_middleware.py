import logging
import traceback

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from opencensus.trace import execution_context
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from clinical_mdr_api.models.error import ErrorResponse

log = logging.getLogger(__name__)


class ExceptionTracebackMiddleware:
    """Middleware for unhandled exceptions: sets tracing attributes, logs exception traceback, returns error response"""

    def __init__(
        self,
        app: ASGIApp,
    ) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def _send(message: Message) -> None:
            nonlocal response_started, send

            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, _send)

        # pylint: disable=broad-except
        except Exception as exc:
            self.add_traceback_attributes(exc)

            # log traceback
            log.exception(exc)

            request = Request(scope)
            response = self.error_response(request, exc)

            if not response_started:
                await response(scope, receive, send)

    @staticmethod
    def add_traceback_attributes(exception):
        """adds traceback attributes to current Span of tracing context"""

        if span := execution_context.get_current_span():
            span.add_attribute(
                COMMON_ATTRIBUTES["ERROR_NAME"], exception.__class__.__name__
            )

            span.add_attribute(COMMON_ATTRIBUTES["ERROR_MESSAGE"], str(exception))

            span.add_attribute(
                COMMON_ATTRIBUTES["STACKTRACE"],
                "\n".join(traceback.format_tb(exception.__traceback__)),
            )

    @staticmethod
    def error_response(request: Request, exception: Exception) -> Response:
        """Returns a 500 error response with JSON payload from Exception"""

        # TODO we should not return the exception cause in production
        # rather consider doing the following instead:
        # if production:
        # user_exception = Exception("No detailed information available.")
        # else:
        user_exception = exception

        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(ErrorResponse(request, user_exception)),
        )

        return response
