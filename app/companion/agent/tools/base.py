"""Base tool class for AI Influencer Agent."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseTool(ABC):
    """Base class for all influencer agent tools."""

    name: str = "BaseTool"
    human_description: str = "Base tool description"
    agent_description: str = "Internal tool description for the agent"

    @abstractmethod
    def run(self, input_data: str, **kwargs) -> Any:
        """Run the tool with the given input.

        Args:
            input_data: The input to process
            **kwargs: Additional arguments

        Returns:
            The tool output
        """
        pass

    def __str__(self) -> str:
        return f"{self.name}: {self.human_description}"
