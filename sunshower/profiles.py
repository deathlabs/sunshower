# Standard library imports.
from dataclasses import dataclass
from typing import Any, Dict, List

# Third party imports.
from pydantic import BaseModel

# Local imports.
from sunshower.models import Model
from sunshower.harnesses import Harness


@dataclass
class AgentProfile:
    name: str
    model: Model
    harness: Harness

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        # Check agent name.
        if "name" not in data:
            raise ValueError('"name" key not found')
        elif data.get("name") is None:
            raise ValueError('"name" key cannot be empty')
        name = data["name"]

        # Check agent model metadata.
        if "model" not in data:
            raise ValueError('"model" key not found')
        model = Model(
            provider=data["model"].get("provider"),
            name=data["model"].get("name"),
            system_prompt=data["model"].get("system_prompt"),
        )

        # Check agent harness metadata.
        if "harness" not in data:
            raise ValueError('"harness" key not found')
        harness = Harness(tool_names=data["harness"].get("tools"))

        return cls(name, model, harness)


class TeamProfile(BaseModel):
    name: str
    agent_profiles: List[AgentProfile]


def get_team_profile(experiment_plan: Dict) -> TeamProfile:
    agent_profiles = []
    for agent_profile in experiment_plan["agents"]:
        try:
            agent_profiles.append(AgentProfile.from_dict(agent_profile))
        except ValueError as error:
            raise ValueError(
                f"{error} in agent profile #{experiment_plan.index(agent_profile) + 1}"
            ) from None
    return TeamProfile(name=experiment_plan["name"], agent_profiles=agent_profiles)
