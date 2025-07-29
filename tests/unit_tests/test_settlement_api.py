import pytest

from bittensor.core.subtensor_api import SubtensorApi


def test_settlement_snapshot_reads_escrow_and_popw(mocker):
    api = SubtensorApi(network="latent-lite", mock=True)
    helper = api.settlement
    q_escrow = mocker.patch.object(helper._escrow, "query_escrow_by_task")
    q_status = mocker.patch.object(helper._popw, "query_status_by_task")
    q_votes = mocker.patch.object(helper._popw, "query_votes_by_task")
    q_escrow.return_value = {"escrow_id": 1}
    q_status.return_value = {"status": "Approved"}
    q_votes.return_value = [("validator-1", True)]

    snap = helper.settlement_snapshot(2, "task-2", block=99)
    assert snap["escrow"]["escrow_id"] == 1
    assert snap["popw_status"]["status"] == "Approved"
    assert snap["popw_votes"] == [("validator-1", True)]


@pytest.mark.parametrize(
    "value,expected",
    [
        (True, True),
        (False, False),
        ("approved", True),
        ("finalized", True),
        ("rejected", False),
        ({"approved": True}, True),
        ({"outcome": "approved"}, True),
        ({"status": "finalized"}, True),
        ({"state": "success"}, True),
        ({"status": "rejected"}, False),
    ],
)
def test_popw_is_approved_variants(value, expected):
    api = SubtensorApi(network="latent-lite", mock=True)
    assert api.settlement.popw_is_approved(value) is expected


def test_guarded_release_call_requires_approved_popw(mocker):
    api = SubtensorApi(network="latent-lite", mock=True)
    helper = api.settlement
    mocker.patch.object(helper, "can_release_by_popw", return_value=False)

    with pytest.raises(RuntimeError, match="not approved"):
        helper.guarded_release_call(1, "task", escrow_id=5)


def test_guarded_release_call_composes_when_approved(mocker):
    api = SubtensorApi(network="latent-lite", mock=True)
    helper = api.settlement
    mocker.patch.object(helper, "can_release_by_popw", return_value=True)
    release = mocker.patch.object(helper._escrow, "release_escrow_call", return_value="call")

    out = helper.guarded_release_call(1, "task", escrow_id=5)
    assert out == "call"
    release.assert_called_once()


@pytest.mark.asyncio
async def test_guarded_submit_release_dispatches_when_approved(mocker):
    api = SubtensorApi(network="latent-lite", mock=True)
    helper = api.settlement
    mocker.patch.object(helper, "can_release_by_popw", return_value=True)
    send = mocker.patch.object(helper._escrow, "submit_release_escrow", return_value=(True, "ok"))

    out = await helper.guarded_submit_release(
        subnet_id=1, task_id="task", escrow_id=10, wallet=mocker.MagicMock()
    )
    assert out == (True, "ok")
    send.assert_called_once()
    assert send.call_args.kwargs["escrow_id"] == 10
