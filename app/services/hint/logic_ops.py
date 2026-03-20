from enum import Enum


class TritUnOp(Enum):
    """
    Opcodes for 1-place operators in ternary logic.
    """
    IDENTITY = "Identity"
    NOT = "Not"


class TritBinOp(Enum):
    """
    Opcodes for 2-place operators in ternary logic.
    """
    AND = "And"
    OR = "Or"
    XOR = "Xor"
    IMPL_KLEENE = "ImplKleene"
    IMPL_LUKASIEWICZ = "ImplLukasiewicz"


class NonBinOp(Enum):
    """
    Opcodes for 2-place operators in nonary (base 9) arithmetic.
    """
    NONARY_PLUS = "NonaryPlus"
    NONARY_MINUS = "NonaryMinus"
    NONARY_CONCAT = "NonaryConcat"
