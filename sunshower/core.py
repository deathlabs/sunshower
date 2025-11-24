# Stand library imports.
from logging import ERROR
from time import perf_counter
from typing import Dict

# https://discuss.ray.io/t/how-to-set-ray-dedup-logs-0/10465/11
from os import environ

environ["RAY_ACCEL_ENV_VAR_OVERRIDE_ON_ZERO"] = (
    "0"  # Do not override "accelerator visible" devices.
)

# Third party imports.
from langchain.agents import create_agent
from langchain_core.load import dumps
from langchain_core.runnables import Runnable
from langgraph.graph import StateGraph, MessagesState, START, END
from ray import get, init, remote, shutdown

# Local imports.
from sunshower.experiments import get_experiment_plans
from sunshower.profiles import get_team_profile, TeamProfile


def build_team(team_profile):
    graph = StateGraph(MessagesState)
    agents = []
    for agent_profile in team_profile.agent_profiles:
        agents.append(agent_profile.name)
        agent = create_agent(
            model=agent_profile.model.name,
            tools=agent_profile.harness.tools,
            system_prompt=agent_profile.model.system_prompt,
        )
        graph.add_node(agent_profile.name, agent)
    graph.add_edge(START, agents[0])
    for previous, next in zip(agents, agents[1:]):
        graph.add_edge(previous, next)
    graph.add_edge(agents[-1], END)
    return graph.compile()


@remote
def evaluate(team_profile: TeamProfile, task: str):
    start = perf_counter()
    team = build_team(team_profile)
    output = team.invoke({"messages": [{"role": "user", "content": task}]})
    end = perf_counter()
    time_taken = f"{end - start:.6f}"
    return {
        "name": team_profile.name,
        "messages": output["messages"],
        "time_taken": time_taken,
    }


def start(file_name: str, task: str):
    """
    The main entrypoint to sunshower.
    """
    # Load agent configurations from a file.
    experiment_plans = get_experiment_plans(file_name)

    # Init a Ray cluster.
    # - Do not include a dashboard (metrics will therefore not be exported).
    # - Do not send agent logs back to the Ray driver (i.e., the process running Ray).
    init(include_dashboard=False, logging_level=ERROR, log_to_driver=False)

    # Run each experiment in parallel on the Ray cluster.
    object_references = []
    for experiment_plan in experiment_plans:
        team_profile = get_team_profile(experiment_plan)
        object_reference = evaluate.remote(team_profile, task)
        object_references.append(object_reference)

    # Get the output of each experiment.
    with open(file="results.ndjson", mode="w", encoding="UTF-8") as output_file:
        objects = get(object_references)
        for object in objects:
            output_file.write(f"{dumps(object)}\n")

    # Shutdown the Ray cluster.
    shutdown()
