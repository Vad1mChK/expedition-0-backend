from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Union, Literal, List

from app.services.hint.logic_ops import TritUnOp, TritBinOp, NonBinOp


class LogicNodeType(Enum):
    """
    Valid types of nodes (values, operators) in ternary (base 3) and nonary (base 9) logic.
    """
    TRIT_VAL = "TritVal"
    TRIT_UN = "TritUn"
    TRIT_BIN = "TritBin"
    NON_VAL = "NonVal"
    NON_BIN = "NonBin"


# ----------------------------------------------------------------------
# Base class (abstract dataclass) – not instantiable directly
# ----------------------------------------------------------------------

@dataclass
class BaseLogicNode(ABC):
    """
    Base class for all representations of logic nodes.
    """
    id: int
    locked: bool = False


@dataclass
class TritValNode(BaseLogicNode):
    type: Literal["TritVal"] = "TritVal"
    val: int = 0  # Expected: 0, 1, 2


@dataclass
class TritUnNode(BaseLogicNode):
    type: Literal["TritUn"] = "TritUn"
    op: TritUnOp = TritUnOp.IDENTITY
    inputId: int = 0


@dataclass
class TritBinNode(BaseLogicNode):
    type: Literal["TritBin"] = "TritBin"
    op: TritBinOp = TritBinOp.AND
    leftId: int = 0
    rightId: int = 0


@dataclass
class NonValNode(BaseLogicNode):
    type: Literal["NonVal"] = "NonVal"
    val: int = 0  # Expected: 0-8


@dataclass
class NonBinNode(BaseLogicNode):
    type: Literal["NonBin"] = "NonBin"
    op: NonBinOp = NonBinOp.NONARY_PLUS
    leftId: int = 0
    rightId: int = 0


# --- Discriminated Union Type ---

LogicNode = Union[
    TritValNode,
    TritUnNode,
    TritBinNode,
    NonValNode,
    NonBinNode
]


@dataclass
class LogicTaskRoot:
    rootId: int
    nodes: List[LogicNode]
