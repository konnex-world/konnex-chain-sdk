from __future__ import annotations

from typing import Union

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
        self._subtensor = subtensor

    def normalize(self, subnet_id: int, task_id: str) -> TaskScope:
        """Validate and normalize a task scope."""
        return TaskScope(subnet_id=subnet_id, task_id=task_id)

    def scope_key(self, subnet_id: int, task_id: str) -> tuple[int, str]:
        """Build stable composite key `(subnet_id, task_id)`."""
        return self.normalize(subnet_id=subnet_id, task_id=task_id).key

    def scope_params(self, subnet_id: int, task_id: str) -> list[object]:
        """Build canonical Subtensor query params for task-scoped storage."""
        scope = self.normalize(subnet_id=subnet_id, task_id=task_id)
        return [scope.subnet_id, scope.task_id]

    def scope_matches(
        self,
        scope_a: TaskScope,
        scope_b: TaskScope,
    ) -> bool:
        """Check exact scope equality for resolver guards."""
        return scope_a.key == scope_b.key

