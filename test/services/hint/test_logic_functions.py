import pytest
from app.services.hint.logic_ops import TritUnOp, TritBinOp, NonBinOp
from app.services.hint.logic_functions import (
    eval_ternary_unary,
    eval_ternary_binary,
    eval_nonary_binary, eval_ternary_binary_short_circuit
)


@pytest.mark.parametrize("op, val, expected", [
    (TritUnOp.IDENTITY, 0, 0),
    (TritUnOp.IDENTITY, 1, 1),
    (TritUnOp.IDENTITY, 2, 2),
    (TritUnOp.NOT, 0, 2),
    (TritUnOp.NOT, 1, 1),
    (TritUnOp.NOT, 2, 0),
])
def test_eval_ternary_unary_valid(op: TritUnOp, val: int, expected: int) -> None:
    assert eval_ternary_unary(op, val) == expected


def test_eval_ternary_unary_invalid_range() -> None:
    with pytest.raises(ValueError, match=r"range \[0, 3\)"):
        eval_ternary_unary(TritUnOp.IDENTITY, 3)


# --- Ternary Binary Tests ---

@pytest.mark.parametrize("op, left, right, expected", [
    # AND: min(L, R)
    (TritBinOp.AND, 0, 2, 0),
    (TritBinOp.AND, 1, 2, 1),
    (TritBinOp.AND, 2, 2, 2),
    # OR: max(L, R)
    (TritBinOp.OR, 0, 2, 2),
    (TritBinOp.OR, 1, 0, 1),
    # XOR: OR(AND(L, NOT(R)), AND(NOT(L), R))
    (TritBinOp.XOR, 0, 2, 2),
    (TritBinOp.XOR, 2, 2, 0),
    (TritBinOp.XOR, 1, 2, 1),
    # ImplKleene: max(2 - L, R)
    (TritBinOp.IMPL_KLEENE, 2, 0, 0),  # Not(2) or 0 -> 0 or 0
    (TritBinOp.IMPL_KLEENE, 0, 0, 2),  # Not(0) or 0 -> 2 or 0
    (TritBinOp.IMPL_KLEENE, 1, 1, 1),  # Not(1) or 1 -> 1 or 1
    # ImplLukasiewicz: min(2, 2 - L + R)
    (TritBinOp.IMPL_LUKASIEWICZ, 2, 0, 0),  # 2 - 2 + 0 = 0
    (TritBinOp.IMPL_LUKASIEWICZ, 1, 1, 2),  # 2 - 1 + 1 = 2
    (TritBinOp.IMPL_LUKASIEWICZ, 0, 2, 2),  # 2 - 0 + 2 = 4 -> min(2, 4) = 2
])
def test_eval_ternary_binary_valid(op: TritBinOp, left: int, right: int, expected: int) -> None:
    assert eval_ternary_binary(op, left, right) == expected


def test_eval_ternary_binary_invalid_range() -> None:
    with pytest.raises(ValueError, match=r"range \[0, 3\)"):
        eval_ternary_binary(TritBinOp.AND, 1, 5)


# --- Nonary Binary Tests ---

@pytest.mark.parametrize("op, left, right, expected", [
    (NonBinOp.NONARY_PLUS, 5, 5, 10),
    (NonBinOp.NONARY_PLUS, 8, 1, 9),
    (NonBinOp.NONARY_MINUS, 10, 2, 8),
    (NonBinOp.NONARY_MINUS, 5, 3, 2),
    (NonBinOp.NONARY_CONCAT, 1, 2, 11),  # 9*1 + 2 = 11
    (NonBinOp.NONARY_CONCAT, 0, 5, 5),  # 9*0 + 5 = 5
    (NonBinOp.NONARY_CONCAT, 8, 8, 80),  # 9*8 + 8 = 80
])
def test_eval_nonary_binary_valid(op: NonBinOp, left: int, right: int, expected: int) -> None:
    assert eval_nonary_binary(op, left, right) == expected


@pytest.mark.parametrize("op, left, right, expected", [
    (TritBinOp.AND, None, None, None),
    (TritBinOp.AND, 0, None, 0),
    (TritBinOp.AND, None, 0, 0),
    (TritBinOp.AND, 1, None, None),
    (TritBinOp.OR, 2, None, 2),
    (TritBinOp.OR, None, 2, 2),
    (TritBinOp.OR, 0, None, None),
    (TritBinOp.XOR, 1, None, 1),
    (TritBinOp.XOR, None, 1, 1),
    (TritBinOp.XOR, 2, None, None),
    (TritBinOp.IMPL_KLEENE, 0, None, 2),
    (TritBinOp.IMPL_KLEENE, None, 2, 2),
    (TritBinOp.IMPL_KLEENE, 2, None, None)
])
def test_eval_ternary_binary_short_circuit(op: TritBinOp, left: int | None, right: int | None, expected: int | None):
    result = eval_ternary_binary_short_circuit(op, left, right)
    if expected is not None:
        assert result == expected
    else:
        assert result is None
