import pytest
from app.services.hint.hint_generators import DeterministicHintTextGenerator
from app.services.hint.logic_ops import TritBinOp, LogicNodeType
from app.services.hint.logic_solver_types import (
    LogicTaskSolverResult,
    LogicTaskSolverState,
    LogicTaskSolverModification
)


@pytest.fixture
def generator():
    return DeterministicHintTextGenerator()


def test_generate_solved_state(generator):
    result = LogicTaskSolverResult(
        state=LogicTaskSolverState.SOLVED,
        modifications=[],
        iterations=0
    )
    hint = generator.generate(result, attempt_count=1, mistake_count=0)
    assert "Отличная работа" in hint.unsanitized
    assert hint.unsanitized == hint.sanitized


def test_generate_solvable_with_op_change(generator):
    # (1 OR 1) -> (1 XOR 1)
    mod = LogicTaskSolverModification(
        node_id=0,
        field="op",
        node_type=LogicNodeType.TRIT_BIN,
        old_value=TritBinOp.OR,
        new_value=TritBinOp.XOR,
        side="left"
    )
    result = LogicTaskSolverResult(
        state=LogicTaskSolverState.SOLVABLE,
        modifications=[mod],
        iterations=1
    )

    hint = generator.generate(result)

    # Check Accusative case for "дизъюнкцию" (from Or)
    assert "замените дизъюнкцию" in hint.unsanitized
    # Check Nominative fallback/Accusative for "исключающее ИЛИ"
    assert "на исключающее ИЛИ" in hint.unsanitized
    assert hint.unsanitized.startswith("Нужно 1 изменение")


def test_generate_solvable_with_val_change_sanitization(generator):
    mod = LogicTaskSolverModification(
        node_id=1,
        field="val",
        node_type=LogicNodeType.TRIT_VAL,
        old_value=0,
        new_value=2,
        side="right"
    )
    result = LogicTaskSolverResult(
        state=LogicTaskSolverState.SOLVABLE,
        modifications=[mod],
        iterations=1
    )

    hint = generator.generate(result, ternary_logic_balanced=False)

    # Unsanitized: "замените цифру 0 на 2"
    assert "цифру 0 на 2" in hint.unsanitized
    # Sanitized: "цифру ноль на две" (Accusative feminine/neuter)
    assert "цифру ноль на две" in hint.sanitized or "цифру ноль на два" in hint.sanitized


def test_balanced_ternary_translation(generator):
    mod = LogicTaskSolverModification(
        node_id=1,
        field="val",
        node_type=LogicNodeType.TRIT_VAL,
        old_value=0,  # This is -1 in balanced
        new_value=2,  # This is 1 in balanced
        side="left"
    )
    result = LogicTaskSolverResult(
        state=LogicTaskSolverState.SOLVABLE,
        modifications=[mod],
        iterations=1
    )

    hint = generator.generate(result, ternary_logic_balanced=True)

    # Check balanced strings
    assert "цифру -1 на 1" in hint.unsanitized
    assert "минус один" in hint.sanitized


def test_pluralization_logic(generator):
    assert generator.determine_quantity_of_number(1) == "singular"
    assert generator.determine_quantity_of_number(3) == "dual"
    assert generator.determine_quantity_of_number(5) == "plural"
    assert generator.determine_quantity_of_number(11) == "plural"  # Test the 11-19 exception
