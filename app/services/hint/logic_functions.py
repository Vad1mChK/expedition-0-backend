from app.services.hint.logic_ops import TritUnOp, TritBinOp, NonBinOp


def eval_ternary_unary(op: TritUnOp, val: int) -> int:
    if not (0 <= val < 3):
        raise ValueError(f"The input value should be in range [0, 3), but {val} given.")

    match op:
        case TritUnOp.IDENTITY:
            return val
        case TritUnOp.NOT:
            return 2 - val
    raise ValueError(f"Unknown unary op: {op}")


def eval_ternary_binary(op: TritBinOp, left: int, right: int):
    if not (0 <= left < 3) or not (0 <= right < 3):
        raise ValueError(f"The input values should be in range [0, 3), but {left} and {right} given.")

    match op:
        case TritBinOp.AND:
            return min(left, right)
        case TritBinOp.OR:
            return max(left, right)
        case TritBinOp.XOR:
            return (left + right) % 3
        case TritBinOp.IMPL_KLEENE:
            return max(2 - left, right)
        case TritBinOp.IMPL_LUKASIEWICZ:
            return min(2, 2 - left + right)

    raise ValueError(f"Unknown ternary binary op: {op}")


def eval_nonary_binary(op: NonBinOp, left: int, right: int) -> int:
    match op:
        case NonBinOp.NONARY_PLUS:
            return (left + right) % 9
        case NonBinOp.NONARY_MINUS:
            return (left - right) % 9
        case NonBinOp.NONARY_CONCAT:
            return 9 * left + right
    raise ValueError(f"Unknown nonary binary op: {op}")
