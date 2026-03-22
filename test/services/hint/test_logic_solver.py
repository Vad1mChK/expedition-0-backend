import pytest
from app.services.hint.logic_models import LogicTaskRoot
from app.services.hint.logic_solver import LogicTaskSolver
from app.services.hint.logic_solver_types import LogicTaskSolverState, LogicNodeOverrideMap
from app.services.hint.logic_ops import TritBinOp, LogicNodeType, TritUnOp


def apply_mods_and_verify(solver: LogicTaskSolver, result) -> bool:
    """Helper to verify that the suggested mods actually solve the puzzle."""
    for mod in result.modifications:
        target_opt = solver.left_opt if mod.side == "left" else solver.right_opt
        setattr(target_opt.nodes[mod.node_id], mod.field, mod.new_value)

    l_val = solver.left_opt.evaluate_node(solver.left_opt.root_id)
    r_val = solver.right_opt.evaluate_node(solver.right_opt.root_id)
    return l_val == r_val


def test_solver_already_solved() -> None:
    """If roots already match, state should be SOLVED with 0 mods."""
    left_data = {
        "rootId": 2,
        "nodes": [
            {"id": 0, "type": "TritVal", "val": 2, "locked": True},
            {"id": 1, "type": "TritVal", "val": 1, "locked": True},
            {"id": 2, "type": "TritBin", "op": TritBinOp.XOR, "leftId": 0, "rightId": 1, "locked": False}
        ]
    }
    right_data = {
        "rootId": 11,
        "nodes": [
            {"id": 10, "type": "TritVal", "val": 1, "locked": False},
            {"id": 11, "type": "TritUn", "op": TritUnOp.NOT, "inputId": 10, "locked": True},
        ]
    }
    left_root = LogicTaskRoot.model_validate(left_data)
    right_root = LogicTaskRoot.model_validate(right_data)
    solver = LogicTaskSolver(left_root, right_root)
    result = solver.solve()

    assert result.state == LogicTaskSolverState.SOLVABLE.SOLVED  # Or just SOLVED depending on your Enum
    assert len(result.modifications) == 0


def test_solver_minimal_trit_val_change() -> None:
    """Should find a single node modification to match the target."""
    # Left: 0 (unlocked), Right: 2 (locked)
    left_data = {
        "rootId": 2,
        "nodes": [
            {"id": 0, "type": "TritVal", "val": 2, "locked": True},
            {"id": 1, "type": "TritVal", "val": 0, "locked": True},
            {"id": 2, "type": "TritBin", "op": TritBinOp.XOR, "leftId": 0, "rightId": 1, "locked": True}
        ]
    }
    right_data = {
        "rootId": 11,
        "nodes": [
            {"id": 10, "type": "TritVal", "val": 1, "locked": False},
            {"id": 11, "type": "TritUn", "op": TritUnOp.NOT, "inputId": 10, "locked": True},
        ]
    }

    solver = LogicTaskSolver(
        LogicTaskRoot.model_validate(left_data),
        LogicTaskRoot.model_validate(right_data)
    )
    result = solver.solve()

    assert result.state == LogicTaskSolverState.SOLVABLE
    assert len(result.modifications) == 1

    mod = result.modifications[0]
    assert mod.old_value == 1
    assert mod.new_value == 0
    assert mod.side == "right"
    assert mod.node_type == LogicNodeType.TRIT_VAL

    assert apply_mods_and_verify(solver, result)


def test_solver_op_confusion_pattern() -> None:
    """Tests if changing an operator (Or -> ImplLukasiewicz) is suggested."""
    # (1 OR 1) = 1. (1 IMPL_LUKASIEWICZ 1) = 2.
    left_data = {
        "rootId": 0,
        "nodes": [
            {"id": 0, "type": "TritBin", "op": "Or", "leftId": 1, "rightId": 2, "locked": False},
            {"id": 1, "type": "TritVal", "val": 1, "locked": True},
            {"id": 2, "type": "TritVal", "val": 1, "locked": True}
        ]
    }
    right_data = {
        "rootId": 10,
        "nodes": [{"id": 10, "type": "TritVal", "val": 2, "locked": True}]
    }

    solver = LogicTaskSolver(
        LogicTaskRoot.model_validate(left_data),
        LogicTaskRoot.model_validate(right_data)
    )
    result = solver.solve()

    assert result.state == LogicTaskSolverState.SOLVABLE
    assert len(result.modifications) == 1
    assert result.modifications[0].old_value == TritBinOp.OR
    assert result.modifications[0].new_value == TritBinOp.IMPL_LUKASIEWICZ

    assert apply_mods_and_verify(solver, result)


def test_solver_unsolvable_state() -> None:
    """If all nodes are locked or no combination works, return UNSOLVABLE."""
    # Left: 0 (LOCKED), Right: 1 (LOCKED)
    left_data = {"rootId": 0, "nodes": [{"id": 0, "type": "TritVal", "val": 0, "locked": True}]}
    right_data = {"rootId": 1, "nodes": [{"id": 1, "type": "TritVal", "val": 1, "locked": True}]}

    solver = LogicTaskSolver(
        LogicTaskRoot.model_validate(left_data),
        LogicTaskRoot.model_validate(right_data)
    )
    result = solver.solve()

    assert result.state == LogicTaskSolverState.UNSOLVABLE
    assert len(result.modifications) == 0


def test_solver_breadth_first_preference() -> None:
    """Ensure it finds a 1-node solution even if a 2-node solution exists."""
    # Left: 0 (unlocked) AND 0 (unlocked). Target: 0.
    # Wait, 0 AND 0 is already 0.
    # Let's try: Left (0 OR 0) [unlocked, unlocked], Target: 2.
    # Solution A: change node 1 to 2. Solution B: change node 2 to 2.
    # Solution C (not minimal): change both to 2.
    left_data = {
        "rootId": 0,
        "nodes": [
            {"id": 0, "type": "TritBin", "op": "Or", "leftId": 1, "rightId": 2, "locked": True},
            {"id": 1, "type": "TritVal", "val": 0, "locked": False},
            {"id": 2, "type": "TritVal", "val": 0, "locked": False}
        ]
    }
    right_data = {"rootId": 10, "nodes": [{"id": 10, "type": "TritVal", "val": 2, "locked": True}]}

    solver = LogicTaskSolver(
        LogicTaskRoot.model_validate(left_data),
        LogicTaskRoot.model_validate(right_data)
    )
    result = solver.solve()

    # Must be exactly 1 modification, not 2
    assert len(result.modifications) == 1
    assert apply_mods_and_verify(solver, result)


def test_solver_with_operator_restrictions_no_solution() -> None:
    """
    Scenario:
    Inputs (1, 1) are LOCKED.
    Current Op: OR (1 OR 1 = 1).
    Target: 2.

    Mathematically, changing OR -> IMPL_LUKASIEWICZ is a 1-node fix.
    However, we override the allowed operators to EXCLUDE Lukasiewicz.
    The solver should return UNSOLVABLE because no other 1-node op works.
    """
    left_data = {
        "rootId": 0,
        "nodes": [
            {"id": 0, "type": "TritBin", "op": "Or", "leftId": 1, "rightId": 2, "locked": False},
            {"id": 1, "type": "TritVal", "val": 1, "locked": True},
            {"id": 2, "type": "TritVal", "val": 1, "locked": True}
        ]
    }
    right_data = {
        "rootId": 10,
        "nodes": [{"id": 10, "type": "TritVal", "val": 2, "locked": True}]
    }

    # Restrict operators to only AND and OR (Soviet hardware limitations!)
    custom_overrides: LogicNodeOverrideMap = {
        LogicNodeType.TRIT_BIN: {TritBinOp.AND, TritBinOp.OR}
    }

    solver = LogicTaskSolver(
        LogicTaskRoot.model_validate(left_data),
        LogicTaskRoot.model_validate(right_data),
        overrides=custom_overrides
    )

    result = solver.solve()

    # Since (1 AND 1) = 1 and (1 OR 1) = 1, and values are locked,
    # there is no solution in the allowed set.
    assert result.state == LogicTaskSolverState.UNSOLVABLE
    assert len(result.modifications) == 0


def test_solver_with_operator_restrictions_some_solution() -> None:
    """
    Scenario:
    Inputs (0, 0) are LOCKED.
    Current Op: OR (0 OR 0 = 0).
    Target: 2.

    We need to change the operator to IMPL_KLEENE or IMPL_LUKASIEWICZ, however only IMPL_LUKASIEWICZ is available.
    So it should yield exactly one solution.
    """
    left_data = {
        "rootId": 0,
        "nodes": [
            {"id": 0, "type": "TritBin", "op": "Or", "leftId": 1, "rightId": 2, "locked": False},
            {"id": 1, "type": "TritVal", "val": 1, "locked": True},
            {"id": 2, "type": "TritVal", "val": 1, "locked": True}
        ]
    }
    right_data = {
        "rootId": 10,
        "nodes": [{"id": 10, "type": "TritVal", "val": 2, "locked": True}]
    }

    # Restrict operators to only AND and OR (Soviet hardware limitations!)
    custom_overrides: LogicNodeOverrideMap = {
        LogicNodeType.TRIT_BIN: {TritBinOp.AND, TritBinOp.OR, TritBinOp.XOR, TritBinOp.IMPL_LUKASIEWICZ}
    }

    solver = LogicTaskSolver(
        LogicTaskRoot.model_validate(left_data),
        LogicTaskRoot.model_validate(right_data),
        overrides=custom_overrides
    )

    result = solver.solve()

    # Since (1 AND 1) = 1 and (1 OR 1) = 1, and values are locked,
    # there is no solution in the allowed set.
    assert result.state == LogicTaskSolverState.SOLVABLE
    assert len(result.modifications) == 1
    assert result.modifications[0].old_value == TritBinOp.OR
    assert result.modifications[0].new_value == TritBinOp.IMPL_LUKASIEWICZ
    assert result.modifications[0].node_id == 0


def test_solver_with_digit_restrictions_no_solution() -> None:
    """
    Scenario:
    A value node is unlocked, but the level only allows '0' and '2'
    (maybe the '1' button is broken).
    Target is 1.
    """
    left_data = {
        "rootId": 0,
        "nodes": [{"id": 0, "type": "TritVal", "val": 0, "locked": False}]
    }
    right_data = {
        "rootId": 1,
        "nodes": [{"id": 1, "type": "TritVal", "val": 1, "locked": True}]
    }

    # Restrict allowed trits to exclude 1
    custom_overrides: LogicNodeOverrideMap = {
        LogicNodeType.TRIT_VAL: {0, 2}
    }

    solver = LogicTaskSolver(
        LogicTaskRoot.model_validate(left_data),
        LogicTaskRoot.model_validate(right_data),
        overrides=custom_overrides
    )

    result = solver.solve()

    # It wants 1, but we only gave it {0, 2}.
    assert result.state == LogicTaskSolverState.UNSOLVABLE


def test_solver_with_digit_restrictions_some_solution() -> None:
    """
    Scenario:
    A value node is unlocked, but the level only allows '0' and '2'
    (maybe the '1' button is broken).
    Target is 1.
    """
    left_data = {
        "rootId": 0,
        "nodes": [
            {"id": 0, "type": "TritBin", "op": "And", "leftId": 1, "rightId": 2, "locked": True},
            {"id": 1, "type": "TritVal", "val": 0, "locked": False},
            {"id": 2, "type": "TritVal", "val": 1, "locked": True}
        ]
    }
    right_data = {
        "rootId": 10,
        "nodes": [{"id": 10, "type": "TritVal", "val": 1, "locked": True}]
    }

    # Restrict allowed trits to exclude 1
    custom_overrides: LogicNodeOverrideMap = {
        LogicNodeType.TRIT_VAL: {0, 2}
    }

    solver = LogicTaskSolver(
        LogicTaskRoot.model_validate(left_data),
        LogicTaskRoot.model_validate(right_data),
        overrides=custom_overrides
    )

    result = solver.solve()

    assert result.state == LogicTaskSolverState.SOLVABLE
    assert len(result.modifications) == 1
    assert result.modifications[0].old_value == 0
    assert result.modifications[0].new_value == 2
    assert result.modifications[0].node_id == 1
