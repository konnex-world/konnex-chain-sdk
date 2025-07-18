from typing import Any, Optional, Union
from bittensor.core.subtensor import Subtensor as _Subtensor
from bittensor.core.async_subtensor import AsyncSubtensor as _AsyncSubtensor
from .task_scopes import TaskScopes as _TaskScopes


class Queries:
    """Class for managing subtensor query operations."""

    def __init__(self, subtensor: Union["_Subtensor", "_AsyncSubtensor"]):
        self._task_scopes = _TaskScopes(subtensor)
        self.query_constant = subtensor.query_constant
        self.query_map = subtensor.query_map
        self.query_map_subtensor = subtensor.query_map_subtensor
        self.query_module = subtensor.query_module
        self.query_runtime_api = subtensor.query_runtime_api
        self.query_subtensor = subtensor.query_subtensor

    def task_scope_params(self, subnet_id: int, task_id: str) -> list[object]:
        """Return validated canonical params for task-scoped storage queries."""
        return self._task_scopes.scope_params(subnet_id=subnet_id, task_id=task_id)

    def query_subtensor_for_task(
        self,
        storage_name: str,
        subnet_id: int,
        task_id: str,
        block: Optional[int] = None,
    ) -> Any:
        """
        Query `SubtensorModule` storage scoped by `(subnet_id, task_id)`.

        `storage_name` is the `storage_function` name on `SubtensorModule` (must exist
        on-chain once Konnex runtime pallets are wired).

        For async subtensor instances this returns an awaitable coroutine.
        """
        return self.query_subtensor(
            name=storage_name,
            block=block,
            params=self.task_scope_params(subnet_id=subnet_id, task_id=task_id),
        )
