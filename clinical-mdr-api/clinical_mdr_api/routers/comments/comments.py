from fastapi import APIRouter, Body, Path, Query, Response, status

from clinical_mdr_api import config, models
from clinical_mdr_api.domains.comments.comments import CommentThreadStatus
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import rbac
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.comments.comments import CommentsService

# Endpoints prefixed with "/comment*"
router = APIRouter()

CommentThreadUID = Path(None, description="Unique id of comment thread")
CommentReplyUID = Path(None, description="Unique id of comment reply")
Service = CommentsService


@router.get(
    "/comment-topics",
    dependencies=[rbac.ANY],
    summary="Returns all comment topics",
    response_model=CustomPage[models.CommentTopic],
    status_code=200,
    responses={
        500: _generic_descriptions.ERROR_500,
    },
)
# pylint: disable=redefined-outer-name
def get_comment_topics(
    topic_path: str
    | None = Query(
        None,
        min_length=1,
        description="If specified, only topic matching the sepcified value are returned.",
    ),
    topic_path_partial_match: bool
    | None = Query(
        False,
        description="""If `false`, only topics whose topic path is equal to the specified `topic_path` are returned.
        If `true`, topics whose topic path partially matches the specified `topic_path` are returned.""",
    ),
    page_number: int
    | None = Query(1, ge=1, description=_generic_descriptions.PAGE_NUMBER),
    page_size: int
    | None = Query(
        config.DEFAULT_PAGE_SIZE,
        ge=0,
        le=config.MAX_PAGE_SIZE,
        description=_generic_descriptions.PAGE_SIZE,
    ),
) -> CustomPage[models.CommentTopic]:
    results = Service().get_all_comment_topics(
        topic_path=topic_path,
        topic_path_partial_match=topic_path_partial_match,
        page_number=page_number,
        page_size=page_size,
    )
    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/comment-threads",
    dependencies=[rbac.ANY],
    summary="Returns all comment threads",
    response_model=CustomPage[models.CommentThread],
    status_code=200,
    responses={
        500: _generic_descriptions.ERROR_500,
    },
)
# pylint: disable=redefined-outer-name
def get_comment_threads(
    topic_path: str
    | None = Query(
        None,
        min_length=1,
        description="The topic path of the comment thread. If not specified, comment threads associated with any topic are returned.",
    ),
    topic_path_partial_match: bool
    | None = Query(
        False,
        description="""If `false`, only comment threads whose topic path is equal to the specified `topic_path` are returned.
        If `true`, comment threads whose topic path partially matches the specified `topic_path` are returned.""",
    ),
    status: CommentThreadStatus
    | None = Query(
        None,
        description="The status of the comment thread. If not specified, comment threads with any status are returned.",
    ),
    page_number: int
    | None = Query(1, ge=1, description=_generic_descriptions.PAGE_NUMBER),
    page_size: int
    | None = Query(
        config.DEFAULT_PAGE_SIZE,
        ge=0,
        le=config.MAX_PAGE_SIZE,
        description=_generic_descriptions.PAGE_SIZE,
    ),
) -> CustomPage[models.CommentThread]:
    results = Service().get_all_comment_threads(
        topic_path=topic_path,
        topic_path_partial_match=topic_path_partial_match,
        status=status,
        page_number=page_number,
        page_size=page_size,
    )
    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/comment-threads/{uid}",
    dependencies=[rbac.ANY],
    summary="Returns the comment thread identified by the specified 'uid'.",
    response_model=models.CommentThread,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_comment_thread(uid: str = CommentThreadUID) -> models.CommentThread:
    return Service().get_comment_thread(uid)


@router.post(
    "/comment-threads",
    dependencies=[rbac.ANY],
    summary="Creates a new comment thread",
    response_model=models.CommentThread,
    status_code=201,
    responses={
        201: {"description": "Comment thread was successfully created"},
        500: _generic_descriptions.ERROR_500,
    },
)
def create_comment_thread(
    create_input: models.CommentThreadCreateInput = Body(
        description="Comment thread that shall be created"
    ),
) -> models.CommentThread:
    return Service().create_comment_thread(create_input)


@router.patch(
    "/comment-threads/{uid}",
    dependencies=[rbac.ANY],
    summary="Edits a comment thread's 'text' and/or 'status' properties",
    response_model=models.CommentThread,
    status_code=200,
    responses={
        200: {"description": "Comment thread was successfully edited"},
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def edit_comment_thread(
    uid: str = CommentThreadUID,
    edit_input: models.CommentThreadEditInput = Body(
        description="Properties of the comment thread that shall be updated"
    ),
) -> models.CommentThread:
    return Service().edit_comment_thread(uid, edit_input)


@router.delete(
    "/comment-threads/{uid}",
    dependencies=[rbac.ANY],
    summary="Deletes the comment thread identified by 'uid'.",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The item was successfully deleted."},
        500: _generic_descriptions.ERROR_500,
    },
)
def delete_comment_thread(uid: str = CommentThreadUID) -> None:
    Service().delete_comment_thread(uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/comment-threads/{thread_uid}/replies",
    dependencies=[rbac.ANY],
    summary="Creates a reply to a comment thread",
    response_model=models.CommentReply,
    status_code=201,
    responses={
        201: {"description": "Reply was successfully created"},
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def create_comment_reply(
    thread_uid: str = CommentThreadUID,
    create_input: models.CommentReplyCreateInput = Body(
        description="Comment reply that shall be created"
    ),
) -> models.CommentReply:
    return Service().create_comment_reply(thread_uid, create_input)


@router.get(
    "/comment-threads/{thread_uid}/replies",
    dependencies=[rbac.ANY],
    summary="Returns all replies to the specified comment thread",
    response_model=list[models.CommentReply],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_comment_thread_replies(
    thread_uid: str = CommentThreadUID,
) -> list[models.CommentReply]:
    return Service().get_all_comment_thread_replies(thread_uid)


@router.get(
    "/comment-threads/{thread_uid}/replies/{reply_uid}",
    dependencies=[rbac.ANY],
    summary="Returns the comment thread reply identified by the specified 'reply_uid'.",
    response_model=models.CommentReply,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
# pylint: disable=unused-argument
def get_comment_thread_reply(
    thread_uid: str = CommentThreadUID, reply_uid: str = CommentReplyUID
) -> models.CommentThread:
    return Service().get_comment_thread_reply(reply_uid)


@router.patch(
    "/comment-threads/{thread_uid}/replies/{reply_uid}",
    dependencies=[rbac.ANY],
    summary="Edits the specified comment reply's text",
    response_model=models.CommentReply,
    status_code=200,
    responses={
        200: {"description": "Comment reply was successfully edited"},
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
# pylint: disable=unused-argument
def edit_comment_thread_reply(
    thread_uid: str = CommentThreadUID,
    reply_uid: str = CommentReplyUID,
    edit_input: models.CommentReplyEditInput = Body(
        description="Updated text of the comment reply"
    ),
) -> models.CommentReply:
    return Service().edit_comment_thread_reply(reply_uid, edit_input)


@router.delete(
    "/comment-threads/{thread_uid}/replies/{reply_uid}",
    dependencies=[rbac.ANY],
    summary="Deletes the comment reply identified by 'reply_uid'.",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The item was successfully deleted."},
        500: _generic_descriptions.ERROR_500,
    },
)
# pylint: disable=unused-argument
def delete_comment_reply(
    thread_uid: str = CommentThreadUID, reply_uid: str = CommentReplyUID
):
    Service().delete_comment_reply(reply_uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
