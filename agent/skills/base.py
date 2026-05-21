from abc import ABC, abstractmethod
from typing import Any
from agent.logger import get_logger


class Skill(ABC):
    name: str = "skill"
    cost_per_call_usd: float = 0.0

    def __init__(self) -> None:
        self.log = get_logger(f"mpl.agent.{self.name}")

    @abstractmethod
    def run(self, **kwargs) -> Any: ...
