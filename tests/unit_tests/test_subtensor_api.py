from bittensor.core.subtensor import Subtensor
from bittensor.core.subtensor_api import SubtensorApi
import pytest


def test_properties_methods_comparable(other_class: "Subtensor" = None):
    """Verifies that methods in SubtensorApi and its properties contains all Subtensors methods."""
    # Preps
    subtensor = (
        other_class(network="latent-lite", _mock=True)
        if other_class
        else Subtensor(network="latent-lite", _mock=True)
    )
    subtensor_api = SubtensorApi(network="latent-lite", mock=True)

    subtensor_methods = [m for m in dir(subtensor) if not m.startswith("_")]

    excluded_subtensor_methods = ["commit"]

    subtensor_api_methods = [m for m in dir(subtensor_api) if not m.startswith("_")]
    chain_methods = [m for m in dir(subtensor_api.chain) if not m.startswith("_")]
    commitments_methods = [
        m for m in dir(subtensor_api.commitments) if not m.startswith("_")
    ]
    delegates_methods = [
        m for m in dir(subtensor_api.delegates) if not m.startswith("_")
    ]
    extrinsics_methods = [
        m for m in dir(subtensor_api.extrinsics) if not m.startswith("_")
    ]
    metagraphs_methods = [
        m for m in dir(subtensor_api.metagraphs) if not m.startswith("_")
    ]
    neurons_methods = [m for m in dir(subtensor_api.neurons) if not m.startswith("_")]
    queries_methods = [m for m in dir(subtensor_api.queries) if not m.startswith("_")]
    stakes_methods = [m for m in dir(subtensor_api.staking) if not m.startswith("_")]
    subnets_methods = [m for m in dir(subtensor_api.subnets) if not m.startswith("_")]
    wallets_methods = [m for m in dir(subtensor_api.wallets) if not m.startswith("_")]

    all_subtensor_api_methods = (
        subtensor_api_methods
        + chain_methods
        + commitments_methods
        + delegates_methods
        + extrinsics_methods
        + metagraphs_methods
        + neurons_methods
        + queries_methods
        + stakes_methods
        + subnets_methods
        + wallets_methods
    )

    # Assertions
    for method in subtensor_methods:
        # skipp excluded methods
        if method in excluded_subtensor_methods:
            continue
        assert method in all_subtensor_api_methods, (
            f"`Subtensor.{method}`is not present in class `SubtensorApi`."
        )


def test__methods_comparable_with_passed_legacy_methods(
    other_class: "Subtensor" = None,
):
    """Verifies that methods in SubtensorApi contains all Subtensors methods if `legacy_methods=True` is passed."""
    # Preps
    subtensor = (
        other_class(network="latent-lite", mock=True)
        if other_class
        else Subtensor(network="latent-lite", _mock=True)
    )
    subtensor_api = SubtensorApi(network="latent-lite", mock=True, legacy_methods=True)

    subtensor_methods = [m for m in dir(subtensor) if not m.startswith("_")]
    subtensor_api_methods = [m for m in dir(subtensor_api) if not m.startswith("_")]

    excluded_subtensor_methods = ["commit"]

    # Assertions
    for method in subtensor_methods:
        # skipp excluded methods
        if method in excluded_subtensor_methods:
            continue
        assert method in subtensor_api_methods, (
            f"`Subtensor.{method}`is not present in class `SubtensorApi`."
        )


def test_failed_if_subtensor_has_new_method():
    """Verifies that SubtensorApi fails if Subtensor has a new method."""
    # Preps

    class SubtensorWithNewMethod(Subtensor):
        def return_my_id(self):
            return id(self)

    # Call and assert

    with pytest.raises(AssertionError):
        test_properties_methods_comparable(other_class=SubtensorWithNewMethod)


def test_konnex_profile_autoloads_fallback_and_archive_defaults():
    api = SubtensorApi(network="konnex-devnet", mock=True)
    profile = api.get_konnex_network_profile("konnex-devnet")
    assert api.konnex_profile_name == "konnex-devnet"
    assert api._fallback_endpoints == profile["fallback_endpoints"]
    assert api._archive_endpoints == profile["archive_endpoints"]


def test_konnex_profile_respects_explicit_overrides():
    api = SubtensorApi(
        network="konnex-testnet",
        mock=True,
        fallback_endpoints=["wss://custom-fallback:9944"],
        archive_endpoints=["wss://custom-archive:9944"],
    )
    assert api.konnex_profile_name == "konnex-testnet"
    assert api._fallback_endpoints == ["wss://custom-fallback:9944"]
    assert api._archive_endpoints == ["wss://custom-archive:9944"]


def test_runtime_spec_version_and_guard(monkeypatch):
    api = SubtensorApi(network="latent-lite", mock=True)
    monkeypatch.setattr(api.substrate, "runtime_version", {"specVersion": 1234})
    assert api.runtime_spec_version() == 1234
    assert api.ensure_min_spec_version(1200) is True
    with pytest.raises(RuntimeError, match="below required"):
        api.ensure_min_spec_version(2000)


def test_escrow_shortcuts_exposed_on_subtensor_api():
    api = SubtensorApi(network="latent-lite", mock=True)
    assert callable(api.create_escrow_call)
    assert callable(api.submit_create_escrow)
    assert callable(api.deposit_escrow_call)
    assert callable(api.release_escrow_call)
    assert callable(api.cancel_escrow_call)
    assert callable(api.query_escrow_by_task)
    assert callable(api.query_escrow_events_by_task)
