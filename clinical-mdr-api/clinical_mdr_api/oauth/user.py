import logging

from starlette_context import context

from clinical_mdr_api.oauth.models import Auth, User

log = logging.getLogger(__name__)


def auth() -> Auth:
    """Retrieves authentication-related information from the request context as Auth object."""

    return context.get("auth")


def user() -> User:
    """Retrieves user information as User object, member of the Auth object in the request context."""

    return auth().user
