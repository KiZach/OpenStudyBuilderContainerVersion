"""Custom exceptions."""

from fastapi import status
from fastapi.security import SecurityScopes
from starlette.datastructures import MutableHeaders


class MDRApiBaseException(Exception):
    """
    A base exception class for the MDR API.

    Attributes:
        status_code (int, optional): The HTTP status code for the exception. Defaults to None.
    """

    status_code: int | None = None

    def __init__(self, msg):
        self.msg = msg
        self.headers = MutableHeaders()


class NotFoundException(MDRApiBaseException):
    """
    An exception raised when a resource cannot be found.

    Attributes:
        status_code (int): The HTTP status code for the exception (404).
    """

    status_code = status.HTTP_404_NOT_FOUND


class ForbiddenException(MDRApiBaseException):
    """
    An exception raised when a client is identified, but does not have the right to perform the requested action on the resource.

    Attributes:
        status_code (int): The HTTP status code for the exception (403).
    """

    status_code = status.HTTP_403_FORBIDDEN


class ValidationException(MDRApiBaseException):
    """
    An exception raised when a submitted form or document did not pass validation.

    Attributes:
        status_code (int): The HTTP status code for the exception (400).
    """

    status_code = status.HTTP_400_BAD_REQUEST


class BusinessLogicException(MDRApiBaseException):
    """
    An exception raised when a request could not be completed because it did not pass a business rule check.

    Attributes:
        status_code (int): The HTTP status code for the exception (400).
    """

    status_code = status.HTTP_400_BAD_REQUEST


class ConflictErrorException(MDRApiBaseException):
    """
    An exception raised when there is a conflict in the request.

    Attributes:
        status_code (int): The HTTP status code for the exception (409).
    """

    status_code = status.HTTP_409_CONFLICT


class NotAuthenticatedException(MDRApiBaseException):
    """
    An exception raised when the client must authenticate itself or get a fresh token.

    Attributes:
        status_code (int): The HTTP status code for the exception (401).
    """

    status_code = status.HTTP_401_UNAUTHORIZED

    def __init__(self, msg: str, security_scopes: SecurityScopes | None = None):
        super().__init__(msg)
        if security_scopes and security_scopes.scopes:
            self.headers[
                "WWW-Authenticate"
            ] = f'Bearer scope="{security_scopes.scope_str}"'
        else:
            self.headers["WWW-Authenticate"] = "Bearer"
