from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING, Union

from bittensor.core.subtensor import Subtensor as _Subtensor
from bittensor.core.async_subtensor import AsyncSubtensor as _AsyncSubtensor

from .extrinsics import Extrinsics as _Extrinsics
from .queries import Queries as _Queries

if TYPE_CHECKING:
    from bittensor_wallet import Wallet


class Escrow:
    """Task-scoped escrow helper facade for Konnex runtime modules."""

    def __init__(self, subtensor: Union["_Subtensor", "_AsyncSubtensor"]):
        self._queries = _Queries(subtensor)
        self._extrinsics = _Extrinsics(subtensor)

    @staticmethod
    def _drop_none(values: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in values.items() if v is not None}

    def create_escrow_call(
        self,
        subnet_id: int,
        task_id: str,
        payer: str,
        payee: str,
        amount_rao: int,
        timeout_blocks: int,
        arbiter: Optional[str] = None,
        module_name: str = "EscrowModule",
        call_function: str = "create_escrow",
    ) -> Any:
        """Compose escrow creation call scoped by `(subnet_id, task_id)`."""
        params = self._drop_none(
            {
                "payer": payer,
                "payee": payee,
                "amount_rao": amount_rao,
                "timeout_blocks": timeout_blocks,
                "arbiter": arbiter,
            }
        )
        return self._extrinsics.compose_call_for_task(
            call_module=module_name,
            call_function=call_function,
            subnet_id=subnet_id,
            task_id=task_id,
            extra_params=params,
        )

    async def submit_create_escrow(
        self,
        subnet_id: int,
        task_id: str,
        wallet: "Wallet",
        payer: str,
        payee: str,
        amount_rao: int,
        timeout_blocks: int,
        arbiter: Optional[str] = None,
        module_name: str = "EscrowModule",
        call_function: str = "create_escrow",
        *,
        wait_for_inclusion: bool = True,
        wait_for_finalization: bool = False,
    ) -> tuple[bool, str]:
        """Compose + submit escrow creation call."""
        params = self._drop_none(
            {
                "payer": payer,
                "payee": payee,
                "amount_rao": amount_rao,
                "timeout_blocks": timeout_blocks,
                "arbiter": arbiter,
            }
        )
        return await self._extrinsics.sign_and_send_extrinsic_for_task(
            call_module=module_name,
            call_function=call_function,
            subnet_id=subnet_id,
            task_id=task_id,
            wallet=wallet,
            extra_params=params,
            wait_for_inclusion=wait_for_inclusion,
            wait_for_finalization=wait_for_finalization,
        )

    def deposit_escrow_call(
        self,
        subnet_id: int,
        task_id: str,
        escrow_id: int,
        amount_rao: int,
        module_name: str = "EscrowModule",
        call_function: str = "deposit_escrow",
    ) -> Any:
        """Compose escrow deposit call."""
        return self._extrinsics.compose_call_for_task(
            call_module=module_name,
            call_function=call_function,
            subnet_id=subnet_id,
            task_id=task_id,
            extra_params={"escrow_id": escrow_id, "amount_rao": amount_rao},
        )

    def release_escrow_call(
        self,
        subnet_id: int,
        task_id: str,
        escrow_id: int,
        verdict: Optional[str] = None,
        module_name: str = "EscrowModule",
        call_function: str = "release_escrow",
    ) -> Any:
        """Compose escrow release call."""
        return self._extrinsics.compose_call_for_task(
            call_module=module_name,
            call_function=call_function,
            subnet_id=subnet_id,
            task_id=task_id,
            extra_params=self._drop_none({"escrow_id": escrow_id, "verdict": verdict}),
        )

    def cancel_escrow_call(
        self,
        subnet_id: int,
        task_id: str,
        escrow_id: int,
        reason: Optional[str] = None,
        module_name: str = "EscrowModule",
        call_function: str = "cancel_escrow",
    ) -> Any:
        """Compose escrow cancel/refund call."""
        return self._extrinsics.compose_call_for_task(
            call_module=module_name,
            call_function=call_function,
            subnet_id=subnet_id,
            task_id=task_id,
            extra_params=self._drop_none({"escrow_id": escrow_id, "reason": reason}),
        )

    def query_escrow_by_task(
        self,
        subnet_id: int,
        task_id: str,
        block: Optional[int] = None,
        storage_name: str = "EscrowByTask",
    ) -> Any:
        """Query escrow state by task key."""
        return self._queries.query_subtensor_for_task(
            storage_name=storage_name,
            subnet_id=subnet_id,
            task_id=task_id,
            block=block,
        )

    def query_escrow_events_by_task(
        self,
        subnet_id: int,
        task_id: str,
        block: Optional[int] = None,
        storage_name: str = "EscrowEventsByTask",
    ) -> Any:
        """Query escrow event map by task key."""
        return self._queries.query_map_subtensor_for_task(
            storage_name=storage_name,
            subnet_id=subnet_id,
            task_id=task_id,
            block=block,
        )
