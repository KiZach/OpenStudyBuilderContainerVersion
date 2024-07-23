import abc
import datetime
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import AbstractSet, Any, Callable, Self

from clinical_mdr_api import exceptions


class VersioningException(Exception):
    def __init__(self, msg, error_code=500, code="unexpected_error"):
        self.error_code = error_code
        self.code = code
        self.msg = msg
        super().__init__(msg)


@dataclass(frozen=True)
class LibraryVO:
    """
    Value object representing Library object. ie. Sponsor, CDISC etc.
    """

    @classmethod
    def from_input_values_2(
        cls,
        library_name: str,
        is_library_editable_callback: Callable[[str], bool | None],
    ) -> Self:
        is_library_editable_callback_result: bool | None = is_library_editable_callback(
            library_name
        )

        if is_library_editable_callback_result is None:
            raise exceptions.BusinessLogicException(
                f"Can't infer if library: {library_name} is editable, "
                f"because the is_editable callback wasn't passed."
            )

        return cls(name=library_name, is_editable=is_library_editable_callback_result)

    @classmethod
    def from_repository_values(cls, library_name: str, is_editable: bool) -> Self:
        return cls(name=library_name, is_editable=is_editable)

    name: str
    is_editable: bool


class LibraryItemStatus(Enum):
    """
    Enumerator for library item statuses
    """

    FINAL = "Final"
    DRAFT = "Draft"
    RETIRED = "Retired"


class ObjectAction(Enum):
    """
    Enumerator for library item actions that can change library item status
    """

    APPROVE = "approve"
    EDIT = "edit"
    DELETE = "delete"
    NEWVERSION = "new_version"
    INACTIVATE = "inactivate"
    REACTIVATE = "reactivate"


@dataclass(frozen=True)
class LibraryItemMetadataVO:
    """
    A 'Version' metadata object represents (in the data layer)
    VersionRelationship - it contains all versioning related information
    """

    # Versioning information
    _change_description: str
    _status: LibraryItemStatus
    _author: str
    _start_date: datetime.datetime
    _end_date: datetime.datetime | None

    _major_version: int
    _minor_version: int

    @classmethod
    def get_initial_item_metadata(
        cls,
        author: str,
        start_date: datetime.datetime | None = None,
    ) -> Self:
        return cls(
            _change_description="Initial version",
            _status=LibraryItemStatus.DRAFT,
            _author=author,
            _start_date=start_date
            if start_date
            else datetime.datetime.now(datetime.timezone.utc),
            _end_date=None,
            _major_version=0,
            _minor_version=1,
        )

    @classmethod
    def from_repository_values(
        cls,
        *,
        change_description: str,
        status: LibraryItemStatus,
        author: str,
        start_date: datetime.datetime,
        end_date: datetime.datetime | None,
        major_version: int,
        minor_version: int,
    ) -> Self:
        assert major_version >= 0
        assert minor_version >= 0
        assert minor_version > 0 or major_version > 0
        return cls(
            _change_description=change_description,
            _status=status,
            _author=author,
            _start_date=start_date,
            _end_date=end_date,
            _major_version=major_version,
            _minor_version=minor_version,
        )

    @property
    def change_description(self):
        return self._change_description

    @property
    def status(self) -> LibraryItemStatus:
        return self._status

    @property
    def user_initials(self) -> str:
        return self._author

    @property
    def start_date(self) -> datetime.datetime:
        return self._start_date

    @property
    def end_date(self) -> datetime.datetime | None:
        return self._end_date

    @property
    def version(self) -> str:
        return f"{self._major_version}.{self._minor_version}"

    @property
    def major_version(self) -> int:
        return self._major_version

    @property
    def minor_version(self) -> int:
        return self._minor_version

    def _get_new_version(self, new_status: LibraryItemStatus) -> tuple[int, int]:
        """
        Helper method for creating new version label
        changing major and minor versions depending on new status.
        It does not update object version information
        """
        v_major, v_minor = self._major_version, self._minor_version
        if (
            self._status == LibraryItemStatus.DRAFT
            and new_status == LibraryItemStatus.FINAL
        ):
            v_major = v_major + 1
            v_minor = 0
        elif (
            self._status == LibraryItemStatus.DRAFT
            and new_status == LibraryItemStatus.DRAFT
        ):
            v_minor = v_minor + 1
        elif (
            self._status in [LibraryItemStatus.FINAL, LibraryItemStatus.RETIRED]
            and new_status == LibraryItemStatus.DRAFT
        ):
            v_minor = 1
        elif (
            self._status == LibraryItemStatus.RETIRED
            and new_status == LibraryItemStatus.RETIRED
        ):
            v_major += 1
        elif (
            self._status == LibraryItemStatus.FINAL
            and new_status == LibraryItemStatus.FINAL
        ):
            v_major += 1
        return v_major, v_minor

    def new_draft_version(self, author: str, change_description: str) -> Self:
        """
        Creates new object in draft version updating properly all values
        """
        if self._status in [LibraryItemStatus.DRAFT, LibraryItemStatus.FINAL]:
            major, minor = self._get_new_version(LibraryItemStatus.DRAFT)
            return replace(
                self,
                _start_date=datetime.datetime.now(datetime.timezone.utc),
                _end_date=None,
                _status=LibraryItemStatus.DRAFT,
                _major_version=major,
                _minor_version=minor,
                _change_description=change_description,
                _author=author,
            )
        raise VersioningException("Cannot create new Draft version")

    def new_final_version(self, author: str, change_description: str) -> Self:
        """
        Creates new object in final version updating properly all values
        """
        if self._status in [LibraryItemStatus.DRAFT, LibraryItemStatus.RETIRED]:
            major, minor = self._get_new_version(LibraryItemStatus.FINAL)
            return replace(
                self,
                _start_date=datetime.datetime.now(datetime.timezone.utc),
                _end_date=None,
                _status=LibraryItemStatus.FINAL,
                _major_version=major,
                _minor_version=minor,
                _change_description=change_description,
                _author=author,
            )
        raise VersioningException("The object is not in draft status.")

    def new_retired_version(self, author: str, change_description: str) -> Self:
        """
        Creates new object in retired version updating properly all values
        """
        if self._status in [LibraryItemStatus.FINAL]:
            major, minor = self._get_new_version(LibraryItemStatus.RETIRED)
            return replace(
                self,
                _start_date=datetime.datetime.now(datetime.timezone.utc),
                _end_date=None,
                _status=LibraryItemStatus.RETIRED,
                _major_version=major,
                _minor_version=minor,
                _change_description=change_description,
                _author=author,
            )
        raise VersioningException("Cannot retire draft version.")

    # @deprecated
    def new_version_start_date(self, author, change_description, date):
        """
        Creates new object in the same version - used for cascading updates
        """
        major, minor = self._get_new_version(self.status)
        return replace(
            self,
            _start_date=date,
            _major_version=major,
            _minor_version=minor,
            _change_description=change_description,
            _author=author,
        )


class VersioningActionMixin:
    # Setting labels of updated objects
    _NEW_VERSION_LABEL = "New draft created"
    _FINAL_VERSION_LABEL = "Approved version"
    _RETIRED_VERSION_LABEL = "Inactivated version"
    _REACTIVATED_VERSION_LABEL = "Reactivated version"

    # implementations of basic versioning actions
    def approve(
        self, author: str, change_description: str = _FINAL_VERSION_LABEL
    ) -> None:
        """
        Approves the latest draft version and sets the latest version to final.
        """
        self.__raise_error_if_deleted()
        self.__raise_error_if_edit_is_not_allowed_in_the_library()
        new_metadata = self._item_metadata.new_final_version(
            author=author, change_description=change_description
        )
        if self.item_metadata.status != LibraryItemStatus.DRAFT:
            raise VersioningException(
                "Only DRAFT version can be approved.",
                error_code=403,
                code="invalid_status_non_draft",
            )
        self._item_metadata = new_metadata

    def inactivate(
        self, author: str, change_description: str = _RETIRED_VERSION_LABEL
    ) -> None:
        """
        Inactivates latest version.
        """
        self.__raise_error_if_deleted()
        self.__raise_error_if_edit_is_not_allowed_in_the_library()
        self._item_metadata = self._item_metadata.new_retired_version(
            author=author, change_description=change_description
        )

    def reactivate(
        self, author: str, change_description: str = _REACTIVATED_VERSION_LABEL
    ) -> None:
        """
        Reactivates latest retired version and sets the version to draft.
        """
        self.__raise_error_if_deleted()
        self.__raise_error_if_edit_is_not_allowed_in_the_library()
        if self.item_metadata.status != LibraryItemStatus.RETIRED:
            raise VersioningException("Only RETIRED version can be reactivated.")
        new_metadata = self._item_metadata.new_final_version(
            author=author, change_description=change_description
        )
        self._item_metadata = new_metadata

    def _create_new_version(
        self, author: str, change_description: str = _NEW_VERSION_LABEL
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        self.__raise_error_if_deleted()
        self.__raise_error_if_edit_is_not_allowed_in_the_library()
        new_metadata = self._item_metadata.new_draft_version(
            author=author, change_description=change_description
        )
        if self.item_metadata.status != LibraryItemStatus.FINAL:
            raise VersioningException(
                "New draft version can be created only for FINAL versions.",
                error_code=403,
                code="invalid_status_non_final",
            )
        self._item_metadata = new_metadata

    def _edit_draft(self, author: str, change_description: str) -> None:
        """
        Edits a draft version of the object, creating a new draft version.
        """
        self.__raise_error_if_deleted()
        self.__raise_error_if_edit_is_not_allowed_in_the_library()

        if self._item_metadata.status != LibraryItemStatus.DRAFT:
            raise VersioningException("The object is not in draft status.")
        self._item_metadata = self._item_metadata.new_draft_version(
            author=author, change_description=change_description
        )

    def soft_delete(self) -> None:
        if self._item_metadata.major_version == 0:
            self._is_deleted = True
        else:
            raise VersioningException("Object has been accepted")

    @abc.abstractmethod
    def get_possible_actions(self) -> AbstractSet[ObjectAction]:
        raise NotImplementedError("You cannot get possible actions for abstract class")

    def __raise_error_if_deleted(self) -> None:
        if self.is_deleted:
            raise exceptions.BusinessLogicException("Cannot use deleted object.")

    # Validator functions
    def __raise_error_if_edit_is_not_allowed_in_the_library(self) -> None:
        # some of the derived classes allow to edit theirs instances even
        # when connected to not editable library
        if self._is_edit_allowed_in_non_editable_library():
            return
        if not self.library.is_editable:
            raise VersioningException(
                "Library is not editable.", error_code=403, code="invalid_status_final"
            )


@dataclass
class LibraryItemAggregateRootBase(VersioningActionMixin, abc.ABC):
    """
    An abstract generic library item aggregate for versioning objects
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    # Properties from VersionRoot
    _uid: str | None

    _library: LibraryVO

    # Properties from relationship
    _item_metadata: LibraryItemMetadataVO

    # used for soft delete
    _is_deleted: bool = field(init=False, default=False)

    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    # Getters
    @property
    def item_metadata(self) -> LibraryItemMetadataVO:
        self.__raise_error_if_deleted()
        return self._item_metadata

    @property
    def library(self) -> LibraryVO:
        self.__raise_error_if_deleted()
        return self._library

    @property
    def uid(self) -> str:
        return self._uid  # type: ignore

    @uid.setter
    def uid(self, uid: str) -> None:
        self.__set_uid(uid)

    @property
    def is_deleted(self) -> bool:
        return self._is_deleted

    # Setter for supporting uid creation
    def __set_uid(self, uid: str) -> None:
        self.__raise_error_if_deleted()
        if self._uid is None:
            self._uid = uid
        else:
            raise TypeError("Cannot modify existing uid.")

    def _is_edit_allowed_in_non_editable_library(self) -> bool:
        return False

    @classmethod
    def _from_input_values(
        cls,
        *,
        author: str,
        library: LibraryVO,
        uid_supplier: Callable[[], str | None] = lambda: None,
        **kwargs,
    ) -> Self:
        if not library.is_editable:
            raise exceptions.BusinessLogicException(
                "Creating objects in non-editable library is forbidden."
            )

        return cls(
            _uid=uid_supplier(),
            _library=library,
            _item_metadata=LibraryItemMetadataVO.get_initial_item_metadata(
                author=author
            ),
            **kwargs,
        )

    @classmethod
    def _from_repository_values(
        cls,
        *,
        library: LibraryVO,
        uid: str,
        item_metadata: LibraryItemMetadataVO,
        **kwargs,
    ) -> Self:
        # noinspection PyArgumentList
        return cls(
            _uid=uid,
            _library=library,
            _item_metadata=item_metadata,
            **kwargs,
        )

    def __raise_error_if_deleted(self) -> None:
        if self.is_deleted:
            raise exceptions.BusinessLogicException("Cannot use deleted object.")
