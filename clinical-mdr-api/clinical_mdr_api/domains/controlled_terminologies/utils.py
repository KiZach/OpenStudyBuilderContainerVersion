from enum import Enum


class TermParentType(Enum):
    """
    Enum for Type of has_parent relationship
    """

    PARENT_TYPE = "type"
    PARENT_SUB_TYPE = "subtype"
    VALID_FOR_EPOCH_TYPE = "valid_for_epoch"
