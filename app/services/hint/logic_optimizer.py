# app/services/hint/processor.py
from app.services.hint.logic_models import LogicTaskRoot, TritValNode, NonValNode, LogicNode
from app.services.hint.logic_functions import eval_ternary_unary, eval_ternary_binary, eval_nonary_binary, \
    eval_ternary_binary_short_circuit


class LogicTaskOptimizer:
    def __init__(self, task: LogicTaskRoot):
        self.root_id = task.rootId
        self.nodes = {n.id: n for n in task.nodes}
        self.parents = self._build_parent_map()

    def _build_parent_map(self):
        parent_map = {node_id: set() for node_id in self.nodes}
        for node in self.nodes.values():
            for child_id in self._get_children(node):
                if child_id in parent_map:
                    parent_map[child_id].add(node.id)
        return parent_map

    @staticmethod
    def _get_children(node):
        if hasattr(node, 'inputId'):
            return [node.inputId]
        if hasattr(node, 'leftId'):
            return [node.leftId, node.rightId]
        return []

    def is_perfectly_locked(self, node_id: int) -> bool:
        node = self.nodes[node_id]
        if not node.locked:
            return False
        return all(self.is_perfectly_locked(c) for c in self._get_children(node))

    def prune(self):
        """Iterative pruning using folding and short-circuiting."""
        changed = True
        while changed:
            changed = False
            to_replace = []

            for node_id, node in self.nodes.items():
                if node.type in ["TritVal", "NonVal"]:
                    continue

                # 1. Perfect Locking Pruning
                if self.is_perfectly_locked(node_id):
                    val = self.evaluate_node(node_id)
                    to_replace.append((node_id, val))
                    continue

                # 2. Short-circuiting Heuristics
                sc_val = self._check_short_circuit(node)
                if sc_val is not None:
                    to_replace.append((node_id, sc_val))

            if to_replace:
                for nid, val in to_replace:
                    self._replace_with_value(nid, val)
                self._garbage_collect()
                changed = True

    def _check_short_circuit(self, node: LogicNode):
        """Applies identities only if the short-circuiting child is locked."""
        if not node.locked or node.type != "TritBin":
            return None

        l_node = self.nodes[node.leftId]
        r_node = self.nodes[node.rightId]

        # We only care about the value if the node is a locked TritVal
        l_val = l_node.val if (l_node.type == "TritVal" and l_node.locked) else None
        r_val = r_node.val if (r_node.type == "TritVal" and r_node.locked) else None

        # This should return None if no logical identity is triggered by LOCKED values
        return eval_ternary_binary_short_circuit(node.op, l_val, r_val)

    def _replace_with_value(self, node_id, val):
        old_node = self.nodes[node_id]
        new_type = "TritVal" if "Trit" in old_node.type else "NonVal"

        # Create new Value Node
        if new_type == "TritVal":
            self.nodes[node_id] = TritValNode(id=node_id, locked=True, type="TritVal", val=val)
        else:
            self.nodes[node_id] = NonValNode(id=node_id, locked=True, type="NonVal", val=val)

    # def _garbage_collect(self):
    #     """Removes orphaned nodes (no parents and not root)."""
    #     # Rebuild parent map to reflect severance
    #     self.parents = self._build_parent_map()
    #     to_del = [nid for nid, parents in self.parents.items()
    #               if not parents and nid != self.root_id]
    #     for nid in to_del:
    #         del self.nodes[nid]

    def _garbage_collect(self):
        """
        Removes orphaned nodes recursively until only the root and
        nodes reachable from it remain.
        """
        while True:
            # Rebuild parent map to reflect current state of edges
            self.parents = self._build_parent_map()

            # Find all nodes that have no parents and are NOT the root
            to_del = [
                nid for nid, parents in self.parents.items()
                if not parents and nid != self.root_id
            ]

            if not to_del:
                break  # No more orphans found, sweep complete

            for nid in to_del:
                del self.nodes[nid]

    def evaluate_node(self, node_id: int) -> int:
        """Standard recursive evaluation."""
        node = self.nodes[node_id]

        match node.type:
            case "TritVal" | "NonVal":
                return node.val
            case "TritUn":
                return eval_ternary_unary(node.op, self.evaluate_node(node.inputId))
            case "TritBin":
                return eval_ternary_binary(node.op, self.evaluate_node(node.leftId), self.evaluate_node(node.rightId))
            case "NonBin":
                return eval_nonary_binary(node.op, self.evaluate_node(node.leftId), self.evaluate_node(node.rightId))

        raise ValueError(f"Invalid node type: {node.type}")

    def get_optimized_root(self) -> LogicTaskRoot:
        """
        Constructs a new validated LogicTaskRoot from the pruned internal state.
        """
        return LogicTaskRoot(
            rootId=self.root_id,
            nodes=list(self.nodes.values())
        )
