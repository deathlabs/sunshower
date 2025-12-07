"""sunshower/experiments.py"""

# Standard library imports.
from enum import Enum
from typing import List

# Third party imports.
from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import Any, Dict, List


class Model(BaseModel):
    provider: str
    name: str
    system_prompt: str = Field(alias="systemPrompt")


class Harness(BaseModel):
    tool_names: List[str] = Field(default=[], alias="tools")
    tools: List[Any] = []

    def model_post_init(self, context: Any) -> None:
        self.tools = []
        for tool_name in self.tool_names:
            match tool_name:
                case "serper":
                    from langchain_community.utilities import GoogleSerperAPIWrapper

                    search = GoogleSerperAPIWrapper()
                    serper_tool = tool(name_or_callable="serper")(search.run)
                    self.tools.append(serper_tool)
                case "whois":
                    from whois import whois

                    whois_tool = tool(name_or_callable="whois")(whois)
                    self.tools.append(whois_tool)
                case _:
                    raise RuntimeError(f"unknown tool: {tool}")


class AgentProfile(BaseModel):
    name: str
    model: Model
    harness: Harness


class TeamProfile(BaseModel):
    name: str
    agent_profiles: List[AgentProfile] = Field(alias="agents")


class Metrics(str, Enum):
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    COST = "cost"
    PRECISION = "precision"
    PREFERENCES = "preferences"
    RECALL = "recall"
    SPEED = "speed"
    TRAJECTORY = "trajectory"


class JudgeProfile(AgentProfile):
    name: str
    model: Model
    metricsToEvaluate: Dict[Metrics, str]
    teamsToEvaluate: List[str]


class Spec(BaseModel):
    task: str
    rounds: int
    team_profiles: List[TeamProfile] = Field(alias="teams")


class Metadata(BaseModel):
    name: str
    description: str


class ExperimentSet(BaseModel):
    apiVersion: str = Field(..., pattern="^v1$")
    kind: str = Field(..., pattern="^ExperimentSet$")
    metadata: Metadata
    spec: Spec
