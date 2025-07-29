import pytest

from bittensor.core.subtensor_api import SubtensorApi


def test_popw_vote_call_builds_task_scoped_call(mocker):
    api = SubtensorApi(network="latent-lite", mock=True)
    compose = mocker.patch.object(api._subtensor.substrate, "compose_call")
    compose.return_value = "call"

    out = api.popw_vote_call(
        subnet_id=11,
        task_id="task-11",
        vote=True,
        report_hash="0xabc",
        confidence_bps=9000,
    )

    assert out == "call"
    compose.assert_called_once_with(
        call_module="PoPWModule",
        call_function="vote_popw",
        call_params={
            "subnet_id": 11,
            "task_id": "task-11",
            "vote": True,
            "report_hash": "0xabc",
            "confidence_bps": 9000,
        },
    )


@pytest.mark.asyncio
async def test_submit_popw_vote_dispatches_sign_send(mocker):
    api = SubtensorApi(network="latent-lite", mock=True)
    helper = api.popw
    send = mocker.patch.object(
        helper._extrinsics,
        "sign_and_send_extrinsic_for_task",
        return_value=(True, "ok"),
    )

    out = await helper.submit_vote(
        subnet_id=2,
        task_id="t-2",
        wallet=mocker.MagicMock(),
        vote=False,
        confidence_bps=7000,
    )
    assert out == (True, "ok")
    send.assert_called_once()
    assert send.call_args.kwargs["subnet_id"] == 2
    assert send.call_args.kwargs["task_id"] == "t-2"
    assert send.call_args.kwargs["extra_params"]["vote"] is False


def test_popw_finalize_call_helper(mocker):
    api = SubtensorApi(network="latent-lite", mock=True)
    compose = mocker.patch.object(api._subtensor.substrate, "compose_call")
    compose.return_value = "call"

    out = api.popw_finalize_call(1, "x", outcome="approved")
    assert out == "call"
    compose.assert_called_once_with(
        call_module="PoPWModule",
        call_function="finalize_popw",
        call_params={"subnet_id": 1, "task_id": "x", "outcome": "approved"},
    )


def test_query_popw_status_and_votes_by_task(mocker):
    api = SubtensorApi(network="latent-lite", mock=True)
    helper = api.popw
    q1 = mocker.patch.object(helper._queries, "query_subtensor_for_task")
    q2 = mocker.patch.object(helper._queries, "query_map_subtensor_for_task")
    q1.return_value = {"status": "approved"}
    q2.return_value = [("validator", True)]

    status = api.query_popw_status_by_task(7, "task-7", block=100)
    votes = api.query_popw_votes_by_task(7, "task-7", block=100)

    assert status == {"status": "approved"}
    assert votes == [("validator", True)]
    q1.assert_called_once_with(
        storage_name="PoPWStatusByTask", subnet_id=7, task_id="task-7", block=100
    )
    q2.assert_called_once_with(
        storage_name="PoPWVotesByTask", subnet_id=7, task_id="task-7", block=100
    )


@pytest.mark.parametrize(
    "value,decision,releasable",
    [
        ("pending", "pending", False),
        ("approved", "approved", True),
        ("rejected", "rejected", False),
        ("finalized", "finalized", True),
        ({"status": "finalized"}, "finalized", True),
        ({"approved": False}, "rejected", False),
        (None, "unknown", False),
    ],
)
def test_popw_normalize_status_variants(value, decision, releasable):
    api = SubtensorApi(network="latent-lite", mock=True)
    normalized = api.popw.normalize_popw_status(value)
    assert normalized.decision.value == decision
    assert normalized.releasable is releasable


def test_query_popw_normalized_status_by_task(mocker):
    api = SubtensorApi(network="latent-lite", mock=True)
    helper = api.popw
    q = mocker.patch.object(helper, "query_status_by_task", return_value={"status": "approved"})

    out = api.query_popw_normalized_status_by_task(9, "task-9", block=33)
    assert out.decision.value == "approved"
    assert out.releasable is True
    q.assert_called_once_with(
        subnet_id=9,
        task_id="task-9",
        block=33,
        storage_name="PoPWStatusByTask",
    )
