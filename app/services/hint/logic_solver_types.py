# app/hint/logic_solver_types.py
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Set, Any, Union
from app.services.hint.logic_ops import TritUnOp, TritBinOp, NonBinOp, LogicNodeType


class LogicTaskSolverState(Enum):
    SOLVED = "SOLVED"
    SOLVABLE = "SOLVABLE"
    UNSOLVABLE = "UNSOLVABLE"
    UNKNOWN_INCOMPLETE = "UNKNOWN_INCOMPLETE"
    SOLVABLE_INCOMPLETE = "SOLVABLE_INCOMPLETE"


LogicNodeContent = Union[int, TritUnOp, TritBinOp, NonBinOp]


@dataclass
class LogicTaskSolverModification:
    node_id: int
    field: str  # 'val' or 'op'
    node_type: LogicNodeType
    old_value: LogicNodeContent
    new_value: LogicNodeContent
    side: str   # 'left' or 'right'


@dataclass
class LogicTaskSolverResult:
    state: LogicTaskSolverState
    modifications: list[LogicTaskSolverModification]
    iterations: int


# A type alias for clarity in the solver
LogicNodeOverrideMap = Dict[
    LogicNodeType,
    Set[LogicNodeContent]
]

# Default values if no overrides are provided
DEFAULT_OVERRIDES: LogicNodeOverrideMap = {
    LogicNodeType.TRIT_VAL: {0, 1, 2},
    LogicNodeType.NON_VAL:  set(range(9)),
    LogicNodeType.TRIT_UN:  {TritUnOp.IDENTITY, TritUnOp.NOT},
    LogicNodeType.TRIT_BIN: {
        TritBinOp.AND, TritBinOp.OR, TritBinOp.XOR,
        TritBinOp.IMPL_KLEENE, TritBinOp.IMPL_LUKASIEWICZ
    },
    LogicNodeType.NON_BIN: {
        NonBinOp.NONARY_PLUS, NonBinOp.NONARY_MINUS, NonBinOp.NONARY_CONCAT
    }
}
