from bittensor.core.subtensor_api import SubtensorApi
from bittensor.utils import TaskScope


def test_task_scopes_normalize_and_key():
    api = SubtensorApi(network="latent-lite", mock=True)

    scope = api.task_scopes.normalize(subnet_id=7, task_id="task-007")
    assert isinstance(scope, TaskScope)
    assert scope.key == (7, "task-007")
    assert api.task_scopes.scope_key(7, "task-007") == (7, "task-007")


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

