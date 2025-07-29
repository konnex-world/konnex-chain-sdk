from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, TYPE_CHECKING, Union

from bittensor.core.subtensor import Subtensor as _Subtensor
from bittensor.core.async_subtensor import AsyncSubtensor as _AsyncSubtensor

from .extrinsics import Extrinsics as _Extrinsics
from .queries import Queries as _Queries

if TYPE_CHECKING:
    from bittensor_wallet import Wallet


class PoPW:
    """Task-scoped PoPW helper facade for Konnex runtime modules."""

    class Decision(str, Enum):
        PENDING = "pending"
        APPROVED = "approved"
        REJECTED = "rejected"
        FINALIZED = "finalized"
        UNKNOWN = "unknown"

    @dataclass(frozen=True)
    class NormalizedStatus:
        decision: "PoPW.Decision"
        raw: Any
        reason: Optional[str] = None

        @property
        def releasable(self) -> bool:
            return self.decision in {PoPW.Decision.APPROVED, PoPW.Decision.FINALIZED}

    def __init__(self, subtensor: Union["_Subtensor", "_AsyncSubtensor"]):
        self._queries = _Queries(subtensor)
        self._extrinsics = _Extrinsics(subtensor)

    @staticmethod
    def _drop_none(values: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in values.items() if v is not None}

    def vote_call(
        self,
        subnet_id: int,
        task_id: str,
        vote: bool,
        report_hash: Optional[str] = None,
        confidence_bps: Optional[int] = None,
        module_name: str = "PoPWModule",
        call_function: str = "vote_popw",
    ) -> Any:
        """Compose a PoPW vote call scoped by `(subnet_id, task_id)`."""
        params = self._drop_none(
            {
                "vote": vote,
                "report_hash": report_hash,
                "confidence_bps": confidence_bps,
            }
        )
        return self._extrinsics.compose_call_for_task(
            call_module=module_name,
            call_function=call_function,
            subnet_id=subnet_id,
            task_id=task_id,
            extra_params=params,
        )

    async def submit_vote(
        self,
        subnet_id: int,
        task_id: str,
        wallet: "Wallet",
        vote: bool,
        report_hash: Optional[str] = None,
        confidence_bps: Optional[int] = None,
        module_name: str = "PoPWModule",
        call_function: str = "vote_popw",
        *,
        wait_for_inclusion: bool = True,
        wait_for_finalization: bool = False,
    ) -> tuple[bool, str]:
        """Compose + submit a PoPW vote call."""
        params = self._drop_none(
            {
                "vote": vote,
                "report_hash": report_hash,
                "confidence_bps": confidence_bps,
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

    def finalize_call(
        self,
        subnet_id: int,
        task_id: str,
        outcome: Optional[str] = None,
        module_name: str = "PoPWModule",
        call_function: str = "finalize_popw",
    ) -> Any:
        """Compose a PoPW finalize call."""
        return self._extrinsics.compose_call_for_task(
            call_module=module_name,
            call_function=call_function,
            subnet_id=subnet_id,
            task_id=task_id,
            extra_params=self._drop_none({"outcome": outcome}),
        )

    def query_status_by_task(
        self,
        subnet_id: int,
        task_id: str,
        block: Optional[int] = None,
        storage_name: str = "PoPWStatusByTask",
    ) -> Any:
        """Query PoPW status by task key."""
        return self._queries.query_subtensor_for_task(
            storage_name=storage_name,
            subnet_id=subnet_id,
            task_id=task_id,
            block=block,
        )

    def query_votes_by_task(
        self,
        subnet_id: int,
        task_id: str,
        block: Optional[int] = None,
        storage_name: str = "PoPWVotesByTask",
    ) -> Any:
        """Query PoPW votes map by task key."""
        return self._queries.query_map_subtensor_for_task(
            storage_name=storage_name,
            subnet_id=subnet_id,
            task_id=task_id,
            block=block,
        )

    @staticmethod
    def normalize_popw_status(popw_status: Any) -> "PoPW.NormalizedStatus":
        """Normalize raw PoPW status into deterministic SDK decision enum."""
        if popw_status is None:
            return PoPW.NormalizedStatus(
                decision=PoPW.Decision.UNKNOWN,
                raw=popw_status,
                reason="missing status",
            )
        if isinstance(popw_status, bool):
            return PoPW.NormalizedStatus(
                decision=PoPW.Decision.APPROVED if popw_status else PoPW.Decision.REJECTED,
                raw=popw_status,
                reason="bool fallback",
            )
        if isinstance(popw_status, str):
            normalized = popw_status.strip().lower()
            mapping = {
                "pending": PoPW.Decision.PENDING,
                "approved": PoPW.Decision.APPROVED,
                "rejected": PoPW.Decision.REJECTED,
                "finalized": PoPW.Decision.FINALIZED,
                "success": PoPW.Decision.FINALIZED,
            }
            decision = mapping.get(normalized, PoPW.Decision.UNKNOWN)
            return PoPW.NormalizedStatus(
                decision=decision,
                raw=popw_status,
                reason=None if decision != PoPW.Decision.UNKNOWN else "unknown string",
            )
        if isinstance(popw_status, dict):
            if isinstance(popw_status.get("approved"), bool):
                return PoPW.NormalizedStatus(
                    decision=(
                        PoPW.Decision.APPROVED
                        if popw_status["approved"]
                        else PoPW.Decision.REJECTED
                    ),
                    raw=popw_status,
                )
            for key in ("outcome", "status", "state"):
                value = popw_status.get(key)
                if isinstance(value, str):
                    return PoPW.normalize_popw_status(value)
            return PoPW.NormalizedStatus(
                decision=PoPW.Decision.UNKNOWN,
                raw=popw_status,
                reason="dict without recognized keys",
            )
        return PoPW.NormalizedStatus(
            decision=PoPW.Decision.UNKNOWN,
            raw=popw_status,
            reason="unsupported type",
        )

    @staticmethod
    def is_releasable_status(popw_status: Any) -> bool:
        """Check whether a raw PoPW payload permits escrow release."""
        return PoPW.normalize_popw_status(popw_status).releasable

    def query_normalized_status_by_task(
        self,
        subnet_id: int,
        task_id: str,
        block: Optional[int] = None,
        storage_name: str = "PoPWStatusByTask",
    ) -> "PoPW.NormalizedStatus":
        """Query and normalize PoPW status in one step."""
        raw = self.query_status_by_task(
            subnet_id=subnet_id,
            task_id=task_id,
            block=block,
            storage_name=storage_name,
        )
        return self.normalize_popw_status(raw)
