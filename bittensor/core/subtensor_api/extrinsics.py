import inspect
from typing import Any, Optional, TYPE_CHECKING, Union

from bittensor.utils import TaskScope
from bittensor.core.subtensor import Subtensor as _Subtensor
from bittensor.core.async_subtensor import AsyncSubtensor as _AsyncSubtensor

from .task_scopes import TaskScopes as _TaskScopes

if TYPE_CHECKING:
    from bittensor_wallet import Wallet


class Extrinsics:
    """Class for managing extrinsic operations."""

    def __init__(self, subtensor: Union["_Subtensor", "_AsyncSubtensor"]):
        self._subtensor = subtensor
        self._task_scopes = _TaskScopes(subtensor)
        self.add_stake = subtensor.add_stake
        self.add_stake_multiple = subtensor.add_stake_multiple
        self.burned_register = subtensor.burned_register
        self.commit_weights = subtensor.commit_weights
        self.move_stake = subtensor.move_stake
        self.register = subtensor.register
        self.register_subnet = subtensor.register_subnet
        self.reveal_weights = subtensor.reveal_weights
        self.root_register = subtensor.root_register
        self.root_set_weights = subtensor.root_set_weights
        self.root_set_pending_childkey_cooldown = (
            subtensor.root_set_pending_childkey_cooldown
        )
        self.set_children = subtensor.set_children
        self.set_subnet_identity = subtensor.set_subnet_identity
        self.set_weights = subtensor.set_weights
        self.serve_axon = subtensor.serve_axon
        self.start_call = subtensor.start_call
        self.swap_stake = subtensor.swap_stake
        self.transfer = subtensor.transfer
        self.transfer_stake = subtensor.transfer_stake
        self.unstake = subtensor.unstake
        self.unstake_multiple = subtensor.unstake_multiple

    def compose_call_for_task(
        self,
        call_module: str,
        call_function: str,
        subnet_id: int,
        task_id: str,
        extra_params: Optional[dict[str, Any]] = None,
    ) -> Any:
        """
        Compose a chain call with validated `(subnet_id, task_id)` in `call_params`.

        Runtime pallets must expose matching extrinsic names and parameter shapes.
        For async subtensor, ``substrate.compose_call`` returns an awaitable.
        """
        call_params = self._task_scopes.scope_call_params(
            subnet_id=subnet_id,
            task_id=task_id,
            extra_params=extra_params,
        )
        return self._subtensor.substrate.compose_call(
            call_module=call_module,
            call_function=call_function,
            call_params=call_params,
        )

    def compose_call_for_task_from_scope(
        self,
        call_module: str,
        call_function: str,
        scope: TaskScope,
        extra_params: Optional[dict[str, Any]] = None,
    ) -> Any:
        """
        Same as ``compose_call_for_task`` but uses a pre-built ``TaskScope``.
        """
        call_params = self._task_scopes.scope_call_params_from_scope(
            scope, extra_params=extra_params
        )
        return self._subtensor.substrate.compose_call(
            call_module=call_module,
            call_function=call_function,
            call_params=call_params,
        )

    async def sign_and_send_extrinsic_for_task(
        self,
        call_module: str,
        call_function: str,
        subnet_id: int,
        task_id: str,
        wallet: "Wallet",
        extra_params: Optional[dict[str, Any]] = None,
        *,
        wait_for_inclusion: bool = True,
        wait_for_finalization: bool = False,
        sign_with: str = "coldkey",
        use_nonce: bool = False,
        period: Optional[int] = None,
        nonce_key: str = "hotkey",
        raise_error: bool = False,
    ) -> tuple[bool, str]:
        """
        Compose a task-scoped call and submit it (sync or async Subtensor).

        ``substrate.compose_call`` may return a coroutine on ``AsyncSubtensor``; this
        method awaits it when needed, then dispatches to ``sign_and_send_extrinsic``.
        """
        call = self.compose_call_for_task(
            call_module=call_module,
            call_function=call_function,
            subnet_id=subnet_id,
            task_id=task_id,
            extra_params=extra_params,
        )
        return await self._dispatch_signed_call(
            call=call,
            wallet=wallet,
            wait_for_inclusion=wait_for_inclusion,
            wait_for_finalization=wait_for_finalization,
            sign_with=sign_with,
            use_nonce=use_nonce,
            period=period,
            nonce_key=nonce_key,
            raise_error=raise_error,
        )

    async def sign_and_send_extrinsic_for_task_from_scope(
        self,
        call_module: str,
        call_function: str,
        scope: TaskScope,
        wallet: "Wallet",
        extra_params: Optional[dict[str, Any]] = None,
        *,
        wait_for_inclusion: bool = True,
        wait_for_finalization: bool = False,
        sign_with: str = "coldkey",
        use_nonce: bool = False,
        period: Optional[int] = None,
        nonce_key: str = "hotkey",
        raise_error: bool = False,
    ) -> tuple[bool, str]:
        """Submit a task-scoped extrinsic using a ``TaskScope`` instead of raw ids."""
        call = self.compose_call_for_task_from_scope(
            call_module=call_module,
            call_function=call_function,
            scope=scope,
            extra_params=extra_params,
        )
        return await self._dispatch_signed_call(
            call=call,
            wallet=wallet,
            wait_for_inclusion=wait_for_inclusion,
            wait_for_finalization=wait_for_finalization,
            sign_with=sign_with,
            use_nonce=use_nonce,
            period=period,
            nonce_key=nonce_key,
            raise_error=raise_error,
        )

    async def _dispatch_signed_call(
        self,
        call: Any,
        wallet: "Wallet",
        wait_for_inclusion: bool,
        wait_for_finalization: bool,
        sign_with: str,
        use_nonce: bool,
        period: Optional[int],
        nonce_key: str,
        raise_error: bool,
    ) -> tuple[bool, str]:
        """Resolve sync/async compose call and dispatch to sign_and_send_extrinsic."""
        if inspect.isawaitable(call):
            call = await call

        send = self._subtensor.sign_and_send_extrinsic
        kwargs = dict(
            call=call,
            wallet=wallet,
            wait_for_inclusion=wait_for_inclusion,
            wait_for_finalization=wait_for_finalization,
            sign_with=sign_with,
            use_nonce=use_nonce,
            period=period,
            nonce_key=nonce_key,
            raise_error=raise_error,
        )
        if inspect.iscoroutinefunction(send):
            return await send(**kwargs)
        return send(**kwargs)
