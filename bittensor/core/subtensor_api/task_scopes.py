from __future__ import annotations

from typing import Any, Optional, Union

from bittensor.utils import TaskScope
from bittensor.core.subtensor import Subtensor as _Subtensor
from bittensor.core.async_subtensor import AsyncSubtensor as _AsyncSubtensor


class TaskScopes:
    """
    Helper facade for subnet-aware task scope operations.

    This keeps a single place to normalize `(subnet_id, task_id)` handling
    for future PoPW/Escrow API calls.
    """

    def __init__(self, subtensor: Union["_Subtensor", "_AsyncSubtensor"]):
        # Kept for future typed helpers that need the live Subtensor/AsyncSubtensor instance.
        self._subtensor = subtensor

    def normalize(self, subnet_id: int, task_id: str) -> TaskScope:
        """Validate and normalize a task scope."""
        return TaskScope(subnet_id=subnet_id, task_id=task_id)

    def scope_key(self, subnet_id: int, task_id: str) -> tuple[int, str]:
        """Build stable composite key `(subnet_id, task_id)`."""
        return self.normalize(subnet_id=subnet_id, task_id=task_id).key

    def scope_label(self, subnet_id: int, task_id: str) -> str:
        """Compact string for logs, metrics, and cache keys (validated scope)."""
        scope = self.normalize(subnet_id=subnet_id, task_id=task_id)
        return f"subnet_id={scope.subnet_id};task_id={scope.task_id}"

    def scope_params(self, subnet_id: int, task_id: str) -> list[object]:
        """Build canonical Subtensor query params for task-scoped storage."""
        scope = self.normalize(subnet_id=subnet_id, task_id=task_id)
        return [scope.subnet_id, scope.task_id]

    def scope_params_from_scope(self, scope: TaskScope) -> list[object]:
        """Return storage query params for an existing `TaskScope` (already validated)."""
        return [scope.subnet_id, scope.task_id]

    def extend_params(
        self,
        subnet_id: int,
        task_id: str,
        *extra_params: object,
    ) -> list[object]:
        """Return canonical query params with additional positional values appended."""
        return self.scope_params(subnet_id=subnet_id, task_id=task_id) + list(extra_params)

    def extend_params_from_scope(
        self,
        scope: TaskScope,
        *extra_params: object,
    ) -> list[object]:
        """Return canonical query params from `TaskScope` with extra positional values."""
        return self.scope_params_from_scope(scope) + list(extra_params)

    def scope_call_params(
        self,
        subnet_id: int,
        task_id: str,
        *,
        extra_params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Build canonical `call_params` for task-scoped extrinsics (`compose_call`).

        Keys `subnet_id` and `task_id` are reserved; `extra_params` may add further
        fields but must not reuse those names.
        """
        scope = self.normalize(subnet_id=subnet_id, task_id=task_id)
        return self._merge_scope_call_params(
            scope=scope,
            extra_params=extra_params,
            overlap_error=(
                "extra_params must not set subnet_id or task_id; pass them as arguments"
            ),
        )

    def scope_call_params_from_scope(
        self,
        scope: TaskScope,
        *,
        extra_params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Like `scope_call_params` but starts from an existing `TaskScope` instance."""
        return self._merge_scope_call_params(
            scope=scope,
            extra_params=extra_params,
            overlap_error=(
                "extra_params must not set subnet_id or task_id; use TaskScope fields"
            ),
        )

    @staticmethod
    def _merge_scope_call_params(
        scope: TaskScope,
        extra_params: Optional[dict[str, Any]],
        overlap_error: str,
    ) -> dict[str, Any]:
        merged: dict[str, Any] = {
            "subnet_id": scope.subnet_id,
            "task_id": scope.task_id,
        }
        if extra_params:
            overlap = set(extra_params) & {"subnet_id", "task_id"}
            if overlap:
                raise ValueError(overlap_error)
            merged.update(extra_params)
        return merged

    def scope_matches(
        self,
        scope_a: TaskScope,
        scope_b: TaskScope,
    ) -> bool:
        """Check exact scope equality for resolver guards."""
        return scope_a.key == scope_b.key

