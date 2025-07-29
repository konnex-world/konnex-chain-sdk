from typing import Optional, Union, TYPE_CHECKING

from bittensor.core import settings
from bittensor.core.async_subtensor import AsyncSubtensor as _AsyncSubtensor
from bittensor.core.subtensor import Subtensor as _Subtensor
from .chain import Chain as _Chain
from .commitments import Commitments as _Commitments
from .delegates import Delegates as _Delegates
from .escrow import Escrow as _Escrow
from .extrinsics import Extrinsics as _Extrinsics
from .metagraphs import Metagraphs as _Metagraphs
from .neurons import Neurons as _Neurons
from .popw import PoPW as _PoPW
from .queries import Queries as _Queries
from .staking import Staking as _Staking
from .subnets import Subnets as _Subnets
from .task_scopes import TaskScopes as _TaskScopes
from .utils import add_legacy_methods as _add_classic_fields
from .wallets import Wallets as _Wallets

if TYPE_CHECKING:
    from bittensor.core.config import Config


class SubtensorApi:
    """Subtensor API class.

    Arguments:
        network: The network to connect to. Defaults to `None` -> "finney".
        config: Bittensor configuration object. Defaults to `None`.
        legacy_methods: If `True`, all methods from the Subtensor class will be added to the root level of this class.
        fallback_endpoints: List of fallback endpoints to use if default or provided network is not available. Defaults to `None`.
        retry_forever: Whether to retry forever on connection errors. Defaults to `False`.
        log_verbose: Enables or disables verbose logging.
        mock: Whether this is a mock instance. Mainly just for use in testing.
        archive_endpoints: Similar to fallback_endpoints, but specifically only archive nodes. Will be used in cases
            where you are requesting a block that is too old for your current (presumably lite) node. Defaults to `None`
        websocket_shutdown_timer: Amount of time, in seconds, to wait after the last response from the chain to close
            the connection. Only applicable to AsyncSubtensor.

    Example:
        # sync version
        import bittensor as bt

        subtensor = bt.SubtensorApi()
        print(subtensor.block)
        print(subtensor.delegates.get_delegate_identities())
        subtensor.chain.tx_rate_limit()

        # async version
        import bittensor as bt

        subtensor = bt.SubtensorApi(async_subtensor=True)
        async with subtensor:
            print(await subtensor.block)
            print(await subtensor.delegates.get_delegate_identities())
            print(await subtensor.chain.tx_rate_limit())

        # using `legacy_methods`
        import bittensor as bt

        subtensor = bt.SubtensorApi(legacy_methods=True)
        print(subtensor.bonds(0))

        # using `fallback_endpoints` or `retry_forever`
        import bittensor as bt

        subtensor = bt.SubtensorApi(
            network="finney",
            fallback_endpoints=["wss://localhost:9945", "wss://some-other-endpoint:9945"],
            retry_forever=True,
        )
        print(subtensor.block)

        # Konnex: task-scoped subnet helpers (validated `subnet_id` + `task_id`)
        import bittensor as bt

        api = bt.SubtensorApi(network="finney", mock=True)
        scope = api.task_scopes.normalize(subnet_id=1, task_id="escrow-1")
        params = api.task_scope_params_from_scope(scope)
        call_params = api.task_scope_call_params_from_scope(scope, extra_params={"cid": "bafy..."})
        _ = api.query_subtensor_for_task_from_scope("EscrowByTask", scope, block=None)
        _ = api.compose_call_for_task_from_scope(
            "SubtensorModule", "submit_proof", scope, extra_params={"cid": "bafy..."}
        )
    """

    def __init__(
        self,
        network: Optional[str] = None,
        config: Optional["Config"] = None,
        async_subtensor: bool = False,
        legacy_methods: bool = False,
        fallback_endpoints: Optional[list[str]] = None,
        retry_forever: bool = False,
        log_verbose: bool = False,
        mock: bool = False,
        archive_endpoints: Optional[list[str]] = None,
        websocket_shutdown_timer: float = 5.0,
    ):
        self.network = network
        self.konnex_profile_name: Optional[str] = None
        if network in settings.KONNEX_NETWORK_PROFILES:
            profile = settings.get_konnex_network_profile(network)
            self.konnex_profile_name = network
            if fallback_endpoints is None:
                fallback_endpoints = profile["fallback_endpoints"]
            if archive_endpoints is None:
                archive_endpoints = profile["archive_endpoints"]

        self._fallback_endpoints = fallback_endpoints
        self._archive_endpoints = archive_endpoints
        self._retry_forever = retry_forever
        self._ws_shutdown_timer = websocket_shutdown_timer
        self._mock = mock
        self.log_verbose = log_verbose
        self.is_async = async_subtensor
        self._config = config

        # assigned only for async instance
        self.initialize = None
        self._subtensor = self._get_subtensor()

        # fix naming collision
        self._neurons = _Neurons(self._subtensor)

        # define empty fields
        self.substrate = self._subtensor.substrate
        self.chain_endpoint = self._subtensor.chain_endpoint
        self.close = self._subtensor.close
        self.config = self._subtensor.config
        self.setup_config = self._subtensor.setup_config
        self.help = self._subtensor.help

        self.determine_block_hash = self._subtensor.determine_block_hash
        self.encode_params = self._subtensor.encode_params
        self.query_subtensor_for_task = self.queries.query_subtensor_for_task
        self.query_subtensor_for_task_from_scope = (
            self.queries.query_subtensor_for_task_from_scope
        )
        self.query_map_subtensor_for_task = self.queries.query_map_subtensor_for_task
        self.query_map_subtensor_for_task_from_scope = (
            self.queries.query_map_subtensor_for_task_from_scope
        )
        self.query_module_for_task = self.queries.query_module_for_task
        self.query_module_for_task_from_scope = (
            self.queries.query_module_for_task_from_scope
        )
        self.task_scope_params = self.queries.task_scope_params
        self.task_scope_call_params = self.queries.task_scope_call_params
        self.task_scope_params_from_scope = self.queries.task_scope_params_from_scope
        self.task_scope_call_params_from_scope = (
            self.queries.task_scope_call_params_from_scope
        )
        self.task_scope_params_with = self.queries.task_scope_params_with
        self.task_scope_params_with_from_scope = (
            self.queries.task_scope_params_with_from_scope
        )
        self.compose_call_for_task = self.extrinsics.compose_call_for_task
        self.compose_call_for_task_from_scope = (
            self.extrinsics.compose_call_for_task_from_scope
        )
        self.sign_and_send_extrinsic_for_task = (
            self.extrinsics.sign_and_send_extrinsic_for_task
        )
        self.sign_and_send_extrinsic_for_task_from_scope = (
            self.extrinsics.sign_and_send_extrinsic_for_task_from_scope
        )
        self.sign_and_send_extrinsic = self._subtensor.sign_and_send_extrinsic
        self.start_call = self._subtensor.start_call
        self.wait_for_block = self._subtensor.wait_for_block
        self.konnex_network_profiles = settings.KONNEX_NETWORK_PROFILES
        self.create_escrow_call = self.escrow.create_escrow_call
        self.submit_create_escrow = self.escrow.submit_create_escrow
        self.deposit_escrow_call = self.escrow.deposit_escrow_call
        self.release_escrow_call = self.escrow.release_escrow_call
        self.cancel_escrow_call = self.escrow.cancel_escrow_call
        self.query_escrow_by_task = self.escrow.query_escrow_by_task
        self.query_escrow_events_by_task = self.escrow.query_escrow_events_by_task
        self.popw_vote_call = self.popw.vote_call
        self.submit_popw_vote = self.popw.submit_vote
        self.popw_finalize_call = self.popw.finalize_call
        self.query_popw_status_by_task = self.popw.query_status_by_task
        self.query_popw_votes_by_task = self.popw.query_votes_by_task

        # adds all Subtensor methods into main level of SubtensorApi class
        if legacy_methods:
            _add_classic_fields(self)

    @staticmethod
    def get_konnex_network_profile(profile_name: str) -> dict[str, object]:
        """Return endpoint/fallback defaults for a named Konnex network profile."""
        return settings.get_konnex_network_profile(profile_name)

    def runtime_spec_version(self) -> Optional[int]:
        """
        Best-effort read of runtime spec version from current substrate connection.

        Returns `None` if substrate does not expose runtime version metadata.
        """
        runtime_version = getattr(self.substrate, "runtime_version", None)
        if runtime_version is None:
            return None
        if isinstance(runtime_version, dict):
            return runtime_version.get("specVersion") or runtime_version.get(
                "spec_version"
            )
        return getattr(runtime_version, "specVersion", None) or getattr(
            runtime_version, "spec_version", None
        )

    def ensure_min_spec_version(self, min_spec_version: int) -> bool:
        """
        Validate that connected runtime meets minimum spec version.

        Raises RuntimeError when runtime version is missing or below minimum.
        """
        current = self.runtime_spec_version()
        if current is None:
            raise RuntimeError("Runtime spec version is unavailable on current substrate")
        if current < min_spec_version:
            raise RuntimeError(
                f"Runtime spec version {current} is below required {min_spec_version}"
            )
        return True

    def _get_subtensor(self) -> Union["_Subtensor", "_AsyncSubtensor"]:
        """Returns the subtensor instance based on the provided config and subtensor type flag."""
        if self.is_async:
            _subtensor = _AsyncSubtensor(
                network=self.network,
                config=self._config,
                log_verbose=self.log_verbose,
                fallback_endpoints=self._fallback_endpoints,
                retry_forever=self._retry_forever,
                _mock=self._mock,
                archive_endpoints=self._archive_endpoints,
                websocket_shutdown_timer=self._ws_shutdown_timer,
            )
            self.initialize = _subtensor.initialize
            return _subtensor
        else:
            return _Subtensor(
                network=self.network,
                config=self._config,
                log_verbose=self.log_verbose,
                fallback_endpoints=self._fallback_endpoints,
                retry_forever=self._retry_forever,
                _mock=self._mock,
                archive_endpoints=self._archive_endpoints,
            )

    def _determine_chain_endpoint(self) -> str:
        """Determines the connection and mock flag."""
        if self._mock:
            return "Mock"
        return self.substrate.url

    def __str__(self):
        return (
            f"<Network: {self.network}, "
            f"Chain: {self._determine_chain_endpoint()}, "
            f"{'Async version' if self.is_async else 'Sync version'}>"
        )

    def __repr__(self):
        return self.__str__()

    def __enter__(self):
        if self.is_async:
            raise NotImplementedError(
                "Async version of SubtensorApi cannot be used with sync context manager."
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.is_async:
            raise NotImplementedError(
                "Async version of SubtensorApi cannot be used with sync context manager."
            )
        self.close()

    async def __aenter__(self):
        if not self.is_async:
            raise NotImplementedError(
                "Sync version of SubtensorApi cannot be used with async context manager."
            )
        return await self._subtensor.__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not self.is_async:
            raise NotImplementedError(
                "Sync version of SubtensorApi cannot be used with async context manager."
            )
        await self.substrate.close()

    @classmethod
    def add_args(cls, parser):
        _Subtensor.add_args(parser)

    @property
    def block(self):
        """Returns current chain block number."""
        return self._subtensor.block

    @property
    def chain(self):
        """Property of interaction with chain methods."""
        return _Chain(self._subtensor)

    @property
    def commitments(self):
        """Property to access commitments methods."""
        return _Commitments(self._subtensor)

    @property
    def delegates(self):
        """Property to access delegates methods."""
        return _Delegates(self._subtensor)

    @property
    def extrinsics(self):
        """Property to access extrinsics methods."""
        return _Extrinsics(self._subtensor)

    @property
    def escrow(self):
        """Property to access task-scoped escrow helper methods."""
        return _Escrow(self._subtensor)

    @property
    def popw(self):
        """Property to access task-scoped PoPW helper methods."""
        return _PoPW(self._subtensor)

    @property
    def metagraphs(self):
        """Property to access metagraphs methods."""
        return _Metagraphs(self._subtensor)

    @property
    def neurons(self):
        """Property to access neurons methods."""
        return self._neurons

    @neurons.setter
    def neurons(self, value):
        """Setter for neurons property."""
        self._neurons = value

    @property
    def queries(self):
        """Property to access subtensor queries methods."""
        return _Queries(self._subtensor)

    @property
    def staking(self):
        """Property to access staking methods."""
        return _Staking(self._subtensor)

    @property
    def subnets(self):
        """Property of interaction with subnets methods."""
        return _Subnets(self._subtensor)

    @property
    def wallets(self):
        """Property of interaction methods with cold/hotkeys, and balances, etc."""
        return _Wallets(self._subtensor)

    @property
    def task_scopes(self):
        """Property for subnet-aware `(subnet_id, task_id)` helpers."""
        return _TaskScopes(self._subtensor)
