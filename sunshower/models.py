# Standard library imports.
from dataclasses import dataclass


@dataclass
class Model:
    provider: str
    name: str
    system_prompt: str

    def __post_init__(self) -> None:
        if not self.provider:
            raise ValueError('"provider" key cannot be empty')

        if not self.name:
            raise ValueError('"name" key cannot be empty')

        if not self.system_prompt:
            raise ValueError('"system_prompt" key cannot be empty')
