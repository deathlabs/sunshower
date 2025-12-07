"""sunshower/engine.py"""

# Stand library imports.
from logging import ERROR
from os import environ
from time import perf_counter

# https://discuss.ray.io/t/how-to-set-ray-dedup-logs-0/10465/11
environ["RAY_ACCEL_ENV_VAR_OVERRIDE_ON_ZERO"] = (
    "0"  # Do not override "accelerator visible" devices.
)

# Third party imports.
from langchain_core.load import dumps
from ray import get, init, remote, shutdown

# Local imports.
from sunshower.schema import TeamProfile
from sunshower.utils import build_team, get_experiment_set


@remote
def evaluate_team(team_profile: TeamProfile, task: str):
    team = build_team(team_profile)
    start = perf_counter()
    output = team.invoke({"messages": [{"role": "user", "content": task}]})
    end = perf_counter()
    time_taken = f"{end - start:.6f}"
    return {
        "name": team_profile.name,
        "messages": output["messages"],
        "time_taken": time_taken,
    }


def start(file_name: str):
    """
    The main entrypoint to sunshower.
    """
    # Get the experiment set.
    experiment_set = get_experiment_set(file_name)

    # Init a Ray cluster.
    # - Do not include a dashboard (metrics will therefore not be exported).
    # - Do not send agent logs back to the Ray driver (i.e., the process running Ray).
    init(include_dashboard=False, logging_level=ERROR, log_to_driver=False)

    # Run each experiment declared in parallel on the Ray cluster.
    object_references = []
    for team_profile in experiment_set.spec.team_profiles:
        object_reference = evaluate_team.remote(team_profile, experiment_set.spec.task)
        object_references.append(object_reference)

    # Get the output of each experiment.
    with open(file="results.ndjson", mode="w", encoding="UTF-8") as output_file:
        objects = get(object_references)
        for object in objects:
            output_file.write(f"{dumps(object)}\n")

    # Shutdown the Ray cluster.
    shutdown()
