from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING, Union

from bittensor.core.subtensor import Subtensor as _Subtensor
from bittensor.core.async_subtensor import AsyncSubtensor as _AsyncSubtensor

from .escrow import Escrow as _Escrow
from .popw import PoPW as _PoPW

if TYPE_CHECKING:
    from bittensor_wallet import Wallet


class Settlement:
    """High-level escrow + PoPW orchestration helpers for task settlement."""

    def __init__(self, subtensor: Union["_Subtensor", "_AsyncSubtensor"]):
        self._escrow = _Escrow(subtensor)
        self._popw = _PoPW(subtensor)

    def settlement_snapshot(
        self,
        subnet_id: int,
        task_id: str,
        block: Optional[int] = None,
    ) -> dict[str, Any]:
        """Read escrow + PoPW state for a `(subnet_id, task_id)` pair."""
        return {
            "subnet_id": subnet_id,
            "task_id": task_id,
            "escrow": self._escrow.query_escrow_by_task(
                subnet_id=subnet_id, task_id=task_id, block=block
            ),
            "popw_status": self._popw.query_status_by_task(
                subnet_id=subnet_id, task_id=task_id, block=block
            ),
            "popw_votes": self._popw.query_votes_by_task(
                subnet_id=subnet_id, task_id=task_id, block=block
            ),
        }

    @staticmethod
    def popw_is_approved(popw_status: Any) -> bool:
        """
        Heuristic approval detector for heterogeneous runtime status formats.

        Accepts booleans, strings (`approved`, `finalized`), or dict payloads with
        common keys (`approved`, `outcome`, `status`, `state`).
        """
        if popw_status is None:
            return False
        if isinstance(popw_status, bool):
            return popw_status
        if isinstance(popw_status, str):
            return popw_status.strip().lower() in {"approved", "finalized", "success"}
        if isinstance(popw_status, dict):
            if isinstance(popw_status.get("approved"), bool):
                return popw_status["approved"]
            for key in ("outcome", "status", "state"):
                value = popw_status.get(key)
                if isinstance(value, str) and value.strip().lower() in {
                    "approved",
                    "finalized",
                    "success",
                }:
                    return True
        return False

    def can_release_by_popw(
        self,
        subnet_id: int,
        task_id: str,
        block: Optional[int] = None,
    ) -> bool:
        """Return True when PoPW status indicates escrow is releasable."""
        status = self._popw.query_status_by_task(
            subnet_id=subnet_id, task_id=task_id, block=block
        )
        return self.popw_is_approved(status)

    def guarded_release_call(
        self,
        subnet_id: int,
        task_id: str,
        escrow_id: int,
        verdict: Optional[str] = "approved",
        block: Optional[int] = None,
    ) -> Any:
        """Compose release call only when current PoPW status appears approved."""
        if not self.can_release_by_popw(subnet_id=subnet_id, task_id=task_id, block=block):
            raise RuntimeError("PoPW is not approved for this task; release is blocked")
        return self._escrow.release_escrow_call(
            subnet_id=subnet_id,
            task_id=task_id,
            escrow_id=escrow_id,
            verdict=verdict,
        )

    async def guarded_submit_release(
        self,
        subnet_id: int,
        task_id: str,
        escrow_id: int,
        wallet: "Wallet",
        verdict: Optional[str] = "approved",
        block: Optional[int] = None,
        module_name: str = "EscrowModule",
        call_function: str = "release_escrow",
        *,
        wait_for_inclusion: bool = True,
        wait_for_finalization: bool = False,
    ) -> tuple[bool, str]:
        """Submit escrow release only if PoPW currently evaluates to approved."""
        if not self.can_release_by_popw(subnet_id=subnet_id, task_id=task_id, block=block):
            raise RuntimeError("PoPW is not approved for this task; release is blocked")

        return await self._escrow._extrinsics.sign_and_send_extrinsic_for_task(
            call_module=module_name,
            call_function=call_function,
            subnet_id=subnet_id,
            task_id=task_id,
            wallet=wallet,
            extra_params={"escrow_id": escrow_id, "verdict": verdict},
            wait_for_inclusion=wait_for_inclusion,
            wait_for_finalization=wait_for_finalization,
        )
