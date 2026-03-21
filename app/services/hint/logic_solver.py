# app/hint/logic_solver.py
import itertools
from typing import Any, Optional, List, Dict
from app.services.hint.logic_optimizer import LogicTaskOptimizer
from app.services.hint.logic_models import LogicTaskRoot
from app.services.hint.logic_ops import LogicNodeType
from app.services.hint.logic_solver_types import (
    LogicTaskSolverState,
    LogicTaskSolverModification,
    LogicTaskSolverResult,
    LogicNodeOverrideMap,
    DEFAULT_OVERRIDES
)

HINT_DESCARTES_MAX_ITERATIONS = 1024


class LogicTaskSolver:
    def __init__(
            self,
            left_root: LogicTaskRoot,
            right_root: LogicTaskRoot,
            overrides: Optional[LogicNodeOverrideMap] = None
    ) -> None:
        self.left_opt = LogicTaskOptimizer(left_root)
        self.right_opt = LogicTaskOptimizer(right_root)

        # Initial deterministic pruning
        self.left_opt.prune()
        self.right_opt.prune()

        self.overrides = DEFAULT_OVERRIDES.copy()
        if overrides:
            self.overrides.update(overrides)

    def _get_unlocked_params(self, optimizer: LogicTaskOptimizer, side: str) -> List[Dict[str, Any]]:
        """Identifies mutable fields and captures their current (old) state."""
        params = []
        for node_id, node in optimizer.nodes.items():
            if node.locked:
                continue

            node_type_enum = LogicNodeType(node.type)
            field = "val" if node_type_enum in (LogicNodeType.TRIT_VAL, LogicNodeType.NON_VAL) else "op"
            current_content = getattr(node, field)

            # Normalize current value for comparison
            raw_current = current_content.value if hasattr(current_content, 'value') else current_content

            allowed_set = self.overrides.get(node_type_enum, set())
            possibilities = [
                p for p in allowed_set
                if (p.value if hasattr(p, 'value') else p) != raw_current
            ]

            if possibilities:
                params.append({
                    "node_id": node_id,
                    "field": field,
                    "old_value": current_content,
                    "possibilities": possibilities,
                    "side": side,
                    "node_type": node_type_enum
                })
        return params

    def solve(self) -> LogicTaskSolverResult:
        # Step 1: Deterministic check of current state
        if self.left_opt.evaluate_node(self.left_opt.root_id) == \
                self.right_opt.evaluate_node(self.right_opt.root_id):
            return LogicTaskSolverResult(LogicTaskSolverState.SOLVED, [], 0)

        # Step 2: Build the search space (Left side prioritized by list order)
        unlocked = (
                self._get_unlocked_params(self.left_opt, "left") +
                self._get_unlocked_params(self.right_opt, "right")
        )

        if not unlocked:
            return LogicTaskSolverResult(LogicTaskSolverState.UNSOLVABLE, [], 0)

        iterations = 0
        limit_reached = False

        # Step 3: Breadth-First Search for minimal modifications
        for num_changes in range(1, len(unlocked) + 1):
            for target_combinations in itertools.combinations(unlocked, num_changes):
                # Generate all value permutations for this specific set of nodes
                options = [t["possibilities"] for t in target_combinations]

                for chosen_values in itertools.product(*options):
                    iterations += 1
                    if iterations > HINT_DESCARTES_MAX_ITERATIONS:
                        limit_reached = True
                        break

                    # Apply trial modifications
                    for i, param in enumerate(target_combinations):
                        target_opt = self.left_opt if param["side"] == "left" else self.right_opt
                        setattr(target_opt.nodes[param["node_id"]], param["field"], chosen_values[i])

                    # Logic Evaluation
                    l_val = self.left_opt.evaluate_node(self.left_opt.root_id)
                    r_val = self.right_opt.evaluate_node(self.right_opt.root_id)

                    if l_val == r_val:
                        # Success: Construct the detailed modification list
                        mods = [
                            LogicTaskSolverModification(
                                node_id=p["node_id"],
                                field=p["field"],
                                old_value=p["old_value"],
                                new_value=chosen_values[i],
                                side=p["side"],
                                node_type=p["node_type"]
                            ) for i, p in enumerate(target_combinations)
                        ]

                        state = (
                            LogicTaskSolverState.SOLVABLE_INCOMPLETE
                            if limit_reached
                            else LogicTaskSolverState.SOLVABLE
                        )
                        return LogicTaskSolverResult(state, mods, iterations)

                    # Revert for next iteration to keep optimizers clean
                    for param in target_combinations:
                        target_opt = self.left_opt if param["side"] == "left" else self.right_opt
                        setattr(target_opt.nodes[param["node_id"]], param["field"], param["old_value"])

                if limit_reached:
                    break
            if limit_reached:
                break

        final_state = LogicTaskSolverState.UNKNOWN_INCOMPLETE if limit_reached else LogicTaskSolverState.UNSOLVABLE
        return LogicTaskSolverResult(final_state, [], iterations)
