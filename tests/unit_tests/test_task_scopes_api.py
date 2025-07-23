import pytest

from bittensor.core.subtensor_api import SubtensorApi
from bittensor.utils import TaskScope


def test_task_scopes_normalize_and_key():
    api = SubtensorApi(network="latent-lite", mock=True)

    scope = api.task_scopes.normalize(subnet_id=7, task_id="task-007")
    assert isinstance(scope, TaskScope)
    assert scope.key == (7, "task-007")
    assert api.task_scopes.scope_key(7, "task-007") == (7, "task-007")
    assert api.task_scopes.scope_label(7, "task-007") == "subnet_id=7;task_id=task-007"


def test_task_scopes_match_guard():
    api = SubtensorApi(network="latent-lite", mock=True)

    left = api.task_scopes.normalize(subnet_id=3, task_id="job-1")
    same = api.task_scopes.normalize(subnet_id=3, task_id="job-1")
    other_subnet = api.task_scopes.normalize(subnet_id=4, task_id="job-1")

    assert api.task_scopes.scope_matches(left, same) is True
    assert api.task_scopes.scope_matches(left, other_subnet) is False


def test_queries_task_scope_params():
    api = SubtensorApi(network="latent-lite", mock=True)
    assert api.queries.task_scope_params(11, "job-11") == [11, "job-11"]


def test_queries_task_scope_call_params_matches_task_scopes():
    api = SubtensorApi(network="latent-lite", mock=True)
    d = api.queries.task_scope_call_params(9, "q-9", extra_params={"proof": b"\x01"})
    assert d == api.task_scopes.scope_call_params(9, "q-9", extra_params={"proof": b"\x01"})


def test_task_scopes_scope_call_params():
    api = SubtensorApi(network="latent-lite", mock=True)
    p = api.task_scopes.scope_call_params(3, "t-1", extra_params={"amount": 10})
    assert p == {"subnet_id": 3, "task_id": "t-1", "amount": 10}


def test_task_scopes_scope_call_params_rejects_subnet_override():
    api = SubtensorApi(network="latent-lite", mock=True)
    with pytest.raises(ValueError, match="extra_params"):
        api.task_scopes.scope_call_params(3, "t-1", extra_params={"subnet_id": 99})


def test_compose_call_for_task_merges_params(mocker):
    api = SubtensorApi(network="latent-lite", mock=True)
    compose = mocker.patch.object(api._subtensor.substrate, "compose_call")
    compose.return_value = "call"

    out = api.compose_call_for_task(
        call_module="SubtensorModule",
        call_function="submit_task_proof",
        subnet_id=2,
        task_id="proof-1",
        extra_params={"cid": "bafy..."},
    )

    assert out == "call"
    compose.assert_called_once_with(
        call_module="SubtensorModule",
        call_function="submit_task_proof",
        call_params={
            "subnet_id": 2,
            "task_id": "proof-1",
            "cid": "bafy...",
        },
    )


@pytest.mark.asyncio
async def test_sign_and_send_extrinsic_for_task_sync_subtensor(mocker):
    api = SubtensorApi(network="latent-lite", mock=True)
    mocker.patch.object(
        api._subtensor.substrate, "compose_call", return_value="call_obj"
    )
    send = mocker.patch.object(
        api._subtensor, "sign_and_send_extrinsic", return_value=(True, "ok")
    )
    wallet = mocker.MagicMock()

    result = await api.sign_and_send_extrinsic_for_task(
        call_module="SubtensorModule",
        call_function="task_action",
        subnet_id=4,
        task_id="job-a",
        wallet=wallet,
        extra_params={"payload": 42},
        wait_for_inclusion=False,
    )

    assert result == (True, "ok")
    send.assert_called_once()
    assert send.call_args.kwargs["call"] == "call_obj"
    assert send.call_args.kwargs["wallet"] is wallet
    assert send.call_args.kwargs["wait_for_inclusion"] is False


@pytest.mark.asyncio
async def test_sign_and_send_extrinsic_for_task_awaits_async_compose_and_send(mocker):
    api = SubtensorApi(network="latent-lite", mock=True, async_subtensor=True)

    async def fake_compose(**kwargs):
        assert kwargs["call_params"]["subnet_id"] == 1
        return "async_call"

    async def fake_send(**kwargs):
        assert kwargs["call"] == "async_call"
        return (False, "chain msg")

    mocker.patch.object(api._subtensor.substrate, "compose_call", side_effect=fake_compose)
    mocker.patch.object(
        api._subtensor, "sign_and_send_extrinsic", side_effect=fake_send
    )

    out = await api.sign_and_send_extrinsic_for_task(
        call_module="SubtensorModule",
        call_function="bar",
        subnet_id=1,
        task_id="t1",
        wallet=mocker.MagicMock(),
    )
    assert out == (False, "chain msg")


def test_query_subtensor_for_task_uses_canonical_params(mocker):
    api = SubtensorApi(network="latent-lite", mock=True)
    query_subtensor_spy = mocker.patch.object(api._subtensor, "query_subtensor")
    query_subtensor_spy.return_value = "ok"

    result = api.query_subtensor_for_task(
        storage_name="EscrowByTask",
        subnet_id=5,
        task_id="task-xyz",
        block=123,
    )

    assert result == "ok"
    query_subtensor_spy.assert_called_once_with(
        name="EscrowByTask",
        block=123,
        params=[5, "task-xyz"],
    )

