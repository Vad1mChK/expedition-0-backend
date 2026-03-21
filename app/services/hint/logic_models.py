# app/services/hint/logic_models.py
from enum import Enum

from pydantic import BaseModel, Field
from typing import Literal, Optional, Union
from app.services.hint.logic_ops import TritUnOp, TritBinOp, NonBinOp


class BaseNode(BaseModel):
    id: int
    locked: bool


class TritValNode(BaseNode):
    type: Literal["TritVal"]
    val: int = Field(ge=0, le=2)


class TritUnNode(BaseNode):
    type: Literal["TritUn"]
    op: TritUnOp
    inputId: int


class TritBinNode(BaseNode):
    type: Literal["TritBin"]
    op: TritBinOp
    leftId: int
    rightId: int


class NonValNode(BaseNode):
    type: Literal["NonVal"]
    val: int = Field(ge=0, le=8)


class NonBinNode(BaseNode):
    type: Literal["NonBin"]
    op: NonBinOp
    leftId: int
    rightId: int


# This Union allows Pydantic to automatically pick the right class based on the 'type' field
LogicNode = Union[TritValNode, TritUnNode, TritBinNode, NonValNode, NonBinNode]


class LogicTaskRoot(BaseModel):
    rootId: int
    nodes: list[LogicNode]


class LogicInterfaceTypes(Enum):
    TERNARY_EQUATION = "TernaryEquation"
    NONARY_EQUATION = "NonaryEquation"
    TERNARY_CIRCUIT = "TernaryCircuit"
