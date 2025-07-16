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

