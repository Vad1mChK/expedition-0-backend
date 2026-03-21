import pytest
from app.services.hint.models import LogicTaskRoot
from app.services.hint.logic_optimizer import LogicTaskOptimizer
from app.services.hint.logic_ops import TritBinOp


def test_evaluation_simple_dag():
    """Tests that a simple AND gate evaluates correctly."""
    data = {
        "rootId": 1,
        "nodes": [
            {"id": 1, "type": "TritBin", "op": "And", "leftId": 2, "rightId": 3, "locked": True},
            {"id": 2, "type": "TritVal", "val": 1, "locked": True},
            {"id": 3, "type": "TritVal", "val": 2, "locked": True}
        ]
    }
    root = LogicTaskRoot.model_validate(data)
    optimizer = LogicTaskOptimizer(root)

    # min(1, 2) = 1
    assert optimizer.evaluate_node(root.rootId) == 1


def test_prune_perfectly_locked_subtree():
    """
    Tests that a fully locked subtree is collapsed into a single value node.
    Root(1) -> Bin(2) -> [Val(3), Val(4)]
    All locked. Should result in Root(1) being a TritVal.
    """
    data = {
        "rootId": 1,
        "nodes": [
            {"id": 1, "type": "TritBin", "op": "Or", "leftId": 2, "rightId": 3, "locked": True},
            {"id": 2, "type": "TritVal", "val": 0, "locked": True},
            {"id": 3, "type": "TritVal", "val": 2, "locked": True}
        ]
    }
    root = LogicTaskRoot.model_validate(data)
    optimizer = LogicTaskOptimizer(root)

    optimizer.prune()

    # The root node itself should have been replaced by a TritValNode(val=2)
    assert optimizer.nodes[1].type == "TritVal"
    assert optimizer.nodes[1].val == 2
    # Children should be garbage collected
    assert 2 not in optimizer.nodes
    assert 3 not in optimizer.nodes


def test_prune_short_circuit_and():
    """Tests 0 AND X = 0 where X is unlocked."""
    data = {
        "rootId": 1,
        "nodes": [
            {"id": 1, "type": "TritBin", "op": "And", "leftId": 2, "rightId": 3, "locked": True},
            {"id": 2, "type": "TritVal", "val": 0, "locked": True},
            {"id": 3, "type": "TritVal", "val": 2, "locked": False}  # Unlocked!
        ]
    }
    root = LogicTaskRoot.model_validate(data)
    optimizer = LogicTaskOptimizer(root)

    optimizer.prune()

    # Even though node 3 is unlocked, 0 AND anything is 0.
    assert optimizer.nodes[1].type == "TritVal"
    assert optimizer.nodes[1].val == 0


def test_prune_short_circuit_xor():
    """Tests 1 XOR X = 1 for the symmetric XOR."""
    data = {
        "rootId": 1,
        "nodes": [
            {"id": 1, "type": "TritBin", "op": "Xor", "leftId": 2, "rightId": 3, "locked": True},
            {"id": 2, "type": "TritVal", "val": 1, "locked": True},
            {"id": 3, "type": "TritVal", "val": 0, "locked": False}  # Unlocked
        ]
    }
    root = LogicTaskRoot.model_validate(data)
    optimizer = LogicTaskOptimizer(root)

    optimizer.prune()

    # 1 XOR X is always 1 in your Symmetric XOR formula
    assert optimizer.nodes[1].type == "TritVal"
    assert optimizer.nodes[1].val == 1


def test_garbage_collection_shared_child():
    """
    Tests that a node is NOT deleted if it still has a parent,
    even if one of its parents was pruned.
    """
    data = {
        "rootId": 1,
        "nodes": [
            {"id": 1, "type": "TritBin", "op": "Or", "leftId": 2, "rightId": 3, "locked": True},
            {"id": 2, "type": "TritBin", "op": "And", "leftId": 4, "rightId": 5, "locked": True},  # To be pruned
            {"id": 3, "type": "TritBin", "op": "And", "leftId": 2, "rightId": 6, "locked": False},  # Unlocked parent
            {"id": 4, "type": "TritVal", "val": 0, "locked": True},
            {"id": 5, "type": "TritVal", "val": 0, "locked": True},
            {"id": 6, "type": "TritVal", "val": 2, "locked": True}
        ]
    }
    # Node 2 is a child of Node 1 and Node 3.
    # Node 2 is perfectly locked and will be converted to a value.
    # Node 2 should still exist as a value because Node 3 (unlocked) needs it.

    root = LogicTaskRoot.model_validate(data)
    optimizer = LogicTaskOptimizer(root)
    optimizer.prune()

    assert 2 in optimizer.nodes
    assert optimizer.nodes[2].type == "TritVal"
    assert optimizer.nodes[3] in optimizer.nodes.values()


def test_prune_lukasiewicz_short_circuit():
    """Tests 0 IMPL_L X = 2."""
    data = {
        "rootId": 1,
        "nodes": [
            {"id": 1, "type": "TritBin", "op": "ImplLukasiewicz", "leftId": 2, "rightId": 3, "locked": True},
            {"id": 2, "type": "TritVal", "val": 0, "locked": True},
            {"id": 3, "type": "TritBin", "op": "And", "leftId": 4, "rightId": 5, "locked": False}
        ]
    }
    root = LogicTaskRoot.model_validate(data)
    optimizer = LogicTaskOptimizer(root)
    optimizer.prune()

    assert optimizer.nodes[1].val == 2


def test_optimized_evaluation_consistency() -> None:
    """
    Test 1: Juxtaposition of original vs optimized.
    The result of evaluating the root must remain identical after pruning.
    """
    # (1 AND (2 OR X)) where X is unlocked.
    # Since 1 is NOT a short-circuit for AND, it must not prune the root,
    # but (2 OR X) should short-circuit to 2.
    # Result: (1 AND 2) = 1.
    task_data = {
        "rootId": 0,
        "nodes": [
            {"id": 0, "type": "TritBin", "op": "And", "leftId": 1, "rightId": 2, "locked": True},
            {"id": 1, "type": "TritVal", "val": 1, "locked": True},
            {"id": 2, "type": "TritBin", "op": "Or", "leftId": 3, "rightId": 4, "locked": True},
            {"id": 3, "type": "TritVal", "val": 2, "locked": True},
            {"id": 4, "type": "TritVal", "val": 0, "locked": False}
        ]
    }

    root_obj = LogicTaskRoot.model_validate(task_data)
    optimizer = LogicTaskOptimizer(root_obj)

    # Evaluate original
    original_val = optimizer.evaluate_node(root_obj.rootId)

    # Optimize
    optimizer.prune()
    optimized_root = optimizer.get_optimized_root()

    # Evaluate optimized
    optimized_val = optimizer.evaluate_node(optimized_root.rootId)

    assert original_val == optimized_val
    assert original_val == 1


def test_optimized_structure_ground_truth() -> None:
    """
    Test 2: Juxtaposition of built optimized vs a ground truth dictionary.
    Verifies that specific nodes are removed and folded as expected.
    """
    task_data = {
        "rootId": 7,
        "nodes": [
            {"id": 0, "type": "TritVal", "val": 0, "locked": False},
            {"id": 1, "type": "TritVal", "val": 1, "locked": True},
            {"id": 2, "type": "TritVal", "val": 2, "locked": False},
            {"id": 3, "type": "TritBin", "op": "Or", "leftId": 0, "rightId": 1, "locked": False},
            {"id": 4, "type": "TritBin", "op": "Xor", "leftId": 1, "rightId": 2, "locked": True},
            {"id": 5, "type": "TritBin", "op": "Xor", "leftId": 3, "rightId": 4, "locked": True},
            {"id": 6, "type": "TritVal", "val": 1, "locked": False},
            {"id": 7, "type": "TritBin", "op": "Or", "leftId": 5, "rightId": 6, "locked": False}
        ]
    }

    root_obj = LogicTaskRoot.model_validate(task_data)
    optimizer = LogicTaskOptimizer(root_obj)
    optimizer.prune()
    optimized_root = optimizer.get_optimized_root()

    # Convert to dict for comparison (Pydantic V2)
    result_dict = optimized_root.model_dump()

    expected_dict = {
        "rootId": 7,
        "nodes": [
            {"id": 5, "type": "TritVal", "val": 1, "locked": True},
            {"id": 6, "type": "TritVal", "val": 1, "locked": False},
            {"id": 7, "type": "TritBin", "op": TritBinOp.OR, "leftId": 5, "rightId": 6, "locked": False}
        ]
    }

    assert result_dict == expected_dict
    assert len(optimized_root.nodes) == 3
