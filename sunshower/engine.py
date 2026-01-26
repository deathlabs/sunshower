"""sunshower/engine.py"""

# Standard library imports.
from logging import ERROR
from os import environ
from textwrap import dedent
from time import perf_counter

# https://discuss.ray.io/t/how-to-set-ray-dedup-logs-0/10465/11
environ["RAY_ACCEL_ENV_VAR_OVERRIDE_ON_ZERO"] = (
    "0"  # Do not override "accelerator visible" devices.
)

# Third party imports.
from langchain.agents import create_agent
from langchain_core.load import dumps
from ray import get, init, is_initialized, remote, shutdown

# Local imports.
from sunshower.schema import Spec, TeamProfile
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


def run_judge(spec: Spec):
    with open(file="results.ndjson", mode="r", encoding="UTF-8") as output_file:
        results = output_file.readlines()

    for judge_profile in spec.judge_profiles:
        judge = create_agent(
            model=judge_profile.model.name,
            tools=judge_profile.harness.tools,
            system_prompt=judge_profile.model.prompt,
        )
        metrics = []
        for metricToEvaluate in judge_profile.metricsToEvaluate:
            metric = dedent(f"""
                ## {metricToEvaluate.type} Requirements  
                {metricToEvaluate.prompt}
            """)
            metrics.append(metric)

        team_output = dedent(f"""
            ## Agent Output
            {results}
            """)
        metrics.append(team_output)
        task = "\n\n".join([str(metric) for metric in metrics])
    return judge.invoke({"messages": [{"role": "user", "content": task}]})


def start(file_name: str):
    """
    The main entrypoint to sunshower.
    """
    # Get the experiment set.
    experiment_set = get_experiment_set(file_name)

    if is_initialized:
        shutdown()

    # Init a Ray cluster.
    # - Do not include a dashboard (metrics will therefore not be exported).
    # - Do not send agent logs back to the Ray driver (i.e., the process running Ray).
    init(include_dashboard=False, logging_level=ERROR, log_to_driver=False)

    # Run each experiment declared in parallel on the Ray cluster.
    object_references = []
    trials = experiment_set.spec.trials
    for trial in range(trials):
        for team_profile in experiment_set.spec.team_profiles:
            object_reference = evaluate_team.remote(
                team_profile, experiment_set.spec.task
            )
            object_references.append(object_reference)

    # Save the output of each experiment.
    with open(file="results.ndjson", mode="w", encoding="UTF-8") as output_file:
        objects = get(object_references)
        for object in objects:
            output_file.write(f"{dumps(object)}\n")

    # Shutdown the Ray cluster.
    shutdown()
    with open(file="results.md", mode="w", encoding="UTF-8") as results_markdown:
        judgement = run_judge(experiment_set.spec)
        results_markdown.write(f"{dumps(judgement)}\n")
