"""sunshower/utils.py"""

# Third party imports.
from langchain.agents import create_agent
from langgraph.graph import StateGraph, MessagesState, START, END
from yaml import safe_load

# Local imports
from sunshower.schema import ExperimentSet, TeamProfile


def get_experiment_set(file_name: str) -> ExperimentSet:
    with open(file_name, "r", encoding="UTF-8") as file:
        return ExperimentSet(**safe_load(file))


def build_team(team_profile: TeamProfile):
    graph = StateGraph(MessagesState)
    agent_names = []
    for agent_profile in team_profile.agent_profiles:
        agent_names.append(agent_profile.name)
        agent = create_agent(
            model=agent_profile.model.name,
            tools=agent_profile.harness.tools,
            system_prompt=agent_profile.model.system_prompt,
        )
        graph.add_node(agent_profile.name, agent)
    graph.add_edge(START, agent_names[0])
    for current_agent_name, next_agent_name in zip(agent_names, agent_names[1:]):
        graph.add_edge(current_agent_name, next_agent_name)
    graph.add_edge(agent_names[-1], END)
    return graph.compile()
