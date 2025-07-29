import pytest

from bittensor.core.subtensor_api import SubtensorApi


def test_create_escrow_call_builds_task_scoped_call(mocker):
    api = SubtensorApi(network="latent-lite", mock=True)
    compose = mocker.patch.object(api._subtensor.substrate, "compose_call")
    compose.return_value = "call"

    out = api.create_escrow_call(
        subnet_id=11,
        task_id="task-11",
        payer="5p",
        payee="5q",
        amount_rao=1000,
        timeout_blocks=64,
        arbiter="5a",
    )

    assert out == "call"
    compose.assert_called_once_with(
        call_module="EscrowModule",
        call_function="create_escrow",
        call_params={
            "subnet_id": 11,
            "task_id": "task-11",
            "payer": "5p",
            "payee": "5q",
            "amount_rao": 1000,
            "timeout_blocks": 64,
            "arbiter": "5a",
        },
    )


@pytest.mark.asyncio
async def test_submit_create_escrow_dispatches_sign_send(mocker):
    api = SubtensorApi(network="latent-lite", mock=True)
    helper = api.escrow
    send = mocker.patch.object(
        helper._extrinsics,
        "sign_and_send_extrinsic_for_task",
        return_value=(True, "ok"),
    )

    out = await helper.submit_create_escrow(
        subnet_id=2,
        task_id="t-2",
        wallet=mocker.MagicMock(),
        payer="5p",
        payee="5q",
        amount_rao=500,
        timeout_blocks=32,
    )
    assert out == (True, "ok")
    send.assert_called_once()
    assert send.call_args.kwargs["subnet_id"] == 2
    assert send.call_args.kwargs["task_id"] == "t-2"
    assert send.call_args.kwargs["extra_params"]["amount_rao"] == 500


@pytest.mark.asyncio
async def test_submit_release_escrow_dispatches_sign_send(mocker):
    api = SubtensorApi(network="latent-lite", mock=True)
    helper = api.escrow
    send = mocker.patch.object(
        helper._extrinsics,
        "sign_and_send_extrinsic_for_task",
        return_value=(True, "released"),
    )

    out = await helper.submit_release_escrow(
        subnet_id=2,
        task_id="t-2",
        escrow_id=9,
        wallet=mocker.MagicMock(),
        verdict="approved",
    )
    assert out == (True, "released")
    send.assert_called_once()
    assert send.call_args.kwargs["extra_params"]["escrow_id"] == 9


def test_deposit_release_cancel_call_helpers(mocker):
    api = SubtensorApi(network="latent-lite", mock=True)
    compose = mocker.patch.object(api._subtensor.substrate, "compose_call")
    compose.return_value = "call"

    _ = api.deposit_escrow_call(1, "x", escrow_id=8, amount_rao=10)
    _ = api.release_escrow_call(1, "x", escrow_id=8, verdict="approved")
    _ = api.cancel_escrow_call(1, "x", escrow_id=8, reason="timeout")

    assert compose.call_count == 3
    assert compose.call_args_list[0].kwargs["call_function"] == "deposit_escrow"
    assert compose.call_args_list[1].kwargs["call_function"] == "release_escrow"
    assert compose.call_args_list[2].kwargs["call_function"] == "cancel_escrow"


def test_query_escrow_by_task_uses_query_subtensor_for_task(mocker):
    api = SubtensorApi(network="latent-lite", mock=True)
    helper = api.escrow
    query = mocker.patch.object(helper._queries, "query_subtensor_for_task")
    query.return_value = {"id": 9}

    out = helper.query_escrow_by_task(7, "task-7", block=100)
    assert out == {"id": 9}
    query.assert_called_once_with(
        storage_name="EscrowByTask",
        subnet_id=7,
        task_id="task-7",
        block=100,
    )


def test_query_escrow_events_by_task_uses_map_query(mocker):
    api = SubtensorApi(network="latent-lite", mock=True)
    helper = api.escrow
    query_map = mocker.patch.object(helper._queries, "query_map_subtensor_for_task")
    query_map.return_value = [("evt", 1)]

    out = helper.query_escrow_events_by_task(7, "task-7", block=100)
    assert out == [("evt", 1)]
    query_map.assert_called_once_with(
        storage_name="EscrowEventsByTask",
        subnet_id=7,
        task_id="task-7",
        block=100,
    )
